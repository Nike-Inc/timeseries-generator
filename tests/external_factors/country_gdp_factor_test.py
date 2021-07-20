import unittest
from typing import List

from pandas import DataFrame

from timeseries_generator.external_factors import CountryGdpFactor


class TestCountryGdpFactor(unittest.TestCase):

    def test_loading(self):
        country_list: List[str] = ["Netherlands", "Belgium"]
        cgf: CountryGdpFactor = CountryGdpFactor(country_list=country_list)
        df: DataFrame = cgf.generate("01-01-2018", "01-01-2020")
        self.assertEqual(set(country_list), set(df["country"].unique()).intersection(set(country_list)))
