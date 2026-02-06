import os
import urllib.request
import ssl

# Setup paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_ROOT = os.path.join(BASE_DIR, 'apps', 'dashboard', 'static', 'dashboard', 'lib', 'luckysheet')

# Create directories
PLUGINS_JS_DIR = os.path.join(STATIC_ROOT, 'plugins', 'js')
PLUGINS_CSS_DIR = os.path.join(STATIC_ROOT, 'plugins', 'css')
CSS_DIR = os.path.join(STATIC_ROOT, 'css')
ASSETS_DIR = os.path.join(STATIC_ROOT, 'assets', 'iconfont')

for d in [PLUGINS_JS_DIR, PLUGINS_CSS_DIR, CSS_DIR, ASSETS_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)
        print(f"Created directory: {d}")

# Files to download
# Map: (url, local_path_relative_to_static_root)
FILES = [
    # Main JS
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/luckysheet.umd.js', 'luckysheet.umd.js'),
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/luckysheet.css', 'luckysheet.css'),
    
    # Plugins
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/plugins/js/plugin.js', 'plugins/js/plugin.js'),
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/plugins/css/pluginsCss.css', 'plugins/css/pluginsCss.css'),
    
    # CSS & Fonts
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/assets/iconfont/iconfont.css', 'assets/iconfont/iconfont.css'),
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/assets/iconfont/iconfont.ttf', 'assets/iconfont/iconfont.ttf'),
    ('https://cdn.jsdelivr.net/npm/luckysheet@latest/dist/assets/iconfont/iconfont.woff', 'assets/iconfont/iconfont.woff'),
    
    # We might need jquery/other deps if they are not included. 
    # Luckysheet docs say: <link rel='stylesheet' href='./plugins/css/pluginsCss.css' />
    # <link rel='stylesheet' href='./plugins/plugins.css' /> 
    # <link rel='stylesheet' href='./css/luckysheet.css' />
    # <link rel='stylesheet' href='./assets/iconfont/iconfont.css' />
    # <script src="./plugins/js/plugin.js"></script>
    # <script src="./luckysheet.umd.js"></script>
]

# Bypass SSL verification if needed (for dev env)
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

opener = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
opener.addheaders = [('User-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')]
urllib.request.install_opener(opener)

for url, rel_path in FILES:
    full_path = os.path.join(STATIC_ROOT, rel_path)
    print(f"Downloading {url} to {full_path}...")
    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
            with open(full_path, 'wb') as f:
                f.write(content)
            print(f"Success: {len(content)} bytes")
    except Exception as e:
        print(f"Error downloading {url}: {e}")

# Verify
print("\nVerifying files:")
for root, dirs, files in os.walk(STATIC_ROOT):
    for file in files:
        path = os.path.join(root, file)
        size = os.path.getsize(path)
        print(f"{path} ({size} bytes)")
