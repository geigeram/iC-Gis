#!/usr/bin/env python3
# streamlit_app.py
import io
import time
import pandas as pd
import streamlit as st

from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

st.set_page_config(page_title="Excel Address Geocoder", page_icon="📍", layout="centered")

st.title("📍 Excel Address Geocoder")
st.write("Upload an Excel file, select the address column, and download the file with latitude/longitude. Uses OpenStreetMap Nominatim (fair-use limits).")

with st.expander("ℹ️ How it works / Notes", expanded=False):
    st.markdown("""
- Expected: one column with full address (e.g., *address*, *adresse*, *full_address*).
- For high volumes, consider a paid geocoding provider. Please set a meaningful **User-Agent**.
- Respect Nominatim's usage policy: add a small delay between requests.
    """)

st.sidebar.header("Settings")
user_agent = st.sidebar.text_input("User-Agent (required)", value="excel-geocoder-streamlit")
pause = st.sidebar.number_input("Pause between lookups (seconds)", min_value=0.5, max_value=10.0, value=1.0, step=0.5)
country_bias = st.sidebar.text_input("Country bias (ISO code, optional)", value="")
language = st.sidebar.text_input("Language (ISO code)", value="en")

uploaded = st.file_uploader("Upload Excel (.xlsx)", type=["xlsx"])

if uploaded is not None:
    try:
        # Read all sheets, but default to the first one
        xls = pd.ExcelFile(uploaded)
        sheet_name = st.selectbox("Select sheet", xls.sheet_names, index=0)
        df = pd.read_excel(uploaded, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Failed to read Excel: {e}")
        st.stop()

    if df.empty:
        st.warning("The selected sheet is empty.")
        st.stop()

    st.subheader("Preview")
    st.dataframe(df.head(10))

    # Guess common address columns
    candidates = [c for c in df.columns if str(c).lower() in {"address", "adresse", "full_address", "location"}]
    default_index = df.columns.get_indexer(candidates[:1]).tolist()
    default_index = default_index[0] if default_index else 0

    addr_col = st.selectbox("Select the address column", options=list(df.columns), index=default_index)

    do_geocode = st.button("🚀 Geocode addresses")

    if do_geocode:
        if not user_agent.strip():
            st.error("Please set a User-Agent in the sidebar.")
            st.stop()

        geolocator = Nominatim(user_agent=user_agent.strip(), timeout=10)
        geocode = RateLimiter(geolocator.geocode, min_delay_seconds=float(pause), swallow_exceptions=True)

        out = df.copy()
        out["latitude"] = None
        out["longitude"] = None
        out["geo_status"] = None
        out["geo_display_name"] = None
        out["geo_precision_hint"] = None
        out["geo_source"] = "nominatim"
        out["geo_query"] = out[addr_col].astype(str)

        progress = st.progress(0)
        status_text = st.empty()

        params_base = {"language": language.strip() or "en"}
        if country_bias.strip():
            params_base["country_codes"] = country_bias.strip()

        total = len(out)
        ok_count = 0
        nf_count = 0
        err_count = 0

        for i, (idx, row) in enumerate(out.iterrows(), start=1):
            addr = row[addr_col]
            if pd.isna(addr) or not str(addr).strip():
                out.at[idx, "geo_status"] = "no_address"
                nf_count += 1
            else:
                try:
                    loc = geocode(str(addr).strip(), **params_base)
                    if loc is None:
                        out.at[idx, "geo_status"] = "not_found"
                        nf_count += 1
                    else:
                        out.at[idx, "latitude"] = loc.latitude
                        out.at[idx, "longitude"] = loc.longitude
                        raw = getattr(loc, "raw", {})
                        out.at[idx, "geo_precision_hint"] = raw.get("type") or raw.get("class")
                        out.at[idx, "geo_display_name"] = loc.address
                        out.at[idx, "geo_status"] = "ok"
                        ok_count += 1
                except Exception as e:
                    out.at[idx, "geo_status"] = f"error: {e}"
                    err_count += 1

            progress.progress(min(i / total, 1.0))
            status_text.text(f"Geocoded {i}/{total} • ok={ok_count} • not_found={nf_count} • errors={err_count}")

        st.success(f"Done: ok={ok_count}, not_found={nf_count}, errors={err_count}")

        st.subheader("Result preview")
        st.dataframe(out.head(20))

        # Prepare Excel for download
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            out.to_excel(writer, index=False, sheet_name=sheet_name)
        buffer.seek(0)

        st.download_button(
            label="📥 Download geocoded Excel",
            data=buffer,
            file_name="geocoded_addresses.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.caption("Built with Streamlit, pandas, geopy, and OpenStreetMap Nominatim.")
