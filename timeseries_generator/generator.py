from itertools import product
from typing import List, Dict, Set, Optional

import pandas as pd

from timeseries_generator.base_factor import BaseFactor
from timeseries_generator.errors import FactorAlreadyExistsError, DuplicateNameError


class Generator:
    def __init__(
        self,
        factors: Set[BaseFactor],
        features: Optional[Dict[str, List[str]]] = None,
        date_range: pd.DatetimeIndex = None,
        base_value: float = 1.0,
    ):
        """
        Collects relevant features and creates a resulting DataFrame based on the selected features.

        Args:
            factors: factors that will be applied to the timeseries.
            features: features that will be taken into account in the timeseries generation.
            date_range: daterange of the resulting dataframe.
            base_value: base value of the resulting value of the time series. Mainly useful to give a correct order of
                magnitude to your resulting data.
        """
        if features is None:
            features = {}
        if date_range is None:
            pd.date_range(pd.datetime(1970, 1, 1), periods=50),
        self._factors = factors
        self._features = features
        self._base_value = base_value
        self._date_range = date_range
        self._ts = None

    @property
    def factors(self):
        return self._factors

    @factors.setter
    def factors(self, factors: Set[BaseFactor]):
        self._factors = factors

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, features: Dict[str, List[str]]):
        self._features = features

    @property
    def base_value(self):
        return self._base_value

    @base_value.setter
    def base_value(self, value: float):
        self._base_value = value

    @property
    def ts(self):
        return self._ts

    @ts.setter
    def ts(self, ts: pd.DataFrame):
        self._ts = ts

    def generate(self) -> pd.DataFrame:
        """
        generates synthetic time series data based on the input factors. Uses the generate method in the factors to
        obtain mergeable dataframes.

        Returns:
            DataFrame containing the feature labels and values.

        Raises:
            DuplicateNameError: when factors have overlapping names.
        """
        # generate a combination of date and features data
        ts: pd.DataFrame = pd.DataFrame(
            product(list(self._date_range), *self._features.values()),
            columns=["date"] + list(self._features.keys()),
        )

        # Add base amount
        ts["base_amount"] = self._base_value

        # Merge the factors on the base_df
        for f in self._factors:
            if f.apply_to_all:
                f.features = self._features  # apply all features to the factor
            df: pd.DataFrame = f.generate(
                start_date=self._date_range[0], end_date=self._date_range[-1]
            )
            if f.date_col_name != "date":
                df.rename(
                    columns={f.date_col_name: "date"}
                )  # rename date column to standard "date" name

            ts = ts.merge(
                df,
                how="left",
                on=list(f.features.keys()) + ["date"],  # Add date to merge columns
            ).fillna(
                1
            )  # Factor 1 means no effect

        factor_names = list(map(lambda factor: factor.col_name, self._factors))
        if len(factor_names) != len(set(factor_names)):
            raise DuplicateNameError(
                f'duplicate factor names in factor names: "{factor_names}"'
            )

        ts["total_factor"] = ts[factor_names].prod(axis=1)
        ts["value"] = ts["total_factor"] * ts["base_amount"]
        self._ts = ts

        return ts

    def plot(self):
        """
        plots the generated timeseries data
        """
        self._ts.plot(x="date", y="value", figsize=(24, 8))

    def add_factor(self, factor: BaseFactor):
        """
        Add factor to time series.

        Args:
            factor: factor to add to the generator.

        Raises:
             FactorAlreadyExistsError: when the factor already exists in the generator.
        """
        if factor.col_name in map(lambda f: f.col_name, self._factors):
            raise FactorAlreadyExistsError(
                f'factor "{factor}" already exists in generator '
                f"{self.__class__.__name__}."
            )
        self._factors.add(factor)

    def update_factor(self, factor: BaseFactor):
        """
        add or update factor to the time series.

        Args:
            factor: factor to add to the generator, or factor to update the definition of.
        """
        factors: Set[BaseFactor] = self._factors
        if factor.col_name in map(lambda f: f.col_name, self._factors):
            factors = set(
                filter(lambda f: f.col_name != factor.col_name, self._factors)
            )
        factors.add(factor)
        self._factors = factors
        return factors

    def remove_factor(self, factor: BaseFactor):
        """
        remove factor from time series.
        Args:
            factor: factor to remove from the generator.
        """
        self._factors.remove(factor)
