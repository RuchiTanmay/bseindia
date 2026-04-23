from urllib.parse import quote
import datetime as dt
import zipfile
from io import StringIO, BytesIO
from bseindia.libutil import *


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


def get_equity_bhav_copy(trade_date: str):
    trade_date = dt.datetime.strptime(trade_date, dd_mm_yyyy)
    _url = 'https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_'
    _payload = f"{str(trade_date.strftime('%Y%m%d'))}_F_0000.CSV"
    try:
        data_obj = requests.request("GET", _url + _payload, headers=header)
        if data_obj.status_code != 200:
            raise NSEdataNotFound(f" equities_bhav_copy not available for {trade_date}")
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available MSG: {e}")
    return data_obj.content


def get_equity_turnover() -> pd.DataFrame:
    _url = "https://www.bseindia.com/markets/keystatics/Keystat_turnoverequity.aspx"
    r = bse_urlfetch(_url)
    all_dfs = pd.read_html(StringIO(r.text))
    candidates = [
        df for df in all_dfs
        if any("year" in str(c).lower() for c in df.columns)
        or any("year" in str(v).lower() for v in df.iloc[0].values)
    ]
    if not candidates:
        candidates = all_dfs   # fallback
    df = max(candidates, key=lambda x: x.shape[0])
    if not any("year" in str(c).lower() for c in df.columns):
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(c) for c in col).strip() for col in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    df = df.reset_index(drop=True)
    return df


def get_equity_segment_history(timeout: int = 30) -> pd.DataFrame:
    _url = "https://www.bseindia.com/markets/Equity/EQReports/Historical_EquitySegment.aspx"
    r = bse_urlfetch(_url)

    all_dfs = pd.read_html(StringIO(r.text))

    # Pick the dataframe that has a "Year" column and the most rows
    candidates = [
        df for df in all_dfs
        if any("year" in str(c).lower() for c in df.columns)
        or any("year" in str(v).lower() for v in df.iloc[0].values)
    ] or all_dfs

    df = max(candidates, key=lambda x: x.shape[0])
    # If header landed in row 0, promote it
    if not any("year" in str(c).lower() for c in df.columns):
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(c) for c in col).strip() for col in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    return df.reset_index(drop=True)


def get_category_wise_turnover(period: str = 'monthly', month: str = '01', year:str = '2026',
                               from_date:str = '01-04-2026', to_date:str = '30-03-2026'):
    if period == 'monthly' and month and year :
        url = f"https://api.bseindia.com/BseIndiaAPI/api/StockpricesearchData/w?MonthDate={month}"\
              f"&Scode=&Seg=C&YearDate={year}&pageType=1&rbType=M"
    elif period == 'yearly' and year:
        url = f"https://api.bseindia.com/BseIndiaAPI/api/StockpricesearchData/w?MonthDate=&Scode=&Seg=C&YearDate={year}&pageType=1&rbType=Y"
    elif from_date and to_date:
        url = f"https://api.bseindia.com/BseIndiaAPI/api/StockpricesearchData/w?MonthDate={quote(from_date.replace('-', '/'), safe='')}"\
              f"&Scode=&Seg=C&YearDate={quote(to_date.replace('-', '/'), safe='')}&pageType=1&rbType=D"
    else:
        raise ValueError(f" Bad parameter: please validate the parameters")
    referer_url = "https://www.bseindia.com/markets/equity/EQReports/StockPrcHistori.html?flag=1"
    return bse_urlfetch(url, get_custom_header(referer=referer_url))


def get_market_cap() -> pd.DataFrame:
    _url = "https://www.bseindia.com/markets/keystatics/Keystat_maktcap.aspx"
    r = bse_urlfetch(_url)
    all_dfs = pd.read_html(StringIO(r.text))
    candidates = [
        df for df in all_dfs
        if any("year" in str(c).lower() for c in df.columns)
        or any("year" in str(v).lower() for v in df.iloc[0].values)
    ] or all_dfs
    df = max(candidates, key=lambda x: x.shape[0] * x.shape[1])
    if not any("year" in str(c).lower() for c in df.columns):
        df.columns = df.iloc[0]
        df = df.iloc[1:].reset_index(drop=True)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [" ".join(str(c) for c in col).strip() for col in df.columns]
    df.columns = [str(c).strip() for c in df.columns]
    return df.reset_index(drop=True)


def get_gross_delivery(trade_date) -> pd.DataFrame:
    d = parse_date(trade_date)
    url = f"https://www.bseindia.com/BSEDATA/gross/{d.year}/SCBSEALL{d.strftime('%d%m')}.zip"
    r = bse_urlfetch(url)

    with zipfile.ZipFile(BytesIO(r.content)) as zf:
        with zf.open(zf.namelist()[0]) as f:
            raw = f.read()

    df = pd.read_csv(BytesIO(raw), sep="|", dtype=str)
    df.columns = [c.strip() for c in df.columns]
    return df
