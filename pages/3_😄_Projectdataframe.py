import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import io

def build_address_from_columns(row: pd.Series, cols: list[str]) -> str:
    parts = []
    for c in cols:
        if c in row and pd.notna(row[c]) and str(row[c]).strip():
            parts.append(str(row[c]).strip())
    if not parts:
        return ""
    return ", ".join(parts)

def detect_address_column(df: pd.DataFrame, explicit_col: str = None) -> str:
    if explicit_col:
        for c in df.columns:
            if c.lower() == explicit_col.lower():
                return c
        return None
    # try common names
    candidates = ["address", "adresse", "full_address", "location"]
    for cand in candidates:
        for c in df.columns:
            if c.lower() == cand:
                return c
    return None

def geocode_dataframe(df: pd.DataFrame, address_cols: list[str] = None, address_col: str = None):
    # Determine address series
    if address_cols:
        address_series = df.apply(lambda r: build_address_from_columns(r, address_cols), axis=1)
    else:
        detected = detect_address_column(df, address_col)
        if not detected:
            st.error("No address column found. Please specify address columns.")
            return df
        address_series = df[detected]

    # Geocode
    geolocator = Nominatim(user_agent="streamlit-gis", timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)

    lats = []
    lons = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    total = len(address_series)
    for idx, addr in enumerate(address_series):
        if pd.isna(addr) or not str(addr).strip():
            lats.append(None)
            lons.append(None)
        else:
            try:
                loc = geocode(str(addr).strip())
                if loc:
                    lats.append(loc.latitude)
                    lons.append(loc.longitude)
                else:
                    lats.append(None)
                    lons.append(None)
            except Exception as e:
                lats.append(None)
                lons.append(None)
                st.warning(f"Error geocoding {addr}: {e}")

        progress_bar.progress((idx + 1) / total)
        status_text.text(f"Geocoding {idx + 1}/{total}")

    progress_bar.empty()
    status_text.empty()

    df['lat'] = lats
    df['lon'] = lons
    return df

st.title("Project Dataframe")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.write("Original DataFrame:")
    st.dataframe(df)

    if st.button("Compute Coordinates"):
        with st.spinner("Computing coordinates..."):
            df_geocoded = geocode_dataframe(df.copy())
        st.success("Coordinates computed!")
        st.write("Updated DataFrame:")
        st.dataframe(df_geocoded)
        st.session_state['geocoded_df'] = df_geocoded

    if 'df_geocoded' in st.session_state:
        df_to_download = st.session_state['df_geocoded']
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_to_download.to_excel(writer, index=False)
        buffer.seek(0)

        st.download_button(
            label="Download Results",
            data=buffer,
            file_name="geocoded_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
