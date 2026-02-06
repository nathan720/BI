from pyecharts.charts import Bar, Grid
from pyecharts import options as opts

def test_grid():
    bar = Bar()
    bar.add_xaxis(["A", "B"])
    bar.add_yaxis("S1", [10, 20])
    bar.set_global_opts(title_opts=opts.TitleOpts(title="Test"))
    
    grid = Grid()
    grid.add(bar, grid_opts=opts.GridOpts(pos_left="10%"))
    
    try:
        print(grid.dump_options_with_quotes())
        print("Grid dump success")
    except Exception as e:
        print(f"Grid dump failed: {e}")

if __name__ == "__main__":
    test_grid()
