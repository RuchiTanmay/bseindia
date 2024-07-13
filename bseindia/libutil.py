import os
from datetime import datetime, timedelta, date
from bseindia.logger import *
import numpy as np
from dateutil.relativedelta import relativedelta
import pandas as pd
from bseindia.constants import *

logger = mylogger(logging.getLogger(__name__))

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
                  period.upper() == '6M',
                  period.upper() == '1Y'
                  ]
    value = [today - timedelta(days=1),
             today - timedelta(weeks=1),
             today - relativedelta(months=1),
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
    mydir = os.getcwd()
    return mydir.split(r'\bselib', 1)[0]


def all_listed_securities():
    """
    Get all securities listed on bse as on JULY-2024
    :return: DataFrame of all listed securities
    """
    logger.info('Get all securities as of JULY-2024')
    path = get_bselib_path() + "\\bseindia\\bseindia\\bse_security_list.csv"
    data_df = pd.read_csv(path, delimiter=',')
    return data_df


def get_scode_from_symbol(symbol):
    """
    get security code from symbol
    :param symbol:
    :return:
    """
    df = all_listed_securities()
    return df[df['symbol'] == symbol]['security_code'].values[0]


def convert_date_format_1(in_date: str):
    """
    convert date string to date format (01%2F07%2F2022)
    :param in_date:
    :return:
    """
    return in_date[0:1] + '%2F' + in_date[2:3] + '%2F' + in_date[4:7]


# if __name__ == '__main__':
    # data = derive_from_and_to_date('6M')
    # print(all_listed_securities())
