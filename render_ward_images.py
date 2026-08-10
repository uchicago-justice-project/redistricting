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

BG_COLOR            = "#0f0f0f"
COLOR_NEVER_CHANGED = "#b2e2dd"
COLOR_BOUNDARY      = "#aaaaaa"

ROOT     = Path(__file__).parent
HEX_PATH = ROOT / "web" / "data" / "chicago_hexagons_web.geojson"
WRD_PATH = ROOT / "web" / "data" / "chicago_wards_all_years.geojson"
OUT_DIR  = ROOT / "web" / "images"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Image size — wide enough for retina displays, keeps file sizes manageable
FIG_W, FIG_H = 16, 8    # inches — 2:1 ratio matches the map container
DPI = 120                # → 1920×960 px


def main():
    print("Loading hexagons…")
    hex_gdf = gpd.read_file(HEX_PATH)

    # Static classification: based on full 1923–2023 history.
    # never_changed_wards=1 means the hex was in city in 1923 and never moved wards.
    in_city      = hex_gdf["never_changed_wards"].notna()
    never_changed = hex_gdf[hex_gdf["never_changed_wards"] == 1]
    changed       = hex_gdf[(hex_gdf["never_changed_wards"] == 0) &
                             (hex_gdf["ward2023"].fillna(0).astype(int) != 0)]

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
        fig.patch.set_facecolor(BG_COLOR)
        ax.set_facecolor(BG_COLOR)

        # Only color hexagons that never changed — others stay white
        if not never_changed.empty:
            never_changed.plot(ax=ax, color=COLOR_NEVER_CHANGED,
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
            fontsize=22, color="#cccccc",
            fontfamily="monospace",
            fontweight="normal",
            va="center", ha="left",
        )

        plt.tight_layout(pad=0)
        out = OUT_DIR / f"ward_{year}.png"
        fig.savefig(out, dpi=DPI, bbox_inches="tight",
                    facecolor=BG_COLOR, pad_inches=0.05)
        plt.close(fig)

        size_kb = out.stat().st_size // 1024
        print(f"saved ({size_kb} KB)")

    print(f"\nDone — {len(YEARS)} images in {OUT_DIR}/")


if __name__ == "__main__":
    main()
