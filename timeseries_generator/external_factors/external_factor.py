from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Union

from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator.base_factor import BaseFactor


class ExternalFactor(BaseFactor, ABC):
    def __init__(
        self,
        col_name: str,
        features: Optional[Dict[str, List[str]]] = None,
        date_col_name: str = "date",
        apply_to_all: bool = False,
        min_date: Optional[Union[Timestamp, str, int, float]] = None,
        max_date: Optional[Union[Timestamp, str, int, float]] = None,
    ):
        super().__init__(
            col_name=col_name,
            features=features,
            date_col_name=date_col_name,
            apply_to_all=apply_to_all,
        )
        self._min_date = min_date
        self._max_date = max_date

    @property
    def min_date(self) -> Optional[Union[Timestamp, str, int, float]]:
        return self._min_date

    @min_date.setter
    def min_date(self, date: Optional[Union[Timestamp, str, int, float]]):
        self._min_date = date

    @property
    def max_date(self) -> Optional[Union[Timestamp, str, int, float]]:
        return self._max_date

    @max_date.setter
    def max_date(self, date: Optional[Union[Timestamp, str, int, float]]):
        self._max_date = date

    @abstractmethod
    def load_data(self) -> DataFrame:
        ...

    def generate(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DataFrame:
        data: DataFrame = self.load_data()
        if end_date is None:
            df_sel = data[(data["date"] >= start_date)]
        else:
            df_sel = data[(data["date"] >= start_date) & (data["date"] < end_date)]
        return df_sel
