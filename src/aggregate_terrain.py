from pathlib import Path

import numpy as np
import pandas as pd
import rasterio  # pyright: ignore[reportMissingImports]
from rasterio.windows import from_bounds  # pyright: ignore[reportMissingImports]


# ============================================================
# MAFURIKO AI
# AGGREGATE TERRAIN FEATURES TO RAINFALL GRID
# ============================================================

print("=" * 60)
print("MAFURIKO AI")
print("TERRAIN FEATURE AGGREGATION")
print("=" * 60)


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAINFALL_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "rainfall"
    / "mafuriko_rainfall_nairobi.csv"
)

DEM_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "elevation"
    / "nairobi_dem_glo30.tif"
)

SLOPE_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "elevation"
    / "nairobi_slope_glo30.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "features"
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_FILE = (
    OUTPUT_DIR
    / "mafuriko_terrain_features.csv"
)


# ------------------------------------------------------------
# RAINFALL GRID
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("READING RAINFALL GRID")
print("=" * 60)

rainfall = pd.read_csv(
    RAINFALL_FILE
)

longitude_values = sorted(
    rainfall["longitude"].unique()
)

latitude_values = sorted(
    rainfall["latitude"].unique()
)

print("\nLongitude cells:")
print(longitude_values)

print("\nLatitude cells:")
print(latitude_values)

print(
    "\nTotal cells:",
    len(longitude_values)
    * len(latitude_values)
)


# ------------------------------------------------------------
# DETERMINE RAINFALL CELL SIZE
# ------------------------------------------------------------

if len(longitude_values) < 2:
    raise SystemExit(
        "Not enough longitude values to determine cell size."
    )

if len(latitude_values) < 2:
    raise SystemExit(
        "Not enough latitude values to determine cell size."
    )


lon_spacing = (
    longitude_values[1]
    - longitude_values[0]
)

lat_spacing = (
    latitude_values[1]
    - latitude_values[0]
)


print("\nRainfall longitude spacing:")
print(lon_spacing, "degrees")

print("\nRainfall latitude spacing:")
print(lat_spacing, "degrees")


# Each rainfall coordinate represents the center
# of a rainfall grid cell.

half_lon = lon_spacing / 2
half_lat = lat_spacing / 2


# ------------------------------------------------------------
# OPEN DEM
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("OPENING DEM")
print("=" * 60)

dem_src = rasterio.open(
    DEM_FILE
)

print("\nDEM:")
print(dem_src.name)

print("CRS:", dem_src.crs)
print("Resolution:", dem_src.res)
print("Bounds:", dem_src.bounds)


# ------------------------------------------------------------
# OPEN SLOPE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("OPENING SLOPE")
print("=" * 60)

slope_src = rasterio.open(
    SLOPE_FILE
)

print("\nSlope:")
print(slope_src.name)

print("CRS:", slope_src.crs)
print("Resolution:", slope_src.res)
print("Bounds:", slope_src.bounds)


# ------------------------------------------------------------
# CHECK DEM + SLOPE MATCH
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CHECKING TERRAIN RASTERS")
print("=" * 60)

if dem_src.crs != slope_src.crs:
    raise SystemExit(
        "DEM and slope CRS do not match."
    )

if dem_src.width != slope_src.width:
    raise SystemExit(
        "DEM and slope widths do not match."
    )

if dem_src.height != slope_src.height:
    raise SystemExit(
        "DEM and slope heights do not match."
    )

print("\nDEM and slope grids match.")


# ------------------------------------------------------------
# AGGREGATE EACH RAINFALL CELL
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("AGGREGATING TERRAIN")
print("=" * 60)

terrain_records = []


total_cells = (
    len(longitude_values)
    * len(latitude_values)
)

cell_number = 0


for latitude in latitude_values:

    for longitude in longitude_values:

        cell_number += 1

        print(
            f"\nProcessing cell "
            f"{cell_number}/{total_cells}: "
            f"lon={longitude}, lat={latitude}"
        )


        # ----------------------------------------------------
        # RAINFALL CELL BOUNDARIES
        # ----------------------------------------------------

        west = longitude - half_lon
        east = longitude + half_lon

        south = latitude - half_lat
        north = latitude + half_lat


        print(
            "Bounds:",
            west,
            south,
            east,
            north
        )


        # ----------------------------------------------------
        # DEM WINDOW
        # ----------------------------------------------------

        dem_window = from_bounds(
            west,
            south,
            east,
            north,
            transform=dem_src.transform
        )

        dem_window = (
            dem_window
            .round_offsets()
            .round_lengths()
        )


        # ----------------------------------------------------
        # SLOPE WINDOW
        # ----------------------------------------------------

        slope_window = from_bounds(
            west,
            south,
            east,
            north,
            transform=slope_src.transform
        )

        slope_window = (
            slope_window
            .round_offsets()
            .round_lengths()
        )


        # ----------------------------------------------------
        # READ DEM
        # ----------------------------------------------------

        dem_data = dem_src.read(
            1,
            window=dem_window
        ).astype(np.float32)


        # ----------------------------------------------------
        # READ SLOPE
        # ----------------------------------------------------

        slope_data = slope_src.read(
            1,
            window=slope_window
        ).astype(np.float32)


        # ----------------------------------------------------
        # VALID DEM VALUES
        # ----------------------------------------------------

        dem_valid = dem_data[
            np.isfinite(dem_data)
            & (dem_data != -9999)
        ]


        # ----------------------------------------------------
        # VALID SLOPE VALUES
        # ----------------------------------------------------

        slope_valid = slope_data[
            np.isfinite(slope_data)
            & (slope_data != -9999)
        ]


        # ----------------------------------------------------
        # SAFETY CHECK
        # ----------------------------------------------------

        if dem_valid.size == 0:

            raise RuntimeError(
                f"No valid DEM data for "
                f"cell {longitude}, {latitude}"
            )

        if slope_valid.size == 0:

            raise RuntimeError(
                f"No valid slope data for "
                f"cell {longitude}, {latitude}"
            )


        # ----------------------------------------------------
        # TERRAIN STATISTICS
        # ----------------------------------------------------

        record = {

            "longitude": longitude,

            "latitude": latitude,

            "mean_elevation":
                float(np.mean(dem_valid)),

            "min_elevation":
                float(np.min(dem_valid)),

            "max_elevation":
                float(np.max(dem_valid)),

            "mean_slope":
                float(np.mean(slope_valid)),

            "max_slope":
                float(np.max(slope_valid)),

            "terrain_pixels":
                int(dem_valid.size),

        }


        terrain_records.append(
            record
        )


# ------------------------------------------------------------
# CLOSE RASTERS
# ------------------------------------------------------------

dem_src.close()
slope_src.close()


# ------------------------------------------------------------
# CREATE TERRAIN DATAFRAME
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CREATING TERRAIN TABLE")
print("=" * 60)

terrain = pd.DataFrame(
    terrain_records
)


print("\nTerrain rows:")
print(len(terrain))

print("\nTerrain columns:")
print(list(terrain.columns))


# ------------------------------------------------------------
# DISPLAY TERRAIN TABLE
# ------------------------------------------------------------

print("\nTerrain statistics:")

print(
    terrain[
        [
            "mean_elevation",
            "min_elevation",
            "max_elevation",
            "mean_slope",
            "max_slope",
        ]
    ].describe()
)


# ------------------------------------------------------------
# CHECK FOR MISSING VALUES
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CHECKING TERRAIN DATA")
print("=" * 60)

print("\nMissing values:")

print(
    terrain.isna().sum()
)


# ------------------------------------------------------------
# CHECK UNIQUE CELLS
# ------------------------------------------------------------

unique_cells = terrain[
    [
        "longitude",
        "latitude"
    ]
].drop_duplicates()


print("\nUnique terrain cells:")
print(len(unique_cells))


expected_cells = (
    len(longitude_values)
    * len(latitude_values)
)


print("\nExpected cells:")
print(expected_cells)


if len(unique_cells) != expected_cells:

    raise RuntimeError(
        "Terrain cell count does not match "
        "the rainfall grid."
    )


# ------------------------------------------------------------
# SAVE TERRAIN FEATURES
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SAVING TERRAIN FEATURES")
print("=" * 60)

terrain.to_csv(
    OUTPUT_FILE,
    index=False
)


print("\nSaved:")
print(OUTPUT_FILE)


# ------------------------------------------------------------
# SHOW FINAL TABLE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("FINAL TERRAIN FEATURE TABLE")
print("=" * 60)

print(
    terrain.to_string(
        index=False
    )
)


# ------------------------------------------------------------
# DONE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SUCCESS!")
print("=" * 60)

print(
    "\nTerrain features have been "
    "aggregated to the rainfall grid."
)

print("\nOutput:")
print(
    "data/processed/features/"
    "mafuriko_terrain_features.csv"
)

print("\nNext step:")
print(
    "Join terrain features with "
    "daily rainfall."
)