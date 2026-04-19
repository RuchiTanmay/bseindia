import unittest
from unittest.mock import patch

import pandas as pd

from bseindia.get_data import client_categorywise_turnover


class DummyResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


class CategorywiseTurnoverTests(unittest.TestCase):
    @patch("bseindia.get_data._request")
    def test_client_categorywise_turnover_normalizes_legacy_rows(self, request_mock):
        csv_text = "\n".join(
            [
                "Trade Date,Clients Buy,Clients Sales,Clients Net,NRI Buy,NRI Sales,NRI Net,Proprietary Buy,Proprietary Sales,Proprietary Net,IFIs Buy,IFIs Sales,IFIs Net,Banks Buy,Banks Sales,Banks Net,Insurance Buy,Insurance Sales,Insurance Net,DII(BSE + NSE + MCX-SX) Buy,DII(BSE + NSE + MCX-SX) Sales,DII(BSE + NSE + MCX-SX) Net,,,",
                "01-Dec-2004,1352.74,1408.46,-55.72,,,,586.72,554.39,32.33,17.49,29.61,-12.12,5.60,8.93,-3.34,,,,,,,",
            ]
        )
        request_mock.return_value = DummyResponse(text=csv_text)

        frame = client_categorywise_turnover(
            from_date="01-12-2004",
            to_date="01-12-2004",
            chunk_days=10000,
        )

        self.assertEqual(list(frame["REPORTING_DATE"]), ["01-12-2004"])
        self.assertEqual(frame.iloc[0]["SEGMENT"], "C")
        self.assertTrue(pd.isna(frame.iloc[0]["PURCHASE_NRI"]))
        self.assertAlmostEqual(frame.iloc[0]["PURCHASE_CLIENT"], 1352.74)
        self.assertAlmostEqual(frame.iloc[0]["NET_DFI"], -12.12)
        self.assertTrue(pd.isna(frame.iloc[0]["NET_DII_BSENSE"]))

    @patch("bseindia.get_data._request")
    def test_client_categorywise_turnover_maps_short_modern_header(self, request_mock):
        csv_text = "\n".join(
            [
                "Trade Date,Clients Buy,Clients Sales,Clients Net,NRI Buy,NRI Sales,NRI Net,Proprietary Buy,Proprietary Sales,Proprietary Net,DII(BSE + NSE + MCX-SX) Buy,DII(BSE + NSE + MCX-SX) Sales,DII(BSE + NSE + MCX-SX) Net,,,",
                "17-Apr-2026,3896.17,3986.64,-90.48,33.14,41.42,-8.28,3980.64,3642.09,338.55,17513.99,22235.47,-4721.48,,,,,,,,,",
            ]
        )
        request_mock.return_value = DummyResponse(text=csv_text)

        frame = client_categorywise_turnover(
            from_date="17-04-2026",
            to_date="17-04-2026",
            chunk_days=10000,
        )

        self.assertEqual(list(frame["REPORTING_DATE"]), ["17-04-2026"])
        self.assertTrue(pd.isna(frame.iloc[0]["NET_DFI"]))
        self.assertAlmostEqual(frame.iloc[0]["NET_DII_BSENSE"], -4721.48)


if __name__ == "__main__":
    unittest.main()
