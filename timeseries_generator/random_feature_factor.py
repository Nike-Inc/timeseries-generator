from typing import List, Any, Optional, Union

import numpy as np
from pandas import DataFrame
from pandas._libs.tslibs.timestamps import Timestamp

from timeseries_generator import BaseFactor
from timeseries_generator.utils import get_cartesian_product


class RandomFeatureFactor(BaseFactor):
    def __init__(
        self,
        feature: str,
        feature_values: List[Any],
        min_factor_value: float = 1.0,
        max_factor_value: float = 10.0,
        col_name: str = "random_feature_factor",
    ):
        """
        Creates a random factor for every feature value.

        Args:
            feature: feature name.
            feature_values: values (labels) of the feature.
            min_factor_value: minimum factor value.
            max_factor_value: maximum factor value.
            col_name:

        Examples:
            Create a factor for every store in our store list: "store_1", "store_2"
                >>> rff = RandomFeatureFactor(
                ...     feature="store",
                ...     feature_values=["store_1", "store_2"],
                ...     min_factor_value=1,
                ...     max_factor_value=10
                ... )
        """
        super().__init__(col_name=col_name, features={feature: feature_values})

        self._feature = feature
        self._feature_values = feature_values
        if min_factor_value > max_factor_value:
            raise ValueError(
                f'min_factor_value: "{min_factor_value}" > max_factor_value: "{max_factor_value}"'
            )
        self._min_factor_value = min_factor_value
        self._max_factor_value = max_factor_value

    def generate(
        self,
        start_date: Union[Timestamp, str, int, float],
        end_date: Optional[Union[Timestamp, str, int, float]] = None,
    ) -> DataFrame:

        dr: DataFrame = self.get_datetime_index(
            start_date=start_date, end_date=end_date
        ).to_frame(index=False, name=self._date_col_name)

        # randomly generate factor
        # rand_value = min + ((max - min) * value)
        feat_factor = self._min_factor_value + (
            (self._max_factor_value - self._min_factor_value)
            * np.random.random(len(self._feature_values))
        )

        # generate factor df
        factor_df = DataFrame(
            {self._feature: self._feature_values, self._col_name: feat_factor}
        )

        # cartesian product of factor df and datetime df
        return get_cartesian_product(dr, factor_df)
