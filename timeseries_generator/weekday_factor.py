from typing import Optional, Dict, Union

from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.base_factor import BaseFactor


class WeekdayFactor(BaseFactor):
    """
    Some time series may behave differently depending on the day of the week. With this factor you can emulate this
    behaviour. Default behavior is to show an increased factor in the weekends, and a slightly increased factor on
    friday.

    The output dataframe will be two columns: date and factor


    Examples:
        Generate the default behaviour.
        >>> wf = WeekdayFactor()
        ... wf.generate(start_date="01-01-2020", end_date="01-14-2020")

        Generate custom weekday behaviour with a 1.5 increase on mondays and tuesdays.
        >>> wf = WeekdayFactor(
        ...     col_name="early_week_boost_factor",
        ...     factor_values={1: 1.5, 2: 1.5}
        ... )
    """

    def __init__(
        self,
        factor_values: Optional[Dict[int, float]] = None,
        col_name: str = "weekend_trend_factor",
        intensity_scale: int = 1,
    ):

        if factor_values is None:
            # default is a weekend factor
            factor_values = {4: 1.15, 5: 1.3, 6: 1.3}

        if type(factor_values) is not dict:
            raise ValueError(f"WeekdayFactor factor_values should be a dictionary")

        self._factor_values = factor_values
        self._intensity_scale = intensity_scale

        super().__init__(col_name=col_name)

    def generate(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Union[Timestamp, str, int, float] = None,
    ) -> DataFrame:
        df: DataFrame = self.get_datetime_index(
            start_date=start_date, end_date=end_date
        ).to_frame(index=False, name=self._date_col_name)

        df["weekday"] = df[self._date_col_name].dt.dayofweek
        df[self._col_name] = df["weekday"].apply(
            lambda day_number: self._factor_values.get(day_number, 1)
            * self._intensity_scale
        )

        df = df.drop(axis=1, columns="weekday")

        if end_date is None:
            df_sel = df[(df[self._date_col_name] >= start_date)]
        else:
            df_sel = df[
                (df[self._date_col_name] >= start_date)
                & (df[self._date_col_name] < end_date)
            ]

        # reindex to rangelist
        return df_sel.reset_index().drop(axis=1, columns="index")
