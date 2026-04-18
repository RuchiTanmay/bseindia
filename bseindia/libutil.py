import html
import re
from datetime import datetime, timedelta, date
from io import StringIO
from pathlib import Path

import requests
from bseindia.logger import *
import numpy as np
from dateutil.relativedelta import relativedelta
import pandas as pd
from bseindia.constants import *

logger = mylogger(logging.getLogger(__name__))

PACKAGE_DIR = Path(__file__).resolve().parent
SECURITY_CACHE_PATH = PACKAGE_DIR / "bse_security_list.csv"
SECURITY_MASTER_URL = "https://api.bseindia.com/BseIndiaAPI/api/LitsOfScripCSVDownload/w"
SMART_SEARCH_URL = "https://api.bseindia.com/BseIndiaAPI/api/ListScripSmartSearch/w"
TRADING_HOLIDAY_URL = "https://www.bseindia.com/static/markets/marketinfo/listholi.aspx/1000"

header = {
    "Connection": "keep-alive",
    "Cache-Control": "max-age=0",
    "DNT": "1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/111.0.0.0 Safari/537.36",
    "Sec-Fetch-User": "?1", "Accept": "*/*", "Sec-Fetch-Site": "none", "Sec-Fetch-Mode": "navigate",
    "Accept-Encoding": "gzip, deflate, br", "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
    "Referer": "https://www.bseindia.com/"
    }


class CalenderNotFound(Exception):
    def __init__(self, message):

        # Call the base class constructor with the parameters it needs
        super(CalenderNotFound, self).__init__(message)


class NSEdataNotFound(Exception):
    def __init__(self, message):
        super(NSEdataNotFound, self).__init__(message)


def validate_date_param(from_date: str, to_date: str, period: str):
    if not period and (not from_date or not to_date):
        raise ValueError(' Please provide the valid parameters')
    elif period and period.upper() not in equity_periods:
        raise ValueError(f'period = {period} is not a valid value')

    try:
        if not period:
            from_date = datetime.strptime(from_date, dd_mm_yyyy)
            to_date = datetime.strptime(to_date, dd_mm_yyyy)
            time_delta = (to_date - from_date).days
            if time_delta < 1:
                raise ValueError(f'to_date should greater than from_date ')
    except Exception as e:
        print(e)
        raise ValueError(f'either or both from_date = {from_date} || to_date = {to_date} are not valid value')


def derive_from_and_to_date(from_date: str = None, to_date: str = None, period: str = None):
    if not period:
        return from_date, to_date
    today = date.today()
    conditions = [period.upper() == '1D',
                  period.upper() == '1W',
                  period.upper() == '1M',
                  period.upper() == '3M',
                  period.upper() == '6M',
                  period.upper() == '1Y'
                  ]
    value = [today - timedelta(days=1),
             today - timedelta(weeks=1),
             today - relativedelta(months=1),
             today - relativedelta(months=3),
             today - relativedelta(months=6),
             today - relativedelta(months=12)]

    f_date = np.select(conditions, value, default=(today - timedelta(days=1)))
    from_date = pd.to_datetime(str(f_date)).strftime(dd_mm_yyyy)
    today = today.strftime(dd_mm_yyyy)
    return from_date, today


def cleaning_column_name(col: list):
    unwanted_str_list = ['FH_', 'EOD_', 'HIT_']
    new_col = col
    for unwanted in unwanted_str_list:
        new_col = [name.replace(f'{unwanted}', '') for name in new_col]
    return new_col


def convert_date_format(date_str, in_format, out_format):
    date_obj = datetime.strptime(date_str, in_format)
    return date_obj.strftime(out_format)


def get_bselib_path():
    """
    Extract bseindia installed path
    """
    return str(PACKAGE_DIR.parent)


def _request(url: str, **kwargs):
    return requests.get(url, headers=header, timeout=30, **kwargs)


def _normalize_security_frame(data_df: pd.DataFrame):
    if data_df is None or data_df.empty:
        return pd.DataFrame(
            columns=[
                'security_code',
                'issuer_name',
                'symbol',
                'security_name',
                'status',
                'group',
                'face_value',
                'isin_no',
                'instrument',
            ]
        )

    frame = data_df.copy()
    rename_map = {
        'Security Code': 'security_code',
        'Issuer Name': 'issuer_name',
        'Security Id': 'symbol',
        'Security Name': 'security_name',
        'Status': 'status',
        'Group': 'group',
        'Face Value': 'face_value',
        'ISIN No': 'isin_no',
        'Instrument': 'instrument',
    }
    frame.rename(columns=rename_map, inplace=True)
    expected_columns = list(rename_map.values())
    for column in expected_columns:
        if column not in frame.columns:
            frame[column] = None
    frame = frame[expected_columns].copy()

    for column in ['security_code', 'issuer_name', 'symbol', 'security_name', 'status', 'group', 'face_value', 'isin_no', 'instrument']:
        frame[column] = frame[column].astype(str).str.strip()

    frame['symbol'] = frame['symbol'].str.upper()
    frame = frame[(frame['security_code'] != '') & (frame['security_code'].str.lower() != 'nan')]
    frame = frame[(frame['symbol'] != '') & (frame['symbol'].str.lower() != 'nan')]
    frame = frame.drop_duplicates(subset=['security_code'], keep='first').reset_index(drop=True)
    return frame


def _read_security_cache():
    if not SECURITY_CACHE_PATH.exists():
        return pd.DataFrame()
    return _normalize_security_frame(pd.read_csv(SECURITY_CACHE_PATH))


def _write_security_cache(data_df: pd.DataFrame):
    normalized = _normalize_security_frame(data_df)
    if normalized.empty:
        return normalized
    normalized.to_csv(SECURITY_CACHE_PATH, index=False)
    return normalized


def _download_security_master():
    response = _request(
        SECURITY_MASTER_URL,
        params={'segment': 'Equity', 'status': '', 'Group': '', 'Scripcode': ''},
    )
    if response.status_code != 200:
        raise NSEdataNotFound('BSE security master is not available')
    data_df = pd.read_csv(StringIO(response.text), usecols=range(9), index_col=False, engine='python')
    return _write_security_cache(data_df)


def _extract_search_candidates(fragment: str):
    matches = re.findall(r"<li.*?liclick\('(\d+)','([^']*)'\).*?<span>(.*?)</span>.*?</li>", fragment, flags=re.IGNORECASE | re.DOTALL)
    candidates = []
    for security_code, security_name, span_html in matches:
        span_text = html.unescape(re.sub(r'<[^>]+>', ' ', span_html))
        span_text = re.sub(r'\s+', ' ', span_text.replace('#', ' ')).strip()
        symbol = span_text.split(' ')[0].upper() if span_text else ''
        candidates.append(
            {
                'security_code': security_code.strip(),
                'security_name': html.unescape(security_name).strip(),
                'symbol': symbol,
            }
        )
    return candidates


def _lookup_security_in_live_search(symbol: str):
    response = _request(SMART_SEARCH_URL, params={'text': symbol, 'Flag': 'liclick'})
    if response.status_code != 200:
        raise NSEdataNotFound(f'BSE smart search is not available for {symbol}')
    fragment = response.json()
    if not isinstance(fragment, str):
        raise NSEdataNotFound(f'Unexpected BSE smart search response for {symbol}')
    candidates = _extract_search_candidates(fragment)
    exact_symbol_matches = [candidate for candidate in candidates if candidate['symbol'] == symbol]
    if exact_symbol_matches:
        return exact_symbol_matches[0]
    if candidates:
        return candidates[0]
    raise NSEdataNotFound(f'No BSE security code found for {symbol}')


def all_listed_securities(refresh: bool = False):
    """
    Get the live BSE equity security master and cache it locally.
    :return: DataFrame of all listed securities
    """
    logger.info('Get BSE listed securities')
    if not refresh:
        cached_df = _read_security_cache()
        if not cached_df.empty:
            return cached_df
    try:
        return _download_security_master()
    except Exception as exc:
        cached_df = _read_security_cache()
        if not cached_df.empty:
            logger.warning(f'Using cached BSE security master due to live fetch failure: {exc}')
            return cached_df
        raise


def get_scode_from_symbol(symbol):
    """
    get security code from symbol
    :param symbol:
    :return:
    """
    normalized_symbol = str(symbol).strip().upper()
    if normalized_symbol.isdigit():
        return normalized_symbol

    df = all_listed_securities()
    exact_match = df[df['symbol'].str.upper() == normalized_symbol]
    if not exact_match.empty:
        return exact_match.iloc[0]['security_code']

    live_match = _lookup_security_in_live_search(normalized_symbol)
    updated_df = pd.concat([df, pd.DataFrame([live_match])], ignore_index=True)
    _write_security_cache(updated_df)
    return live_match['security_code']


def convert_date_format_1(in_date: str):
    """
    convert date string to date format (01%2F07%2F2022)
    :param in_date:
    :return:
    """
    return in_date[0:1] + '%2F' + in_date[2:3] + '%2F' + in_date[4:7]


def trading_holiday_calendar(year: int = None):
    """
    Get BSE trading holidays for the equity segment from the official BSE holiday page.
    :param year: optional calendar year filter
    :return: DataFrame with SI.NO., Holidays, Date, Day
    """
    response = _request(TRADING_HOLIDAY_URL)
    if response.status_code != 200:
        raise CalenderNotFound('BSE trading holiday calendar not available')

    tables = pd.read_html(StringIO(response.text))
    for table in tables:
        if table.shape[1] != 4:
            continue
        header_row = [str(value).strip() for value in table.iloc[0].tolist()]
        if 'Holidays' not in header_row or 'Date' not in header_row or 'Day' not in header_row:
            continue
        calendar_df = table.copy()
        calendar_df.columns = header_row
        calendar_df = calendar_df.iloc[1:].dropna(how='all').reset_index(drop=True)
        calendar_df = calendar_df[['SI.NO.', 'Holidays', 'Date', 'Day']].copy()
        calendar_df['Date'] = calendar_df['Date'].astype(str).str.strip()
        parsed_date = pd.to_datetime(calendar_df['Date'], format='%d-%b-%y', errors='coerce')
        if year is not None:
            calendar_df = calendar_df[parsed_date.dt.year == int(year)].reset_index(drop=True)
        return calendar_df
    raise CalenderNotFound('Unable to parse BSE trading holiday calendar')


# if __name__ == '__main__':
    # data = derive_from_and_to_date('6M')
    # print(all_listed_securities())
