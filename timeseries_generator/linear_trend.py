from typing import Optional, Dict, Union

from numpy.ma import arange
from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.base_factor import BaseFactor
from timeseries_generator.utils import get_cartesian_product


class LinearTrend(BaseFactor):
    def __init__(
        self,
        coef: Optional[float] = None,
        offset: Optional[float] = None,
        feature: Optional[str] = None,
        feature_values: Optional[Dict[str, Dict[str, float]]] = None,
        col_name: str = "lin_trend",
    ):
        """
        Linear Trend Factor. Can either just be a linear trend, or a trend that acts on certain features.

        Args:
            coef: coefficient of the linear trend. Optional when specifying a feature that the trend depends on.
            offset: offset of the linear trend. Optional when specifying a feature that the trend depends on.
            feature: feature that the linear trend depends on.
            feature_values: coefficient and offset values per feature value.
            col_name: column name of the feature in the resulting DataFrames.

        Examples:
        Linear trend over all features:
        >>> LinearTrend(coef=0.05, offset=1.)

        different trends for different features:
        >>> LinearTrend(feature="my_feature", feature_values={
        ...     "foo_feat": {"coef": 0.05, "offset": 1.},
        ...     "bar_feat": {"coef": 0.1, "offset": 0.5}
        ...     }
        ... })
        """
        if not (
            (coef is not None and offset is not None and feature is None and feature_values is None)
            or (coef is None and offset is None and feature is not None and feature_values is not None)
        ):
            raise AttributeError(
                "Either set `coef` and `offset` or `features` and `feature_values`"
            )
        if feature:
            if any(
                map(
                    lambda value: value.get("coef") is None
                    or value.get("offset") is None,
                    feature_values.values(),
                )
            ):
                raise AttributeError(
                    f"Each feature value should have a `coef` and an `offset`, you have entered: {feature_values}"
                )
            features = {feature: list(feature_values.keys())}
        else:
            features = None
        super().__init__(col_name=col_name, features=features)
        self._coef = coef
        self._offset = offset
        self._feature = feature
        self._feature_values = feature_values

    @property
    def coef(self):
        return self._coef

    @coef.setter
    def coef(self, value: float):
        if self._feature_values:
            raise ValueError("Cannot set coef when feature_values is set.")
        self._coef = value

    @property
    def offset(self):
        return self._offset

    @offset.setter
    def offset(self, value: float):
        if self._feature_values:
            raise ValueError("Cannot set offset when feature_values is set.")
        self._offset = value

    @property
    def feature(self):
        return self._feature

    @feature.setter
    def feature(self, feature: str):
        self._feature = feature

    @property
    def feature_values(self):
        return self._feature_values

    @feature_values.setter
    def feature_values(self, feature_values):
        if self._coef or self._offset:
            raise ValueError("Cannot set feature_values when offset and coef are set.")
        elif any(
            map(
                lambda value: value.get("coef") is None or value.get("offset") is None,
                feature_values.values(),
            )
        ):
            raise AttributeError(
                f"Each feature value should have a `coef` and an `offset`, you have entered: {feature_values}"
            )
        self._feature_values = feature_values

    def generate(
        self,
        start_date: Optional[Union[Timestamp, str, int, float]],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DataFrame:

        dr: DataFrame = self.get_datetime_index(
            start_date=start_date, end_date=end_date
        ).to_frame(index=False, name=self._date_col_name)

        start_date_ts: Timestamp = dr.iloc[0][self._date_col_name]

        if self._feature_values:

            def get_factor_col(row) -> float:
                days: float = float(
                    getattr(row[self._date_col_name] - start_date_ts, "days")
                )  # Only working in days
                # y = ax + b
                # the coef is the total slope across the whole time period
                # in order to calculate the daily delta, we need to divide the length of the date
                return row["coef"] / len(dr) * days + 1 + row["offset"]

            df: DataFrame = DataFrame(
                {
                    self._feature: self._feature_values.keys(),
                    "coef": map(
                        lambda feat: feat["coef"], self._feature_values.values()
                    ),
                    "offset": map(
                        lambda feat: feat["offset"], self._feature_values.values()
                    ),
                }
            )

            factor_df: DataFrame = get_cartesian_product(dr, df)
            factor_df[self._col_name] = factor_df.apply(get_factor_col, axis=1)
            factor_df = factor_df.drop(["coef", "offset"], axis=1)

        else:
            # y = ax + b
            df: DataFrame = DataFrame(
                (self._coef / len(dr) * arange(start=0, stop=len(dr)) + 1)
                + self._offset,
                columns=[self._col_name],
            )
            factor_df: DataFrame = dr.join(df)

        return factor_df
