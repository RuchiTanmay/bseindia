import csv
import datetime as dt
from io import BytesIO, StringIO

import pandas as pd
import requests
from bseindia.logger import *
from bseindia.libutil import *
from bseindia.libutil import _request
from bseindia.constants import *

logger = mylogger(logging.getLogger(__name__))

CATEGORY_TURNOVER_CSV_URL = "https://api.bseindia.com/BseIndiaAPI/api/StockPriceCSVDownload/w"
CATEGORY_TURNOVER_CREATE_YEAR_URL = "https://api.bseindia.com/BseIndiaAPI/api/CreateYear/w"
CATEGORY_TURNOVER_SEGMENTS = {"C", "EQT0", "D", "M"}
CATEGORY_TURNOVER_COLUMNS = [
    "REPORTING_DATE",
    "PURCHASE_CLIENT",
    "SALE_CLIENT",
    "NET_CLIENT",
    "PURCHASE_NRI",
    "SALE_NRI",
    "NET_NRI",
    "PURCHASE_OWN",
    "SALE_OWN",
    "NET_OWN",
    "PURCHASE_DFI",
    "SALE_DFI",
    "NET_DFI",
    "PURCHASE_BANK",
    "SALE_BANK",
    "NET_BANK",
    "PURCHASE_INSURANCE",
    "SALE_INSURANCE",
    "NET_INSURANCE",
    "PURCHASE_DII_BSENSE",
    "SALE_DII_BSENSE",
    "NET_DII_BSENSE",
    "SEGMENT",
]
CATEGORY_TURNOVER_HEADER_MAP = {
    "Clients Buy": "PURCHASE_CLIENT",
    "Clients Sales": "SALE_CLIENT",
    "Clients Net": "NET_CLIENT",
    "NRI Buy": "PURCHASE_NRI",
    "NRI Sales": "SALE_NRI",
    "NRI Net": "NET_NRI",
    "Proprietary Buy": "PURCHASE_OWN",
    "Proprietary Sales": "SALE_OWN",
    "Proprietary Net": "NET_OWN",
    "IFIs Buy": "PURCHASE_DFI",
    "IFIs Sales": "SALE_DFI",
    "IFIs Net": "NET_DFI",
    "Banks Buy": "PURCHASE_BANK",
    "Banks Sales": "SALE_BANK",
    "Banks Net": "NET_BANK",
    "Insurance Buy": "PURCHASE_INSURANCE",
    "Insurance Sales": "SALE_INSURANCE",
    "Insurance Net": "NET_INSURANCE",
    "DII(BSE + NSE + MCX-SX) Buy": "PURCHASE_DII_BSENSE",
    "DII(BSE + NSE + MCX-SX) Sales": "SALE_DII_BSENSE",
    "DII(BSE + NSE + MCX-SX) Net": "NET_DII_BSENSE",
}


def _empty_category_turnover_frame():
    return pd.DataFrame(columns=CATEGORY_TURNOVER_COLUMNS)


def _normalize_category_turnover_value(value):
    text = str(value).strip()
    if text in {"", "-", "--", "NA", "N/A", "None", "nan"}:
        return pd.NA
    return float(text.replace(",", ""))


def _coerce_history_date(value, label: str):
    if value is None or value == "":
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.datetime.strptime(str(value), dd_mm_yyyy).date()
    except ValueError as exc:
        raise ValueError(f"{label} should be in dd-mm-YYYY format") from exc


def _category_turnover_start_date():
    fallback = dt.date(2004, 1, 1)
    try:
        response = _request(CATEGORY_TURNOVER_CREATE_YEAR_URL)
        if response.status_code != 200:
            return fallback
        data = response.json()
        years = [int(item.get("YearValue")) for item in data if str(item.get("YearValue", "")).isdigit()]
        if not years:
            return fallback
        return dt.date(min(years), 1, 1)
    except Exception:
        return fallback


def _parse_category_turnover_csv(csv_text: str, segment: str):
    rows = [row for row in csv.reader(StringIO(csv_text)) if any(str(cell).strip() for cell in row)]
    if len(rows) <= 1:
        return _empty_category_turnover_frame()

    header_row = [str(cell).strip() for cell in rows[0]]
    records = []
    for raw_row in rows[1:]:
        row = list(raw_row)
        reporting_date = str(row[0]).strip() if row else ""
        if not reporting_date:
            continue
        parsed_date = pd.to_datetime(reporting_date, format="%d-%b-%Y", errors="coerce")
        if pd.isna(parsed_date):
            continue
        record = {column: pd.NA for column in CATEGORY_TURNOVER_COLUMNS}
        record["REPORTING_DATE"] = parsed_date.strftime("%d-%m-%Y")
        record["SEGMENT"] = segment
        record["__sort_date"] = parsed_date
        for index, header_name in enumerate(header_row):
            canonical_name = CATEGORY_TURNOVER_HEADER_MAP.get(header_name)
            if not canonical_name or index >= len(row):
                continue
            record[canonical_name] = _normalize_category_turnover_value(row[index])
        records.append(record)

    if not records:
        return _empty_category_turnover_frame()

    frame = pd.DataFrame.from_records(records)
    frame = frame.sort_values("__sort_date").drop_duplicates(subset=["REPORTING_DATE", "SEGMENT"], keep="last")
    frame = frame.drop(columns="__sort_date").reset_index(drop=True)
    return frame[CATEGORY_TURNOVER_COLUMNS]


def _download_category_turnover_chunk(from_date: dt.date, to_date: dt.date, segment: str):
    params = {
        "pageType": "1",
        "rbType": "D",
        "Scode": "",
        "FDates": from_date.strftime("%d/%m/%Y"),
        "TDates": to_date.strftime("%d/%m/%Y"),
        "Seg": segment,
    }
    try:
        data_obj = _request(CATEGORY_TURNOVER_CSV_URL, params=params)
        if data_obj.status_code != 200:
            raise NSEdataNotFound("Resource not available for client_categorywise_turnover")
    except Exception as exc:
        raise NSEdataNotFound(f"Resource not available MSG: {exc}") from exc
    return _parse_category_turnover_csv(data_obj.text, segment)


def historical_stock_data(symbol: str, from_date: str = None, to_date: str = None, period: str = None):
    """
    get historical Security wise price volume data set which is available in bse site.
    :param symbol: symbol eg: 'SBIN', use all_listed_securities() for list of symbol
    :param from_date: '17-03-2022' ('dd-mm-YYYY')
    :param to_date: '17-06-2023' ('dd-mm-YYYY')
    :param period: use one {'1D': last day data,'1W': for last 7 days data,
                            '1M': from last month same date, '6M': last 6 months data, '1Y': from last year same date)
    :return: pandas.DataFrame
    :raise ValueError if the parameter input is not proper
    """
    validate_date_param(from_date, to_date, period)
    from_date, to_date = derive_from_and_to_date(from_date=from_date, to_date=to_date, period=period)
    from_date = dt.datetime.strptime(from_date, dd_mm_yyyy)
    to_date = dt.datetime.strptime(to_date, dd_mm_yyyy)
    end_date = to_date.strftime(dd_mm_yyyy)
    start_date = from_date.strftime(dd_mm_yyyy)
    data_df = get_historical_stock_data(symbol=symbol, from_date=start_date, to_date=end_date)
    return data_df


def client_categorywise_turnover(
    from_date: str = None,
    to_date: str = None,
    segment: str = "C",
    chunk_days: int = 365,
):
    """
    Get BSE client categorywise turnover history from the Stock Price page's category-turnover report.
    :param from_date: optional start date in dd-mm-YYYY; defaults to earliest BSE category-turnover year
    :param to_date: optional end date in dd-mm-YYYY; defaults to today
    :param segment: one of {'C': Equity T+1, 'EQT0': Equity T+0, 'D': Debt/Others, 'M': MF/ETFs}
    :param chunk_days: daily history fetch window per request; defaults to 365 for reliable backfills
    :return: pandas.DataFrame
    """
    normalized_segment = str(segment).strip().upper()
    if normalized_segment not in CATEGORY_TURNOVER_SEGMENTS:
        raise ValueError(f"segment = {segment} is not a valid value")
    if int(chunk_days) < 1:
        raise ValueError("chunk_days should be greater than 0")

    history_start = _category_turnover_start_date()
    start_date = _coerce_history_date(from_date, "from_date") or history_start
    end_date = _coerce_history_date(to_date, "to_date") or dt.date.today()
    if start_date > end_date:
        raise ValueError("to_date should be greater than or equal to from_date")

    frames = []
    cursor = start_date
    chunk_delta = dt.timedelta(days=int(chunk_days) - 1)
    while cursor <= end_date:
        chunk_end = min(cursor + chunk_delta, end_date)
        frame = _download_category_turnover_chunk(cursor, chunk_end, normalized_segment)
        if not frame.empty:
            frames.append(frame)
        cursor = chunk_end + dt.timedelta(days=1)

    if not frames:
        return _empty_category_turnover_frame()

    data_df = pd.concat(frames, ignore_index=True)
    sort_order = pd.to_datetime(data_df["REPORTING_DATE"], format="%d-%m-%Y", errors="coerce")
    data_df = data_df.assign(__sort_date=sort_order)
    data_df = data_df.sort_values("__sort_date").drop_duplicates(subset=["REPORTING_DATE", "SEGMENT"], keep="last")
    data_df = data_df.drop(columns="__sort_date").reset_index(drop=True)
    return data_df[CATEGORY_TURNOVER_COLUMNS]


def categorywise_turnover(from_date: str = None, to_date: str = None, segment: str = "C", chunk_days: int = 365):
    """Backward-friendly alias for client_categorywise_turnover()."""
    return client_categorywise_turnover(
        from_date=from_date,
        to_date=to_date,
        segment=segment,
        chunk_days=chunk_days,
    )


def get_historical_stock_data(symbol: str, from_date: str, to_date: str):
    _url = "https://api.bseindia.com/BseIndiaAPI/api/StockPriceCSVDownload/w?pageType=0&rbType=D"
    start_date = from_date[0:2] + '/' + from_date[3:5] + '/' + from_date[6:10]
    end_date = to_date[0:2] + '/' + to_date[3:5] + '/' + to_date[6:10]
    security_code = get_scode_from_symbol(symbol)
    _payload = f"&Scode={security_code}&FDates={start_date}&TDates={end_date}&Seg=C"
    try:
        data_obj = requests.request("GET", _url + _payload, headers=header)
        if data_obj.status_code != 200:
            raise NSEdataNotFound(f" Resource not available for historical_stock_data")
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available MSG: {e}")
    data_dict = data_obj.content
    data_df = pd.read_csv(BytesIO(data_dict), index_col=False)
    data_df.columns = [name.replace(' ', '') for name in data_df.columns]
    data_df['Date'] = pd.to_datetime(data_df['Date'], format='%d-%B-%Y')
    data_df['Date'] = data_df['Date'].dt.strftime('%d-%m-%Y')
    return data_df


def equity_bhav_copy(trade_date: str):
    """
    get new CM-UDiFF Common Bhavcopy Final as per the traded date provided
    :param trade_date:
    :return: pandas dataframe
    """
    trade_date = dt.datetime.strptime(trade_date, dd_mm_yyyy)
    _url = 'https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_'
    _payload = f"{str(trade_date.strftime('%Y%m%d'))}_F_0000.CSV"
    try:
        data_obj = requests.request("GET", _url + _payload, headers=header)
        if data_obj.status_code != 200:
            raise NSEdataNotFound(f" equities_bhav_copy not available for {trade_date}")
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available MSG: {e}")
    data_dict = data_obj.content
    bhav_df = pd.read_csv(BytesIO(data_dict), index_col=False)
    return bhav_df


def derivative_bhav_copy(trade_date: str):
    """
    get new derivative UDiFF Bhavcopy Final as per the traded date provided
    :param trade_date:
    :return: pandas dataframe
    """
    trade_date = dt.datetime.strptime(trade_date, dd_mm_yyyy)
    _url = 'https://www.bseindia.com/download/Bhavcopy/Derivative/BhavCopy_BSE_FO_0_0_0_'
    _payload = f"{str(trade_date.strftime('%Y%m%d'))}_F_0000.CSV"
    try:
        data_obj = requests.request("GET", _url + _payload, headers=header)
        if data_obj.status_code != 200:
            raise NSEdataNotFound(f" equities_bhav_copy not available for {trade_date}")
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available MSG: {e}")
    data_dict = data_obj.content
    bhav_df = pd.read_csv(BytesIO(data_dict), index_col=False)
    return bhav_df


def stock_info(symbol: str):
    """
    get new derivative UDiFF Bhavcopy Final as per the traded date provided
    :symbol : stock symbol eg.'SBIN', 'TCS'
    :return: python dictionary
    """
    security_code = get_scode_from_symbol(symbol)
    _url = f'https://api.bseindia.com/BseIndiaAPI/api/ComHeadernew/w?quotetype=EQ&scripcode={security_code}&seriesid='
    try:
        data_obj = requests.request("GET", _url, headers=header)
        if data_obj.status_code != 200:
            raise NSEdataNotFound(f" bse stock information is not available for {symbol}")
        data_dict = data_obj.json()
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available please try after 10 minutes: {e}")
    return data_dict


if __name__ == '__main__':
    data = historical_stock_data(symbol='TCS', from_date='01-01-2004', to_date='01-07-2024')
    # data = historical_stock_data(symbol='TCS', period='1W')
    # data = equity_bhav_copy(trade_date='01-07-2024')
    # data = derivative_bhav_copy(trade_date='01-07-2024')
    # data = stock_info(symbol='TCS')
    print(data)
    print(data.columns)
