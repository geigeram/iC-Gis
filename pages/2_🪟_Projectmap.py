import streamlit as st
import leafmap.foliumap as leafmap
import pandas as pd

st.title("Project Map")
df = pd.read_csv('data\Alle Projekte 15_04_2025 14-34-31.csv', sep=';')
df['Breite'] = df['Breite'].str.replace(',', '.').astype(float)
df['Laenge'] = df['Laenge'].str.replace(',', '.').astype(float)

projekt_options = ["All"] + list(df['Team'].unique())
selected_projekt = st.selectbox("Select Projektname", projekt_options)


if selected_projekt == "All":
    filtered_df = df
    filtered_df = filtered_df.dropna(subset=["Breite", "Laenge"])
else:
    filtered_df = df[df['Team'] == selected_projekt]
    filtered_df = filtered_df.dropna(subset=["Breite", "Laenge"])



st.set_page_config(layout="wide")


st.sidebar.title("About")

logo = r'C:\Users\a.geiger\Documents\GitHub\streamlit_gis\gis.png'
st.sidebar.image(logo)

m = leafmap.Map(center=[54, 15], zoom=4)
#cities = pd.read_csv('data/230710_GeoDatenbank_Lage.csv', sep=';')
        #regions = "https://raw.githubusercontent.com/giswqs/leafmap/master/examples/data/us_regions.geojson"

        #m.add_geojson(regions, layer_name="US Regions")
m.add_points_from_xy(filtered_df, x="Laenge", y="Breite")
        #m.add_points_from_xy(
           # cities,
           # x="lat",
           # y="lon",
           # color_column="Projektnummer",
           # icon_names=["gear", "map", "leaf", "globe"],
           # spin=True,
           # add_legend=True,)

m.to_streamlit(height=700)
