from core.reporting.charts import ChartFactory
import json

def test_bar_race():
    data = [
        {"Country": "A", "GDP": 100},
        {"Country": "B", "GDP": 200},
        {"Country": "C", "GDP": 300},
    ]
    
    # Simulate Bar Race config
    config = {
        "reversal_axis": True, # Horizontal bar
        "realtime_sort": True,
        "label_value_animation": True,
        "animation_duration": 0,
        "animation_duration_update": 300,
        "animation_easing": "linear",
        "animation_easing_update": "linear",
        "y_axis_inverse": True, # Highest value at top? Or typically inverse for rank
        "x_axis_line_on_zero": False, # Just to test parameter passing
        "label_position": "right",
        "label_show": True
    }
    
    # We need to adapt the config to what create_chart expects in kwargs
    # In reality, views.py unpacks these.
    
    try:
        chart = ChartFactory.create_chart(
            chart_type="bar",
            title="Bar Race Test",
            data=data,
            # Let's stick to standard input:
            x_col="Country",
            y_col="GDP",
            **config
        )
        
        # Dump options
        options = json.loads(chart.dump_options())
        
        # Verify realtimeSort
        series = options['series'][0]
        if series.get('realtimeSort'):
            print("PASS: realtimeSort is True")
        else:
            print("FAIL: realtimeSort is missing or False")
            
        # Verify label value animation
        label_opts = series.get('label', {})
        if label_opts.get('valueAnimation'):
             print("PASS: label valueAnimation is True")
        else:
             print("FAIL: label valueAnimation is missing or False")
             print(f"Label opts: {label_opts}")

        # Verify animation opts
        if options.get('animationDurationUpdate') == 300:
             print("PASS: animationDurationUpdate is 300")
        else:
             print(f"FAIL: animationDurationUpdate is {options.get('animationDurationUpdate')}")

        # Verify axis inverse
        # Since reversal_axis is True, the original Y-axis (Value) is swapped to the X position (Horizontal).
        # The original X-axis (Category) is swapped to the Y position (Vertical).
        # We set y_axis_inverse=True in config. This applies to the logical Y-axis (Value).
        # So after swap, the logical Y-axis is now the physical X-axis.
        # Therefore, we expect options['xAxis'][0] to have inverse=True.
        
        target_axis = options['xAxis'][0]
        
        if target_axis.get('inverse') is True:
             print("PASS: Axis Inverse Check (Logical Y/Physical X is inverse)")
        else:
             print(f"FAIL: Axis Inverse Check - Expected True, got {target_axis.get('inverse')}")
             # Debug info
             print(f"xAxis inverse: {options['xAxis'][0].get('inverse')}")
             print(f"yAxis inverse: {options['yAxis'][0].get('inverse')}")

             
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_bar_race()
