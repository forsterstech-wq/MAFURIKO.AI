import xarray as xr
from pathlib import Path

# Input NASA IMERG file
input_file = Path(
    "data/raw/rainfall/"
    "3B-DAY.MS.MRG.3IMERG.20200318-V07B.nc4"
)

# Nairobi study area
WEST = 36.6
EAST = 37.2
SOUTH = -1.6
NORTH = -1.0

# Output folder
output_dir = Path("data/processed/rainfall")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "IMERG_20200318_Nairobi.nc"

print("Opening IMERG file...")

with xr.open_dataset(input_file, engine="netcdf4") as ds:

    print("Original grid:")
    print("  Longitude:", float(ds.lon.min()), "to", float(ds.lon.max()))
    print("  Latitude:", float(ds.lat.min()), "to", float(ds.lat.max()))

    # Extract Nairobi area
    cropped = ds.sel(
        lon=slice(WEST, EAST),
        lat=slice(SOUTH, NORTH)
    )

    print()
    print("Cropped Nairobi grid:")
    print(cropped)

    # Keep only the rainfall variable
    rainfall = cropped[["precipitation"]]

    # Save
    rainfall.to_netcdf(output_file)

print()
print("SUCCESS!")
print("Saved to:", output_file)
print("File size:", output_file.stat().st_size / (1024 * 1024), "MB")