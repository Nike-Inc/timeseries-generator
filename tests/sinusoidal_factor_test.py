import unittest

from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator import SinusoidalFactor


class TestSinusoidalFactor(unittest.TestCase):
    def setUp(self) -> None:
        self.start_date = Timestamp("01-01-2018")
        self.end_date = Timestamp("01-01-2020")

    def testGenerateOnAll(self):
        sf: SinusoidalFactor = SinusoidalFactor(wavelength=365., amplitude=1., phase=0., mean=1.)
        df: DataFrame = sf.generate(start_date=self.start_date, end_date=self.end_date)
        self.assertAlmostEqual(1., df[sf.col_name].values[0])

    def testGenerateOnFeature(self):
        sf: SinusoidalFactor = SinusoidalFactor(feature="my_feature", feature_values={
            "foo": {
                "wavelength": 365,
                "amplitude": 1.,
                "phase": 0.,
                "mean": 1.
            },
            "bar": {
                "wavelength": 365.,
                "amplitude": 1.,
                "phase": 365/4,
                "mean": 1.
            }
        })
        df: DataFrame = sf.generate(start_date=self.start_date, end_date=self.end_date)
        self.assertAlmostEqual(1., df[sf.col_name].head(1).values[0])
        self.assertAlmostEqual(2., df[sf.col_name].head(2).values[1])
