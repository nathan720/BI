
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'bi-system')))

from core.reporting.charts import ChartFactory

def test_line_chart_features():
    print("Testing Line Chart Features...")
    
    # Test Data
    data = [
        {'date': '2023-01-01', 'value': 100, 'value2': 10},
        {'date': '2023-01-02', 'value': 200, 'value2': 100},
        {'date': '2023-01-03', 'value': 150, 'value2': 1000},
        {'date': '2023-01-04', 'value': None, 'value2': 10000}, # None for connect_nones
        {'date': '2023-01-05', 'value': 300, 'value2': 100000},
    ]
    
    # 1. Test Step Line & Symbol
    print("\n1. Testing Step Line & Symbol...")
    c1 = ChartFactory.create_chart(
        chart_type='line',
        title='Step Line Chart',
        data=data,
        x_col='date',
        y_col='value',
        is_step=True,
        symbol='triangle',
        title_show=True
    )
    opts1 = json.loads(c1.dump_options())
    series1 = opts1['series'][0]
    if series1.get('step') is not False and series1.get('symbol') == 'triangle':
        print("PASS: Step and Symbol configured correctly.")
    else:
        print(f"FAIL: Step or Symbol mismatch. Step: {series1.get('step')}, Symbol: {series1.get('symbol')}")

    # 2. Test Connect Nones
    print("\n2. Testing Connect Nones...")
    c2 = ChartFactory.create_chart(
        chart_type='line',
        title='Connect Nones Chart',
        data=data,
        x_col='date',
        y_col='value',
        is_connect_nones=True
    )
    opts2 = json.loads(c2.dump_options())
    series2 = opts2['series'][0]
    if series2.get('connectNulls'):
        print("PASS: Connect Nulls configured correctly.")
    else:
        print(f"FAIL: Connect Nulls mismatch. Got: {series2.get('connectNulls')}")

    # 3. Test Log Axis
    print("\n3. Testing Log Axis...")
    c3 = ChartFactory.create_chart(
        chart_type='line',
        title='Log Axis Chart',
        data=data,
        x_col='date',
        y_col='value2',
        y_axis_type='log'
    )
    opts3 = json.loads(c3.dump_options())
    y_axis = opts3['yAxis'][0]
    if y_axis.get('type') == 'log':
        print("PASS: Y Axis type is log.")
    else:
        print(f"FAIL: Y Axis type mismatch. Got: {y_axis.get('type')}")

    # 4. Test Title Visibility (Duplicate Title Fix)
    print("\n4. Testing Title Visibility...")
    c4 = ChartFactory.create_chart(
        chart_type='line',
        title='Hidden Title',
        data=data,
        x_col='date',
        y_col='value',
        title_show=False
    )
    opts4 = json.loads(c4.dump_options())
    title_opts = opts4.get('title', [{}])[0]
    # Pyecharts might handle is_show=False by setting show: false
    if title_opts.get('show') is False:
        print("PASS: Title show is False.")
    else:
        print(f"FAIL: Title show mismatch. Got: {title_opts.get('show')}")

if __name__ == '__main__':
    try:
        test_line_chart_features()
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
