
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bi_system.settings") # Adjust if settings module name differs

try:
    django.setup()
except Exception as e:
    print(f"Django setup failed (might be fine if not using models): {e}")

from core.reporting.charts import ChartFactory
# from pyecharts.charts import Chart # Removed invalid import

def test_chart_creation():
    print("Testing ChartFactory...")
    
    # Common data
    data_basic = [{"category": "A", "value": 10}, {"category": "B", "value": 20}]
    
    chart_types = [
        ("bar", data_basic, {}),
        ("line", data_basic, {}),
        ("pie", data_basic, {}),
        ("scatter", data_basic, {}),
        ("radar", [{"category": "Metric1", "value": 100}, {"category": "Metric2", "value": 80}], {}),
        ("funnel", data_basic, {}),
        ("gauge", [{"name": "Speed", "value": 80}], {}),
        ("heatmap", [{"x": "Mon", "y": "Morning", "value": 5}], {"x_col": "x", "y_col": ["y", "value"]}), # Mocking complex data structure logic
        ("calendar", [{"date": "2023-01-01", "value": 100}], {"x_col": "date", "y_col": "value", "calendar_range": "2023"}),
        ("graph", [{"source": "A", "target": "B", "value": 10}], {"x_col": "source", "y_col": ["target", "value"]}),
        ("liquid", [{"name": "Score", "value": 0.6}], {"y_col": "value"}),
        ("parallel", [{"dim1": 1, "dim2": 2}], {"y_col": ["dim1", "dim2"]}),
        ("pictorial_bar", data_basic, {}),
        ("sankey", [{"source": "A", "target": "B", "value": 10}], {"x_col": "source", "y_col": ["target", "value"]}),
        ("map", [{"city": "Beijing", "value": 100}], {"x_col": "city", "y_col": "value"}),
        ("grid", data_basic, {"grid_type": "basic"}),
        ("page", data_basic, {}),
    ]

    for c_type, data, kwargs in chart_types:
        try:
            print(f"Creating {c_type}...", end="")
            chart = ChartFactory.create_chart(c_type, f"Test {c_type}", data, **kwargs)
            if chart is not None:
                print(" OK")
            else:
                print(" Failed (None returned)")
        except Exception as e:
            print(f" Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_chart_creation()
