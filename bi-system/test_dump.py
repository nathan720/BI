
import json
import re
from pyecharts.charts import Bar
from pyecharts import options as opts

JS_CODE_MARKER = "__JSCODE__"

def dump_options(chart):
    if not chart:
        return None
        
    options = chart.dump_options()
    print("RAW OPTIONS:", options)
    
    pattern = f'"{JS_CODE_MARKER}(.*?){JS_CODE_MARKER}"'
    
    def replacer(match):
        content = match.group(1)
        content = content.replace('\\"', '"')
        content = content.replace('\\n', '\n')
        content = content.replace('\\\\', '\\')
        return content
        
    return re.sub(pattern, replacer, options, flags=re.DOTALL)

def get_tooltip_formatter():
    map_str = '{"A": {"type": "float2"}}'
    safe_global_suffix = ""
    
    js = f"""
    function(params) {{
        const configMap = {map_str};
        return 'test';
    }}
    """
    return f"{JS_CODE_MARKER}{js}{JS_CODE_MARKER}"

def test():
    c = Bar()
    c.add_xaxis(["A", "B"])
    c.add_yaxis("Series A", [1, 2])
    
    fmt = get_tooltip_formatter()
    print("FORMATTER STR:", repr(fmt))
    
    c.set_global_opts(tooltip_opts=opts.TooltipOpts(formatter=fmt))
    
    dumped = dump_options(c)
    print("DUMPED:", dumped)

if __name__ == "__main__":
    test()
