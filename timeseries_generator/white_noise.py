import itertools
from typing import Optional, Dict

from numpy.random.mtrand import randn
from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.base_factor import BaseFactor
from timeseries_generator.utils import get_cartesian_product


FeatureValues = Dict[str, Dict[str, float]]


class WhiteNoise(BaseFactor):
    def __init__(
        self,
        stdev_factor: float = 0.05,
        feature_values: Optional[FeatureValues] = None,
        col_name: str = "white_noise",
    ):
        """
        Add white noise to the timeseries. The noise component will have a bell-shaped distribution, based on the input
        standard deviation.

        Args:
            stdev_factor: standard deviation of the factor random noise component. Do not supply when specifying
                feature_values
            feature_values: dictionary with the feature name as key and a dictionaty as value. This dictionaty contains
                the feature values as keys and the stdev_factors as values.
            col_name: name of the factor column.

        Raises:
            AttributeError when stdev_factor and feature_values are set, or when more then one feature gets a unique
            noise factor.

        Examples:
            This can either act on all features in the same way:
                >>> WhiteNoise(stdev_factor=0.05, col_name="White Noise")

            Or can be specified per feature value:
                >>> WhiteNoise(feature_values={
                ...     "my_feature": {
                ...         "feature1": 0.05,
                ...         "feature2": 0.10
                ...     }
                ... })
        """

        if (stdev_factor and feature_values) or not (stdev_factor or feature_values):
            raise AttributeError("Either set `stdev_factor` or `feature_values`")
        if feature_values:
            if len(feature_values) > 1:
                raise AttributeError(
                    f"{self.__class__.__name__}, can only set feature values on one feature"
                )
            features = feature_values
            apply_to_all = False
        else:
            features = None
            apply_to_all = True  # random noise applied to all factors

        super().__init__(
            col_name=col_name, features=features, apply_to_all=apply_to_all
        )
        self._stdev_factor = stdev_factor
        self._feature_values = feature_values

    @property
    def stdev_factor(self):
        return self._stdev_factor

    @stdev_factor.setter
    def stdev_factor(self, f):
        self._stdev_factor = f

    @property
    def feature_values(self) -> Optional[FeatureValues]:
        return self._feature_values

    @feature_values.setter
    def feature_values(self, feature_values: Optional[FeatureValues]):
        if len(feature_values) > 1:
            raise AttributeError(
                f"{self.__class__.__name__}, can only set feature values on one feature"
            )
        self._feature_values = feature_values

    def generate(self, start_date: Timestamp, end_date: Timestamp = None) -> DataFrame:
        dr: DataFrame = self.get_datetime_index(
            start_date=start_date, end_date=end_date
        ).to_frame(index=False, name=self._date_col_name)

        if self._features:
            # Using self.features here gets all the features from the generator
            df: DataFrame = DataFrame(
                itertools.product(*self._features.values()),
                columns=list(self._features.keys()),
            )
            factor_df = get_cartesian_product(dr, df)
            if self._feature_values:
                feature: str = iter(
                    self._feature_values
                ).__next__()  # len(self._features is always 1)
                factor_df["noise_1"] = randn(len(factor_df))

                def get_factor_col(row):
                    stdev_factor: float = self._feature_values[feature][row[feature]]
                    return stdev_factor * row["noise1"] + 1

                factor_df[self._col_name] = factor_df.apply(
                    get_factor_col, axis=1
                ).drop("noise1", axis=1)
            else:
                factor_df[self._col_name] = (
                    self._stdev_factor * randn(len(factor_df)) + 1
                )

        else:
            # self._features can be none if used outside of generator
            df: DataFrame = DataFrame(
                self._stdev_factor * randn(len(dr)) + 1, columns=[self._col_name]
            )
            factor_df = dr.join(df)

        return factor_df
