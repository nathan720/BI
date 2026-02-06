from pyecharts.charts import Bar
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode

def test_jscode_dump():
    bar = Bar()
    bar.add_xaxis(["A"])
    bar.add_yaxis("S1", [10], label_opts=opts.LabelOpts(formatter=JsCode("function(x){return x}")))
    
    dump = bar.dump_options_with_quotes()
    print("DUMP OUTPUT:")
    print(dump)

if __name__ == "__main__":
    test_jscode_dump()
