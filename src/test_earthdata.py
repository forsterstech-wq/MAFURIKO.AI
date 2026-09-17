import getpass
import requests
from pathlib import Path

TOKEN = getpass.getpass("Paste your Earthdata token (it will be hidden): ")

url = (
    "https://data.gesdisc.earthdata.nasa.gov/"
    "data/GPM_L3/GPM_3IMERGDF.07/2020/03/"
    "3B-DAY.MS.MRG.3IMERG.20200318-S000000-E235959.V07B.nc4"
)

output_dir = Path("data/raw/rainfall")
output_dir.mkdir(parents=True, exist_ok=True)

output_file = output_dir / "3B-DAY.MS.MRG.3IMERG.20200318-V07B.nc4"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

print("Downloading IMERG file...")

response = requests.get(
    url,
    headers=headers,
    stream=True
)

print("HTTP status:", response.status_code)

if response.status_code != 200:
    print("Download failed.")
    print(response.text[:500])
    raise SystemExit(1)

with open(output_file, "wb") as f:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            f.write(chunk)

print("Download successful!")
print("Saved to:", output_file)
print("File size:", output_file.stat().st_size / (1024 * 1024), "MB")