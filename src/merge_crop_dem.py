from pathlib import Path

import rasterio  # type: ignore[reportMissingImports]
from rasterio.merge import merge  # type: ignore[reportMissingImports]
from rasterio.windows import from_bounds  # type: ignore[reportMissingImports]
import numpy as np


# ============================================================
# MAFURIKO AI
# MERGE + CROP COPERNICUS DEM
# ============================================================

print("=" * 60)
print("MAFURIKO AI")
print("COPERNICUS DEM MERGE + NAIROBI CROP")
print("=" * 60)


# ------------------------------------------------------------
# PROJECT PATHS
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent

INPUT_DIR = PROJECT_ROOT / "data" / "raw" / "elevation"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "elevation"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# NAIROBI STUDY AREA
# ------------------------------------------------------------

WEST = 36.6
SOUTH = -1.6
EAST = 37.2
NORTH = -1.0


# ------------------------------------------------------------
# FIND DEM FILES
# ------------------------------------------------------------

dem_files = sorted(INPUT_DIR.glob("*.tif"))

print("\nInput directory:")
print(INPUT_DIR)

print(f"\nFound {len(dem_files)} DEM file(s).")

if len(dem_files) != 4:
    print("\nWARNING:")
    print("Expected 4 DEM tiles.")
    print("Found:", len(dem_files))

    for file in dem_files:
        print(" -", file.name)

    raise SystemExit("Stopping because the expected DEM tiles were not found.")


print("\nDEM tiles:")

for file in dem_files:
    print(" -", file.name)


# ------------------------------------------------------------
# OPEN DEM TILES
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("OPENING DEM TILES")
print("=" * 60)

src_files = []

for file in dem_files:
    print("\nOpening:")
    print(file.name)

    src = rasterio.open(file)

    print("CRS:", src.crs)
    print("Width:", src.width)
    print("Height:", src.height)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("Data type:", src.dtypes[0])

    src_files.append(src)


# ------------------------------------------------------------
# CHECK CRS
# ------------------------------------------------------------

crs_values = {src.crs.to_string() for src in src_files}

print("\nCRS values found:")

for crs in crs_values:
    print(" -", crs)

if len(crs_values) != 1:
    raise SystemExit("DEM tiles have different coordinate systems.")


# ------------------------------------------------------------
# MERGE THE FOUR TILES
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("MERGING DEM TILES")
print("=" * 60)

print("\nMerging...")

merged, merged_transform = merge(src_files)

print("Merge complete.")

print("\nMerged raster shape:")
print(merged.shape)

print("\nMerged resolution:")
print(
    merged_transform.a,
    abs(merged_transform.e)
)


# ------------------------------------------------------------
# MERGED BOUNDS
# ------------------------------------------------------------

merged_height = merged.shape[1]
merged_width = merged.shape[2]

merged_left = merged_transform.c
merged_top = merged_transform.f

merged_right = (
    merged_left +
    merged_width * merged_transform.a
)

merged_bottom = (
    merged_top +
    merged_height * merged_transform.e
)

print("\nMerged bounds:")

print("West :", merged_left)
print("South:", merged_bottom)
print("East :", merged_right)
print("North:", merged_top)


# ------------------------------------------------------------
# CREATE NAIROBI CROP WINDOW
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("CROPPING TO NAIROBI STUDY AREA")
print("=" * 60)

print("\nRequested bounds:")

print("West :", WEST)
print("South:", SOUTH)
print("East :", EAST)
print("North:", NORTH)


window = from_bounds(
    WEST,
    SOUTH,
    EAST,
    NORTH,
    transform=merged_transform
)

# Convert window coordinates to integer pixel boundaries
window = window.round_offsets().round_lengths()

print("\nCrop window:")
print(window)


# ------------------------------------------------------------
# CROP
# ------------------------------------------------------------

cropped = merged[
    :,
    window.row_off:window.row_off + window.height,
    window.col_off:window.col_off + window.width
]

cropped_transform = rasterio.windows.transform(
    window,
    merged_transform
)

print("\nCropped raster shape:")
print(cropped.shape)


# ------------------------------------------------------------
# CHECK DATA
# ------------------------------------------------------------

data = cropped[0].astype(np.float32)

# Replace extreme invalid values if present
nodata_mask = ~np.isfinite(data)

valid_data = data[~nodata_mask]

print("\n" + "=" * 60)
print("ELEVATION CHECK")
print("=" * 60)

print("\nValid pixels:", valid_data.size)

if valid_data.size > 0:

    print(
        "Minimum elevation:",
        round(float(np.min(valid_data)), 2),
        "m"
    )

    print(
        "Maximum elevation:",
        round(float(np.max(valid_data)), 2),
        "m"
    )

    print(
        "Mean elevation:",
        round(float(np.mean(valid_data)), 2),
        "m"
    )

    print(
        "Median elevation:",
        round(float(np.median(valid_data)), 2),
        "m"
    )


# ------------------------------------------------------------
# OUTPUT FILE
# ------------------------------------------------------------

output_file = (
    OUTPUT_DIR /
    "nairobi_dem_glo30.tif"
)

print("\n" + "=" * 60)
print("SAVING CROPPED DEM")
print("=" * 60)

print("\nOutput:")
print(output_file)


profile = src_files[0].profile.copy()

profile.update(
    {
        "driver": "GTiff",
        "height": cropped.shape[1],
        "width": cropped.shape[2],
        "transform": cropped_transform,
        "count": 1,
        "dtype": "float32",
        "compress": "deflate",
        "predictor": 3,
        "nodata": -9999,
    }
)


# Replace invalid pixels with nodata
output_data = cropped.astype(np.float32)

output_data[~np.isfinite(output_data)] = -9999


with rasterio.open(
    output_file,
    "w",
    **profile
) as dst:

    dst.write(output_data)


# ------------------------------------------------------------
# CLOSE SOURCE FILES
# ------------------------------------------------------------

for src in src_files:
    src.close()


# ------------------------------------------------------------
# VERIFY OUTPUT
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("VERIFYING OUTPUT")
print("=" * 60)

with rasterio.open(output_file) as check:

    print("\nFile:", check.name)
    print("CRS:", check.crs)
    print("Width:", check.width)
    print("Height:", check.height)
    print("Resolution:", check.res)
    print("Bounds:", check.bounds)
    print("Data type:", check.dtypes[0])
    print("NoData:", check.nodata)

    check_data = check.read(1)

    valid = check_data[
        check_data != check.nodata
    ]

    print(
        "Minimum:",
        round(float(np.min(valid)), 2),
        "m"
    )

    print(
        "Maximum:",
        round(float(np.max(valid)), 2),
        "m"
    )

    print(
        "Mean:",
        round(float(np.mean(valid)), 2),
        "m"
    )


# ------------------------------------------------------------
# DONE
# ------------------------------------------------------------

print("\n" + "=" * 60)
print("SUCCESS!")
print("=" * 60)

print("\nNairobi DEM created successfully.")

print("\nSaved to:")

print(output_file)

print("\nNext step:")
print("Calculate terrain slope from the DEM.")
