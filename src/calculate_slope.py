from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import Affine


# ============================================================
# MAFURIKO AI
# TERRAIN SLOPE CALCULATION
# ============================================================

print("=" * 60)
print("MAFURIKO AI")
print("TERRAIN SLOPE CALCULATION")
print("=" * 60)


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_FILE = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "elevation"
    / "nairobi_dem_glo30.tif"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "elevation"
)

OUTPUT_FILE = OUTPUT_DIR / "nairobi_slope_glo30.tif"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# CHECK INPUT
# ------------------------------------------------------------

print("\nInput DEM:")
print(INPUT_FILE)

if not INPUT_FILE.exists():
    raise SystemExit(
        "\nERROR: Nairobi DEM was not found."
    )


# ------------------------------------------------------------
# OPEN DEM
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("READING DEM")
print("=" * 60)

with rasterio.open(INPUT_FILE) as src:

    dem = src.read(1).astype(np.float32)

    profile = src.profile.copy()

    transform = src.transform

    crs = src.crs

    nodata = src.nodata

    width = src.width
    height = src.height

    bounds = src.bounds

    resolution = src.res


print("\nDEM dimensions:")
print("Width :", width)
print("Height:", height)

print("\nResolution:")
print(resolution)

print("\nCRS:")
print(crs)

print("\nBounds:")
print(bounds)

print("\nNoData:")
print(nodata)


# ------------------------------------------------------------
# VALID DATA MASK
# ------------------------------------------------------------

if nodata is not None:

    valid_mask = (
        np.isfinite(dem)
        & (dem != nodata)
    )

else:

    valid_mask = np.isfinite(dem)


valid_values = dem[valid_mask]

print("\nValid DEM pixels:")
print(valid_values.size)


# ------------------------------------------------------------
# CONVERT DEGREE PIXEL SIZE TO METRES
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CALCULATING PIXEL SIZE")
print("=" * 60)

pixel_width_deg = abs(transform.a)
pixel_height_deg = abs(transform.e)

# Approximate latitude at the center of the study area
center_lat = (
    (bounds.top + bounds.bottom) / 2.0
)

# Earth radius in metres
EARTH_RADIUS = 6371000.0

# Convert latitude/longitude degrees to metres
meters_per_degree_lat = (
    np.pi * EARTH_RADIUS / 180.0
)

meters_per_degree_lon = (
    np.pi
    * EARTH_RADIUS
    * np.cos(np.radians(center_lat))
    / 180.0
)

pixel_width_m = (
    pixel_width_deg
    * meters_per_degree_lon
)

pixel_height_m = (
    pixel_height_deg
    * meters_per_degree_lat
)


print("\nPixel width:")
print(round(pixel_width_m, 2), "metres")

print("\nPixel height:")
print(round(pixel_height_m, 2), "metres")

print("\nApproximate DEM pixel size:")
print(
    round(
        (pixel_width_m + pixel_height_m) / 2,
        2
    ),
    "metres"
)


# ------------------------------------------------------------
# PREPARE DEM FOR GRADIENT CALCULATION
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CALCULATING TERRAIN SLOPE")
print("=" * 60)

# Copy DEM so the original is never modified
dem_work = dem.copy()

# Temporarily replace invalid cells with nearest-safe values
# so numpy.gradient does not propagate NaNs everywhere.
if np.any(~valid_mask):

    valid_mean = float(np.mean(valid_values))

    dem_work[~valid_mask] = valid_mean


# ------------------------------------------------------------
# CALCULATE ELEVATION GRADIENTS
# ------------------------------------------------------------

print("\nCalculating elevation gradients...")

dz_dy, dz_dx = np.gradient(
    dem_work,
    pixel_height_m,
    pixel_width_m
)


# ------------------------------------------------------------
# CALCULATE SLOPE
# ------------------------------------------------------------

print("Calculating slope angle...")

slope_radians = np.arctan(
    np.sqrt(
        dz_dx ** 2
        +
        dz_dy ** 2
    )
)

slope_degrees = np.degrees(
    slope_radians
).astype(np.float32)


# Restore NoData pixels
slope_degrees[~valid_mask] = -9999.0


# ------------------------------------------------------------
# SLOPE STATISTICS
# ------------------------------------------------------------

valid_slope = slope_degrees[
    slope_degrees != -9999.0
]

print("\n" + "=" * 60)
print("SLOPE STATISTICS")
print("=" * 60)

print("\nMinimum slope:")
print(
    round(float(np.min(valid_slope)), 4),
    "degrees"
)

print("\nMaximum slope:")
print(
    round(float(np.max(valid_slope)), 4),
    "degrees"
)

print("\nMean slope:")
print(
    round(float(np.mean(valid_slope)), 4),
    "degrees"
)

print("\nMedian slope:")
print(
    round(float(np.median(valid_slope)), 4),
    "degrees"
)

print("\nSlope percentiles:")

print(
    "25th percentile:",
    round(
        float(np.percentile(valid_slope, 25)),
        4
    ),
    "degrees"
)

print(
    "50th percentile:",
    round(
        float(np.percentile(valid_slope, 50)),
        4
    ),
    "degrees"
)

print(
    "75th percentile:",
    round(
        float(np.percentile(valid_slope, 75)),
        4
    ),
    "degrees"
)

print(
    "90th percentile:",
    round(
        float(np.percentile(valid_slope, 90)),
        4
    ),
    "degrees"
)

print(
    "95th percentile:",
    round(
        float(np.percentile(valid_slope, 95)),
        4
    ),
    "degrees"
)


# ------------------------------------------------------------
# SLOPE CATEGORIES
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SLOPE CATEGORIES")
print("=" * 60)

flat = valid_slope < 2

gentle = (
    (valid_slope >= 2)
    & (valid_slope < 5)
)

moderate = (
    (valid_slope >= 5)
    & (valid_slope < 10)
)

steep = (
    (valid_slope >= 10)
    & (valid_slope < 20)
)

very_steep = valid_slope >= 20


total_pixels = valid_slope.size


print(
    "\n< 2°:",
    round(
        100 * np.sum(flat) / total_pixels,
        2
    ),
    "%"
)

print(
    "2°–5°:",
    round(
        100 * np.sum(gentle) / total_pixels,
        2
    ),
    "%"
)

print(
    "5°–10°:",
    round(
        100 * np.sum(moderate) / total_pixels,
        2
    ),
    "%"
)

print(
    "10°–20°:",
    round(
        100 * np.sum(steep) / total_pixels,
        2
    ),
    "%"
)

print(
    ">= 20°:",
    round(
        100 * np.sum(very_steep) / total_pixels,
        2
    ),
    "%"
)


# ------------------------------------------------------------
# SAVE SLOPE RASTER
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SAVING SLOPE RASTER")
print("=" * 60)

profile.update(
    {
        "driver": "GTiff",
        "dtype": "float32",
        "count": 1,
        "nodata": -9999.0,
        "compress": "deflate",
        "predictor": 3,
    }
)


with rasterio.open(
    OUTPUT_FILE,
    "w",
    **profile
) as dst:

    dst.write(
        slope_degrees,
        1
    )


print("\nSaved:")
print(OUTPUT_FILE)


# ------------------------------------------------------------
# VERIFY OUTPUT
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("VERIFYING OUTPUT")
print("=" * 60)

with rasterio.open(OUTPUT_FILE) as check:

    check_data = check.read(1)

    valid = check_data[
        check_data != -9999.0
    ]

    print("\nFile:")
    print(check.name)

    print("\nWidth:")
    print(check.width)

    print("\nHeight:")
    print(check.height)

    print("\nCRS:")
    print(check.crs)

    print("\nResolution:")
    print(check.res)

    print("\nBounds:")
    print(check.bounds)

    print("\nData type:")
    print(check.dtypes[0])

    print("\nNoData:")
    print(check.nodata)

    print("\nVerified minimum slope:")
    print(
        round(float(np.min(valid)), 4),
        "degrees"
    )

    print("\nVerified maximum slope:")
    print(
        round(float(np.max(valid)), 4),
        "degrees"
    )


# ------------------------------------------------------------
# DONE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SUCCESS!")
print("=" * 60)

print("\nTerrain slope has been calculated.")

print("\nOutput:")
print(
    "data/processed/elevation/"
    "nairobi_slope_glo30.tif"
)

