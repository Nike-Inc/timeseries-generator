import unittest
from typing import List, Dict

from pandas import date_range
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator import SinusoidalFactor, Generator


class TestGenerator(unittest.TestCase):
    def setUp(self) -> None:
        self.start_date: Timestamp = Timestamp("01-01-2018")
        self.end_date: Timestamp = Timestamp("01-01-2020")
        self.features_dict: Dict[str, List[str]] = {
            "country": ["Netherlands", "Italy", "Romania"],
            "store": ["store1", "store2", "store3"],
            "product": ["winter jacket", "Yoga Mat", "basketball top"]
        }
        self.product_seasonal_components: SinusoidalFactor = SinusoidalFactor(
            feature="product",
            col_name="product_seasonal_trend_factor",
            feature_values={
                "winter jacket": {
                    "wavelength": 365.,
                    "amplitude": 0.2,
                    "phase": 365 / 4,
                    "mean": 1.
                },
                "basketball top": {
                    "wavelength": 365.,
                    "amplitude": 0.2,
                    "phase": 0.,
                    "mean": 1.
                }
            }
        )

    def testGeneratorForUnrepresentedFeatures(self):
        """
        test whether values unrepresented in a certain feature still show up with factor 1
        """
        g: Generator = Generator(
            factors={
                self.product_seasonal_components
            },
            features=self.features_dict,
            date_range=date_range(start=self.start_date, end=self.end_date),
            base_value=1
        )
        self.assertEqual(len(self.features_dict), len(g.generate()["product"].unique()))
