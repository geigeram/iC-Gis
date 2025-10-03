#!/usr/bin/env python3
import argparse
import sys
import time
from typing import List, Optional

import pandas as pd

try:
    from geopy.geocoders import Nominatim
    from geopy.extra.rate_limiter import RateLimiter
except ImportError:
    sys.stderr.write("Error: geopy is not installed. Install with: pip install geopy\n")
    sys.exit(1)


def build_address_from_columns(row: pd.Series, cols: List[str]) -> Optional[str]:
    parts = []
    for c in cols:
        if c in row and pd.notna(row[c]) and str(row[c]).strip():
            parts.append(str(row[c]).strip())
    if not parts:
        return None
    return ", ".join(parts)


def detect_address_column(df: pd.DataFrame, explicit_col: Optional[str]) -> Optional[str]:
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


def main():
    parser = argparse.ArgumentParser(description="Geocode addresses in an Excel file (Nominatim / OSM).")
    parser.add_argument("input", help="Input Excel file path (.xlsx)")
    parser.add_argument("--sheet", default=None, help="Worksheet name to read (default: first sheet)")
    parser.add_argument("--output", default=None, help="Output Excel file path (default: input file name with _geocoded.xlsx)")
    parser.add_argument("--address-column", dest="address_column", default=None,
                        help="Name of a single address column (case-insensitive)")
    parser.add_argument("--address-columns", dest="address_columns", nargs="+", default=None,
                        help="Multiple columns to concatenate into an address (order matters)")
    parser.add_argument("--user-agent", default="excel-geocoder-script",
                        help="User-Agent for Nominatim (please set to your app or email/URL)")
    parser.add_argument("--pause", type=float, default=1.0,
                        help="Seconds to wait between queries to respect rate limits (default: 1.0)")
    parser.add_argument("--country-bias", default=None,
                        help="Optional ISO country code to bias results (e.g., 'DE', 'AT')")
    parser.add_argument("--city-bias", default=None,
                        help="Optional city name to bias results using viewbox around that city (requires OSM lookup)")
    parser.add_argument("--language", default="en", help="Preferred language for results (default: en)")
    args = parser.parse_args()

    # Read Excel
    try:
        df = pd.read_excel(args.input, sheet_name=args.sheet)
    except Exception as e:
        sys.stderr.write(f"Failed to read Excel: {e}\n")
        sys.exit(1)

    if df.empty:
        sys.stderr.write("Input sheet is empty.\n")
        sys.exit(1)

    # Determine how to build the address string
    address_series = None
    used_columns = None

    if args.address_columns:
        missing = [c for c in args.address_columns if c not in df.columns]
        if missing:
            sys.stderr.write(f"Missing address columns: {missing}\n")
            sys.exit(1)
        used_columns = args.address_columns
        address_series = df.apply(lambda r: build_address_from_columns(r, used_columns), axis=1)
    else:
        detected = detect_address_column(df, args.address_column)
        if not detected:
            sys.stderr.write("Could not find an address column. Provide --address-column or --address-columns.\n")
            sys.stderr.write(f"Available columns: {list(df.columns)}\n")
            sys.exit(1)
        used_columns = [detected]
        address_series = df[detected]

    # Prepare geocoder
    geolocator = Nominatim(user_agent=args.user_agent, timeout=10)
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=args.pause, swallow_exceptions=False)

    # Optional: bias by country or city
    # For country bias, we'll pass 'country_codes' parameter.
    # For city bias, we could compute a viewbox; here we do a simple pre-geocode to get the city's bounding box.
    viewbox = None
    bounded = None
    # no-op to keep compatibility if someone misspells; handled below

    if args.city_bias:
        try:
            city_loc = geolocator.geocode(args.city_bias, language=args.language)
            if city_loc and hasattr(city_loc, "raw") and "boundingbox" in city_loc.raw:
                bbox = city_loc.raw["boundingbox"]  # [south, north, west, east] as strings
                south, north, west, east = map(float, bbox)
                viewbox = f"{west},{south},{east},{north}"  # 'west,south,east,north'
                bounded = 1  # hint to prefer results within the viewbox
        except Exception as e:
            sys.stderr.write(f"Warning: could not compute city bias viewbox ({e}). Continuing without it.\n")

    # Geocode rows
    lats = []
    lons = []
    precisions = []
    sources = []
    display_names = []
    statuses = []

    total = len(address_series)
    for idx, addr in enumerate(address_series):
        if pd.isna(addr) or not str(addr).strip():
            lats.append(None); lons.append(None); precisions.append(None); sources.append(None); display_names.append(None); statuses.append("no_address")
            continue
        query = str(addr).strip()
        try:
            params = {"language": args.language}
            if args.country_bias:
                params["country_codes"] = args.country_bias
            if viewbox:
                params["viewbox"] = viewbox
                params["bounded"] = bounded

            loc = geocode(query, **params)
            if loc is None:
                lats.append(None); lons.append(None); precisions.append(None); sources.append("nominatim"); display_names.append(None); statuses.append("not_found")
            else:
                lats.append(loc.latitude); lons.append(loc.longitude)
                # Extract a rough precision from OSM "type" and "class"
                raw = getattr(loc, "raw", {})
                precisions.append(raw.get("type") or raw.get("class"))
                sources.append("nominatim")
                display_names.append(loc.address)
                statuses.append("ok")
        except Exception as e:
            lats.append(None); lons.append(None); precisions.append(None); sources.append("nominatim"); display_names.append(None); statuses.append(f"error: {e}")

        # Optional progress to stderr
        sys.stderr.write(f"\rGeocoded {idx+1}/{total}")
        sys.stderr.flush()
        # RateLimiter already enforces min delay; no manual sleep needed

    sys.stderr.write("\n")

    # Append results
    out = df.copy()
    out["geo_status"] = statuses
    out["latitude"] = lats
    out["longitude"] = lons
    out["geo_precision_hint"] = precisions
    out["geo_display_name"] = display_names
    out["geo_source"] = sources
    out["geo_query"] = address_series

    # Save
    output_path = args.output or args.input.replace(".xlsx", "_geocoded.xlsx")
    try:
        out.to_excel(output_path, index=False)
    except Exception as e:
        sys.stderr.write(f"Failed to write output Excel: {e}\n")
        sys.exit(1)

    print(f"Done. Wrote {output_path}")
    if out["geo_status"].eq("ok").any():
        ok_count = int(out["geo_status"].eq("ok").sum())
        print(f"Geocoded successfully: {ok_count} / {len(out)} rows.")
    if out["geo_status"].eq("not_found").any():
        nf_count = int(out["geo_status"].eq("not_found").sum())
        print(f"Not found: {nf_count} rows.")
    if out["geo_status"].str.startswith("error").any():
        err_count = int(out["geo_status"].str.startswith("error").sum())
        print(f"Errors: {err_count} rows.")

if __name__ == "__main__":
    main()
