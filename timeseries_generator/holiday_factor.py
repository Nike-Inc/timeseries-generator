import pkgutil
from datetime import date, datetime
from typing import Optional, List, Dict, Tuple, Union

import workalendar
from pandas import DataFrame, Series, date_range, concat, isnull
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.external_factors.external_factor import BaseFactor

WORKALENDAR_CONTINENTS = ["africa", "america", "asia", "europe", "oceania", "usa"]


class HolidayFactor(BaseFactor):
    def __init__(
        self,
        col_name="holiday_trend_factor",
        holiday_factor: float = 3.0,
        special_holiday_factors: Optional[Dict[str, float]] = None,
        country_feature_name: Optional[str] = None,
        country_list: Optional[List[str]] = None,
    ):

        """
        This component uses public holiday information to generate factor

        We use python workalendar (https://github.com/peopledoc/workalendar) to retrieve holiday information

        N.B. we use `pip install workalendar` to install the package

        An example dataframe as holiday trend:
        date        country       factor
        2020-01-01  Netherlands   10
        2020-02-01  Netherlands   1
        2020-01-01  Italy         12
        2020-02-01  Italy         1
        ...

        Args:
            col_name: column name of the factor
            holiday_factor: factor of the found holiday
            special_holiday_factors: a dictionary countaining the holidays (keys) and altered factors from the
                `holiday_factor` (values).
            country_feature_name: name of the country feature introduced here.
            country_list: list of countries included in the feature.
        """
        if special_holiday_factors is None:
            special_holiday_factors = {}

        if country_feature_name is None:
            country_feature_name = "country"

        if country_list is None:
            country_list = ["Netherlands", "Italy", "Romania"]

        self._holiday_factor = holiday_factor
        self._special_holiday_factors = special_holiday_factors

        super().__init__(
            features={country_feature_name: country_list}, col_name=col_name
        )

    @property
    def holiday_factor(self):
        return self._holiday_factor

    @holiday_factor.setter
    def holiday_factor(self, factor: float):
        self._holiday_factor = factor

    @property
    def special_holiday_factors(self):
        return self._special_holiday_factors

    @special_holiday_factors.setter
    def special_holiday_factors(self, factors: Dict[str, float]):
        self._special_holiday_factors = factors

    def generate(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DataFrame:
        def clean_holiday_tuples(input_tuples: Tuple[datetime, str]):
            """
            The return value of holidays may have overlapping date, for example:
            2016-05-05    Ascension Thursday
            2016-05-05        Liberation Day

            Then, we only keep the first holiday
            """
            visited = set()
            output = []

            for a, b in input_tuples:
                if not a in visited:
                    visited.add(a)
                    output.append((a, b))

            return output

        def get_holiday_factor(holiday: Optional[str]):
            """
            get factor from holidays.
            """
            if isnull(holiday):
                return 1

            if holiday in self._special_holiday_factors:
                return self._special_holiday_factors[holiday]

            return self._holiday_factor

        def get_country_holiday_df(country_name: str):
            """
            Get all holiday days by give country in MAX_HISTORY_YEARS
            """
            # get all workalendar modules
            workalendar_country_modules: List[str] = [
                modname
                for importer, modname, ispkg in pkgutil.walk_packages(
                    workalendar.__path__, prefix=f"{workalendar.__name__}."
                )
                if not ispkg and modname.count(".") == 2
            ]
            workalendar_country_module = list(
                filter(
                    lambda work_cal: country_name.lower()
                    in work_cal,  # module names are lowercase
                    workalendar_country_modules,
                )
            )
            if len(workalendar_country_module) != 1:
                raise ValueError(
                    f'country_name: "{country_name}" not recognized in workalendar modules:'
                    f"{workalendar_country_modules}"
                )
            # Dynamically import the right class
            module_parts = workalendar_country_module[0].split(".")
            cal = getattr(
                getattr(getattr(workalendar, module_parts[1]), module_parts[2]),
                country_name,
            )()

            df = DataFrame()
            for year in range(
                start_date.year, end_date.year + 1
            ):  # plus one to include the end_date year itself
                holidays_tuples = clean_holiday_tuples(cal.holidays(int(year)))

                # TODO: make this more efficient, loop over tuple once
                datetime_l = [elem[0] for elem in holidays_tuples]
                holiday_l = [elem[1] for elem in holidays_tuples]

                # create series and fill NA for non-holiday date
                holiday_series = Series(holiday_l, index=datetime_l)

                # set full year index datetime
                ix = date_range(
                    start=date(int(year), 1, 1), end=date(int(year), 12, 31), freq="D"
                )
                holiday_series = holiday_series.reindex(ix)

                country_holiday_df = holiday_series.to_frame()

                # add country column
                country_holiday_df["country"] = country_name

                country_holiday_df = country_holiday_df.reset_index()
                country_holiday_df.columns = [self._date_col_name, "holiday", "country"]

                # get factor
                country_holiday_df[self._col_name] = country_holiday_df[
                    "holiday"
                ].apply(get_holiday_factor)

                df = concat([df, country_holiday_df], ignore_index=True)


            # Apply smoothing to the curve using a gaussian moving window
            df[self._col_name] = (
                df[self._col_name]
                .rolling(10, win_type="gaussian", min_periods=1)
                .mean(std=2)
            )

            return df

        holiday_df = concat(
            map(get_country_holiday_df, self._features[iter(self._features).__next__()])
        )
        holiday_df = holiday_df.drop(axis=1, columns="holiday")

        if end_date is None:
            df_sel = holiday_df[(holiday_df[self._date_col_name] >= start_date)]
        else:
            df_sel = holiday_df[
                (holiday_df[self._date_col_name] >= start_date)
                & (holiday_df[self._date_col_name] < end_date)
            ]

            # reindex to rangelist
        return df_sel.reset_index().drop(axis=1, columns="index")
