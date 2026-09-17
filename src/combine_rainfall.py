import xarray as xr
import pandas as pd
from pathlib import Path


# ============================================================
# SETTINGS
# ============================================================

input_dir = Path("data/processed/rainfall")

output_file = (
    input_dir / "mafuriko_rainfall_nairobi.csv"
)


# ============================================================
# FIND DAILY FILES
# ============================================================

files = sorted(
    input_dir.glob("IMERG_*_Nairobi.nc")
)

print("=" * 60)
print("MAFURIKO AI — COMBINING RAINFALL DATA")
print("=" * 60)

print()
print("Daily files found:", len(files))

if len(files) == 0:
    print("ERROR: No rainfall files found.")
    raise SystemExit(1)


# ============================================================
# READ EACH DAILY FILE
# ============================================================

all_data = []

for number, file in enumerate(files, start=1):

    print(
        f"[{number}/{len(files)}] "
        f"Reading {file.name}"
    )

    with xr.open_dataset(
        file,
        engine="netcdf4"
    ) as ds:

        # Convert the rainfall grid to a table
        df = ds["precipitation"].to_dataframe(
            name="precipitation"
        ).reset_index()

        all_data.append(df)


# ============================================================
# COMBINE EVERYTHING
# ============================================================

print()
print("Combining all daily data...")

rainfall = pd.concat(
    all_data,
    ignore_index=True
)


# ============================================================
# CLEAN THE TABLE
# ============================================================

rainfall = rainfall[
    [
        "time",
        "lon",
        "lat",
        "precipitation"
    ]
]

rainfall = rainfall.rename(
    columns={
        "time": "date",
        "lon": "longitude",
        "lat": "latitude"
    }
)

# Make date easier to work with
rainfall["date"] = pd.to_datetime(
    rainfall["date"]
).dt.date


# ============================================================
# SORT DATA
# ============================================================

rainfall = rainfall.sort_values(
    [
        "date",
        "latitude",
        "longitude"
    ]
).reset_index(drop=True)


# ============================================================
# SAVE CSV
# ============================================================

print()
print("Saving master rainfall dataset...")

rainfall.to_csv(
    output_file,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 60)
print("SUCCESS!")
print("=" * 60)

print()
print("Output:")
print(output_file)

print()
print("Rows:", len(rainfall))
print("Columns:", len(rainfall.columns))

print()
print("Date range:")
print(
    rainfall["date"].min(),
    "to",
    rainfall["date"].max()
)

print()
print("Grid cells:")

print(
    "  Longitudes:",
    rainfall["longitude"].nunique()
)

print(
    "  Latitudes:",
    rainfall["latitude"].nunique()
)

print(
    "  Total grid cells:",
    rainfall["longitude"].nunique()
    * rainfall["latitude"].nunique()
)

print()
print("Missing rainfall values:")

print(
    rainfall["precipitation"].isna().sum()
)

print()
print("First 10 rows:")
print(
    rainfall.head(10).to_string(index=False)
)

print()
print("Last 10 rows:")
print(
    rainfall.tail(10).to_string(index=False)
)

print()
print(
    "File size:",
    round(
        output_file.stat().st_size / (1024 * 1024),
        2
    ),
    "MB"
)
