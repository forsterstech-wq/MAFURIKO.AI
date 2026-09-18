import os
import sys
import requests
import boto3
from pathlib import Path


# ============================================================
# MAFURIKO AI
# COPERNICUS DEM GLO-30 COG DOWNLOADER
# ============================================================

STAC_URL = "https://stac.dataspace.copernicus.eu/v1"

STAC_SEARCH_URL = f"{STAC_URL}/search"

S3_ENDPOINT = "https://eodata.dataspace.copernicus.eu"

S3_BUCKET = "eodata"

OUTPUT_DIR = Path("data/raw/elevation")

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# Nairobi bounding box
# [west, south, east, north]

NAIROBI_BBOX = [
    36.6,
    -1.6,
    37.2,
    -1.0
]


COLLECTION_ID = "cop-dem-glo-30-dged-cog"


# ============================================================
# CREATE S3 CLIENT
# ============================================================

def create_s3_client():

    access_key = os.getenv(
        "CDSE_S3_ACCESS_KEY"
    )

    secret_key = os.getenv(
        "CDSE_S3_SECRET_KEY"
    )

    print()
    print("=" * 60)
    print("CHECKING S3 CREDENTIALS")
    print("=" * 60)

    if not access_key:

        print(
            "ERROR: CDSE_S3_ACCESS_KEY is missing."
        )

        return None

    if not secret_key:

        print(
            "ERROR: CDSE_S3_SECRET_KEY is missing."
        )

        return None

    print("Access key: FOUND")
    print("Secret key: FOUND")

    print()
    print("Creating CDSE S3 client...")

    try:

        s3 = boto3.client(
            "s3",
            endpoint_url=S3_ENDPOINT,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="default"
        )

    except Exception as e:

        print()
        print("Could not create S3 client:")
        print(e)

        return None

    print(
        "S3 client created successfully."
    )

    return s3


# ============================================================
# SEARCH STAC
# ============================================================

def search_dem_tiles():

    print()
    print("=" * 60)
    print("SEARCHING CDSE STAC")
    print("=" * 60)

    print()
    print("Collection:")
    print(COLLECTION_ID)

    print()
    print("Nairobi bounding box:")
    print(NAIROBI_BBOX)

    payload = {
        "collections": [
            COLLECTION_ID
        ],
        "bbox": NAIROBI_BBOX,
        "limit": 20
    }

    print()
    print("Sending STAC search...")

    try:

        response = requests.post(
            STAC_SEARCH_URL,
            json=payload,
            timeout=60
        )

    except Exception as e:

        print()
        print("STAC request failed:")
        print(e)

        return []

    print()
    print(
        "HTTP status:",
        response.status_code
    )

    if response.status_code != 200:

        print()
        print("STAC search failed:")
        print(response.text[:3000])

        return []

    data = response.json()

    features = data.get(
        "features",
        []
    )

    print()
    print(
        f"STAC returned {len(features)} item(s)."
    )

    return features


# ============================================================
# EXTRACT DATA ASSET
# ============================================================

def get_dem_asset(item):

    item_id = item.get(
        "id",
        "UNKNOWN"
    )

    assets = item.get(
        "assets",
        {}
    )

    print()
    print("-" * 60)
    print("ITEM")
    print("-" * 60)

    print(
        "ID:",
        item_id
    )

    print()
    print("Available assets:")

    for asset_name, asset in assets.items():

        print(
            " ",
            asset_name,
            "->",
            asset.get("href")
        )

    # The CDSE COG collection uses
    # the "data" asset.
    data_asset = assets.get(
        "data"
    )

    if not data_asset:

        print()
        print(
            "WARNING: No 'data' asset found."
        )

        return None

    href = data_asset.get(
        "href"
    )

    if not href:

        print(
            "WARNING: Data asset has no href."
        )

        return None

    print()
    print("DEM data asset:")
    print(href)

    return {
        "id": item_id,
        "href": href
    }


# ============================================================
# CONVERT S3 URI
# ============================================================

def parse_s3_uri(s3_uri):

    if not s3_uri.startswith(
        "s3://"
    ):

        print()
        print(
            "ERROR: Expected an S3 URI:"
        )

        print(s3_uri)

        return None, None

    without_scheme = s3_uri[
        5:
    ]

    parts = without_scheme.split(
        "/",
        1
    )

    if len(parts) != 2:

        print()
        print(
            "ERROR: Invalid S3 URI:"
        )

        print(s3_uri)

        return None, None

    bucket = parts[0]

    key = parts[1]

    return bucket, key


# ============================================================
# DOWNLOAD ONE DEM
# ============================================================

def download_dem(
    s3,
    item
):

    item_id = item["id"]

    href = item["href"]

    bucket, key = parse_s3_uri(
        href
    )

    if not bucket or not key:

        return False

    print()
    print("=" * 60)
    print("DOWNLOADING DEM")
    print("=" * 60)

    print()
    print("STAC item:")
    print(item_id)

    print()
    print("Bucket:")
    print(bucket)

    print()
    print("S3 key:")
    print(key)

    # --------------------------------------------------------
    # Get filename
    # --------------------------------------------------------

    filename = Path(key).name

    local_file = (
        OUTPUT_DIR / filename
    )

    print()
    print("Local file:")
    print(local_file)

    # --------------------------------------------------------
    # Check whether already downloaded
    # --------------------------------------------------------

    if local_file.exists():

        print()
        print(
            "File already exists."
        )

        print(
            "Skipping download."
        )

        return True

    # --------------------------------------------------------
    # Get object metadata
    # --------------------------------------------------------

    try:

        metadata = s3.head_object(
            Bucket=bucket,
            Key=key
        )

    except Exception as e:

        print()
        print(
            "Could not access S3 object:"
        )

        print(e)

        return False

    object_size = metadata.get(
        "ContentLength",
        0
    )

    size_mb = (
        object_size
        / (1024 * 1024)
    )

    print()
    print(
        f"Remote file size: "
        f"{size_mb:.2f} MB"
    )

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    print()
    print("Downloading...")

    try:

        s3.download_file(
            bucket,
            key,
            str(local_file)
        )

    except Exception as e:

        print()
        print(
            "Download failed:"
        )

        print(e)

        return False

    # --------------------------------------------------------
    # Verify
    # --------------------------------------------------------

    if not local_file.exists():

        print()
        print(
            "Download appeared to complete "
            "but file was not found."
        )

        return False

    local_size = (
        local_file.stat().st_size
    )

    print()
    print(
        f"Downloaded: "
        f"{local_size / (1024 * 1024):.2f} MB"
    )

    print()
    print(
        "Saved successfully:"
    )

    print(
        local_file.resolve()
    )

    return True


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("MAFURIKO AI")
    print("COPERNICUS DEM GLO-30 COG DOWNLOADER")
    print("=" * 60)

    print()
    print(
        "Target collection:"
    )

    print(
        COLLECTION_ID
    )

    # --------------------------------------------------------
    # Check S3 environment variables
    # --------------------------------------------------------

    if not os.getenv(
        "CDSE_S3_ACCESS_KEY"
    ):

        print()
        print(
            "ERROR: CDSE_S3_ACCESS_KEY missing."
        )

        sys.exit(1)

    if not os.getenv(
        "CDSE_S3_SECRET_KEY"
    ):

        print()
        print(
            "ERROR: CDSE_S3_SECRET_KEY missing."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Search STAC
    # --------------------------------------------------------

    features = search_dem_tiles()

    if not features:

        print()
        print(
            "No DEM tiles were found."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Extract data assets
    # --------------------------------------------------------

    dem_items = []

    for feature in features:

        dem = get_dem_asset(
            feature
        )

        if dem:

            dem_items.append(
                dem
            )

    print()
    print("=" * 60)
    print("DEM TILE SUMMARY")
    print("=" * 60)

    print()
    print(
        f"Found {len(dem_items)} "
        f"DEM data assets."
    )

    for item in dem_items:

        print()
        print(
            item["id"]
        )

        print(
            item["href"]
        )

    # --------------------------------------------------------
    # Create S3 client
    # --------------------------------------------------------

    s3 = create_s3_client()

    if s3 is None:

        sys.exit(1)

    # --------------------------------------------------------
    # Confirm
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("READY")
    print("=" * 60)

    print()
    print(
        f"The script will download "
        f"{len(dem_items)} DEM GeoTIFF(s)."
    )

    answer = input(
        "Continue? (y/n): "
    ).strip().lower()

    if answer != "y":

        print()
        print(
            "Download cancelled."
        )

        return

    # --------------------------------------------------------
    # Download
    # --------------------------------------------------------

    successful = 0

    for item in dem_items:

        if download_dem(
            s3,
            item
        ):

            successful += 1

    # --------------------------------------------------------
    # Final summary
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("FINAL SUMMARY")
    print("=" * 60)

    print()
    print(
        f"Successful downloads: "
        f"{successful}/{len(dem_items)}"
    )

    print()
    print(
        "Output directory:"
    )

    print(
        OUTPUT_DIR.resolve()
    )

    if successful == len(dem_items):

        print()
        print(
            "SUCCESS!"
        )

        print()
        print(
            "The Copernicus DEM GeoTIFFs "
            "are now available."
        )

        print()
        print(
            "Next we will merge/crop them "
            "to the Nairobi study area."
        )

    else:

        print()
        print(
            "Some downloads failed."
        )

        print(
            "We will troubleshoot the "
            "specific error next."
        )

    print()


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    main()