import requests
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
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


