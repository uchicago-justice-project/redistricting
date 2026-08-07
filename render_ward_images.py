#!/usr/bin/env python3
"""
Renders one PNG per redistricting year for the ward-slider interactive.
Output: web/images/ward_{year}.png
"""

from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MplPath
import geopandas as gpd
from shapely.geometry import shape

YEARS = [1923, 1931, 1947, 1961, 1970, 1981, 1985, 1995, 2005, 2015, 2023]

COLOR_NEVER_CHANGED = "#4a90d9"
COLOR_CHANGED       = "#e8521a"
COLOR_BOUNDARY      = "#333333"

ROOT     = Path(__file__).parent
HEX_PATH = ROOT / "web" / "data" / "chicago_hexagons_web.geojson"
WRD_PATH = ROOT / "web" / "data" / "chicago_wards_all_years.geojson"
OUT_DIR  = ROOT / "web" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Image size — wide enough for retina displays, keeps file sizes manageable
FIG_W, FIG_H = 16, 8    # inches — 2:1 ratio matches the map container
DPI = 120                # → 1920×960 px


def first_change_year(props):
    """First year this hex changed wards (cumulative), or None if never."""
    if int(props.get("ward1923", 0) or 0) == 0:
        for y in YEARS:
            if int(props.get(f"ward{y}", 0) or 0) != 0:
                return y
        return None  # never in city
    for y in YEARS[1:]:
        if int(props.get(f"changed_in_{y}", 0) or 0) == 1:
            return y
    return None  # never changed


def main():
    print("Loading hexagons…")
    hex_gdf = gpd.read_file(HEX_PATH)
    hex_gdf["_fcy"] = hex_gdf.apply(
        lambda row: first_change_year(row.to_dict()), axis=1
    )

    print("Loading ward boundaries…")
    wrd_gdf = gpd.read_file(WRD_PATH)

    # Shared map extent — tight around Chicago
    minx, miny, maxx, maxy = hex_gdf.total_bounds
    pad_x = (maxx - minx) * 0.02
    pad_y = (maxy - miny) * 0.02

    for year in YEARS:
        print(f"  Rendering {year}…", end=" ", flush=True)

        fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
        ax.set_aspect("equal")
        ax.set_xlim(minx - pad_x, maxx + pad_x)
        ax.set_ylim(miny - pad_y, maxy + pad_y)
        ax.axis("off")
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

        # Classify hexagons for this year
        in_city = hex_gdf[f"ward{year}"].fillna(0).astype(int) != 0
        has_changed = hex_gdf["_fcy"].apply(
            lambda fcy: fcy is not None and fcy <= year
        )

        never_changed = hex_gdf[in_city & ~has_changed]
        changed       = hex_gdf[in_city & has_changed]

        # Plot hexagon fills
        if not never_changed.empty:
            never_changed.plot(ax=ax, color=COLOR_NEVER_CHANGED,
                               linewidth=0, antialiased=True)
        if not changed.empty:
            changed.plot(ax=ax, color=COLOR_CHANGED,
                         linewidth=0, antialiased=True)

        # Ward boundaries for this year
        wards_yr = wrd_gdf[wrd_gdf["year"] == year]
        if not wards_yr.empty:
            wards_yr.plot(ax=ax, facecolor="none",
                          edgecolor=COLOR_BOUNDARY, linewidth=0.8)

        # Year label — middle left
        ax.text(
            0.02, 0.5, f"{year} Wards",
            transform=ax.transAxes,
            fontsize=22, color="#222222",
            fontfamily="monospace",
            fontweight="normal",
            va="center", ha="left",
        )

        plt.tight_layout(pad=0)
        out = OUT_DIR / f"ward_{year}.png"
        fig.savefig(out, dpi=DPI, bbox_inches="tight",
                    facecolor="white", pad_inches=0.05)
        plt.close(fig)

        size_kb = out.stat().st_size // 1024
        print(f"saved ({size_kb} KB)")

    print(f"\nDone — {len(YEARS)} images in {OUT_DIR}/")


if __name__ == "__main__":
    main()
