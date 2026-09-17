import getpass
import time
from datetime import datetime, timedelta
from pathlib import Path

import requests
import xarray as xr


# ============================================================
# SETTINGS
# ============================================================

START_DATE = datetime(2020, 1, 1)
END_DATE = datetime(2025, 9, 1)

# Nairobi study area
WEST = 36.6
EAST = 37.2
SOUTH = -1.6
NORTH = -1.0

# NASA IMERG
BASE_URL = (
    "https://data.gesdisc.earthdata.nasa.gov/"
    "data/GPM_L3/GPM_3IMERGDF.07"
)

# Folders
raw_dir = Path("data/raw/rainfall")
processed_dir = Path("data/processed/rainfall")
logs_dir = Path("data/processed/rainfall_logs")

raw_dir.mkdir(parents=True, exist_ok=True)
processed_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)

# Progress files
success_log = logs_dir / "successful_dates.txt"
failed_log = logs_dir / "failed_dates.txt"


# ============================================================
# EARTHDATA TOKEN
# ============================================================

TOKEN = getpass.getpass(
    "Paste your Earthdata token (it will be hidden): "
)

HEADERS = {
    "Authorization": f"Bearer {TOKEN}"
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def read_log(filename):
    """Read dates already recorded in a log."""
    if not filename.exists():
        return set()

    with open(filename, "r", encoding="utf-8") as f:
        return {
            line.strip()
            for line in f
            if line.strip()
        }


def write_log(filename, date_string):
    """Add a date to a log."""
    with open(filename, "a", encoding="utf-8") as f:
        f.write(date_string + "\n")


def get_filename(date):
    """Create the NASA IMERG filename for a date."""
    date_string = date.strftime("%Y%m%d")

    return (
        f"3B-DAY.MS.MRG.3IMERG."
        f"{date_string}-S000000-E235959.V07B.nc4"
    )


def download_file(url, output_file, retries=3):
    """Download a NASA file with retries."""

    for attempt in range(1, retries + 1):

        try:
            print(
                f"  Download attempt "
                f"{attempt}/{retries}..."
            )

            response = requests.get(
                url,
                headers=HEADERS,
                stream=True,
                timeout=120
            )

            print(
                f"  HTTP status: "
                f"{response.status_code}"
            )

            if response.status_code != 200:
                print("  Download failed.")
                print(
                    "  NASA response:",
                    response.text[:300]
                )

                if attempt < retries:
                    print("  Waiting 10 seconds...")
                    time.sleep(10)

                continue

            with open(output_file, "wb") as f:

                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):
                    if chunk:
                        f.write(chunk)

            print("  Download successful!")

            return True

        except Exception as e:

            print("  Download error:", e)

            if attempt < retries:
                print("  Waiting 10 seconds...")
                time.sleep(10)

    return False


# ============================================================
# LOAD PROGRESS
# ============================================================

successful_dates = read_log(success_log)
failed_dates = read_log(failed_log)

print()
print("=" * 60)
print("MAFURIKO AI — IMERG RAINFALL COLLECTION")
print("=" * 60)

print()
print("Date range:")
print(
    START_DATE.strftime("%Y-%m-%d"),
    "to",
    END_DATE.strftime("%Y-%m-%d")
)

print()
print("Already completed:", len(successful_dates))
print("Previously failed:", len(failed_dates))


# ============================================================
# MAIN DOWNLOAD LOOP
# ============================================================

current_date = START_DATE
total_days = (END_DATE - START_DATE).days + 1
day_number = 0

while current_date <= END_DATE:

    day_number += 1

    date_string = current_date.strftime("%Y-%m-%d")

    output_file = (
        processed_dir
        / f"IMERG_{current_date.strftime('%Y%m%d')}_Nairobi.nc"
    )

    # --------------------------------------------------------
    # SKIP ALREADY COMPLETED DAYS
    # --------------------------------------------------------

    if (
        date_string in successful_dates
        and output_file.exists()
    ):
        print()
        print(
            f"[{day_number}/{total_days}] "
            f"{date_string} — already complete, skipping."
        )

        current_date += timedelta(days=1)
        continue

    print()
    print("=" * 60)
    print(
        f"[{day_number}/{total_days}] "
        f"Processing {date_string}"
    )
    print("=" * 60)

    filename = get_filename(current_date)

    year = current_date.strftime("%Y")
    month = current_date.strftime("%m")

    url = (
        f"{BASE_URL}/"
        f"{year}/{month}/{filename}"
    )

    raw_file = raw_dir / filename

    # --------------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------------

    print()
    print("Downloading NASA IMERG file...")

    success = download_file(
        url,
        raw_file
    )

    if not success:

        print()
        print(
            f"FAILED: {date_string}"
        )

        write_log(
            failed_log,
            date_string
        )

        current_date += timedelta(days=1)
        continue

    # --------------------------------------------------------
    # CROP
    # --------------------------------------------------------

    try:

        print()
        print("Cropping to Nairobi...")

        with xr.open_dataset(
            raw_file,
            engine="netcdf4"
        ) as ds:

            cropped = ds.sel(
                lon=slice(WEST, EAST),
                lat=slice(SOUTH, NORTH)
            )

            rainfall = cropped[["precipitation"]]

            rainfall.to_netcdf(
                output_file
            )

            print()
            print("Nairobi grid:")
            print(
                "  Longitude:",
                cropped.lon.values
            )
            print(
                "  Latitude:",
                cropped.lat.values
            )

        # ----------------------------------------------------
        # DELETE LARGE GLOBAL FILE
        # ----------------------------------------------------

        raw_file.unlink()

        # ----------------------------------------------------
        # RECORD SUCCESS
        # ----------------------------------------------------

        write_log(
            success_log,
            date_string
        )

        print()
        print(
            f"SUCCESS: {date_string}"
        )

        print(
            "Saved:",
            output_file
        )

        print(
            "Size:",
            round(
                output_file.stat().st_size
                / (1024 * 1024),
                4
            ),
            "MB"
        )

    except Exception as e:

        print()
        print(
            f"PROCESSING FAILED: {date_string}"
        )

        print("Error:", e)

        write_log(
            failed_log,
            date_string
        )

        # Delete incomplete/large file
        if raw_file.exists():
            raw_file.unlink()

    current_date += timedelta(days=1)


# ============================================================
# FINAL SUMMARY
# ============================================================

successful_dates = read_log(success_log)
failed_dates = read_log(failed_log)

print()
print("=" * 60)
print("COLLECTION FINISHED")
print("=" * 60)

print()
print("Successful dates:", len(successful_dates))
print("Failed dates:", len(failed_dates))

print()
print("Processed rainfall folder:")
print(processed_dir)

print()
print("Success log:")
print(success_log)

print()
print("Failed log:")
print(failed_log)

print()
print("Next step will be combining the daily files")
print("into one clean rainfall dataset.")