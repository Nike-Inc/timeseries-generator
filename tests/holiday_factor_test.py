import unittest

from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator import HolidayFactor


class TestHolidayFactor(unittest.TestCase):

    def setUp(self) -> None:
        self.start_date = Timestamp("01-01-2018")
        self.end_date = Timestamp("01-01-2020")

    def testGenerate(self):
        holiday_factor = HolidayFactor(
            holiday_factor=2.,
            special_holiday_factors={
                "Thanksgiving Day": 10.
            }
        )
        df: DataFrame = holiday_factor.generate(start_date=self.start_date, end_date=self.end_date)
        self.assertAlmostEqual(2., df[holiday_factor.col_name].head(1).values[0])
