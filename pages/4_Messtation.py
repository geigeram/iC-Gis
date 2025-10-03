import streamlit as st
import pandas as pd

st.title("Messtation Data")

# URL for the measurement station data
url = "http://176.66.66.28/cgi-bin/download.cgi?loginstring=admin&user_pw=1AQuality&dec=COMMA&header_name&nohtml&status&avg3=12327,12333,12111,12213,12189,12117,12339,12153,12195,12171&tstart=2025-09-29,00:00:00&tend=2025-09-30,00:00:00"

try:
    # Read the CSV data from the URL with appropriate encoding
    df = pd.read_csv(url, encoding='latin1')
    st.write("Data from Messtation:")
    st.dataframe(df)
except Exception as e:
    st.error(f"Failed to load data: {e}")
