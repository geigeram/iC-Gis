import streamlit as st
import leafmap.foliumap as leafmap
from st_excel_table import Table
import pandas as pd

st.title("Project Dataframe")
df = pd.read_csv('data\Alle Projekte 15_04_2025 14-34-31.csv', sep=';')
df['Breite'] = df['Breite'].str.replace(',', '.').astype(float)
df['Laenge'] = df['Laenge'].str.replace(',', '.').astype(float)

projekt_options = ["All"] + list(df['Team'].unique())
selected_projekt = st.selectbox("Select Projektname", projekt_options)


if selected_projekt == "All":
    filtered_df = df
    filtered_df = filtered_df.dropna(subset=["Breite", "Laenge"])
else:
    filtered_df = df[df['Projektname'] == selected_projekt]
    filtered_df = filtered_df.dropna(subset=["Breite", "Laenge"])



st.set_page_config(layout="wide")


st.sidebar.title("iC Gis")

logo = r'C:\Users\a.geiger\Documents\GitHub\streamlit_gis\gis.png'
st.sidebar.image(logo)

columns = filtered_df.columns.tolist()
Table(filtered_df.to_dict(orient="records"), columns)
#m.to_streamlit(height=700)
