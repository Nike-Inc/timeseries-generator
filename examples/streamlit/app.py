import sys
from contextlib import contextmanager
from io import StringIO

import numpy as np
import pandas as pd
import datetime

import streamlit as st
from threading import current_thread
import altair as alt
import functools
import base64

from timeseries_generator import (
    Generator,
    HolidayFactor,
    LinearTrend,
    RandomFeatureFactor,
    WeekdayFactor,
    WhiteNoise,
)
from timeseries_generator.external_factors import (
    CountryGdpFactor,
    EUIndustryProductFactor,
)

sys.path.append("../..")

np.random.seed(42)

st.set_page_config(
    page_title="Awesome TS Generator", layout="wide", initial_sidebar_state="auto"
)


# Streamlit APP start from here

st.title("Awesome Time Series Syntheic Data Generator")


@st.cache
def get_country_gdppc_df():
    df = pd.read_csv(
        "./examples/streamlit/GDP_per_capita_countries.csv", encoding="utf-8-sig"
    )
    return df


@st.cache()
def get_country_list():
    df = get_country_gdppc_df()
    return df["Country Name"].unique()


st.sidebar.subheader("Input a base amount")
base_amount = st.sidebar.number_input("", value=1000, format="%d")

feature_dict = {}

st.sidebar.subheader("Input features")
country_factor_flag = st.sidebar.checkbox("Country")
if country_factor_flag:
    countries = st.sidebar.multiselect(
        "Choose countries", list(get_country_list()), ["Netherlands", "Italy"]
    )
    feature_dict["country"] = countries

feature_flag = st.sidebar.checkbox("Add more feature(s)")
if feature_flag:
    feature_raw_str = st.sidebar.text_input(
        "Input feature list (must separate by comma)", "product"
    )
    feature_list = feature_raw_str.split(",")

    for feat in feature_list:
        default_val_l = [f"{feat}_{i}" for i in range(3)]
        feat_val_l = st.sidebar.text_input(
            f"Input values of feature [{feat}] (must separate by comma)",
            ",".join(default_val_l),
        )
        feature_dict[feat] = feat_val_l.split(",")

factor_list = []


# -------------------------
# add feature related factors

st.sidebar.subheader("Select factor for each feature")

feat_factor_dict = {
    "random_factor": RandomFeatureFactor,
    "country_factor": CountryGdpFactor,
}

factor_switch_dict = {}
for feat in feature_dict.keys():
    factor_switch = st.sidebar.checkbox(f"{feat}", key=f"factor_switch_{feat}")
    if factor_switch:
        feat_factor_options = st.sidebar.multiselect(
            f"select factor for [{feat}]",
            ("random_factor", "country_factor", "linear_factor"),
        )
        if len(feat_factor_options) > 0:
            for factor in feat_factor_options:
                if factor == "random_factor":
                    factor_list.append(
                        RandomFeatureFactor(
                            feature=feat,
                            feature_values=feature_dict[feat],
                            col_name=f"random_feature_factor_{feat}",
                        )
                    )
                if factor == "country_factor":
                    if feat == "country":
                        factor_list.append(
                            CountryGdpFactor(country_list=feature_dict[feat])
                        )
                if factor == "linear_factor":
                    feat_val_linear_trend_dict = {}
                    for feat_val in feature_dict[feat]:
                        coef = st.sidebar.number_input(
                            f"Linear slope of {feat_val}",
                            value=1.0,
                            format="%f",
                            key="linear_trend_{feat}_{feat_val}",
                        )
                        feat_val_linear_trend_dict[feat_val] = {
                            "coef": coef,
                            "offset": 0,
                        }
                    factor_list.append(
                        LinearTrend(
                            feature=feat,
                            feature_values=feat_val_linear_trend_dict,
                            col_name=f"lin_trend_{feat}",
                        )
                    )


# add global factors

st.sidebar.subheader("Add other factor")

if country_factor_flag:
    is_holiday = st.sidebar.checkbox("Add holiday factor")
    holiday_scale = st.sidebar.slider(
        "Holiday factor scale", min_value=1, max_value=10, value=2, step=1
    )
    if is_holiday:
        if "country" in feature_dict:
            holiday_factor = HolidayFactor(
                country_list=feature_dict["country"], holiday_factor=holiday_scale
            )
        else:
            holiday_factor = HolidayFactor(
                country_list=["Netherlands"], holiday_factor=holiday_scale
            )
        factor_list.append(holiday_factor)


is_weekend = st.sidebar.checkbox("Add weekend factor")
weekend_scale = st.sidebar.slider(
    "weekend factor scale", min_value=1, max_value=10, value=1, step=1
)
if is_weekend:
    factor_list.append(WeekdayFactor(intensity_scale=weekend_scale))

is_eu_economics = st.sidebar.checkbox("Add EU economics factor")
eu_eco_scale = st.sidebar.slider(
    "EU eco factor scale", min_value=1, max_value=20, value=5, step=1
)
if is_eu_economics:
    factor_list.append(EUIndustryProductFactor(intensive_scale=eu_eco_scale))

is_noise = st.sidebar.checkbox("Add random noise")
if is_noise:
    factor_list.append(WhiteNoise())


# ---------------------------
# select time period

st.subheader("Input start date and end date")
col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input(
        "Start data", datetime.date(2019, 1, 1), min_value=datetime.date(2012, 1, 1)
    )
with col2:
    end_date = st.date_input(
        "End date", datetime.date(2020, 12, 31), min_value=start_date
    )

# generate time series
g: Generator = Generator(
    factors=set(factor_list),
    features=feature_dict,
    date_range=pd.date_range(start_date, end_date),
    base_value=base_amount,
)
df_sale = g.generate()


# ------------------------------------------------
# visualization

st.subheader("Generated time series data")

# get all features in feature_dict
all_features = list(feature_dict.keys())

vis_feat_l = st.multiselect("Choose features to aggregate", all_features, all_features)
if len(vis_feat_l) > 0:
    group_feat_l = vis_feat_l.copy()
    group_feat_l.insert(0, "date")
    df_vis = df_sale.groupby(group_feat_l)["value"].sum().reset_index()
else:
    df_vis = df_sale.copy()


df_plot = df_vis[["date", "value"]]

if len(vis_feat_l) > 0:
    color_col = "-".join(vis_feat_l)
    df_plot[color_col] = functools.reduce(
        lambda x, y: x + "-" + y, (df_vis[feat] for feat in vis_feat_l)
    )

    base = (
        alt.Chart(df_plot)
        .mark_line()
        .encode(x="date:T", y="value:Q", color=f"{color_col}:N")
    )

    selection = alt.selection_multi(fields=[color_col], bind="legend")

    chart = (
        base.mark_line()
        .encode(opacity=alt.condition(selection, alt.value(1), alt.value(0.2)))
        .add_selection(selection)
        .interactive()
    )

    st.altair_chart(chart, use_container_width=True)
else:

    base = (
        alt.Chart(df_plot)
        .mark_line()
        .encode(
            x="date:T",
            y="value:Q",
        )
        .interactive()
    )

    st.altair_chart(base, use_container_width=True)


# --------------
# download dataframe
def get_table_download_link(df):
    """Generates a link allowing the data in a given panda dataframe to be downloaded
    in:  dataframe
    out: href string
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(
        csv.encode()
    ).decode()  # some strings <-> bytes conversions necessary here
    href = f'<a href="data:file/csv;base64,{b64}">Download csv file</a>'
    return href


st.markdown(get_table_download_link(df_vis), unsafe_allow_html=True)


# -------------
# show dataframe

col1, col2 = st.columns(2)
with col1:
    show_base_df = st.checkbox("Show dataframe")
with col2:
    topn = st.number_input("Top N rows", value=50, format="%d")
if show_base_df:
    show_col = ["date"] + vis_feat_l + ["value"]
    st.dataframe(df_vis[show_col].head(topn))
