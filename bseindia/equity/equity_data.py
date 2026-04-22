import datetime as dt
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


if __name__ == "__main__":
    # data = historical_stock_data(symbol='TCS', from_date='01-01-2004', to_date='01-07-2024')
    # data = stock_info(symbol='TCS')
    data = equity_bhav_copy(trade_date='01-07-2025')
    print(data)
