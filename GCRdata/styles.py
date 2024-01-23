# styles.py
import streamlit as st

def apply_general_styles():
    st.markdown(
        """
        <style>
        div[data-testid="stHorizontalBlock"] {
            width: 60vw;
        }
        div[data-testid="metric-container"] {
            padding:10px;
            border-radius: 3px;
            min-height: 20vh;
            width: 185px;
            background: linear-gradient(to top, rgba(243, 184, 6, 0.3), rgba(243, 184, 6, 0));
        }
        div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div {
            overflow-wrap: break-word;
            white-space: break-spaces;
            color: black;
        }
        div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div p {
            font-size: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_delta_styles():
    st.markdown(
        """
        <style>
        [data-testid="stMetricDelta"] {
            margin-top: -20px;
            font-weight: 600;
            font-size: 1.2rem;
        }
        [data-testid="stMetricDelta"] svg {
            display: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_sidebar_styles():
    st.markdown(
        """
        <style>
        [data-testid=stSidebar] {
            background-color: #F3B806;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_score_card_styles():
    st.markdown(
        """
        <style>
        div[data-testid="metric-container"], div[data-testid="stMetric"] {
            border: 1.5px solid #F3B806;
            background: linear-gradient(to bottom, #F3B806, rgba(243, 184, 6, 0));
            padding: 10px;
            border-radius: 3px;
            height: 150px;
        }
        p {
            color: red;
        }
        div[data-testid="metric-container"] > label[data-testid="stMetricLabel"] > div p {
            font-size: 1rem !important;
            color: white; 
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            height: 100px;
        }
        div[data-testid="stMetricValue"] > div {
            background-color: ;
            margin-bottom: -10px;
            padding: 10px;
            font-weight: 600;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def apply_radio_btn_styles():
    st.markdown(
        """
        <style>
        [data-testid="stMarkdownContainer"]>p, [data-testid="stMarkdownContainer"] {
            color: black;
            font-weight: 600;
            font-size: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

