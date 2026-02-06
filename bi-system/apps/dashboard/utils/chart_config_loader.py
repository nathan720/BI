import json
import os
from django.conf import settings

def load_chart_configs():
    """
    Load chart configurations from global and specific config files.
    Merges global_config.json into chart_configs.json.
    """
    global_config_path = os.path.join(settings.BASE_DIR, 'apps', 'dashboard', 'fixtures', 'global_config.json')
    specific_config_path = os.path.join(settings.BASE_DIR, 'apps', 'dashboard', 'fixtures', 'chart_configs.json')
    
    if not os.path.exists(global_config_path) or not os.path.exists(specific_config_path):
        print("Config files not found, falling back to legacy charts_parameter.json")
        # Fallback to legacy
        param_file_path = os.path.join(settings.BASE_DIR, 'apps', 'dashboard', 'fixtures', 'charts_parameter.json')
        if os.path.exists(param_file_path):
            try:
                with open(param_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading charts_parameter.json: {e}")
        return {}

    try:
        # Load Global Config
        with open(global_config_path, 'r', encoding='utf-8') as f:
            global_config = json.load(f)
            global_params = global_config.get("全局配置", [])

        # Load Specific Configs
        with open(specific_config_path, 'r', encoding='utf-8') as f:
            chart_configs = json.load(f)

        # Merge Global into Specific
        for chart_type, config in chart_configs.items():
            # Special handling for Table component to keep its config separate as requested
            if chart_type == 'Table':
                if "全局配置" not in config:
                    config["全局配置"] = []
                continue

            if "全局配置" in config:
                # Prepend global parameters to ensure they appear first (or as appropriate)
                # We use a list comprehension to avoid modifying the original global_params list objects if we were mutable, 
                # but here we just concatenate lists.
                # Check for duplicates? The migration script removed globals from specifics, so we assume no duplicates.
                # However, for Table, we might want to be careful. 
                # For now, we apply universally as requested for "Global Common Parameters".
                
                # Note: Table component might not support all global opts (like toolbox), 
                # but having them in config doesn't break python usually (kwargs ignored).
                
                # Create a new list combining global and specific
                merged_global = global_params + config["全局配置"]
                config["全局配置"] = merged_global
            else:
                config["全局配置"] = global_params

        # Assign to raw_params for compatibility with the processing logic below
        raw_params = chart_configs

    except Exception as e:
        print(f"Error loading/merging chart configs: {e}")
        return {}

    # Define Field Mappings (Param Name -> List of UI Fields)
    # This expands the high-level pyecharts options into individual editable fields
    FIELD_MAPPING = {
        # Axis Configs (Direct Mapping)
        "x_axis_label_size": [{"key": "x_axis_label_size", "label": "X轴标签大小", "type": "number", "default": 12}],
        "x_axis_label_color": [{"key": "x_axis_label_color", "label": "X轴标签颜色", "type": "color", "default": "#333333"}],
        "x_axis_formatter": [{"key": "x_axis_formatter", "label": "X轴标签格式", "type": "text", "default": "{value}"}],
        "y_axis_label_size": [{"key": "y_axis_label_size", "label": "Y轴标签大小", "type": "number", "default": 12}],
        "y_axis_label_color": [{"key": "y_axis_label_color", "label": "Y轴标签颜色", "type": "color", "default": "#333333"}],
        "y_axis_formatter": [{"key": "y_axis_formatter", "label": "Y轴标签格式", "type": "text", "default": "{value}"}],

        "colors": [{"key": "colors", "label": "自定义颜色序列", "type": "color_list", "default": ""}],
        "color_by": [{"key": "color_by", "label": "颜色分组", "type": "select", "options": [
            {"value": "series", "label": "按系列"},
            {"value": "data", "label": "按数据项"}
        ], "default": "series"}],
        "init_opts": [
            {"key": "theme", "label": "图表主题", "type": "select", "options": [
                {"value": "light", "label": "明亮"}, 
                {"value": "dark", "label": "暗黑"},
                {"value": "macarons", "label": "马卡龙"},
                {"value": "chalk", "label": "粉笔"}
            ], "default": "light"},
            {"key": "bg_color", "label": "背景颜色", "type": "color", "default": "#ffffff"}
        ],
        "title_opts": [
            {"key": "title_show", "label": "显示图表标题", "type": "boolean", "default": True},
            {"key": "card_title_show", "label": "显示卡片标题", "type": "boolean", "default": True},
            {"key": "title", "label": "主标题", "type": "text", "default": ""},
            {"key": "card_title_fontsize", "label": "卡片标题大小", "type": "number", "default": 14},
            {"key": "card_title_align", "label": "卡片标题对齐", "type": "select", "options": [
                {"value": "left", "label": "左对齐"}, 
                {"value": "center", "label": "居中"}, 
                {"value": "right", "label": "右对齐"}
            ], "default": "left"},
            {"key": "subtitle", "label": "副标题", "type": "text", "default": ""},
            {"key": "title_pos", "label": "标题位置", "type": "select", "options": [
                {"value": "left", "label": "左对齐"}, 
                {"value": "center", "label": "居中"}, 
                {"value": "right", "label": "右对齐"}
            ], "default": "left"},
            {"key": "title_color", "label": "标题颜色", "type": "color", "default": "#333333"}
        ],
        "card_title_fontsize": [
             {"key": "card_title_fontsize", "label": "卡片标题大小", "type": "number", "default": 14}
        ],
        "card_title_align": [
             {"key": "card_title_align", "label": "卡片标题对齐", "type": "select", "options": [
                {"value": "left", "label": "左对齐"}, 
                {"value": "center", "label": "居中"}, 
                {"value": "right", "label": "右对齐"}
            ], "default": "left"}
        ],
        "grid_opts": [
            {"key": "grid_left", "label": "左边距", "type": "text", "default": "10%"},
            {"key": "grid_right", "label": "右边距", "type": "text", "default": "10%"},
            {"key": "grid_top", "label": "上边距", "type": "text", "default": "60"},
            {"key": "grid_bottom", "label": "下边距", "type": "text", "default": "60"}
        ],
        "legend_text_size": [
            {"key": "legend_text_size", "label": "图例字体大小", "type": "number", "default": 12}
        ],
        "legend_text_color": [
            {"key": "legend_text_color", "label": "图例字体颜色", "type": "color", "default": "#333333"}
        ],
        "legend_opts": [
            {"key": "legend_show", "label": "显示图例", "type": "boolean", "default": True},
            {"key": "legend_orient", "label": "图例方向", "type": "select", "options": [
                {"value": "horizontal", "label": "水平"}, 
                {"value": "vertical", "label": "垂直"}
            ], "default": "horizontal"},
            {"key": "legend_pos", "label": "图例位置", "type": "select", "options": [
                {"value": "top", "label": "顶部"}, 
                {"value": "bottom", "label": "底部"}, 
                {"value": "left", "label": "左侧"}, 
                {"value": "right", "label": "右侧"},
                {"value": "center", "label": "居中"}
            ], "default": "top"}
        ],
        "toolbox_opts": [
            {"key": "toolbox_show", "label": "显示工具箱", "type": "boolean", "default": True}
        ],
        "toolbox_show": [
            {"key": "toolbox_show", "label": "显示工具箱", "type": "boolean", "default": True}
        ],
        "title_size": [
            {"key": "title_size", "label": "主标题大小", "type": "number", "default": 18}
        ],
        "title_color": [
            {"key": "title_color", "label": "主标题颜色", "type": "color", "default": "#333333"}
        ],
        "subtitle_size": [
            {"key": "subtitle_size", "label": "副标题大小", "type": "number", "default": 12}
        ],
        "subtitle_color": [
            {"key": "subtitle_color", "label": "副标题颜色", "type": "color", "default": "#aaaaaa"}
        ],
        "tooltip_opts": [
            {"key": "tooltip_show", "label": "显示提示框", "type": "boolean", "default": True},
            {"key": "tooltip_trigger", "label": "触发方式", "type": "select", "options": [
                {"value": "item", "label": "数据项"},
                {"value": "axis", "label": "坐标轴"}
            ], "default": "axis"},
            {"key": "tooltip_text_size", "label": "文字大小", "type": "number", "default": 14},
            {"key": "tooltip_text_color", "label": "文字颜色", "type": "color", "default": "#ffffff"},
            {"key": "tooltip_background_color", "label": "背景颜色", "type": "color", "default": "rgba(50,50,50,0.7)"},
            {"key": "tooltip_border_color", "label": "边框颜色", "type": "color", "default": "#333"},
            {"key": "tooltip_border_width", "label": "边框宽度", "type": "number", "default": 0}
        ],
        "datazoom_opts": [
            {"key": "datazoom_show", "label": "显示缩放条", "type": "boolean", "default": False},
            {"key": "datazoom_type", "label": "缩放类型", "type": "select", "options": [
                {"value": "slider", "label": "滑动条"},
                {"value": "inside", "label": "内置缩放"},
                {"value": "both", "label": "两者都有"}
            ], "default": "slider"},
            {"key": "datazoom_orient", "label": "缩放方向", "type": "select", "options": [
                {"value": "horizontal", "label": "水平"},
                {"value": "vertical", "label": "垂直"}
            ], "default": "horizontal"}
        ],
        "color_by": [
            {"key": "color_by", "label": "颜色分组依据", "type": "select", "options": [
                {"value": "series", "label": "按系列(默认)"},
                {"value": "data", "label": "按数据项"}
            ], "default": "series"}
        ],
        "visualmap_opts": [
            {"key": "visualmap_opts", "label": "视觉映射配置", "type": "VisualMapOpts", "default": "无"}
        ],
        "label_opts": [
            {"key": "label_show", "label": "显示数值标签", "type": "boolean", "default": False},
            {"key": "label_position", "label": "标签位置", "type": "select", "options": [
                {"value": "top", "label": "顶部"},
                {"value": "left", "label": "左侧"},
                {"value": "right", "label": "右侧"},
                {"value": "bottom", "label": "底部"},
                {"value": "inside", "label": "内部"},
                {"value": "insideLeft", "label": "内部左侧"},
                {"value": "insideRight", "label": "内部右侧"},
                {"value": "insideTop", "label": "内部顶部"},
                {"value": "insideBottom", "label": "内部底部"},
                {"value": "insideTopLeft", "label": "内部左上"},
                {"value": "insideBottomLeft", "label": "内部左下"},
                {"value": "insideTopRight", "label": "内部右上"},
                {"value": "insideBottomRight", "label": "内部右下"}
            ], "default": "top"},
            {"key": "label_formatter", "label": "标签格式(JS函数)", "type": "text", "default": ""},
            {"key": "label_value_animation", "label": "开启数值动画", "type": "boolean", "default": False}
        ],
        "xaxis_opts": [
            {"key": "x_rotate", "label": "X轴标签旋转", "type": "number", "min": 0, "max": 90, "default": 0},
            {"key": "x_axis_name", "label": "X轴名称", "type": "text", "default": ""},
            {"key": "x_axis_type", "label": "X轴类型", "type": "select", "options": [
                {"value": "category", "label": "类目轴"},
                {"value": "value", "label": "数值轴"},
                {"value": "time", "label": "时间轴"},
                {"value": "log", "label": "对数轴"}
            ], "default": "category"},
            {"key": "x_splitline_show", "label": "显示X轴分割线", "type": "boolean", "default": False},
            {"key": "x_axis_label_size", "label": "标签大小", "type": "number", "default": 12},
            {"key": "x_axis_label_color", "label": "标签颜色", "type": "color", "default": "#333333"},
            {"key": "x_axis_formatter", "label": "标签格式", "type": "text", "default": "{value}"},
            {"key": "x_axis_line_on_zero", "label": "轴线在0刻度上", "type": "boolean", "default": True},
            {"key": "x_axis_tick_show", "label": "显示刻度", "type": "boolean", "default": True},
            {"key": "x_axis_line_show", "label": "显示轴线", "type": "boolean", "default": True},
            {"key": "x_axis_inverse", "label": "反向坐标轴", "type": "boolean", "default": False},
            {"key": "x_axis_boundary_gap", "label": "两端留白", "type": "boolean", "default": True}
        ],
        "yaxis_opts": [
            {"key": "y_axis_name", "label": "Y轴名称", "type": "text", "default": ""},
            {"key": "y_axis_min", "label": "Y轴最小值", "type": "number", "default": None},
            {"key": "y_axis_max", "label": "Y轴最大值", "type": "number", "default": None},
            {"key": "y_axis_type", "label": "Y轴类型", "type": "select", "options": [
                {"value": "value", "label": "数值轴"},
                {"value": "category", "label": "类目轴"},
                {"value": "time", "label": "时间轴"},
                {"value": "log", "label": "对数轴"}
            ], "default": "value"},
            {"key": "y_splitline_show", "label": "显示Y轴分割线", "type": "boolean", "default": True},
            {"key": "y_axis_label_size", "label": "标签大小", "type": "number", "default": 12},
            {"key": "y_axis_label_color", "label": "标签颜色", "type": "color", "default": "#333333"},
            {"key": "y_axis_formatter", "label": "标签格式", "type": "text", "default": "{value}"},
            {"key": "y_axis_suffix", "label": "Y轴后缀", "type": "text", "default": ""},
            {"key": "y_axis_line_on_zero", "label": "轴线在0刻度上", "type": "boolean", "default": False},
            {"key": "y_axis_tick_show", "label": "显示刻度", "type": "boolean", "default": True},
            {"key": "y_axis_line_show", "label": "显示轴线", "type": "boolean", "default": True},
            {"key": "y_axis_inverse", "label": "反向坐标轴", "type": "boolean", "default": False}
        ],
        "y_axis_type": [
            {"key": "y_axis_type", "label": "Y轴类型", "type": "select", "options": [
                {"value": "value", "label": "数值轴"},
                {"value": "category", "label": "类目轴"},
                {"value": "time", "label": "时间轴"},
                {"value": "log", "label": "对数轴"}
            ], "default": "value"}
        ],
        "y2_axis_opts": [
            {"key": "y2_axis_name", "label": "Y2轴名称", "type": "text", "default": ""},
            {"key": "y2_axis_min", "label": "Y2轴最小值", "type": "number", "default": None},
            {"key": "y2_axis_max", "label": "Y2轴最大值", "type": "number", "default": None},
            {"key": "y2_axis_label_size", "label": "Y2轴标签大小", "type": "number", "default": 12},
            {"key": "y2_axis_label_color", "label": "Y2轴标签颜色", "type": "color", "default": "#333333"},
            {"key": "y2_axis_formatter", "label": "Y2轴标签格式", "type": "text", "default": "{value}"},
            {"key": "y2_axis_suffix", "label": "Y2轴后缀", "type": "text", "default": ""},
            {"key": "y2_splitline_show", "label": "显示Y2轴分割线", "type": "boolean", "default": False}
        ],
        "center": [
             {"key": "pie_center", "label": "圆心坐标(x,y)", "type": "text", "default": "50%,50%"}
        ],
        "splitline_opts": [
             {"key": "splitline_show", "label": "显示分隔线", "type": "boolean", "default": True}
        ],
        "splitarea_opts": [
             {"key": "splitarea_show", "label": "显示分隔区域", "type": "boolean", "default": True}
        ],
        "radar_opts": [
             {"key": "radar_shape", "label": "雷达形状", "type": "select", "options": [
                 {"value": "polygon", "label": "多边形"},
                 {"value": "circle", "label": "圆形"}
             ], "default": "polygon"}
        ],
        "itemstyle_opts": [
             {"key": "item_color", "label": "图形颜色(覆盖默认)", "type": "color", "default": ""},
             {"key": "bar_border_radius", "label": "圆角半径(如 5 或 5,5,0,0)", "type": "text", "default": ""},
             {"key": "item_border_color", "label": "边框颜色", "type": "color", "default": ""},
             {"key": "item_border_width", "label": "边框宽度", "type": "number", "default": 0},
             {"key": "item_opacity", "label": "透明度(0-1)", "type": "number", "step": 0.1, "min": 0, "max": 1, "default": 1}
        ], 
        "linestyle_opts": [
            {"key": "line_width", "label": "线条宽度", "type": "number", "default": 2},
            {"key": "line_type", "label": "线条类型", "type": "select", "options": [
                {"value": "solid", "label": "实线"},
                {"value": "dashed", "label": "虚线"},
                {"value": "dotted", "label": "点线"}
            ], "default": "solid"},
            {"key": "is_smooth", "label": "平滑曲线", "type": "boolean", "default": False},
            {"key": "is_step", "label": "阶梯图", "type": "boolean", "default": False},
            {"key": "is_connect_nones", "label": "连接空值", "type": "boolean", "default": False}
        ],
        "symbol": [ # Maps to 'symbol' param
             {"key": "symbol", "label": "标记图形", "type": "select", "options": [
                 {"value": "emptyCircle", "label": "空心圆"},
                 {"value": "circle", "label": "实心圆"},
                 {"value": "rect", "label": "矩形"},
                 {"value": "roundRect", "label": "圆角矩形"},
                 {"value": "triangle", "label": "三角形"},
                 {"value": "diamond", "label": "菱形"},
                 {"value": "pin", "label": "大头针"},
                 {"value": "arrow", "label": "箭头"},
                 {"value": "none", "label": "无"}
             ], "default": "emptyCircle"}
        ],
        "symbol_repeat": [
             {"key": "symbol_repeat", "label": "图形重复", "type": "select", "options": [
                 {"value": "fixed", "label": "固定重复(适合打分)"},
                 {"value": "true", "label": "自适应重复(适合数量)"},
                 {"value": "false", "label": "拉伸(不重复)"}
             ], "default": "fixed"}
        ],
        "is_symbol_clip": [
             {"key": "is_symbol_clip", "label": "裁剪超出部分", "type": "boolean", "default": True}
        ],
        "symbol_size": [
             {"key": "symbol_size", "label": "标记大小(数值或JS函数)", "type": "text", "default": "10"},
             {"key": "min_symbol_size", "label": "最小标记大小", "type": "number", "default": 5},
             {"key": "max_symbol_size", "label": "最大标记大小(矩阵模式)", "type": "number", "default": 20},
        ],
        "areastyle_opts": [
             {"key": "area_style", "label": "区域填充", "type": "boolean", "default": False},
             {"key": "area_opacity", "label": "填充透明度", "type": "number", "min": 0, "max": 1, "step": 0.1, "default": 0.5}
        ],
        "area_style": [
             {"key": "area_style", "label": "区域填充", "type": "boolean", "default": False}
        ],
        "area_opacity": [
             {"key": "area_opacity", "label": "填充透明度", "type": "number", "min": 0, "max": 1, "step": 0.1, "default": 0.5}
        ],
        "rosetype": [
             {"key": "rosetype", "label": "玫瑰图模式", "type": "select", "options": [
                {"value": "none", "label": "无"},
                {"value": "radius", "label": "半径模式"},
                {"value": "area", "label": "面积模式"}
            ], "default": "none"}
        ],
        "radius_type": [ # Custom helper mapping
             {"key": "radius_type", "label": "半径模式", "type": "select", "options": [
                {"value": "solid", "label": "实心饼图"},
                {"value": "ring", "label": "环形图"}
            ], "default": "ring"}
        ],
        "reversal_axis": [
             {"key": "reversal_axis", "label": "翻转XY轴", "type": "boolean", "default": False}
        ],
        "bar_gap": [
             {"key": "bar_gap", "label": "系列间距离", "type": "text", "default": "30%"}
        ],
        "category_gap": [
             {"key": "category_gap", "label": "柱间距离", "type": "text", "default": "20%"}
        ],
        "stack": [
             {"key": "stack", "label": "堆叠显示", "type": "boolean", "default": False}
        ],
        "stack_strategy": [
             {"key": "stack_strategy", "label": "堆叠模式", "type": "select", "options": [
                {"value": "normal", "label": "普通堆叠"},
                {"value": "percent", "label": "百分比堆叠"}
            ], "default": "normal"}
        ],
        "realtime_sort": [
             {"key": "realtime_sort", "label": "实时排序(Bar Race)", "type": "boolean", "default": False}
        ],
        "markpoint_opts": [
            {"key": "markpoint_show", "label": "显示标记点", "type": "boolean", "default": False},
            {"key": "markpoint_type", "label": "标记点类型", "type": "select", "options": [
                {"value": "max", "label": "最大值"},
                {"value": "min", "label": "最小值"},
                {"value": "average", "label": "平均值"}
            ], "default": "max"}
        ],
        "markpoint_show": [
            {"key": "markpoint_show", "label": "显示标记点", "type": "boolean", "default": False}
        ],
        "markpoint_type": [
            {"key": "markpoint_type", "label": "标记点类型", "type": "select", "options": [
                {"value": "max", "label": "最大值"},
                {"value": "min", "label": "最小值"},
                {"value": "average", "label": "平均值"}
            ], "default": "max"}
        ],
        "markline_opts": [
            {"key": "markline_show", "label": "显示标记线", "type": "boolean", "default": False},
            {"key": "markline_type", "label": "标记线类型", "type": "select", "options": [
                {"value": "max", "label": "最大值"},
                {"value": "min", "label": "最小值"},
                {"value": "average", "label": "平均值"}
            ], "default": "average"}
        ],
        "markline_show": [
            {"key": "markline_show", "label": "显示标记线", "type": "boolean", "default": False}
        ],
        "markline_type": [
            {"key": "markline_type", "label": "标记线类型", "type": "select", "options": [
                {"value": "max", "label": "最大值"},
                {"value": "min", "label": "最小值"},
                {"value": "average", "label": "平均值"}
            ], "default": "average"}
        ],
        "brush_opts": [
            {"key": "brush_show", "label": "启用区域选择", "type": "boolean", "default": False},
            {"key": "brush_type", "label": "选择工具类型", "type": "select", "options": [
                {"value": "rect", "label": "矩形选择"},
                {"value": "polygon", "label": "圈选"},
                {"value": "lineX", "label": "横向选择"},
                {"value": "lineY", "label": "纵向选择"}
            ], "default": "rect"}
        ],
        "animation_opts": [
            {"key": "animation_show", "label": "开启动画", "type": "boolean", "default": True},
            {"key": "animation_duration", "label": "动画时长(ms)", "type": "number", "default": 1000},
            {"key": "animation_easing", "label": "缓动效果", "type": "select", "options": [
                {"value": "linear", "label": "线性"},
                {"value": "cubicOut", "label": "三次曲线输出"},
                {"value": "elasticOut", "label": "弹性输出"}
            ], "default": "cubicOut"},
            {"key": "animation_duration_update", "label": "更新动画时长(ms)", "type": "number", "default": 300},
            {"key": "animation_easing_update", "label": "更新缓动效果", "type": "select", "options": [
                {"value": "linear", "label": "线性"},
                {"value": "cubicOut", "label": "三次曲线输出"},
                {"value": "elasticOut", "label": "弹性输出"}
            ], "default": "cubicOut"}
        ],
        "timeline_opts": [
            {"key": "timeline_field", "label": "时间维度字段", "type": "text", "default": ""},
            {"key": "timeline_play_interval", "label": "播放间隔(ms)", "type": "number", "default": 1000},
            {"key": "timeline_auto_play", "label": "自动播放", "type": "boolean", "default": True}
        ],
        "min_": [{"key": "min_", "label": "最小值", "type": "number", "default": 0}],
        "max_": [{"key": "max_", "label": "最大值", "type": "number", "default": 100}],
        "split_number": [{"key": "split_number", "label": "分割段数", "type": "number", "default": 10}],
        "radius": [{"key": "radius", "label": "半径", "type": "text", "default": "75%"}],
        "start_angle": [{"key": "start_angle", "label": "起始角度", "type": "number", "default": 225}],
        "end_angle": [{"key": "end_angle", "label": "结束角度", "type": "number", "default": -45}],
        "calendar_range": [{"key": "calendar_range", "label": "年份", "type": "text", "default": "2024"}],
        "cell_size": [{"key": "cell_size", "label": "单元格大小", "type": "number", "default": 20}],
        "layout": [{"key": "layout", "label": "布局算法", "type": "select", "options": [
             {"value": "force", "label": "力引导布局"},
             {"value": "circular", "label": "环形布局"},
             {"value": "none", "label": "无"}
        ], "default": "force"}],
        "repulsion": [{"key": "repulsion", "label": "斥力因子", "type": "number", "default": 50}],
        "edge_length": [{"key": "edge_length", "label": "边长", "type": "number", "default": 30}],
        "is_outline_show": [{"key": "is_outline_show", "label": "显示边框", "type": "boolean", "default": True}],
        "liquid_shape": [{"key": "liquid_shape", "label": "水球形状", "type": "select", "options": [
             {"value": "circle", "label": "圆形"},
             {"value": "rect", "label": "矩形"},
             {"value": "roundRect", "label": "圆角矩形"},
             {"value": "diamond", "label": "菱形"}
        ], "default": "circle"}],
        "symbol": [{"key": "symbol", "label": "图形形状", "type": "select", "options": [
             {"value": "rect", "label": "矩形"},
             {"value": "roundRect", "label": "圆角矩形"},
             {"value": "triangle", "label": "三角形"},
             {"value": "diamond", "label": "菱形"},
             {"value": "pin", "label": "大头针"},
             {"value": "arrow", "label": "箭头"}
        ], "default": "rect"}],
        "symbol_repeat": [{"key": "symbol_repeat", "label": "图形重复", "type": "select", "options": [
             {"value": "fixed", "label": "固定数量"},
             {"value": "true", "label": "自适应"},
             {"value": "false", "label": "不重复"}
        ], "default": "false"}],
        "symbol_margin": [{"key": "symbol_margin", "label": "图形间隔", "type": "number", "default": 5}],
        "symbol_clip": [{"key": "symbol_clip", "label": "是否剪裁", "type": "boolean", "default": True}],
        "grid_type": [{"key": "grid_type", "label": "布局类型", "type": "select", "options": [
            {"value": "basic", "label": "基础布局"},
            {"value": "vertical", "label": "垂直布局"},
            {"value": "horizontal", "label": "水平布局"},
            {"value": "multi_yaxis", "label": "多Y轴"}
        ], "default": "basic"}],
        "grid_pos_left": [{"key": "grid_left", "label": "左边距", "type": "text", "default": "10%"}],
        "grid_pos_right": [{"key": "grid_right", "label": "右边距", "type": "text", "default": "10%"}],
        "grid_pos_top": [{"key": "grid_top", "label": "上边距", "type": "text", "default": "60"}],
        "grid_pos_bottom": [{"key": "grid_bottom", "label": "下边距", "type": "text", "default": "60"}],
        "overlap_type": [{"key": "overlap_type", "label": "叠加类型", "type": "select", "options": [
            {"value": "bar_line", "label": "柱状图+折线图"},
            {"value": "line_scatter", "label": "折线图+散点图"}
        ], "default": "bar_line"}]
    }

    # Chart Type Mapping (Display Name & Icon)
    CHART_META = {
        "bar": {"label": "柱状图", "icon": "bi-bar-chart-fill"},
        "line": {"label": "折线图", "icon": "bi-graph-up"},
        "pie": {"label": "饼图", "icon": "bi-pie-chart-fill"},
        "scatter": {"label": "散点图", "icon": "bi-diagram-2"},
        "radar": {"label": "雷达图", "icon": "bi-hexagon"},
        "funnel": {"label": "漏斗图", "icon": "bi-funnel-fill"},
        "gauge": {"label": "仪表盘", "icon": "bi-speedometer2"},
        "map": {"label": "地图", "icon": "bi-map"},
        "heatmap": {"label": "热力图", "icon": "bi-grid-3x3"},
        "calendar": {"label": "日历图", "icon": "bi-calendar-date"},
        "graph": {"label": "关系图", "icon": "bi-share"},
        "liquid": {"label": "水球图", "icon": "bi-droplet"},
        "parallel": {"label": "平行坐标", "icon": "bi-distribute-vertical"},
        "pictorialbar": {"label": "象形柱图", "icon": "bi-bar-chart-steps"},
        "grid": {"label": "组合图表", "icon": "bi-grid-1x2-fill"},
        "overlap": {"label": "层叠图表", "icon": "bi-layers-fill"},
        "graphic": {"label": "图形组件", "icon": "bi-image"},
        "table": {"label": "数据表", "icon": "bi-table"}
    }

    output_configs = {
        "common_groups": [], 
        "charts": {}
    }

    # Define Group Labels
    PARAM_GROUP_LABELS = {
        "init_opts": "基础配置",
        "reversal_axis": "基础配置",
        "title_opts": "标题配置",
        "title_size": "标题配置",
        "title_color": "标题配置",
        "subtitle_size": "标题配置",
        "subtitle_color": "标题配置",
        "card_title_fontsize": "标题配置",
        "card_title_align": "标题配置",
        "legend_opts": "图例配置",
        "legend_text_size": "图例配置",
        "legend_text_color": "图例配置",
        "grid_opts": "布局配置",
        "tooltip_opts": "提示框配置",
        "toolbox_opts": "工具箱配置",
        "toolbox_show": "工具箱配置",
        "datazoom_opts": "缩放配置",
        "visualmap_opts": "视觉映射",
        "xaxis_opts": "X轴配置",
        "yaxis_opts": "Y轴配置",
        "radar_opts": "雷达配置",
        "itemstyle_opts": "系列配置",
        "linestyle_opts": "系列配置",
        "areastyle_opts": "系列配置",
        "area_style": "系列配置",
        "area_opacity": "系列配置",
        "label_opts": "标签样式",
        "markpoint_opts": "标记点",
        "markpoint_show": "标记点",
        "markpoint_type": "标记点",
        "markline_opts": "标记线",
        "markline_show": "标记线",
        "markline_type": "标记线",
        "brush_opts": "区域选择",
        "animation_opts": "动画配置",
        "center": "布局配置", 
        "radius": "布局配置",
        "rosetype": "系列配置",
        "split_number": "轴配置",
        "min_": "轴配置",
        "max_": "轴配置",
        "symbol": "系列配置",
        "symbol_opts": "系列配置",
        "symbol_size": "系列配置",
        "colors": "系列配置",
        "color_by": "系列配置",
        "max_symbol_size": "系列配置",
        "min_symbol_size": "系列配置",
        "bar_gap": "系列配置",
        "category_gap": "系列配置",
        "stack": "系列配置",
        "stack_strategy": "系列配置",
        "y_axis_type": "Y轴配置",
        "timeline_opts": "时间轴配置"
    }

    for chart_key, sections in raw_params.items():
        # chart_key is like "Bar", "Line"
        normalized_key = chart_key.lower()
        
        # Skip "高级组件" or non-chart keys if they are not actual charts
        if normalized_key in ["高级组件"]:
            continue
            
        # Initialize chart config
        chart_config = {
            "label": CHART_META.get(normalized_key, {}).get("label", chart_key),
            "icon": CHART_META.get(normalized_key, {}).get("icon", "bi-bar-chart"),
            "fields": []
        }

        # Collect all parameters from all sections
        # sections is a dict like {"全局配置": [...], "系列配置": [...]}
        for section_name, params in sections.items():
            for param in params:
                param_name = param.get("参数名称")
                
                # Check if we have a mapping for this param
                if param_name in FIELD_MAPPING:
                    fields = FIELD_MAPPING[param_name]
                    group_label = PARAM_GROUP_LABELS.get(param_name, "其他配置")
                    
                    # Add fields if not already present
                    for f in fields:
                        # Simple check to avoid duplicates if multiple params map to same fields
                        if not any(existing['key'] == f['key'] for existing in chart_config['fields']):
                            f_copy = f.copy()
                            f_copy['group'] = group_label
                            
                            # Special overrides
                            if normalized_key == 'scatter' and f['key'] == 'y_axis_type':
                                f_copy['label'] = "Y轴类型 (矩阵模式)"
                                f_copy['group'] = "基础配置"  # Move to Basic Config for visibility
                                
                            chart_config['fields'].append(f_copy)
                else:
                    # Special handling for some params that might be direct fields
                    # e.g. "rosetype" in Pie is listed as a param in charts_parameter.json?
                    # Let's check the file content structure again.
                    # "rosetype" is in "系列配置" for Pie.
                    if param_name == "rosetype":
                        f_copy = FIELD_MAPPING["rosetype"][0].copy()
                        f_copy['group'] = "系列配置"
                        chart_config['fields'].append(f_copy)
                    elif param_name == "radius_type": # Not in file, but maybe implicit?
                         pass 
        
        # Special logic for Pie radius
        if normalized_key == 'pie':
             # Pie usually needs radius configuration which might not be explicitly 'radius_type' param name in the file
             # The file has 'add' param which takes radius.
             # We manually add radius_type if it's missing
             if not any(f['key'] == 'radius_type' for f in chart_config['fields']):
                 f_copy = FIELD_MAPPING["radius_type"][0].copy()
                 f_copy['group'] = "系列配置"
                 chart_config['fields'].append(f_copy)

        # Special logic for Bar stack and gap
        if normalized_key == 'bar':
             if not any(f['key'] == 'stack' for f in chart_config['fields']):
                 chart_config['fields'].append({"key": "stack", "label": "堆叠显示", "type": "boolean", "default": False, "group": "系列配置"})
             if not any(f['key'] == 'category_gap' for f in chart_config['fields']):
                 chart_config['fields'].append({"key": "category_gap", "label": "柱间距离", "type": "text", "default": "20%", "group": "系列配置"})
             
             if not any(f['key'] == 'bar_width' for f in chart_config['fields']):
                 chart_config['fields'].extend([
                     {"key": "bar_width", "label": "柱子宽度(如 20px 或 50%)", "type": "text", "default": "", "group": "系列配置"},
                     {"key": "bar_max_width", "label": "最大宽度", "type": "text", "default": "", "group": "系列配置"},
                     {"key": "bar_min_width", "label": "最小宽度", "type": "text", "default": "", "group": "系列配置"}
                 ])

             # color_by injection moved to generic block

             # Inject Animation Opts for Bar Race
             if not any(f['group'] == '动画配置' for f in chart_config['fields']):
                 anim_fields = FIELD_MAPPING.get("animation_opts", [])
                 for f in anim_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "动画配置"
                     chart_config['fields'].append(f_copy)
                     
             # Inject Timeline Opts for Bar Race
             if not any(f['group'] == '时间轴配置' for f in chart_config['fields']):
                 tl_fields = FIELD_MAPPING.get("timeline_opts", [])
                 for f in tl_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "时间轴配置"
                     chart_config['fields'].append(f_copy)

                 # Inject PictorialBar Fields (Symbol, Repeat, Clip)
             # Default symbol to 'none' so standard bar is default
             if not any(f['key'] == 'symbol' for f in chart_config['fields']):
                 sym_fields = FIELD_MAPPING.get("symbol", [])
                 for f in sym_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置" # Merged into Series Config
                     f_copy['default'] = "none" # Override default
                     chart_config['fields'].append(f_copy)
                     
                 rep_fields = FIELD_MAPPING.get("symbol_repeat", [])
                 for f in rep_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)

                 clip_fields = FIELD_MAPPING.get("is_symbol_clip", [])
                 for f in clip_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)

             # Inject Line Chart Styles (LineStyle, AreaStyle, Smooth) for Mixed Chart support
             if not any(f['group'] == '系列配置' and f['key'] == 'is_smooth' for f in chart_config['fields']): # Check key instead of group
                 line_fields = FIELD_MAPPING.get("linestyle_opts", [])
                 for f in line_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)

             if not any(f['group'] == '系列配置' and f['key'] == 'area_style' for f in chart_config['fields']):
                 area_fields = FIELD_MAPPING.get("areastyle_opts", [])
                 for f in area_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)
                     
             # Inject Symbol Size if not present
             if not any(f['key'] == 'symbol_size' for f in chart_config['fields']):
                 sz_fields = FIELD_MAPPING.get("symbol_size", [])
                 for f in sz_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)

        if normalized_key == 'scatter':
            # color_by injection moved to generic block
            
            # Inject Max Symbol Size (for Punch Card)
            if not any(f['key'] == 'max_symbol_size' for f in chart_config['fields']):
                 chart_config['fields'].append({
                     "key": "max_symbol_size", 
                     "label": "最大气泡尺寸", 
                     "type": "number", 
                     "default": 20, 
                     "group": "系列配置"
                 })
                 
            # Inject Symbol Size (if not present)
            if not any(f['key'] == 'symbol_size' for f in chart_config['fields']):
                 sz_fields = FIELD_MAPPING.get("symbol_size", [])
                 for f in sz_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)

        # Inject Symbol and Symbol Size for Radar and Graph if missing
        if normalized_key in ['radar', 'graph']:
             if not any(f['key'] == 'symbol' for f in chart_config['fields']):
                 sym_fields = FIELD_MAPPING.get("symbol", [])
                 for f in sym_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)
                     
             if not any(f['key'] == 'symbol_size' for f in chart_config['fields']):
                 sz_fields = FIELD_MAPPING.get("symbol_size", [])
                 for f in sz_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)

        # Inject Y2 Axis Config for Bar and Line (Dual Axis support)
        if normalized_key in ['bar', 'line', 'scatter']:
             # Check if we already have y2 params (unlikely from standard config)
             if not any(f['group'] == 'Y2轴配置' for f in chart_config['fields']):
                 y2_fields = FIELD_MAPPING.get("y2_axis_opts", [])
                 for f in y2_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "Y2轴配置"
                     chart_config['fields'].append(f_copy)

        # Inject Custom Colors (colors) for common charts if missing
        if normalized_key in ['bar', 'line', 'scatter', 'pie', 'funnel', 'radar', 'heatmap', 'graph']:
             if not any(f['key'] == 'colors' for f in chart_config['fields']):
                 c_fields = FIELD_MAPPING.get("colors", [])
                 for f in c_fields:
                     f_copy = f.copy()
                     f_copy['group'] = "系列配置"
                     chart_config['fields'].append(f_copy)
             
             # Inject color_by if missing
             if not any(f['key'] == 'color_by' for f in chart_config['fields']):
                 chart_config['fields'].append({"key": "color_by", "label": "颜色分组", "type": "select", "options": [
                    {"value": "series", "label": "按系列"},
                    {"value": "data", "label": "按数据项"}
                 ], "default": "series", "group": "系列配置"})

        output_configs["charts"][normalized_key] = chart_config

    # Ensure Table is present
    if "table" not in output_configs["charts"]:
        output_configs["charts"]["table"] = {
            "label": "数据表",
            "icon": "bi-table",
            "fields": []
        }

    return output_configs
