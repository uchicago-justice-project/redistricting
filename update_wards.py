import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import numpy as np
from pathlib import Path

# ── Load data ──────────────────────────────────────────────────────────────────
chi_hex = gpd.read_file('data/Chicago Hexagons with Wards/Chicago Hexagons with Wards Join.shp')
mil_hex = gpd.read_file('data/Milwaukee Hexagons with Wards/Milwaukee Hexagons with Wards Join.shp')
mil_wards_2022 = gpd.read_file('data/milwaukee_wards_2022/alderman.shp').to_crs('EPSG:4326')

# Clip 2023 Chicago wards to the 2015 city boundary so ward 41 and any other
# edge wards don't bleed outside the established city footprint.
chi_wards_2015 = gpd.read_file('data/WARDS_2015_20260806/geo_export_f6785472-658a-4a65-a428-f1588e8b6efd.shp')
chi_city_boundary = chi_wards_2015.dissolve().geometry.iloc[0]
chi_wards_2023_raw = gpd.read_file('data/chicago_wards_2023/geo_export_2e9d5db9-dc2a-410e-a627-31de2a0f57a5.shp')
chi_wards_2023 = chi_wards_2023_raw.copy()
chi_wards_2023['geometry'] = chi_wards_2023_raw.geometry.intersection(chi_city_boundary)
chi_wards_2023 = chi_wards_2023[~chi_wards_2023.geometry.is_empty].reset_index(drop=True)
chi_wards_2023.to_file('data/chicago_wards_2023_updated')


# ── Spatial join: assign new ward to each hexagon via centroid ─────────────────
def join_new_wards(hex_gdf, ward_gdf, ward_col, new_col):
    # Project to a planar CRS for accurate centroids, then back
    projected = hex_gdf.to_crs('EPSG:3857')
    centroids = gpd.GeoDataFrame(
        {'GRID_ID': hex_gdf['GRID_ID']},
        geometry=projected.geometry.centroid,
        crs='EPSG:3857'
    ).to_crs(hex_gdf.crs)

    # Primary join: centroid within ward polygon
    joined = gpd.sjoin(centroids, ward_gdf[[ward_col, 'geometry']], how='left', predicate='within')
    joined = joined.drop_duplicates(subset='GRID_ID', keep='first')

    # Fallback: for unmatched centroids, snap to nearest ward polygon (project first)
    unmatched_ids = joined[joined[ward_col].isna()]['GRID_ID']
    if len(unmatched_ids) > 0:
        unmatched_centroids = centroids[centroids['GRID_ID'].isin(unmatched_ids)].to_crs('EPSG:3857')
        ward_gdf_proj = ward_gdf[[ward_col, 'geometry']].to_crs('EPSG:3857')
        nearest = gpd.sjoin_nearest(
            unmatched_centroids, ward_gdf_proj, how='left'
        ).drop_duplicates(subset='GRID_ID', keep='first')
        joined = joined.set_index('GRID_ID')
        for _, row in nearest.iterrows():
            gid = row['GRID_ID']
            joined.loc[gid, ward_col] = row[ward_col]
        joined = joined.reset_index()

    hex_gdf = hex_gdf.merge(
        joined[['GRID_ID', ward_col]].rename(columns={ward_col: new_col}),
        on='GRID_ID', how='left'
    )
    hex_gdf[new_col] = hex_gdf[new_col].fillna(0).astype(int)
    return hex_gdf

chi_hex = join_new_wards(chi_hex, chi_wards_2023, 'ward', 'ward2023')
mil_hex = join_new_wards(mil_hex, mil_wards_2022, 'DISTRICT', 'ward2022')

print('Chicago ward2023 value counts (non-zero):', chi_hex[chi_hex['ward2023'] > 0]['ward2023'].nunique(), 'wards')
print('Milwaukee ward2022 value counts (non-zero):', mil_hex[mil_hex['ward2022'] > 0]['ward2022'].nunique(), 'districts')

# ── Save updated shapefiles ────────────────────────────────────────────────────
out_chi = Path('data/Chicago Hexagons with Wards Updated')
out_mil = Path('data/Milwaukee Hexagons with Wards Updated')
out_chi.mkdir(exist_ok=True)
out_mil.mkdir(exist_ok=True)

chi_hex.to_file(out_chi / 'Chicago Hexagons with Wards Updated.shp')
mil_hex.to_file(out_mil / 'Milwaukee Hexagons with Wards Updated.shp')
print('Shapefiles saved.')


# ── "In Ward Since" logic ─────────────────────────────────────────────────────
def compute_since_year(row, ward_cols):
    """Return the year the hexagon was most recently assigned to its current ward.
    This is either the most recent ward-to-ward transition, or the first year the
    hexagon entered the city (0→non-zero). None only if the hexagon has all zeros."""
    prev_val = None
    first_nonzero_year = None
    last_change_year = None
    for col in ward_cols:
        val = row[col]
        year = int(col.replace('ward', ''))
        if val == 0:
            prev_val = 0
            continue
        if first_nonzero_year is None:
            first_nonzero_year = year  # first year in the city
        if prev_val is not None and prev_val != 0 and val != prev_val:
            last_change_year = year   # ward changed within the city
        prev_val = val
    if first_nonzero_year is None:
        return None  # never in city
    return last_change_year if last_change_year is not None else first_nonzero_year


CHI_WARD_COLS = [
    'ward1837', 'ward1847', 'ward1857', 'ward1863', 'ward1869', 'ward1876',
    'ward1890', 'ward1900', 'ward1910', 'ward1912', 'ward1923', 'ward1931',
    'ward1947', 'ward1961', 'ward1970', 'ward1981', 'ward1985', 'ward1995',
    'ward2005', 'ward2015', 'ward2023',
]
MIL_WARD_COLS = [
    'ward1846', 'ward1856', 'ward1872', 'ward1873', 'ward1874', 'ward1886',
    'ward1887', 'ward1888', 'ward1895', 'ward1901', 'ward1906', 'ward1911',
    'ward1931', 'ward1956', 'ward1963', 'ward1972', 'ward1982', 'ward1991',
    'ward2004', 'ward2011', 'ward2022',
]

chi_hex['since_year'] = chi_hex.apply(lambda r: compute_since_year(r, CHI_WARD_COLS), axis=1)
mil_hex['since_year'] = mil_hex.apply(lambda r: compute_since_year(r, MIL_WARD_COLS), axis=1)

print('\nChicago since_year distribution:')
print(chi_hex[chi_hex['ward2023'] > 0]['since_year'].value_counts().sort_index())
print('\nMilwaukee since_year distribution:')
print(mil_hex[mil_hex['ward2022'] > 0]['since_year'].value_counts().sort_index())


# ── Map generation ─────────────────────────────────────────────────────────────
def make_map(hex_gdf, ward_gdf, ward_cols, new_ward_col, ward_label_col,
             city_name, new_year, core_cutoff_year, output_path,
             cmap_name='viridis', min_hex_for_legend=10):
    """
    hex_gdf            : updated hexagons GeoDataFrame with 'since_year' column
    ward_gdf           : new ward boundaries GeoDataFrame
    ward_cols          : all ward columns in chronological order
    new_ward_col       : column name for the newest ward year (e.g. 'ward2023')
    ward_label_col     : column in ward_gdf to use for ward number labels
    new_year           : int, the new ward map year
    core_cutoff_year   : years <= this are grouped as 'Core Community'
    min_hex_for_legend : years with fewer hexagons than this are folded into Core Community
    """
    # Filter to hexagons inside the city (latest ward non-zero)
    in_city = hex_gdf[hex_gdf[new_ward_col] > 0].copy()

    # Count hexagons per since_year to filter sparse years from the legend
    since_counts = in_city['since_year'].value_counts()

    # Determine legend years: > core_cutoff_year AND enough hexagons to warrant own entry
    all_years = sorted([int(c.replace('ward', '')) for c in ward_cols])
    legend_years = [
        y for y in all_years
        if y > core_cutoff_year and since_counts.get(float(y), since_counts.get(y, 0)) >= min_hex_for_legend
    ]
    legend_years_desc = list(reversed(legend_years))  # newest first

    # Build colormap with enough steps for legend years + Core Community
    n_steps = len(legend_years) + 1  # +1 for Core Community
    cmap = plt.get_cmap(cmap_name, n_steps)

    # Color mapping: i=0 (newest) → yellow end of viridis; i=n_steps-1 (Core) → dark end
    # viridis(0)=dark purple, viridis(1)=bright yellow, so we use 1 - i/(n_steps-1)
    def cmap_color(i):
        return cmap(1.0 - i / max(n_steps - 1, 1))

    year_to_idx = {y: i for i, y in enumerate(legend_years_desc)}  # new_year→0

    def color_index(since_yr):
        if since_yr is None or (isinstance(since_yr, float) and np.isnan(since_yr)):
            return n_steps - 1
        yr = int(since_yr)
        if yr <= core_cutoff_year:
            return n_steps - 1  # Core Community = darkest index
        return year_to_idx.get(yr, n_steps - 1)

    in_city = in_city.copy()
    in_city['color_idx'] = in_city['since_year'].apply(color_index)

    # ── Build figure ───────────────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(13, 12))
    ax.set_aspect('equal')
    ax.axis('off')

    # Draw hexagons grouped by color index
    for idx in sorted(in_city['color_idx'].unique()):
        subset = in_city[in_city['color_idx'] == idx]
        color = cmap_color(idx)
        subset.plot(ax=ax, color=color, edgecolor='none', linewidth=0)

    # Draw new ward boundaries
    ward_gdf_plot = ward_gdf.to_crs(hex_gdf.crs)
    ward_gdf_plot.boundary.plot(ax=ax, color='black', linewidth=0.8)

    # Ward number labels at ward centroids
    for _, row in ward_gdf_plot.iterrows():
        centroid = row.geometry.centroid
        label = str(int(row[ward_label_col]))
        ax.annotate(label, xy=(centroid.x, centroid.y),
                    ha='center', va='center', fontsize=14, fontweight='bold',
                    color='black')

    # ── Legend in its own axes on the right ────────────────────────────────────
    legend_handles = []
    for i, yr in enumerate(legend_years_desc):
        color = cmap_color(i)
        legend_handles.append(mpatches.Patch(facecolor=color, edgecolor='none',
                                              label=f'In Ward Since {yr}'))
    legend_handles.append(mpatches.Patch(facecolor=cmap_color(n_steps - 1),
                                          edgecolor='none', label='Core Community'))
    legend_handles.append(plt.Line2D([0], [0], color='black', linewidth=1.2,
                                      label=f'{new_year} Ward Boundaries'))

    leg = ax.legend(
        handles=legend_handles,
        title='Hexagons',
        title_fontsize=17,
        fontsize=14,
        loc='center left',
        bbox_to_anchor=(1.01, 0.5),
        frameon=False,
        labelspacing=0.7,
        handlelength=1.5,
        handleheight=1.2,
    )
    leg.get_title().set_fontweight('bold')

    fig.savefig(output_path, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f'Saved {output_path}')


# Chicago: Core Community = last change in 1923 or earlier (matches old map style)
chi_wards_2023_plot = chi_wards_2023.copy()
make_map(
    hex_gdf=chi_hex,
    ward_gdf=chi_wards_2023_plot,
    ward_cols=CHI_WARD_COLS,
    new_ward_col='ward2023',
    ward_label_col='ward',
    city_name='Chicago',
    new_year=2023,
    core_cutoff_year=1923,
    output_path=Path('images/chicago_map_2023.png'),
    cmap_name='viridis',
)

# Milwaukee: Core Community = never changed (since 1846); all years after 1846 appear individually
make_map(
    hex_gdf=mil_hex,
    ward_gdf=mil_wards_2022,
    ward_cols=MIL_WARD_COLS,
    new_ward_col='ward2022',
    ward_label_col='DISTRICT',
    city_name='Milwaukee',
    new_year=2022,
    core_cutoff_year=1846,
    output_path=Path('images/milwaukee_map_2022.png'),
    cmap_name='viridis',
)

print('Done.')
