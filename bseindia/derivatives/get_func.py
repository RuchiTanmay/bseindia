import requests
import pandas as pd
import datetime as dt
from bs4 import BeautifulSoup
from io import StringIO, BytesIO
from bseindia.libutil import *


def _get_aspnet_state(soup):
    """Extract ASP.NET hidden fields needed for postback."""
    fields = {}
    for name in ("__VIEWSTATE", "__VIEWSTATEGENERATOR", "__EVENTVALIDATION"):
        tag = soup.find("input", {"name": name})
        if tag and tag.get("value") is not None:
            fields[name] = tag["value"]
    return fields


def get_market_summary(trade_date: str | None = None, timeout: int = 30):
    url = "https://www.bseindia.com/markets/Derivatives/DeriReports/DeriArchive_PG.aspx?flag=0"
    with requests.Session() as s:
        s.headers.update(header)

        # Step 1: GET the page (always needed, gives viewstate for postback too)
        r = s.get(url, timeout=timeout)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "lxml")

        # Step 2: If a specific date was requested, post it back
        if trade_date:
            state = _get_aspnet_state(soup)
            date_input = soup.find("input", {"id": "txtDate"}) or \
                         soup.find("input", {"name": lambda n: n and "txtDate" in n})
            if date_input is None:
                raise RuntimeError("Date input not found on page")

            payload = {
                **state,
                date_input["name"]: trade_date,
                "btnSubmit": "Submit",   # adjust if button name differs
            }
            r = s.post(url, data=payload, timeout=timeout)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "lxml")

        # Step 3: pandas parses every <table> on the page
        tables = pd.read_html(StringIO(str(soup)))
        if not tables:
            raise RuntimeError("No tables found on page")
    return tables


def get_bhav_copy(trade_date: str):
    trade_date = dt.datetime.strptime(trade_date, dd_mm_yyyy)
    _url = 'https://www.bseindia.com/download/Bhavcopy/Derivative/BhavCopy_BSE_FO_0_0_0_'
    _payload = f"{str(trade_date.strftime('%Y%m%d'))}_F_0000.CSV"
    try:
        data_obj = requests.request("GET", _url + _payload, headers=header)
        if data_obj.status_code != 200:
            raise NSEdataNotFound(f" equities_bhav_copy not available for {trade_date}")
    except Exception as e:
        raise NSEdataNotFound(f" Resource not available MSG: {e}")
    return data_obj.content


def get_investors_categorywise_turnover() -> pd.DataFrame:
    _url = "https://www.bseindia.com/markets/Derivatives/DeriReports/InvestorCategorywiseTurnover.aspx"
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
