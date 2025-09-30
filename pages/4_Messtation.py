import streamlit as st
import leafmap.foliumap as leafmap
from st_excel_table import Table
import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

st.title("Project Dataframe")
df = pd.read_excel(r'C:\Users\a.geiger\Documents\GitHub\streamlit_gis\data\250813_alle_projekte_vollständig.xlsx', sheet_name='250813_alle_projekte')

st.dataframe(df)
# Geocoder initialisieren
geolocator = Nominatim(user_agent="geoapi")

# Listen für Ergebnisse
latitudes = []
longitudes = []

for address in df['Adresse']:  # Passe den Spaltennamen ggf. an
    try:
        location = geolocator.geocode(address)
        if location:
            latitudes.append(location.latitude)
            longitudes.append(location.longitude)
        else:
            latitudes.append(None)
            longitudes.append(None)
    except Exception as e:
        latitudes.append(None)
        longitudes.append(None)
    sleep(1)  # Wartezeit, um den Geocoding-Service nicht zu überlasten

# Ergebnisse zum DataFrame hinzufügen
df['Breite'] = latitudes
df['Laenge'] = longitudes

st.dataframe(df)
# Neue Excel-Datei speichern
#df.to_excel('projekte_mit_koordinaten.xlsx', index=False)
#m.to_streamlit(height=700)
