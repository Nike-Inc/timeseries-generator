from math import pi
from typing import Optional, Dict, Union

from numpy import sin, arange
from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.base_factor import BaseFactor
from timeseries_generator.utils import get_cartesian_product

VARIABLES = ["wavelength", "amplitude", "phase", "mean"]


class SinusoidalFactor(BaseFactor):
    def __init__(
        self,
        wavelength: Optional[float] = None,
        amplitude: float = 1,
        phase: float = 0,
        mean: float = 1,
        col_name: str = "sinusoidal_factor",
        date_col_name: str = "date",
        feature: Optional[str] = None,
        feature_values: Optional[Dict[str, Dict[str, float]]] = None,
    ):
        """
        Introduces a sinusoidal factor, useful for introducing seasonal patterns.
        Either supply wavelength, amplitude, phase and mean to apply the factor to the entire time series, or specify
        features with their characteristics to apply different factors to different features.

        Args:
            wavelength: wavelength in days
            amplitude: amplitude of the factor
            phase: phase in days
            mean: absolute mean of the factor.
            col_name: name of the factor column.
            date_col_name: name of the resulting date column
            feature: feature with sinusoidal factor
            feature_values: feature labels affected by the sinusoidal factor

        Examples:
            Create a standard sinusoidal factor for all features:
            >>> sf = SinusoidalFactor(wavelength=5., amplitude=1., phase=2., mean=1.5)
            ... sf.generate(start_date="01-01-2020", end_date="01-14-2020")

            Create a sinusoidal factor over the timespan of a year, to increase the sales of winter jackets in the
            winter 200%, decreasing the sales of the jacket in peak summer times to 0%:
            >>> sf = SinusoidalFactor(feature="product_type", feature_values={
            ...     "winter_jacket": {
            ...         "wavelength": 365., "amplitude": 1., "phase": 365/4, "mean": 1
            ...     }
            ... })
        """
        if (feature is None) ^ (feature_values is None):
            raise AttributeError(
                "Either set `feature` and `feature_values` or set neither."
            )
        elif feature:
            # Check for all keys in dict
            if any(
                map(
                    lambda item: len(
                        {"wavelength", "amplitude", "phase", "mean"}
                        & set(item[1].keys())
                    )
                    != 4,
                    feature_values.items(),
                )
            ):
                raise AttributeError(
                    f"Please set {VARIABLES} for every label. You have entered: {feature_values}"
                )
            features = {feature: list(feature_values.keys())}
        else:
            features = None

        self._wavelength = wavelength
        self._amplitude = amplitude
        self._phase = phase
        self._mean = mean
        self._feature = feature
        self._feature_values = feature_values
        super().__init__(
            col_name=col_name, date_col_name=date_col_name, features=features
        )

    @property
    def wavelength(self) -> float:
        return self._wavelength

    @wavelength.setter
    def wavelength(self, wavelength: Optional[float]):
        self._wavelength = wavelength

    @property
    def amplitude(self) -> float:
        return self._amplitude

    @amplitude.setter
    def amplitude(self, amplitude: float):
        self._amplitude = amplitude

    @property
    def phase(self) -> float:
        return self._phase

    @phase.setter
    def phase(self, phase: float):
        self._phase = phase

    @property
    def mean(self) -> float:
        return self._mean

    @mean.setter
    def mean(self, mean: float):
        self._mean = mean

    @property
    def feature(self) -> str:
        return self._feature

    @feature.setter
    def feature(self, feature: str):
        self._feature = feature

    @property
    def feature_values(self) -> Optional[Dict[str, Dict[str, float]]]:
        return self._feature_values

    @feature_values.setter
    def feature_values(self, values: Optional[Dict[str, Dict[str, float]]]):
        if any(map(lambda label: len(set(VARIABLES) & set(label.keys())) != 4, values)):
            raise AttributeError(
                f"Please set {VARIABLES} for every label. You have entered: {values}"
            )
        self._feature_values = values

    def generate(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DataFrame:
        dr: DataFrame = self.get_datetime_index(
            start_date=start_date, end_date=end_date
        ).to_frame(index=False, name=self._date_col_name)

        start_date_ts: Timestamp = dr.iloc[0][self._date_col_name]

        if self._feature_values:

            def get_factor_col(row) -> float:
                t: float = float(
                    getattr(row[self._date_col_name] - start_date_ts, "days")
                )  # Only working in days
                # y(t) A * sin(2 * pi * freq * t + phase) + mean
                return (
                    row["amplitude"]
                    * sin(2 * pi * (t + row["phase"]) / row["wavelength"])
                    + row["mean"]
                )

            df: DataFrame = DataFrame(
                dict(
                    {self._feature: list(self._feature_values.keys())},
                    **{
                        var: list(
                            map(lambda feat: feat[1][var], self._feature_values.items())
                        )
                        for var in VARIABLES
                    },
                )
            )

            factor_df: DataFrame = get_cartesian_product(dr, df)
            factor_df[self._col_name] = factor_df.apply(get_factor_col, axis=1)
            factor_df = factor_df.drop(VARIABLES, axis=1)
        else:
            # y(t) A * sin(2 * pi * freq * t + phase) + mean
            df: DataFrame = DataFrame(
                self._amplitude
                * sin(
                    2
                    * pi
                    * (arange(start=0, stop=len(dr)) + self._phase)
                    / self._wavelength
                )
                + self._mean,
                columns=[self._col_name],
            )
            factor_df: DataFrame = dr.join(df)

        return factor_df
