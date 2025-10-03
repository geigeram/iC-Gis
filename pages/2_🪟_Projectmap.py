import streamlit as st
import pandas as pd
import keplergl
from keplergl import KeplerGl
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("Project Map")

# Read the geocoded Excel file
try:
    df = pd.read_excel('data/geocoded_results.xlsx')
except FileNotFoundError:
    st.error("Geocoded results file not found. Please run the geocoding in the Project Dataframe page first.")
    st.stop()

# Handle coordinate columns
lat_col = 'latitude' if 'latitude' in df.columns else 'lat'
lon_col = 'longitude' if 'longitude' in df.columns else 'lon'

# Ensure coordinates are float
df[lat_col] = pd.to_numeric(df[lat_col], errors='coerce')
df[lon_col] = pd.to_numeric(df[lon_col], errors='coerce')

# Drop rows with missing coordinates
df = df.dropna(subset=[lat_col, lon_col])

st.write("This is a kepler.gl map with data input in streamlit")

# Toggle fullscreen button
if st.button("Toggle Fullscreen Map"):
    current_height = st.session_state.get('map_height', 800)
    st.session_state['map_height'] = 1200 if current_height == 800 else 800
    st.rerun()

map_height = st.session_state.get('map_height', 1200)
map_1 = KeplerGl(height=map_height)
map_1.add_data(
    data=df, name="Status"
)  # Alternative: KeplerGl(height=400, data={"name": df})

components.html(map_1._repr_html_(), height=map_height)
