#!/usr/bin/env python3
"""
Combines all Chicago ward shapefiles (old_chicago_wards + chicago_wards_2023_updated)
into a single GeoJSON where each feature has 'ward' and 'year' properties.

Also converts Chicago Hexagons with Wards Updated to GeoJSON and generates
web-optimized versions of both files under web/data/.
"""

import json
import re
from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = Path(__file__).parent / "data"
WEB_DATA_DIR = Path(__file__).parent / "web" / "data"

WARD_YEARS = [1923, 1931, 1947, 1961, 1970, 1981, 1985, 1995, 2005, 2015, 2023]


def combine_ward_shapefiles():
    frames = []

    # Old wards: each folder is CHI_{year}, column is ward{year}
    old_wards_dir = DATA_DIR / "old_chicago_wards"
    for ward_dir in sorted(old_wards_dir.iterdir()):
        if not ward_dir.is_dir():
            continue
        match = re.search(r"(\d{4})$", ward_dir.name)
        if not match:
            continue
        year = int(match.group(1))

        shp_files = list(ward_dir.glob("*.shp"))
        if not shp_files:
            continue

        gdf = gpd.read_file(shp_files[0])
        gdf = gdf.to_crs("EPSG:4326")

        # Find the ward column (named ward{year} or similar)
        ward_col = next(
            (c for c in gdf.columns if re.fullmatch(rf"ward{year}", c, re.IGNORECASE)),
            None,
        )
        if ward_col is None:
            # Fallback: first non-geometry column
            ward_col = [c for c in gdf.columns if c != "geometry"][0]

        frames.append(
            gpd.GeoDataFrame(
                {"ward": gdf[ward_col].astype(int), "year": year},
                geometry=gdf.geometry,
                crs="EPSG:4326",
            )
        )
        print(f"  Loaded {year}: {len(gdf)} wards")

    # 2023 updated wards
    wards_2023 = DATA_DIR / "chicago_wards_2023_updated" / "chicago_wards_2023_updated.shp"
    gdf_2023 = gpd.read_file(wards_2023).to_crs("EPSG:4326")
    frames.append(
        gpd.GeoDataFrame(
            {"ward": gdf_2023["ward"].astype(int), "year": 2023},
            geometry=gdf_2023.geometry,
            crs="EPSG:4326",
        )
    )
    print(f"  Loaded 2023: {len(gdf_2023)} wards")

    combined = pd.concat(frames, ignore_index=True)
    combined = gpd.GeoDataFrame(combined, crs="EPSG:4326")

    # Clip all ward polygons to the 2023 Chicago boundary so historical
    # wards never extend beyond the current city limits.
    chicago_2023_union = gdf_2023.geometry.unary_union
    combined["geometry"] = combined.geometry.intersection(chicago_2023_union)
    combined = combined[~combined.geometry.is_empty].reset_index(drop=True)
    print(f"  Clipped to 2023 boundary: {len(combined)} features remain")

    out_path = OUTPUT_DIR / "chicago_wards_all_years.geojson"
    combined.to_file(out_path, driver="GeoJSON")
    print(f"Wrote {len(combined)} features -> {out_path}")


def add_never_changed_wards(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Adds a never_changed_wards column (0 or 1).

    1 = hexagon had a non-zero ward in 1923 AND that ward number never changed
        through every subsequent year up to 2023.
    0 = hexagon had ward 0 in 1923 (not yet part of the city), OR the ward
        number changed at any point from 1923 onward.
    """
    ward_cols = [f"ward{y}" for y in WARD_YEARS]
    in_city_1923 = gdf["ward1923"] != 0
    ward_values = gdf[ward_cols]
    never_changed = ward_values.eq(ward_values.iloc[:, 0], axis=0).all(axis=1)
    gdf["never_changed_wards"] = (in_city_1923 & never_changed).astype(int)
    return gdf


def convert_hexagons():
    shp_path = DATA_DIR / "Chicago Hexagons with Wards Updated" / "Chicago Hexagons with Wards Updated.shp"
    gdf = gpd.read_file(shp_path).to_crs("EPSG:4326")

    gdf = add_never_changed_wards(gdf)

    changed = (gdf["never_changed_wards"] == 0).sum()
    unchanged = (gdf["never_changed_wards"] == 1).sum()
    print(f"  never_changed_wards: {unchanged} unchanged, {changed} changed/not-in-city-1923")

    out_path = OUTPUT_DIR / "chicago_hexagons_with_wards_updated.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    print(f"Wrote {len(gdf)} hexagons -> {out_path}")


# ---------------------------------------------------------------------------
# Web data preparation
# ---------------------------------------------------------------------------

PRE_1923_COLS = [
    "ward1837", "ward1847", "ward1857", "ward1863", "ward1869",
    "ward1876", "ward1890", "ward1900", "ward1910", "ward1912",
]

ALL_CHI_WARD_COLS = [
    "ward1837", "ward1847", "ward1857", "ward1863", "ward1869", "ward1876",
    "ward1890", "ward1900", "ward1910", "ward1912", "ward1923", "ward1931",
    "ward1947", "ward1961", "ward1970", "ward1981", "ward1985", "ward1995",
    "ward2005", "ward2015", "ward2023",
]


def compute_since_year(row) -> int:
    """
    Ported from update_wards.py.  Returns the year the hexagon was most recently
    assigned to its current ward:
      - For hexagons that entered the city after the first ward year, the entry
        year counts as the start (not a 'change').
      - After that, any ward-to-ward transition updates the year.
      - Returns 0 if the hexagon was never in the city.
    """
    prev_val = None
    first_nonzero_year = None
    last_change_year = None

    for col in ALL_CHI_WARD_COLS:
        if col not in row.index:
            continue
        val = row[col]
        if pd.isna(val):
            val = 0
        val = int(val)
        year = int(col.replace("ward", ""))

        if val == 0:
            prev_val = 0
            continue
        if first_nonzero_year is None:
            first_nonzero_year = year
        if prev_val is not None and prev_val != 0 and val != prev_val:
            last_change_year = year
        prev_val = val

    if first_nonzero_year is None:
        return 0  # never in city
    return last_change_year if last_change_year is not None else first_nonzero_year


def write_compact_geojson(gdf: gpd.GeoDataFrame, path: Path, precision: int = 6) -> None:
    """Write GeoJSON with reduced coordinate precision and no whitespace."""

    def round_coords(coords):
        if isinstance(coords[0], (list, tuple)):
            return [round_coords(c) for c in coords]
        return [round(coords[0], precision), round(coords[1], precision)]

    data = json.loads(gdf.to_json())
    for feature in data["features"]:
        if feature["geometry"]:
            feature["geometry"]["coordinates"] = round_coords(
                feature["geometry"]["coordinates"]
            )

    with open(path, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    size_mb = path.stat().st_size / 1e6
    print(f"    {path.name}: {size_mb:.1f} MB")


def prepare_web_data():
    WEB_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # --- Hexagons ---
    print("Preparing hexagons for web...")
    gdf = gpd.read_file(OUTPUT_DIR / "chicago_hexagons_with_wards_updated.geojson")

    # Compute since_year BEFORE dropping pre-1923 columns so all ward history
    # is available (matches update_wards.py logic exactly).
    print("  Computing since_year...")
    gdf["since_year"] = gdf.apply(compute_since_year, axis=1)

    # Drop pre-1923 columns not needed in the browser
    gdf = gdf.drop(columns=[c for c in PRE_1923_COLS if c in gdf.columns])

    # Add changed_in_{year} boolean columns for the slider interactive
    for i in range(1, len(WARD_YEARS)):
        prev, curr = WARD_YEARS[i - 1], WARD_YEARS[i]
        changed = (gdf[f"ward{curr}"] != gdf[f"ward{prev}"]).astype(int)
        changed[gdf[f"ward{curr}"] == 0] = 0
        gdf[f"changed_in_{curr}"] = changed

    write_compact_geojson(gdf, WEB_DATA_DIR / "chicago_hexagons_web.geojson")

    # --- Ward boundaries ---
    print("Preparing ward boundaries for web...")
    wards_gdf = gpd.read_file(OUTPUT_DIR / "chicago_wards_all_years.geojson")
    write_compact_geojson(wards_gdf, WEB_DATA_DIR / "chicago_wards_all_years.geojson")

    print(f"Web data written to {WEB_DATA_DIR}/")


if __name__ == "__main__":
    print("Combining Chicago ward shapefiles...")
    combine_ward_shapefiles()

    print("\nConverting Chicago hexagons shapefile...")
    convert_hexagons()

    print("\nPreparing web-optimized data...")
    prepare_web_data()
