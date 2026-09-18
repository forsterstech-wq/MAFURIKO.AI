from pathlib import Path

import pandas as pd
import rasterio


# ============================================================
# MAFURIKO AI
# SPATIAL ALIGNMENT CHECK
# ============================================================

print("=" * 60)
print("MAFURIKO AI")
print("RAINFALL + DEM SPATIAL ALIGNMENT CHECK")
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


# ------------------------------------------------------------
# CHECK FILES
# ------------------------------------------------------------

print("\nChecking required files...")

for file in [
    RAINFALL_FILE,
    DEM_FILE,
    SLOPE_FILE,
]:

    print("\n", file)

    if not file.exists():
        raise SystemExit(
            f"ERROR: File not found:\n{file}"
        )

    print("OK")


# ------------------------------------------------------------
# READ RAINFALL DATA
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("RAINFALL GRID")
print("=" * 60)

rainfall = pd.read_csv(RAINFALL_FILE)

print("\nRows:")
print(len(rainfall))

print("\nColumns:")
print(list(rainfall.columns))

print("\nDate range:")
print(rainfall["date"].min())
print("to")
print(rainfall["date"].max())

print("\nUnique longitude values:")

longitude_values = sorted(
    rainfall["longitude"].unique()
)

print(longitude_values)

print("\nUnique latitude values:")

latitude_values = sorted(
    rainfall["latitude"].unique()
)

print(latitude_values)

print("\nNumber of longitude cells:")
print(len(longitude_values))

print("\nNumber of latitude cells:")
print(len(latitude_values))

print("\nTotal spatial cells:")
print(
    len(longitude_values)
    * len(latitude_values)
)


# ------------------------------------------------------------
# RAINFALL SPACING
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("RAINFALL GRID SPACING")
print("=" * 60)

if len(longitude_values) > 1:

    lon_spacing = (
        longitude_values[1]
        - longitude_values[0]
    )

    print(
        "\nLongitude spacing:",
        lon_spacing,
        "degrees"
    )

if len(latitude_values) > 1:

    lat_spacing = (
        latitude_values[1]
        - latitude_values[0]
    )

    print(
        "Latitude spacing:",
        lat_spacing,
        "degrees"
    )


# ------------------------------------------------------------
# RAINFALL BOUNDS
# ------------------------------------------------------------

print("\nRainfall coordinate bounds:")

print(
    "West :",
    rainfall["longitude"].min()
)

print(
    "East :",
    rainfall["longitude"].max()
)

print(
    "South:",
    rainfall["latitude"].min()
)

print(
    "North:",
    rainfall["latitude"].max()
)


# ------------------------------------------------------------
# READ DEM
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("DEM")
print("=" * 60)

with rasterio.open(DEM_FILE) as dem:

    print("\nCRS:")
    print(dem.crs)

    print("\nWidth:")
    print(dem.width)

    print("\nHeight:")
    print(dem.height)

    print("\nResolution:")
    print(dem.res)

    print("\nBounds:")
    print(dem.bounds)


# ------------------------------------------------------------
# READ SLOPE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SLOPE")
print("=" * 60)

with rasterio.open(SLOPE_FILE) as slope:

    print("\nCRS:")
    print(slope.crs)

    print("\nWidth:")
    print(slope.width)

    print("\nHeight:")
    print(slope.height)

    print("\nResolution:")
    print(slope.res)

    print("\nBounds:")
    print(slope.bounds)


# ------------------------------------------------------------
# OVERLAP CHECK
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SPATIAL OVERLAP CHECK")
print("=" * 60)

with rasterio.open(DEM_FILE) as dem:

    dem_left = dem.bounds.left
    dem_right = dem.bounds.right
    dem_bottom = dem.bounds.bottom
    dem_top = dem.bounds.top


rain_left = rainfall["longitude"].min()
rain_right = rainfall["longitude"].max()
rain_bottom = rainfall["latitude"].min()
rain_top = rainfall["latitude"].max()


print("\nDEM:")
print(
    dem_left,
    dem_bottom,
    dem_right,
    dem_top
)

print("\nRainfall coordinates:")
print(
    rain_left,
    rain_bottom,
    rain_right,
    rain_top
)


overlap = (
    rain_right >= dem_left
    and rain_left <= dem_right
    and rain_top >= dem_bottom
    and rain_bottom <= dem_top
)


print("\nSpatial overlap:")

if overlap:
    print("YES")
else:
    print("NO")


# ------------------------------------------------------------
# GRID CELL VALIDATION
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("RAINFALL CELL VALIDATION")
print("=" * 60)

outside_cells = []

for lat in latitude_values:

    for lon in longitude_values:

        if not (
            dem_left <= lon <= dem_right
            and
            dem_bottom <= lat <= dem_top
        ):

            outside_cells.append(
                (lon, lat)
            )


print(
    "\nRainfall cells outside DEM:",
    len(outside_cells)
)


if outside_cells:

    print("\nOutside cells:")

    for cell in outside_cells:

        print(
            "Longitude:",
            cell[0],
            "Latitude:",
            cell[1]
        )

else:

    print(
        "\nAll rainfall grid coordinates "
        "fall within the DEM."
    )


# ------------------------------------------------------------
# TEMPORAL CHECK
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("TEMPORAL CHECK")
print("=" * 60)

unique_dates = rainfall["date"].nunique()

print("\nUnique rainfall dates:")
print(unique_dates)

expected_rows = (
    unique_dates
    * len(longitude_values)
    * len(latitude_values)
)

print("\nExpected rows:")
print(expected_rows)

print("\nActual rows:")
print(len(rainfall))

if len(rainfall) == expected_rows:

    print(
        "\nTemporal/spatial grid is COMPLETE."
    )

else:

    print(
        "\nWARNING: Some rainfall grid "
        "observations may be missing."
    )


# ------------------------------------------------------------
# MISSING VALUE CHECK
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("MISSING VALUE CHECK")
print("=" * 60)

print("\nMissing values:")

print(
    rainfall[
        [
            "date",
            "longitude",
            "latitude",
            "precipitation",
        ]
    ]
    .isna()
    .sum()
)


# ------------------------------------------------------------
# FINAL RESULT
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("FINAL RESULT")
print("=" * 60)

if overlap and not outside_cells:

    print(
        "\nSUCCESS:"
    )

    print(
        "Rainfall and terrain datasets "
        "spatially overlap."
    )

    print(
        "\nWe can now aggregate DEM and slope "
        "values into each rainfall grid cell."
    )

else:

    print(
        "\nWARNING:"
    )

    print(
        "Spatial alignment needs attention "
        "before feature construction."
    )


print("\n" + "=" * 60)
print("CHECK COMPLETE")
print("=" * 60)