from pandas import DataFrame
from bseindia.equity.get_func import *


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


def stock_info(symbol: str) -> dict:
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


def equity_bhav_copy(trade_date: str):
    """
    get new CM-UDiFF Common Bhavcopy Final as per the traded date provided
    :param trade_date:
    :return: pandas dataframe
    """
    data_dict = get_equity_bhav_copy(trade_date=trade_date)
    bhav_df = pd.read_csv(BytesIO(data_dict), index_col=False)
    return bhav_df


def equity_turnover() -> pd.DataFrame:
    """
    get turnover on the equity section on bse site
    :return:
    """
    return get_equity_turnover()


def equity_segment_history() -> pd.DataFrame:
    """
    Fetch BSE Equity Segment yearly historical summary
    (listed companies, trades, turnover, etc. from 1997-98 onwards).
    """
    return get_equity_segment_history()


def category_wise_turnover(period: str = 'monthly', month: str = '01', year:str = '2026',
                           from_date:str = '01-04-2026', to_date:str = '30-03-2026'):
    r = get_category_wise_turnover(period=period, month=month, year=year, from_date=from_date, to_date=to_date)
    df = r.json()
    return pd.DataFrame(df['CatStockData'])


def market_cap() -> pd.DataFrame:
    """
    Fetch BSE yearly market capitalisation key statistics.
    Returns a DataFrame with Year + segment-wise market cap columns.
    """
    return get_market_cap()


def market_capitalisation() -> pd.DataFrame:
    """
    Fetch BSE current market capitalisation by instrument type
    (Equity, REIT/INVIT, ETF, Mutual Funds, Corporate Bonds, Commercial Paper).
    Values in ₹ Crores.
    """
    _url = "https://www.bseindia.com/markets/Equity/EQReports/MarketCapitalisation.aspx"
    r = bse_urlfetch(_url)
    data_df = pd.read_html(StringIO(r.text))[2]
    data_df = data_df.drop(columns='Sr.No.')
    return data_df.reset_index(drop=True)


def top_market_cap() -> list[DataFrame]:
    """
    Fetch BSE's top market-capitalisation table.
    """
    _url = "https://www.bseindia.com/markets/equity/EQReports/TopMarketCapitalization.aspx"
    r = bse_urlfetch(_url)
    data_df = pd.read_html(StringIO(r.text))[2][0:100]
    return data_df


def gross_delivery(trade_date) -> pd.DataFrame:
    df = get_gross_delivery(trade_date=trade_date)
    df = df.dropna(axis=1, how="all")
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    df["DATE"] = pd.to_datetime(df["DATE"], format="%d%m%Y")
    numeric_cols = ["SCRIP CODE", "DELIVERY QTY", "DELIVERY VAL",
                    "DAY'S VOLUME", "DAY'S TURNOVER", "DELV. PER."]
    for c in numeric_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    return df.reset_index(drop=True)


def bulk_deal_as_on_today() -> DataFrame:
    """
    Fetch BSE's bulk deals
    """
    _url = "https://www.bseindia.com/markets/equity/EQReports/bulk_deals.aspx"
    r = bse_urlfetch(_url)
    data_df = pd.read_html(StringIO(r.text))[1]
    return data_df


def block_deal_as_on_today() -> DataFrame:
    """
    Fetch BSE's bulk deals
    """
    _url = "https://www.bseindia.com/markets/equity/EQReports/block_deals.aspx"
    r = bse_urlfetch(_url)
    data_df = pd.read_html(StringIO(r.text))[1]
    return data_df


# if __name__ == "__main__":
    # data = historical_stock_data(symbol='TCS', from_date='01-01-2004', to_date='01-07-2024')
    # data = stock_info(symbol='TCS')
    # data = equity_bhav_copy(trade_date='01-07-2025')
    # data = get_equity_turnover()
    # data = get_equity_segment_history()
    # data = get_category_wise_turnover(period='yearly', month='01', year='2026', from_date="01-04-2025", to_date="10-04-2025")
    # data = get_market_cap()
    # data = market_capitalisation()
    # data = top_market_cap()
    # data = get_gross_delivery("21-04-2026")
    # data = bulk_deal_as_on_today()
    # data = block_deal_as_on_today()
    # print(data)

