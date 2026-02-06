
import json
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')
django.setup()

from core.reporting.charts import ChartFactory
from pyecharts import options as opts

def test_dual_yaxis_bar():
    print("Testing Dual Y-axis Bar Chart Configuration...")
    
    # Test with dual Y-axis parameters
    # Scenario: User sets layout margins (grid_*) and Y2 axis scales
    kwargs = {
        # 'grid_type': 'multi_yaxis', # This is usually determined by ChartFactory logic or passed explicitly? 
        # Actually ChartFactory determines grid_type='multi_yaxis' if left_cols and right_cols are present for some charts,
        # or if specific chart types are used. 
        # For 'bar' chart with dual axis, the UI might send specific kwargs.
        # Let's assume standard Bar chart logic uses 'grid_type'='multi_yaxis' if triggered.
        
        'grid_type': 'multi_yaxis',
        'left_cols': ['sales'],
        'right_cols': ['passenger_flow'],
        
        # Primary Y-axis config
        'y_axis_min': 0,
        'y_axis_max': 1000,
        
        # Secondary Y-axis config (User says scale display abnormal)
        'y2_axis_min': 0,
        'y2_axis_max': 100,
        
        # Layout config (User says layout cannot be adjusted)
        # The UI standard for basic charts is grid_left/right/top/bottom.
        # Let's test if these work for dual axis.
        'grid_left': '10%',
        'grid_right': '10%',
        'grid_top': '10%',
        'grid_bottom': '10%',
        
        # Also test grid_pos_* just in case
        # 'grid_pos_left': '10%',
        
        'add_xaxis': ['Jan', 'Feb', 'Mar'],
        'add_yaxis': {'sales': [500, 700, 900], 'passenger_flow': [30, 50, 70]}
    }
    
    # Mock data
    data = [
        {'month': 'Jan', 'sales': 500, 'passenger_flow': 30},
        {'month': 'Feb', 'sales': 700, 'passenger_flow': 50},
        {'month': 'Mar', 'sales': 900, 'passenger_flow': 70}
    ]
    
    print("\n--- Test Case 1: Using grid_* parameters with chart_type='bar' ---")
    try:
        chart = ChartFactory.create_chart(
            chart_type='bar',
            title="Dual Y-axis Bar Chart",
            data=data,
            x_col='month',
            y_col=['sales', 'passenger_flow'],
            **kwargs
        )
        
        # Dump options
        json_str = chart.dump_options_with_quotes()
        options = json.loads(json_str)
        
        # Check Y-axis
        if 'yAxis' in options:
            y_axes = options['yAxis']
            print(f"Y-axes count: {len(y_axes)}")
            for i, axis in enumerate(y_axes):
                print(f"Y-axis {i}: min={axis.get('min')}, max={axis.get('max')}, name={axis.get('name')}")
        
        # Check Grid
        if 'grid' in options:
            grid_opt = options['grid'][0] if isinstance(options['grid'], list) else options['grid']
            print(f"Grid Config: {json.dumps(grid_opt, indent=2)}")
        else:
            print("No grid config found!")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dual_yaxis_bar()
