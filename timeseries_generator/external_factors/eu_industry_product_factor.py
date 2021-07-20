from pathlib import Path

from pandas import read_csv, to_datetime, DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.external_factors.external_factor import ExternalFactor


MIN_DATE = Timestamp("01-01-2000")
MAX_DATE = Timestamp("10-31-2020")


class EUIndustryProductFactor(ExternalFactor):
    def __init__(self, col_name="eu_industry_product_factor", intensive_scale=1):
        """
        This component use EU industry product index to generate a monthly trend
        The raw data is downloaded from https://sdw.ecb.europa.eu/quickview.do;jsessionid=8AE7EC2C574223EB1E7713897E7B7190?SERIES_KEY=132.STS.M.I8.Y.PROD.NS0020.4.000&start=&end=31-12-2020&submitOptions.x=0&submitOptions.y=0&trans=N

        An example dataframe as GlobalEcoTrendComponents trend:
        date        country       factor
        2020-01-01  Netherlands   0.76
        2020-02-01  Netherlands   0.76
        2020-01-01  Italy         0.34
        2020-02-01  Italy         0.34
        ...

        Args:
            col_name: column name of the factor

        """
        super().__init__(col_name=col_name, min_date=MIN_DATE, max_date=MAX_DATE)
        self._intensive_sale = intensive_scale

    def load_data(self) -> DataFrame:
        df = read_csv(
            Path(__file__).parent.parent
            / "resources"
            / "public_data"
            / "eu_prod_index.csv",
            names=[self._date_col_name, "value", "is_estimated"],
        )

        df[self._date_col_name] = to_datetime(df[self._date_col_name], format="%Y-%m")
        df = df.set_index(self._date_col_name)

        # get daily sample and forward fill
        df = df.resample("D").ffill()

        # reset index and rename
        df = df.reset_index()
        df = df.drop(axis=1, columns="is_estimated")
        df.columns = [self._date_col_name, self._col_name]

        # normalize the industry product index
        df[self._col_name] = df[self._col_name] / 100 * self._intensive_sale

        return df
