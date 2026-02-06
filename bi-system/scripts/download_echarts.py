import os
import requests

def download_echarts():
    url = "https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.0/echarts.min.js"
    save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "apps/dashboard/static/dashboard/js")
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        
    save_path = os.path.join(save_dir, "echarts.min.js")
    
    print(f"Downloading ECharts to {save_path}...")
    try:
        response = requests.get(url)
        response.raise_for_status()
        with open(save_path, "wb") as f:
            f.write(response.content)
        print("Download complete.")
    except Exception as e:
        print(f"Error downloading ECharts: {e}")

if __name__ == '__main__':
    download_echarts()