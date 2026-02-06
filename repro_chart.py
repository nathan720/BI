
from pyecharts.charts import Bar, Line, Grid
from pyecharts import options as opts
import random

def create_dual_axis_chart():
    x_data = ["A", "B", "C", "D", "E"]
    y1_data = [random.randint(10, 100) for _ in range(5)]
    y2_data = [random.randint(1000, 5000) for _ in range(5)]
    
    # 1. Base Chart (Bar)
    bar = Bar()
    bar.add_xaxis(x_data)
    
    # Add Series 1 (Left)
    bar.add_yaxis(
        "Series 1", 
        y1_data, 
        yaxis_index=0,
        z=0
    )
    
    # Add Series 2 (Right)
    bar.add_yaxis(
        "Series 2", 
        y2_data, 
        yaxis_index=1,
        z=0
    )
    
    # Global Opts
    bar.set_global_opts(
        yaxis_opts=opts.AxisOpts(
            name="Left Axis",
            type_="value",
            position="left",
            # grid_index=0
        )
    )
    
    # Extend Axis
    bar.extend_axis(
        yaxis=opts.AxisOpts(
            name="Right Axis",
            type_="value",
            position="right",
            # grid_index=0,
            splitline_opts=opts.SplitLineOpts(is_show=False)
        )
    )
    
    # Manually set Grid options on the chart
    # grid_opts is not in set_global_opts, so we add it to options dict
    bar.options['grid'] = opts.GridOpts(pos_left="5%", pos_right="20%")
    
    return bar

if __name__ == "__main__":
    c = create_dual_axis_chart()
    c.render("test_dual.html")
    print("Rendered test_dual.html")
