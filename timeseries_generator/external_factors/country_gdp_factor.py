from pathlib import Path
from typing import Optional, List

from pandas import DataFrame, to_datetime, read_csv
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.external_factors.external_factor import ExternalFactor


MIN_DATE = Timestamp("01-01-1960")
MAX_DATE = Timestamp("12-31-2020")


class CountryGdpFactor(ExternalFactor):
    def __init__(
        self,
        col_name: str = "country_gdp_factor",
        country_feature_name: Optional[str] = None,
        country_list: Optional[List[str]] = None,
    ):
        """
        This factor uses GDP per capita to generate yearly trend.

        Raw GDP per captia data is downloaded from GDP per capita (GDPPC):
        https://api.worldbank.org/v2/en/indicator/NY.GDP.PCAP.CD?downloadformat=excel

            An example dataframe as Country trend:
            date        country       factor
            2020-01-01  Netherlands   0.76
            2020-02-01  Netherlands   0.76
            2020-01-01  Italy         0.34
            2020-02-01  Italy         0.34
            ...

        Args:
            col_name: column name of the feature.
            country_feature_name: customized name of the feature. Defaults to "country".
            country_list: List of countries included in the feature.

        """

        if country_feature_name is None:
            country_feature_name = "country"

        if country_list is None:
            country_list = ["Netherlands", "Italy", "Romania"]

        super().__init__(
            features={country_feature_name: country_list},
            col_name=col_name,
            min_date=MIN_DATE,
            max_date=MAX_DATE,
        )

    def load_data(self) -> DataFrame:
        """
        Load GDPPC data, and prepare for 10 year history
        """
        df = read_csv(
            Path(__file__).parent.parent
            / "resources"
            / "public_data"
            / "GDP_per_capita_countries.csv",
            encoding="utf-8-sig",
        )

        # use GDP per capita of NL in 2015 as the base amount to normalize GDPPC data
        base_gdppc_amount = df.loc[df["Country Name"] == "Netherlands"]["2015"].values[
            0
        ]

        # pick up the countries
        df = df[df["Country Name"].isin(self.features[iter(self.features).__next__()])]
        df = df.set_index("Country Name")

        # transpose the dataframe, so that each row is a year. Remove headers
        df = df.T[3:]

        # set year as datetime type
        df.index = to_datetime(df.index, format="%Y")

        # get daily sample and forward fill
        df = df.resample("D").ffill()

        df = df.stack().reset_index()
        df.columns = [self._date_col_name, "country", self._col_name]

        # normalize the country GDPPC by NL 2015 GDP
        df[self._col_name] = df[self._col_name] / base_gdppc_amount

        return df
