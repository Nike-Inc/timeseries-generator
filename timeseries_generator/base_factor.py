from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union, Tuple

from matplotlib.figure import Figure
from matplotlib.axes._subplots import SubplotBase
from matplotlib.pyplot import subplots
from pandas import DataFrame, date_range, DatetimeIndex
from pandas._libs.tslibs.timestamps import Timestamp


class BaseFactor(ABC):
    def __init__(
        self,
        col_name: str,
        features: Optional[Dict[str, List[str]]] = None,
        date_col_name: str = "date",
        apply_to_all: bool = False,
    ):
        """
        BaseFactor which has to be implemented by all factors.

        Args:
            col_name: Column name of the factor.
            features: Features that this factor applies to.
            date_col_name: Name of the date_column of the generated date.
            apply_to_all: Whether this factor applies to all features in the generator. Use this if you want to access
                all features in the generator
        """
        if features is None:
            features = {}
        if apply_to_all and features:
            raise AttributeError(
                "Factor cannot apply to all features, while specifying a feature."
            )
        self._features = features
        self._col_name = col_name
        self._date_col_name = date_col_name
        self._apply_to_all = apply_to_all

    @property
    def col_name(self):
        return self._col_name

    @col_name.setter
    def col_name(self, name: str):
        self._col_name = name

    @property
    def features(self):
        return self._features

    @features.setter
    def features(self, keys: Dict[str, List[str]]):
        self._features = keys

    @property
    def date_col_name(self):
        return self._date_col_name

    @date_col_name.setter
    def date_col_name(self, name: str):
        self._date_col_name = name

    @property
    def apply_to_all(self):
        return self._apply_to_all

    @staticmethod
    def get_datetime_index(
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DatetimeIndex:
        """
        Utility function to return datetime function from start_date and optional end_date. Takes in multiple types.
        Based on the end date, may take a default number of periods.

        Args:
            start_date: start date of the DateTimeIndex.
            end_date: optional end date.

        Returns:
            :obj:`DateTimeIndex` compatable with this module.
        """
        periods: Optional[int] = None
        if not isinstance(start_date, Timestamp):
            start_date = Timestamp(start_date)
        if end_date and not isinstance(end_date, Timestamp):
            end_date = Timestamp(end_date)
        elif end_date is None:
            periods = 50
        return date_range(start=start_date, end=end_date, periods=periods)

    @abstractmethod
    def generate(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DataFrame:
        """
        Generates a DataFrame compatible with the `Generator` class. Must be implemented for the factor to be used and
        collected in the `Generator` class.
        Args:
            start_date: start date of the DateTimeIndex.
            end_date: optional end date.
        Returns:
            :obj:`DataFrame` containing the factor values, the corresponding date and optionally some feature labels.
        """
        ...

    def plot(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> Tuple[Figure, SubplotBase]:
        """
        Plots the factor on a 2D line plot. Convenience method to show what the factor looks like.
        Args:
            start_date: start date of the DateTimeIndex.
            end_date: optional end date.

        Returns:
            a tuple containing the figure and axes handle
        """
        df: DataFrame = self.generate(start_date=start_date, end_date=end_date)
        fig, ax = subplots()
        if self._features:
            for label, grp in df.groupby(list(self.features.keys())):
                grp.plot(x=self.date_col_name, y=self.col_name, ax=ax, label=label)
        else:
            df.plot(x=self.date_col_name, y=self.col_name, ax=ax)

        return fig, ax
