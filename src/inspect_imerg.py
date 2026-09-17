import xarray as xr
from pathlib import Path

# The NASA IMERG file we already downloaded
file = Path(
    "data/raw/rainfall/"
    "3B-DAY.MS.MRG.3IMERG.20200318-V07B.nc4"
)

print("Opening NASA IMERG file...")
print()

with xr.open_dataset(file, engine="netcdf4") as ds:

    print("=== DATASET STRUCTURE ===")
    print(ds)

    print()
    print("=== DIMENSIONS ===")
    print(ds.dims)

    print()
    print("=== DATA VARIABLES ===")

    for name in ds.data_vars:
        variable = ds[name]

        print(f"\n{name}")
        print("  dimensions:", variable.dims)
        print("  shape:", variable.shape)
        print("  units:", variable.attrs.get("units"))
        print("  long name:", variable.attrs.get("long_name"))  