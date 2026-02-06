import os
import requests

# Base directory for fonts
BASE_DIR = r"d:\work\python\BI\bi-system\apps\dashboard\static\dashboard\lib\luckysheet\fonts"
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# FontAwesome 4.7.0 CDN Base URL
CDN_BASE = "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/fonts"

files = [
    "fontawesome-webfont.eot",
    "fontawesome-webfont.woff2",
    "fontawesome-webfont.woff",
    "fontawesome-webfont.ttf",
    "fontawesome-webfont.svg"
]

for file in files:
    url = f"{CDN_BASE}/{file}"
    path = os.path.join(BASE_DIR, file)
    print(f"Downloading {file} from {url}...")
    try:
        r = requests.get(url, verify=False) # Disable SSL verify to avoid cert issues in dev env
        if r.status_code == 200:
            with open(path, 'wb') as f:
                f.write(r.content)
            print(f"Saved to {path}")
        else:
            print(f"Failed to download {file}: {r.status_code}")
    except Exception as e:
        print(f"Error downloading {file}: {e}")
