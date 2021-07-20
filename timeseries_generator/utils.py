from pandas import DataFrame


def get_cartesian_product(df1: DataFrame, df2: DataFrame) -> DataFrame:
    """
    Utility function that gets cartesian product of two dataframes.
    Args:
        df1: first dataframe.
        df2: second dataframe.

    Returns:
        DataFrame containing the cartesian product of both dataframes

    """
    df = df1.assign(key=1).merge(df2.assign(key=1), on="key").drop("key", axis=1)
    return df
