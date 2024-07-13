import pandas as pd
import datetime as dt
import requests
import ast
from io import BytesIO
from bseindia.logger import *
from bseindia.libutil import *
from bseindia.constants import *

logger = mylogger(logging.getLogger(__name__))


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
    from_date = datetime.strptime(from_date, dd_mm_yyyy)
    to_date = datetime.strptime(to_date, dd_mm_yyyy)
    end_date = to_date.strftime(dd_mm_yyyy)
    start_date = from_date.strftime(dd_mm_yyyy)
    data_df = get_historical_stock_data(symbol=symbol, from_date=start_date, to_date=end_date)
    return data_df


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
    trade_date = datetime.strptime(trade_date, dd_mm_yyyy)
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
    trade_date = datetime.strptime(trade_date, dd_mm_yyyy)
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
        data_str = data_obj.text
        data_dict = ast.literal_eval(data_str)
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available please try after 10 minutes: {e}")
    return data_dict


# if __name__ == '__main__':
    # data = historical_stock_data(symbol='TCS', from_date='01-01-2004', to_date='01-07-2024')
    # data = historical_stock_data(symbol='TCS', period='1W')
    # data = equity_bhav_copy(trade_date='01-07-2024')
    # data = derivative_bhav_copy(trade_date='01-07-2024')
    # data = stock_info(symbol='TCS')
    # print(data)
    # print(data.columns)
