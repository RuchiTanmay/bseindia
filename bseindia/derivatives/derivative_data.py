from bseindia.derivatives.get_func import *


def market_summary():
    """
    Fetch BSE overall market summary on that date.
    :returns index_df, equity_df
    """
    tables = get_market_summary()
    result = {}
    for i, df in enumerate(tables):
        df = df.dropna(how="all").dropna(axis=1, how="all")
        if df.empty:
            continue
        # The derivatives summary page usually has:
        #   - Index F&O summary
        #   - Equity F&O summary
        result[f"table_{i}"] = df
    return result["table_1"], result["table_3"]


def derivative_bhav_copy(trade_date: str):
    """
    get new derivative UDiFF Bhavcopy Final as per the traded date provided
    :param trade_date:
    :return: pandas dataframe
    """
    data_dict = get_bhav_copy(trade_date=trade_date)
    bhav_df = pd.read_csv(BytesIO(data_dict), index_col=False)
    return bhav_df


if __name__ == "__main__":
    # df_index, df_equity = market_summary()
    # print(df_index, df_equity)
    data = derivative_bhav_copy(trade_date='01-07-2024')
    print(data)
