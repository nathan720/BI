from pyecharts.charts import Bar, Line, Pie, Scatter, Radar, Funnel, Gauge, Map, HeatMap, Calendar, Graph, Liquid, Parallel, PictorialBar, Grid, Page, Sankey, Timeline
from pyecharts.components import Table
from pyecharts import options as opts
from pyecharts.commons.utils import JsCode
from pyecharts.globals import ThemeType, SymbolType
import re
import json

JS_CODE_MARKER = "__JSCODE__"

class ChartFactory:
    @staticmethod
    def dump_options(chart):
        """
        Custom dump options to handle JS functions correctly.
        Replaces wrapped JS code markers with actual function objects.
        """
        if not chart:
            return None
            
        # Get standard JSON dump
        options = chart.dump_options()
        
        # 1. Handle custom marker: "__JSCODE__...__JSCODE__"
        pattern = f'"{JS_CODE_MARKER}(.*?){JS_CODE_MARKER}"'
        
        def replacer(match):
            content = match.group(1)
            content = content.replace('\\"', '"')
            content = content.replace('\\n', '\n')
            content = content.replace('\\\\', '\\')
            return content
            
        options = re.sub(pattern, replacer, options, flags=re.DOTALL)
        
        # 2. Handle standard pyecharts JsCode marker: "--x_x--0_0--...--x_x--0_0--"
        # Pyecharts utils.JsCode wraps code in these markers
        standard_marker = "--x_x--0_0--"
        pattern_std = f'"{standard_marker}(.*?){standard_marker}"'
        
        options = re.sub(pattern_std, replacer, options, flags=re.DOTALL)
        
        return options

    @staticmethod
    def create_chart(chart_type, title, data, x_col=None, y_col=None, category_col=None, value_col=None, series_col=None, **kwargs):
        """
        Factory method to create pyecharts objects.
        
        :param chart_type: str, type of chart (bar, line, pie, etc.)
        :param title: str, chart title
        :param data: list of dicts, data rows
        :param x_col: str, column name for X axis (or category) - Legacy
        :param y_col: str or list, column name(s) for Y axis (or value) - Legacy
        :param category_col: str, column name for Category (X axis)
        :param value_col: str, column name for Value (Y axis)
        :param series_col: str, column name for Series (Group)
        :param kwargs: additional config options (legend_show, legend_orient, label_show, etc.)
        :return: pyecharts Chart object
        """
        if not data:
            return None
            
        # --- Timeline Support ---
        timeline_field = kwargs.get('timeline_field')
        if timeline_field:
            # Check if field exists in data
            if data and timeline_field in data[0]:
                try:
                    # Extract unique time points
                    time_points = sorted(list(set([str(row.get(timeline_field)) for row in data])))
                    
                    # Create Timeline
                    init_opts = kwargs.get('init_opts') or opts.InitOpts()
                    tl = Timeline(init_opts=init_opts)
                    
                    # Timeline specific options
                    play_interval = kwargs.get('timeline_play_interval', 1000)
                    auto_play = kwargs.get('timeline_auto_play', True)
                    
                    tl.add_schema(
                        play_interval=play_interval, 
                        is_auto_play=auto_play,
                        is_loop_play=True,
                        is_timeline_show=True
                    )
                    
                    # Recursively create charts for each time point
                    # Remove timeline_field to prevent infinite recursion
                    sub_kwargs = kwargs.copy()
                    del sub_kwargs['timeline_field']
                    
                    # Remove title from sub-charts to avoid duplication (Timeline usually shows title in global or updates it)
                    # Actually, pyecharts Timeline updates the option. 
                    # We might want the title to change dynamically? e.g. "Year: 2023"
                    # For now, let's keep the title static or let the user handle it via formatters?
                    # Usually Bar Race title changes.
                    # Let's append the time point to the title if it's not dynamic?
                    # Or just pass the original title.
                    
                    original_title = title
                    
                    for tp in time_points:
                        # Filter data
                        sub_data = [row for row in data if str(row.get(timeline_field)) == tp]
                        
                        if not sub_data:
                            continue
                            
                        # Update title to include time point?
                        # Standard Bar Race: Title usually static, subtitle or graphic text updates.
                        # But for simplicity, let's append to title or use it as title.
                        current_title = f"{original_title} - {tp}"
                        
                        # Create Chart
                        c = ChartFactory.create_chart(
                            chart_type, 
                            current_title, 
                            sub_data, 
                            x_col, y_col, category_col, value_col, series_col, 
                            **sub_kwargs
                        )
                        
                        if c:
                            tl.add(c, tp)
                            
                    return tl
                except Exception as e:
                    print(f"Error creating Timeline: {e}")
                    import traceback
                    traceback.print_exc()
                    # Fallback to normal chart if timeline fails
                    pass

        # --- Table Component ---
        if chart_type == 'table':
            try:
                table = Table()
                
                # Determine Headers
                headers = []
                target_cols = []
                
                # Prioritize explicit column selection
                if category_col: target_cols.append(category_col)
                if value_col:
                    if isinstance(value_col, list): target_cols.extend(value_col)
                    else: target_cols.append(value_col)
                
                # If no specific columns requested, use all keys from first data row
                if not target_cols and data:
                    target_cols = list(data[0].keys())
                
                headers = [str(c) for c in target_cols if c]
                
                # Prepare Rows
                rows = []
                for row in data:
                    r_data = []
                    for h in headers:
                        val = row.get(h)
                        if val is None: val = ""
                        r_data.append(str(val))
                    rows.append(r_data)
                
                table.add(headers, rows)
                
                if title:
                    table.set_global_opts(title_opts=opts.ComponentTitleOpts(title=title))
                    
                return table
            except Exception as e:
                print(f"Table creation failed: {e}")
                import traceback
                traceback.print_exc()
                return None

        # Auto-promote to grid if dual axis is requested via series configuration or grid_type
        series_axis = kwargs.get('series_axis', {})
        grid_type_arg = kwargs.get('grid_type', 'basic')
        has_right_axis = any(v == 'right' for v in series_axis.values())
        
        if chart_type in ['bar', 'line', 'scatter'] and (has_right_axis or grid_type_arg == 'multi_yaxis'):
            if 'default_series_type' not in kwargs:
                kwargs['default_series_type'] = chart_type
            chart_type = 'grid'
            
        # Extract options with defaults
        if chart_type == 'page':
            # Page Layout
            layout_type = kwargs.get('layout', 'SimplePageLayout')
            try:
                layout = getattr(Page, layout_type, Page.SimplePageLayout)
                page = Page(layout=layout)
                return page
            except Exception as e:
                print(f"Page creation error: {e}")
                return None

        legend_show = kwargs.get('legend_show', True)
        legend_orient = kwargs.get('legend_orient', 'horizontal')
        legend_pos = kwargs.get('legend_pos', 'top')
        label_show = kwargs.get('label_show', False)
        label_formatter = kwargs.get('label_formatter', None) # e.g. "{c}" or "{d}%"
        stack = kwargs.get('stack', False)
        x_rotate = kwargs.get('x_rotate', 0)
        title_show = kwargs.get('title_show', True)
        title_pos = kwargs.get('title_pos', 'left')
        title_color = kwargs.get('title_color', '#333333')
        title_size = kwargs.get('title_size', 18)
        subtitle_color = kwargs.get('subtitle_color', '#aaaaaa')
        subtitle_size = kwargs.get('subtitle_size', 12)
        colors = kwargs.get('colors', None)
        if colors and isinstance(colors, str):
            colors = [c.strip() for c in colors.split(',') if c.strip()]
        color_by = kwargs.get('color_by', 'series')
        legend_type = kwargs.get('legend_type', 'plain')
        
        # Grid Params
        # Allow grid_pos_* as fallback/alias to support different config styles
        grid_left = kwargs.get('grid_left')
        if not grid_left:
             grid_left = kwargs.get('grid_pos_left', '10%')
             
        grid_right = kwargs.get('grid_right')
        if not grid_right:
             grid_right = kwargs.get('grid_pos_right', '10%')
             
        grid_top = kwargs.get('grid_top')
        if not grid_top:
             grid_top = kwargs.get('grid_pos_top', '60')
             
        grid_bottom = kwargs.get('grid_bottom')
        if not grid_bottom:
             grid_bottom = kwargs.get('grid_pos_bottom', '60')
        
        # Legend Params
        legend_text_size = kwargs.get('legend_text_size', 12)
        legend_text_color = kwargs.get('legend_text_color', '#333333')

        # New Params Extraction
        subtitle = kwargs.get('subtitle', '')
        theme = kwargs.get('theme', 'light')
        bg_color = kwargs.get('bg_color', '#ffffff')
        
        # Axis Names
        x_axis_name = kwargs.get('x_axis_name', '')
        y_axis_name = kwargs.get('y_axis_name', '')
        y_axis_min = kwargs.get('y_axis_min')
        y_axis_max = kwargs.get('y_axis_max')
        if y_axis_min == '': y_axis_min = None
        if y_axis_max == '': y_axis_max = None
        
        y_formatter = kwargs.get('y_formatter', None) # Legacy
        
        # New Axis Configs
        x_axis_label_size = kwargs.get('x_axis_label_size', 12)
        x_axis_label_color = kwargs.get('x_axis_label_color', '#333333')
        x_axis_formatter = kwargs.get('x_axis_formatter', '{value}')
        
        y_axis_label_size = kwargs.get('y_axis_label_size', 12)
        y_axis_label_color = kwargs.get('y_axis_label_color', '#333333')
        y_axis_formatter = kwargs.get('y_axis_formatter', '{value}')
        
        # Prefer new y_axis_formatter if provided, else legacy y_formatter
        # Note: y_formatter in UI might be mapped to 'y_formatter' key.
        # But global config has 'y_axis_formatter'.
        # If both present, use specific one.
        if not y_axis_formatter or y_axis_formatter == '{value}':
             if y_formatter:
                 y_axis_formatter = y_formatter

        # New Feature: Series Naming and Formatting
        series_names = kwargs.get('series_names', {})
        series_formats = kwargs.get('series_formats', {})
        series_calculations = kwargs.get('series_calculations', {})
        series_suffixes = kwargs.get('series_suffixes', {})
        series_label_styles = kwargs.get('series_label_styles', {})
        format_type = kwargs.get('format_type', 'none')
        format_js = kwargs.get('format_js', '')
        
        # Helper to get formatter (shared for global and per-series)
        def get_js_formatter(f_type, f_js, suffix="", mode='axis'):
            # mode: 'axis' (default) or 'series'
            safe_suffix = suffix.replace("'", "\\'") if suffix else ""
            
            if f_type == 'custom':
                if f_js and f_js.strip():
                        if f_js.strip().startswith('function'):
                            return f"{JS_CODE_MARKER}{f_js}{JS_CODE_MARKER}"
                        
                        # Use Unified JS Formatter for custom script body
                        # Escape script for JS string literal
                        safe_script = f_js.replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ")
                        
                        if mode == 'axis':
                            return f"{JS_CODE_MARKER}function(value){{ try {{ return window.biFormatter.formatAxis(value, 'custom', '{safe_suffix}', '{safe_script}'); }} catch(e) {{ return value; }} }}{JS_CODE_MARKER}"
                        else:
                            return f"{JS_CODE_MARKER}function(params){{ try {{ return window.biFormatter.formatSeries(params, 'custom', '{safe_suffix}', '{safe_script}'); }} catch(e) {{ return params.value; }} }}{JS_CODE_MARKER}"
                            
                # Fallback if empty custom JS
                return f"{{value}}{suffix}" if mode == 'axis' else f"{{c}}{suffix}"
            
            # Use Unified JS Formatter for standard types
            if f_type in ['integer', 'float1', 'float2', 'percent', 'currency']:
                if mode == 'axis':
                    return f"{JS_CODE_MARKER}function(value){{ try {{ return window.biFormatter.formatAxis(value, '{f_type}', '{safe_suffix}'); }} catch(e) {{ return value; }} }}{JS_CODE_MARKER}"
                else:
                    return f"{JS_CODE_MARKER}function(params){{ try {{ return window.biFormatter.formatSeries(params, '{f_type}', '{safe_suffix}'); }} catch(e) {{ return params.value; }} }}{JS_CODE_MARKER}"
            
            # Default (none)
            # If suffix exists, we can still use biFormatter to be safe, or just string template
            if suffix:
                 if mode == 'axis':
                     return f"{JS_CODE_MARKER}function(value){{ try {{ return window.biFormatter.formatAxis(value, 'none', '{safe_suffix}'); }} catch(e) {{ return value + '{safe_suffix}'; }} }}{JS_CODE_MARKER}"
                 else:
                     return f"{JS_CODE_MARKER}function(params){{ try {{ return window.biFormatter.formatSeries(params, 'none', '{safe_suffix}'); }} catch(e) {{ return params.value + '{safe_suffix}'; }} }}{JS_CODE_MARKER}"
            
            return f"{{value}}" if mode == 'axis' else f"{{c}}"

        # Global formatter (legacy/default)
        y_axis_suffix_early = kwargs.get('y_axis_suffix', '')
        
        axis_formatter = get_js_formatter(format_type, format_js, y_axis_suffix_early, mode='axis')
        series_formatter = get_js_formatter(format_type, format_js, y_axis_suffix_early, mode='series')

        y_axis_formatter = axis_formatter
        label_formatter = series_formatter

        # Bar specific
        category_gap = kwargs.get('category_gap', '20%')
        bar_gap = kwargs.get('bar_gap', '30%')
        bar_width = kwargs.get('bar_width')
        bar_max_width = kwargs.get('bar_max_width')
        bar_min_width = kwargs.get('bar_min_width')
        reversal_axis = kwargs.get('reversal_axis', False)
        bar_border_radius = kwargs.get('bar_border_radius', None)
        
        # DataZoom
        datazoom_show = kwargs.get('datazoom_show', False)
        datazoom_type = kwargs.get('datazoom_type', 'slider')
        datazoom_orient = kwargs.get('datazoom_orient', 'horizontal')
        
        # VisualMap
        visualmap_show = kwargs.get('visualmap_show', False)
        visualmap_min = kwargs.get('visualmap_min', 0)
        visualmap_max = kwargs.get('visualmap_max', 100)

        # Tooltip
        tooltip_show = kwargs.get('tooltip_show', True)
        tooltip_trigger = kwargs.get('tooltip_trigger', 'axis')
        tooltip_text_size = kwargs.get('tooltip_text_size', 14)
        tooltip_text_color = kwargs.get('tooltip_text_color', '#ffffff')
        tooltip_background_color = kwargs.get('tooltip_background_color', 'rgba(50,50,50,0.7)')
        tooltip_border_color = kwargs.get('tooltip_border_color', '#333')
        tooltip_border_width = kwargs.get('tooltip_border_width', 0)

        # Force item trigger for Heatmap and Scatter Matrix (Punch Card)
        # Axis trigger doesn't make sense for matrix/2D-category data
        if chart_type == 'heatmap' or (chart_type == 'scatter' and kwargs.get('y_axis_type') == 'category'):
            tooltip_trigger = 'item'
        
        # Toolbox
        toolbox_show = kwargs.get('toolbox_show', True)
        
        # Brush
        brush_show = kwargs.get('brush_show', False)
        brush_type = kwargs.get('brush_type', 'rect')
        
        # Animation
        animation_show = kwargs.get('animation_show', True)
        animation_duration = kwargs.get('animation_duration', 1000)
        animation_easing = kwargs.get('animation_easing', 'cubicOut')
        
        # MarkPoint/MarkLine
        markpoint_show = kwargs.get('markpoint_show', False)
        markpoint_type = kwargs.get('markpoint_type', 'max')
        markline_show = kwargs.get('markline_show', False)
        markline_type = kwargs.get('markline_type', 'average')

        # Other specific
        smooth = kwargs.get('smooth', kwargs.get('is_smooth', False))
        area_style = kwargs.get('area_style', False)
        radius_type = kwargs.get('radius_type', 'ring')
        rosetype = kwargs.get('rosetype', 'none')
        shape = kwargs.get('shape', 'polygon')
        sort_ = kwargs.get('sort', 'descending')
        symbol_size = kwargs.get('symbol_size', 10)
        
        # Line specific
        is_step = kwargs.get('is_step', False)
        is_connect_nones = kwargs.get('is_connect_nones', False)
        symbol = kwargs.get('symbol', 'emptyCircle')
        area_opacity = kwargs.get('area_opacity', 0.5)
        
        # Pie/Radar/Scatter/Heatmap/Gauge specific
        pie_center = kwargs.get('pie_center', '50%,50%')
        splitline_show = kwargs.get('splitline_show', True)
        splitarea_show = kwargs.get('splitarea_show', True)
        radar_shape = kwargs.get('radar_shape', 'polygon')
        x_splitline_show = kwargs.get('x_splitline_show', False)
        y_splitline_show = kwargs.get('y_splitline_show', False)
        
        # Gauge specific
        min_ = kwargs.get('min_', 0)
        max_ = kwargs.get('max_', 100)
        split_number = kwargs.get('split_number', 10)
        radius = kwargs.get('radius', '75%')
        start_angle = kwargs.get('start_angle', 225)
        end_angle = kwargs.get('end_angle', -45)
        
        # PictorialBar specific
        symbol_repeat = kwargs.get('symbol_repeat', 'fixed')
        # Handle string booleans from UI
        if isinstance(symbol_repeat, str):
            if symbol_repeat.lower() == 'true':
                symbol_repeat = True
            elif symbol_repeat.lower() == 'false':
                symbol_repeat = False
                
        symbol_margin = kwargs.get('symbol_margin', 5)
        # Support both symbol_clip and is_symbol_clip (from config)
        symbol_clip = kwargs.get('symbol_clip', kwargs.get('is_symbol_clip', True))
        
        # Grid/Overlap specific
        grid_type = kwargs.get('grid_type', 'basic') # basic, vertical, horizontal, multi_yaxis
        overlap_type = kwargs.get('overlap_type', 'bar_line') # bar_line, line_scatter
        grid_pos_left = kwargs.get('grid_pos_left') or grid_left or '5%'
        grid_pos_right = kwargs.get('grid_pos_right') or grid_right or '5%'
        grid_pos_top = kwargs.get('grid_pos_top') or grid_top or '5%'
        grid_pos_bottom = kwargs.get('grid_pos_bottom') or grid_bottom or '5%'

        # Graph specific
        layout = kwargs.get('layout', 'force')
        gravity = kwargs.get('gravity', 0.2)
        repulsion = kwargs.get('repulsion', 50)
        edge_length = kwargs.get('edge_length', 30)
        
        # Liquid specific
        is_outline_show = kwargs.get('is_outline_show', True)
        is_liquid_animation = kwargs.get('is_liquid_animation', True)
        # Fix: Allow 'shape' parameter to override 'liquid_shape' if not provided, aligning with config
        liquid_shape = kwargs.get('liquid_shape', kwargs.get('shape', 'circle'))

        # Calendar specific
        calendar_range = kwargs.get('calendar_range', '2024')
        cell_size = kwargs.get('cell_size', 20)


        # Line Style
        line_width = kwargs.get('line_width', 2)
        line_type = kwargs.get('line_type', 'solid')

        # Axis Types
        x_axis_type = kwargs.get('x_axis_type', 'category')
        y_axis_type = kwargs.get('y_axis_type', 'value')
        
        # Axis Configuration (Advanced)
        x_axis_line_on_zero = kwargs.get('x_axis_line_on_zero', True)
        x_axis_tick_show = kwargs.get('x_axis_tick_show', True)
        x_axis_line_show = kwargs.get('x_axis_line_show', True)
        x_axis_inverse = kwargs.get('x_axis_inverse', False)
        x_axis_boundary_gap = kwargs.get('x_axis_boundary_gap', True)
        # Handle string "true"/"false" from UI
        if isinstance(x_axis_boundary_gap, str):
            x_axis_boundary_gap = x_axis_boundary_gap.lower() == 'true'
        
        y_axis_line_on_zero = kwargs.get('y_axis_line_on_zero', False)
        y_axis_tick_show = kwargs.get('y_axis_tick_show', True)
        y_axis_line_show = kwargs.get('y_axis_line_show', True)
        y_axis_inverse = kwargs.get('y_axis_inverse', False)

        # Bar Race / Animation Advanced
        realtime_sort = kwargs.get('realtime_sort', False)
        label_value_animation = kwargs.get('label_value_animation', False)
        animation_duration_update = kwargs.get('animation_duration_update', 300)
        animation_easing_update = kwargs.get('animation_easing_update', 'cubicOut')
        
        # --- Prepare Options Objects ---
        
        # Legend Position
        l_left, l_top, l_right, l_bottom = None, None, None, None
        if legend_pos == 'top':
            l_top = 'top'; l_left = 'center'
        elif legend_pos == 'bottom':
            l_bottom = '10px'; l_left = 'center'
        elif legend_pos == 'left':
            l_left = 'left'; l_top = 'middle'
        elif legend_pos == 'right':
            l_right = '10px'; l_top = 'middle'
        elif legend_pos == 'center':
            l_left = 'center'; l_top = 'top'

        common_legend_opts = opts.LegendOpts(
            type_=legend_type,
            is_show=legend_show, 
            orient=legend_orient, 
            pos_left=l_left, pos_top=l_top, pos_right=l_right, pos_bottom=l_bottom,
            textstyle_opts=opts.TextStyleOpts(color=legend_text_color, font_size=legend_text_size)
        )

        common_grid_opts = opts.GridOpts(
            pos_left=grid_left,
            pos_right=grid_right,
            pos_top=grid_top,
            pos_bottom=grid_bottom
        )
        
        common_title_opts = opts.TitleOpts(
            title=title,
            subtitle=subtitle,
            is_show=title_show,
            pos_left=title_pos,
            title_textstyle_opts=opts.TextStyleOpts(color=title_color, font_size=title_size),
            subtitle_textstyle_opts=opts.TextStyleOpts(color=subtitle_color, font_size=subtitle_size)
        )
        
        # Animation
        animation_opts = opts.AnimationOpts(
            animation=animation_show,
            animation_duration=animation_duration,
            animation_easing=animation_easing,
            animation_duration_update=animation_duration_update,
            animation_easing_update=animation_easing_update
        )
        
        # Init Options
        init_opts = opts.InitOpts(
            theme=theme, 
            bg_color=bg_color,
            animation_opts=animation_opts
        )
        
        # DataZoom
        common_datazoom_opts = None
        if datazoom_show:
            if datazoom_type == 'both':
                 common_datazoom_opts = [
                     opts.DataZoomOpts(is_show=True, type_='slider', orient=datazoom_orient),
                     opts.DataZoomOpts(is_show=True, type_='inside', orient=datazoom_orient)
                 ]
            else:
                 common_datazoom_opts = [opts.DataZoomOpts(is_show=True, type_=datazoom_type, orient=datazoom_orient)]
        
        # VisualMap
        visualmap_opts_input = kwargs.get('visualmap_opts')
        if visualmap_opts_input:
            if isinstance(visualmap_opts_input, dict):
                # Map keys if necessary, but usually pyecharts options map directly
                # However, keys like 'min' might need to be 'min_' if passing to constructor
                # Let's handle 'min' -> 'min_', 'max' -> 'max_' mapping if they exist in dict
                vm_kwargs = visualmap_opts_input.copy()
                if 'min' in vm_kwargs and 'min_' not in vm_kwargs:
                    vm_kwargs['min_'] = vm_kwargs.pop('min')
                if 'max' in vm_kwargs and 'max_' not in vm_kwargs:
                    vm_kwargs['max_'] = vm_kwargs.pop('max')
                if 'type' in vm_kwargs and 'type_' not in vm_kwargs:
                     vm_kwargs['type_'] = vm_kwargs.pop('type')
                
                # Ensure is_show is set if not present
                if 'is_show' not in vm_kwargs:
                    vm_kwargs['is_show'] = True
                    
                common_visualmap_opts = opts.VisualMapOpts(**vm_kwargs)
            elif isinstance(visualmap_opts_input, opts.VisualMapOpts):
                common_visualmap_opts = visualmap_opts_input
            else:
                common_visualmap_opts = None
        else:
            common_visualmap_opts = opts.VisualMapOpts(
                is_show=True, 
                min_=visualmap_min, 
                max_=visualmap_max,
            ) if visualmap_show else None
        
        # Toolbox
        common_toolbox_opts = opts.ToolboxOpts(is_show=toolbox_show)
        
        # Brush
        common_brush_opts = None
        if brush_show:
            common_brush_opts = opts.BrushOpts(tool_box=[brush_type], x_axis_index="all")
            
        # MarkPoint & MarkLine
        series_markpoint = None
        if markpoint_show:
            series_markpoint = opts.MarkPointOpts(
                data=[opts.MarkPointItem(type_=markpoint_type)]
            )
            
        series_markline = None
        if markline_show:
            series_markline = opts.MarkLineOpts(
                data=[opts.MarkLineItem(type_=markline_type)]
            )
            
        # ItemStyle (Border Radius and Color)
        itemstyle_opts = kwargs.get('itemstyle_opts')

        # Construct areastyle_opts if simple boolean is used
        areastyle_opts = kwargs.get('areastyle_opts')
        if not areastyle_opts and area_style:
            areastyle_opts = opts.AreaStyleOpts(opacity=area_opacity)
        
        # Construct itemstyle_opts from flattened params if not provided
        if not itemstyle_opts:
            # Extract item_color (for individual item color override in some contexts, but usually for series)
            # Actually, item_color in UI maps to 'color' in ItemStyle
            item_color = kwargs.get('item_color', None)
            
            # Clean up empty strings
            if item_color and isinstance(item_color, str) and not item_color.strip():
                item_color = None
            
            radius = None
            if bar_border_radius:
                 try:
                     radius = [float(x) for x in str(bar_border_radius).split(',')]
                     if len(radius) == 1: radius = radius[0]
                 except:
                     pass
            
            if item_color or radius:
                itemstyle_opts = opts.ItemStyleOpts(border_radius=radius, color=item_color)

        # Handle string "None" passed from UI for itemstyle_opts components
        if itemstyle_opts:
            if isinstance(itemstyle_opts, str):
                 # If it's a string (e.g. "None", ""), treat as None
                 itemstyle_opts = None
            elif isinstance(itemstyle_opts, opts.ItemStyleOpts):
                 # Check if color is empty string
                 if hasattr(itemstyle_opts, 'color') and itemstyle_opts.color == "":
                     itemstyle_opts.color = None
            elif isinstance(itemstyle_opts, dict):
                 # Clean up dict for itemstyle_opts passed from UI
                 # 1. Handle Color
                 c_val = itemstyle_opts.get('color') or itemstyle_opts.get('item_color')
                 if c_val == "":
                     c_val = None
                 
                 # Update color in dict (Pyecharts uses 'color')
                 if 'item_color' in itemstyle_opts:
                     del itemstyle_opts['item_color']
                 
                 # Only set color if it's not None (to avoid overriding defaults with None if that's an issue, but usually None is fine)
                 # However, if key exists and is None, it dumps as null. Better to remove key if None?
                 if c_val is not None:
                     itemstyle_opts['color'] = c_val
                 elif 'color' in itemstyle_opts:
                     del itemstyle_opts['color']

                 # 2. Handle Border Radius
                 br_val = itemstyle_opts.get('bar_border_radius')
                 if br_val:
                     try:
                         radius = [float(x) for x in str(br_val).split(',')]
                         if len(radius) == 1: radius = radius[0]
                         itemstyle_opts['border_radius'] = radius
                     except:
                         pass
                 
                 # Remove original key if it was bar_border_radius
                 if 'bar_border_radius' in itemstyle_opts:
                     del itemstyle_opts['bar_border_radius']

                 # 3. Handle Border Color
                 bc_val = itemstyle_opts.get('item_border_color')
                 if bc_val:
                     itemstyle_opts['border_color'] = bc_val
                 if 'item_border_color' in itemstyle_opts:
                     del itemstyle_opts['item_border_color']

                 # 4. Handle Border Width
                 bw_val = itemstyle_opts.get('item_border_width')
                 if bw_val is not None:
                     try:
                         itemstyle_opts['border_width'] = float(bw_val)
                     except:
                         pass
                 if 'item_border_width' in itemstyle_opts:
                     del itemstyle_opts['item_border_width']
                 
                 # 5. Handle Opacity
                 op_val = itemstyle_opts.get('item_opacity')
                 if op_val is not None:
                     try:
                         itemstyle_opts['opacity'] = float(op_val)
                     except:
                         pass
                 if 'item_opacity' in itemstyle_opts:
                     del itemstyle_opts['item_opacity']
                 
                 # Convert dict to ItemStyleOpts object for proper serialization (snake_case -> camelCase)
                 try:
                     itemstyle_opts = opts.ItemStyleOpts(**itemstyle_opts)
                 except Exception as e:
                     print(f"Error converting itemstyle_opts dict to object: {e}")

        # AreaStyle
        areastyle_opts = kwargs.get('areastyle_opts')
        if not areastyle_opts and area_style:
            areastyle_opts = opts.AreaStyleOpts(opacity=area_opacity)

        # LineStyle
        common_linestyle_opts = kwargs.get('linestyle_opts')
        if not common_linestyle_opts:
            common_linestyle_opts = opts.LineStyleOpts(
                width=line_width,
                type_=line_type
            )

        def process_value(val, calculation_formula):
            if not calculation_formula or not isinstance(calculation_formula, str) or not calculation_formula.strip():
                return val
            
            try:
                # Try to convert to float first
                if isinstance(val, str):
                    val_num = float(val.replace(',', ''))
                else:
                    val_num = float(val)
                
                calc = calculation_formula.strip()
                # 1. Replace 'value' or 'x' with current value
                if 'value' in calc:
                    calc = calc.replace('value', str(val_num))
                elif 'x' in calc:
                    calc = calc.replace('x', str(val_num))
                else:
                    if calc.startswith(('*', '/', '+', '-')):
                        calc = f"{val_num} {calc}"
                    else:
                        return val

                # 2. Safety check
                import re
                if re.match(r'^[\d\.\+\-\*\/\s\(\)]+$', calc):
                    try:
                        return eval(calc, {"__builtins__": {}}, {})
                    except Exception as e:
                        print(f"Calculation error: {e} for {calc}")
                        return val
                else:
                    print(f"Unsafe calculation string ignored: {calc}")
                    return val
            except (ValueError, TypeError):
                # If cannot convert to number, cannot calculate
                return val

        def to_number(val, col=None):
            try:
                if isinstance(val, str):
                    val = val.replace(',', '')
                val = float(val)
                
                # Apply data transformation if provided (Y-axis)
                # 1. Per-series calculation (priority)
                if col and series_calculations.get(col):
                     val = process_value(val, series_calculations[col])
                # 2. Global calculation (fallback if no series specific calculation)
                elif kwargs.get('data_calculation'):
                     val = process_value(val, kwargs.get('data_calculation'))

                return val
            except (ValueError, TypeError):
                return 0

        # Data Processing
        y_datasets = {}
        y_cols = []
        x_data = []

        # X-axis Calculation
        x_data_calculation = kwargs.get('x_data_calculation')

        # Helper to process X value
        def get_x_val(row, col):
            raw = row.get(col, '')
            if x_data_calculation:
                processed = process_value(raw, x_data_calculation)
                return str(processed)
            return str(raw)

        # Legacy fallback
        if not category_col: category_col = x_col
        if not value_col: value_col = y_col

        # If value_col is a list (multiple metrics), we skip the pivot logic (series_col)
        # because the pivot logic currently only supports single value column split by series.
        # We fall back to standard logic which handles multiple y-axis columns.
        if series_col and not isinstance(value_col, list):
            # Pivot Logic
            # 1. Get unique categories (X-axis)
            cats = []
            seen_cats = set()
            for row in data:
                c = get_x_val(row, category_col)
                if c not in seen_cats:
                    cats.append(c)
                    seen_cats.add(c)
            x_data = cats

            # 2. Get unique series (Y-axis keys)
            sers = []
            seen_sers = set()
            for row in data:
                s = str(row.get(series_col, ''))
                if s not in seen_sers:
                    sers.append(s)
                    seen_sers.add(s)
            y_cols = sers

            # 3. Build map
            data_map = {}
            for row in data:
                c = get_x_val(row, category_col)
                s = str(row.get(series_col, ''))
                # Fix: Pass value_col as second arg so to_number can find series_calculations['xs']
                val = to_number(row.get(value_col, 0), value_col)
                data_map[(c, s)] = val

            # 4. Build y_datasets
            for s in sers:
                series_data = []
                for c in cats:
                    series_data.append(data_map.get((c, s), 0))
                y_datasets[s] = series_data

        else:
            # Standard/Legacy Logic
            if not category_col and len(data) > 0:
                category_col = list(data[0].keys())[0]
            
            # Determine y_cols (series names)
            if value_col:
                if isinstance(value_col, list):
                    y_cols = value_col
                else:
                    y_cols = [value_col]
            else:
                if len(data) > 0:
                    keys = list(data[0].keys())
                    if len(keys) > 1:
                        y_cols = [keys[1]]
                    else:
                        y_cols = [keys[0]]

            # Prepare X axis data
            for row in data:
                if category_col:
                    if isinstance(category_col, list):
                        val = "-".join([str(row.get(c, '')) for c in category_col])
                        x_data.append(val)
                    else:
                        x_data.append(get_x_val(row, category_col))
                else:
                    x_data.append("")
            
            # Prepare Y axis datasets
            for col in y_cols:
                y_datasets[col] = [to_number(row.get(col, 0), col) for row in data]

        c = None
        
        # Label Options
        label_position = kwargs.get('label_position', 'top')
        lbl_opts = opts.LabelOpts(is_show=label_show, position=label_position)
        if label_formatter:
            if isinstance(label_formatter, str) and label_formatter.strip().startswith('function') and JS_CODE_MARKER not in label_formatter:
                label_formatter = f"{JS_CODE_MARKER}{label_formatter}{JS_CODE_MARKER}"
            lbl_opts = opts.LabelOpts(is_show=label_show, position=label_position, formatter=label_formatter)

        # Handle Axis Formatters (support JsCode)
        x_axis_suffix = kwargs.get('x_axis_suffix', '')
        y_axis_suffix = kwargs.get('y_axis_suffix', '')

        # Helper to apply suffix to simple formatters
        def apply_suffix(fmt, suffix):
            if not suffix: return fmt
            if not fmt: return f"{{value}}{suffix}"
            
            # If it's a JS function, we can't easily append string without parsing.
            # But if it's a simple string like "{value} kg", we can append.
            if isinstance(fmt, str) and not fmt.strip().startswith('function') and JS_CODE_MARKER not in fmt:
                return f"{fmt}{suffix}"
            return fmt

        x_axis_formatter = apply_suffix(x_axis_formatter, x_axis_suffix)
        y_axis_formatter = apply_suffix(y_axis_formatter, y_axis_suffix)

        if isinstance(x_axis_formatter, str) and x_axis_formatter.strip().startswith('function') and JS_CODE_MARKER not in x_axis_formatter:
            x_axis_formatter = f"{JS_CODE_MARKER}{x_axis_formatter}{JS_CODE_MARKER}"
            
        if isinstance(y_axis_formatter, str) and y_axis_formatter.strip().startswith('function') and JS_CODE_MARKER not in y_axis_formatter:
            y_axis_formatter = f"{JS_CODE_MARKER}{y_axis_formatter}{JS_CODE_MARKER}"

        # Helper for per-series label options
        def get_series_label_opts(col, default_fmt=None):
            # Resolve target column for config lookup
            # If we are in Pivot mode (series_col exists), the 'col' is a dynamic series name (e.g. "North")
            # We should fallback to the original value column (e.g. "Sales") if specific config is missing
            target_col = col
            if series_col and col not in series_formats and col not in series_label_styles and col not in series_calculations:
                 if value_col and isinstance(value_col, str):
                     target_col = value_col
                 elif value_col and isinstance(value_col, list) and len(value_col) == 1:
                     target_col = value_col[0]

            s_fmt = series_formats.get(target_col)
            s_suffix = series_suffixes.get(target_col, y_axis_suffix) # Fallback to global suffix
            
            # Get label style configs
            s_style = series_label_styles.get(target_col, {})
            s_show = s_style.get('show', label_show)
            s_size = s_style.get('size', None)
            s_color = s_style.get('color', None)
            s_position = s_style.get('position', label_position)

            opt = None
            # If specific format or specific suffix is defined
            if (s_fmt and s_fmt != 'none') or (s_suffix and s_suffix != y_axis_suffix):
                s_js = series_calculations.get(target_col, '') if s_fmt == 'custom' else ''
                f_type = s_fmt if s_fmt and s_fmt != 'none' else 'none'
                s_formatter = get_js_formatter(f_type, s_js, s_suffix, mode='series')
                opt = opts.LabelOpts(is_show=s_show, formatter=s_formatter, font_size=s_size, color=s_color, position=s_position)
            
            # If no specific format/suffix, but we have specific style
            elif s_style:
                # Use global formatter if present, else default_fmt
                fmt = label_formatter if label_formatter else default_fmt
                opt = opts.LabelOpts(is_show=s_show, formatter=fmt, font_size=s_size, color=s_color, position=s_position)
            
            # If we have a default format and no global format, return new opts with default
            elif default_fmt and not label_formatter:
                opt = opts.LabelOpts(is_show=label_show, formatter=default_fmt, position=label_position)
                 
            else:
                opt = lbl_opts
            
            # Inject valueAnimation if needed
            if label_value_animation and opt:
                # If it's the shared global object (lbl_opts), we should copy it to avoid side effects if needed, 
                # but pyecharts usually creates new dicts on dump. 
                # However, modifying .opts of a shared object modifies it for all.
                # Since all series share this property if set globally, it's fine.
                # But to be safe if we want to support per-series override later, we might want to clone.
                # For now, just modifying works as it's a global toggle.
                # Actually, opt might be a new instance or the global lbl_opts.
                # If it's lbl_opts, we modify it once.
                if hasattr(opt, 'opts'):
                     opt.opts['valueAnimation'] = True
            
            return opt

        # Helper for Tooltip Formatter
        def get_tooltip_formatter(trigger, stack_strategy='normal'):
            # Percent Stack Strategy Override
            if stack_strategy == 'percent':
                 js = f"""
                 function(params) {{
                     let res = '';
                     if (Array.isArray(params)) {{
                         if (params.length > 0) {{
                             res += params[0].name + '<br/>';
                         }}
                         params.forEach(item => {{
                             let val = item.value;
                             // ECharts axis trigger: item.value might be Y value or [X, Y]
                             // For bar, it's usually just value or [x, y] if using dataset
                             // In pyecharts add_yaxis, it's usually simple value or [val]
                             if (Array.isArray(val)) {{
                                 val = val[val.length - 1]; 
                             }}
                             
                             if (typeof val === 'number') {{
                                 val = val.toFixed(2) + '%';
                             }}
                             res += item.marker + item.seriesName + ': ' + val + '<br/>';
                         }});
                     }} else {{
                         let val = params.value;
                         if (Array.isArray(val)) {{
                             val = val[val.length - 1];
                         }}
                         if (typeof val === 'number') {{
                             val = val.toFixed(2) + '%';
                         }}
                         res += params.marker + params.name + ': ' + val;
                     }}
                     return res;
                 }}
                 """
                 return f"{JS_CODE_MARKER}{js.strip()}{JS_CODE_MARKER}"

            # Build configuration map for series
            config_map = {}
            for col in y_cols:
                # Resolve target column for config lookup (same logic as get_series_label_opts)
                target_col = col
                if series_col and col not in series_formats and col not in series_calculations:
                    if value_col and isinstance(value_col, str):
                         target_col = value_col
                    elif value_col and isinstance(value_col, list) and len(value_col) == 1:
                         target_col = value_col[0]

                s_name = series_names.get(col, col)
                fmt = series_formats.get(target_col, 'none')
                suff = series_suffixes.get(target_col, y_axis_suffix)
                if fmt != 'none' or suff:
                    entry = {'type': fmt, 'suffix': suff}
                    if fmt == 'custom':
                        entry['script'] = series_calculations.get(target_col, '')
                    config_map[s_name] = entry
            
            # Special handling for Scatter Matrix (Punch Card)
            # In this mode, y_cols are Y-axis categories, but the series name is derived from value_col.
            # We need to ensure config_map has an entry for the series name.
            is_scatter_matrix = chart_type == 'scatter' and kwargs.get('y_axis_type') == 'category'
            if is_scatter_matrix and value_col:
                target_col = value_col
                if isinstance(value_col, list):
                    if len(value_col) > 0: target_col = value_col[0]
                    else: target_col = None
                
                if target_col:
                    s_name = series_names.get(target_col, target_col) if isinstance(target_col, str) else "数值"
                    fmt = series_formats.get(target_col, 'none')
                    suff = series_suffixes.get(target_col, y_axis_suffix)
                    
                    if fmt != 'none' or suff:
                        entry = {'type': fmt, 'suffix': suff}
                        if fmt == 'custom':
                            entry['script'] = series_calculations.get(target_col, '')
                        config_map[s_name] = entry

            # If no specific configs, and no global suffix, return None (use default)
            if not config_map and not y_axis_suffix and chart_type != 'heatmap':
                return None

            map_str = json.dumps(config_map)
            safe_global_suffix = y_axis_suffix.replace("'", "\\'") if y_axis_suffix else ""
            
            # Note: We use window.biFormatter.formatTooltip
            # HeatMap specific handling: value is [x, y, value]
            if chart_type == 'heatmap' or is_scatter_matrix:
                js = f"""function(params) {{ 
                    try {{
                        const configMap = {map_str};
                        // Handle both item (object) and axis (array) triggers
                        let item = Array.isArray(params) ? params[0] : params;
                        
                        // HeatMap/ScatterMatrix value is [x, y, value]
                        // item.value might be null or undefined
                        if (!item.value || item.value.length < 3) return '';
                        
                        let val = item.value[2];
                        let seriesName = item.seriesName;
                        
                        // Look up config for this series
                        const cfg = configMap[seriesName] || {{ 'type': 'none', 'suffix': '{safe_global_suffix}' }};
                        
                        let formatted = val;
                        if (window.biFormatter && window.biFormatter.formatTooltip) {{
                             // We construct a mock item object with just the value we want to format
                             // or pass the value directly if supported?
                             // window.biFormatter.formatTooltip expects (params, type, suffix, script)
                             // It usually uses params.value. If params.value is array, it might use the last one?
                             // Let's create a proxy object to ensure it formats the correct scalar value
                             let proxyItem = {{ value: val, seriesName: seriesName, name: item.name }};
                             formatted = window.biFormatter.formatTooltip(proxyItem, cfg.type, cfg.suffix, cfg.script);
                        }} else {{
                             if (val !== undefined && val !== null) {{
                                 formatted = val + cfg.suffix;
                             }}
                        }}
                        
                        return item.marker + item.name + '<br/>' + seriesName + ': ' + formatted;
                    }} catch (e) {{
                        console.error('Tooltip error:', e);
                        return '';
                    }}
                }}"""
                return f"{JS_CODE_MARKER}{js.strip()}{JS_CODE_MARKER}"

            # Compact JS to avoid issues with newlines and comments in some environments
            js = f"""function(params) {{ try {{ const configMap = {map_str}; let res = ''; if (Array.isArray(params)) {{ if (params.length > 0) {{ res += params[0].name + '<br/>'; }} params.forEach(item => {{ const cfg = configMap[item.seriesName] || {{ 'type': 'none', 'suffix': '{safe_global_suffix}' }}; let formatted = item.value; try {{ if (window.biFormatter && window.biFormatter.formatTooltip) {{ formatted = window.biFormatter.formatTooltip(item, cfg.type, cfg.suffix, cfg.script); }} else if (Array.isArray(item.value) && item.value.length > 2) {{ formatted = item.value[2]; }} }} catch (e) {{ }} res += item.marker + item.seriesName + ': ' + formatted + '<br/>'; }}); }} else {{ const cfg = configMap[params.seriesName] || {{ 'type': 'none', 'suffix': '{safe_global_suffix}' }}; let formatted = params.value; try {{ if (window.biFormatter && window.biFormatter.formatTooltip) {{ formatted = window.biFormatter.formatTooltip(params, cfg.type, cfg.suffix, cfg.script); }} else if (Array.isArray(params.value) && params.value.length > 2) {{ formatted = params.value[2]; }} }} catch (e) {{ }} res += params.marker + params.name + ': ' + formatted; if (params.percent !== undefined) {{ res += ' (' + params.percent + '%)'; }} }} return res; }} catch (e) {{ console.error('Tooltip error:', e); return ''; }} }}"""
            return f"{JS_CODE_MARKER}{js.strip()}{JS_CODE_MARKER}"

        # Common Tooltip Options
        stack_strategy = kwargs.get('stack_strategy', 'normal')
        tooltip_formatter = kwargs.get('tooltip_formatter')
        if not tooltip_formatter:
             tooltip_formatter = get_tooltip_formatter(tooltip_trigger, stack_strategy)
             
        common_tooltip_opts = opts.TooltipOpts(
            trigger=tooltip_trigger, 
            is_show=tooltip_show,
            formatter=tooltip_formatter,
            background_color=tooltip_background_color,
            border_color=tooltip_border_color,
            border_width=tooltip_border_width,
            textstyle_opts=opts.TextStyleOpts(
                font_size=tooltip_text_size,
                color=tooltip_text_color
            )
        )

        # Axis Options
        xaxis_opts = opts.AxisOpts(
            name=x_axis_name,
            type_=x_axis_type,
            is_inverse=x_axis_inverse,
            boundary_gap=x_axis_boundary_gap,
            axislabel_opts=opts.LabelOpts(
                rotate=x_rotate, 
                font_size=x_axis_label_size,
                color=x_axis_label_color,
                formatter=x_axis_formatter
            ),
            splitline_opts=opts.SplitLineOpts(is_show=x_splitline_show),
            axisline_opts=opts.AxisLineOpts(
                is_show=x_axis_line_show,
                is_on_zero=x_axis_line_on_zero
            ),
            axistick_opts=opts.AxisTickOpts(
                is_show=x_axis_tick_show
            )
        )
        yaxis_opts = opts.AxisOpts(
            name=y_axis_name,
            type_=y_axis_type,
            is_inverse=y_axis_inverse,
            axislabel_opts=opts.LabelOpts(
                font_size=y_axis_label_size,
                color=y_axis_label_color,
                formatter=y_axis_formatter
            ),
            splitline_opts=opts.SplitLineOpts(is_show=y_splitline_show),
            axisline_opts=opts.AxisLineOpts(
                is_show=y_axis_line_show,
                is_on_zero=y_axis_line_on_zero
            ),
            axistick_opts=opts.AxisTickOpts(
                is_show=y_axis_tick_show
            )
        )

        # Default colors to use if none provided (Bright/Standard palette)
        default_colors = [
            "#5470c6", "#91cc75", "#fac858", "#ee6666", "#73c0de", 
            "#3ba272", "#fc8452", "#9a60b4", "#ea7ccc"
        ]
        
        if chart_type == 'bar':
            # Check if PictorialBar features are requested
            # If symbol is present and valid (not none/emptyCircle/null), use PictorialBar implementation
            use_pictorial = False
            if symbol and str(symbol).lower() not in ['none', 'emptycircle', 'null', '']:
                use_pictorial = True
                
            if use_pictorial:
                c = PictorialBar(init_opts=init_opts)
            else:
                c = Bar(init_opts=init_opts)
                
            if colors: 
                c.set_colors(colors)
            else:
                c.set_colors(default_colors)
            
            c.add_xaxis(x_data)
            
            # If stack is enabled, we need to ensure all series have the same stack name if just "stack=True"
            # Handle string "None" or empty string from UI
            if isinstance(stack, str) and (stack.lower() == 'none' or not stack.strip()):
                stack = False
            
            if isinstance(stack, str) and stack:
                 stack_name = stack
            else:
                 stack_name = 'stack1' if stack else None
            
                # Percent Stack Strategy
            stack_strategy = kwargs.get('stack_strategy', 'normal')
            if stack and stack_strategy == 'percent' and len(y_cols) > 0:
                 # Force Y-axis type to value
                 y_axis_type = 'value'
                 
                 # Calculate totals per X-axis index
                 # y_datasets values are lists of numbers
                 data_len = len(x_data)
                 totals = []
                 
                 # Ensure we only process columns that exist in both y_cols and y_datasets
                 # to avoid KeyError or mismatch
                 valid_y_cols = [col for col in y_cols if col in y_datasets]
                 
                 for i in range(data_len):
                     t = sum(y_datasets[col][i] for col in valid_y_cols if i < len(y_datasets[col]))
                     totals.append(t)
                 
                 # Normalize
                 for col in valid_y_cols:
                     new_vals = []
                     for i, v in enumerate(y_datasets[col]):
                         t = totals[i]
                         if t == 0:
                             new_vals.append(0)
                         else:
                             new_vals.append((v / t) * 100)
                     y_datasets[col] = new_vals
                 
                 # Update Y-Axis to 0-100%
                 # Re-create yaxis_opts with percent configuration
                 yaxis_opts = opts.AxisOpts(
                    name=y_axis_name,
                    type_=y_axis_type,
                    min_=0,
                    max_=100,
                    axislabel_opts=opts.LabelOpts(
                        font_size=y_axis_label_size,
                        color=y_axis_label_color,
                        formatter='{value}%'
                    ),
                    splitline_opts=opts.SplitLineOpts(is_show=y_splitline_show)
                 )
            
            # DEBUG: Print options relevant to rendering
            print(f"ChartFactory Bar Options: Stack={stack_name}, Strategy={stack_strategy}, BarGap={bar_gap}, CatGap={category_gap}, VisualMap={visualmap_show}, Pictorial={use_pictorial}, Symbol={symbol}")
            
            for col, vals in y_datasets.items():
                if use_pictorial:
                     # PictorialBar does not support 'stack'
                     c.add_yaxis(
                        series_names.get(col, col), 
                        vals, 
                        label_opts=get_series_label_opts(col), 
                        # stack=stack_name, # Removed for PictorialBar
                        gap=bar_gap,
                        category_gap=category_gap,
                        markpoint_opts=series_markpoint,
                        markline_opts=series_markline,
                        itemstyle_opts=itemstyle_opts,
                        symbol=symbol,
                        symbol_size=symbol_size,
                        symbol_repeat=symbol_repeat,
                        symbol_margin=symbol_margin,
                        is_symbol_clip=symbol_clip
                    )
                else:
                    c.add_yaxis(
                        series_names.get(col, col), 
                        vals, 
                        label_opts=get_series_label_opts(col), 
                        stack=stack_name,
                        gap=bar_gap,
                        category_gap=category_gap,
                        bar_width=bar_width,
                        bar_max_width=bar_max_width,
                        bar_min_width=bar_min_width,
                        markpoint_opts=series_markpoint,
                        markline_opts=series_markline,
                        itemstyle_opts=itemstyle_opts
                    )
                
                # Apply realtime sort if enabled
                if realtime_sort:
                    c.options['series'][-1]['realtimeSort'] = True
            
            if len(data) > 0:
                print(f"ChartFactory Data Sample (First 2): {data[:2]}")
                print(f"ChartFactory X Data (First 5): {x_data[:5]}")
                print(f"ChartFactory Y Cols: {y_cols}")
                for yc in y_cols:
                     print(f"ChartFactory Y Data [{yc}] (First 5): {y_datasets[yc][:5]}")

            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                tooltip_opts=common_tooltip_opts,
                xaxis_opts=xaxis_opts,
                yaxis_opts=yaxis_opts,
                datazoom_opts=common_datazoom_opts,
                visualmap_opts=common_visualmap_opts,
                toolbox_opts=common_toolbox_opts,
                brush_opts=common_brush_opts
            )

            if reversal_axis:
                # c.reversal_axis()
                # Manual swap to ensure it works
                c.options["xAxis"], c.options["yAxis"] = c.options["yAxis"], c.options["xAxis"]

            if color_by == 'data':
                c.set_series_opts(colorBy='data')
            
            grid = Grid(init_opts=init_opts)
            grid.add(c, grid_opts=common_grid_opts)
            
            # Ensure global colors are propagated to Grid
            if colors:
                grid.options['color'] = colors
            else:
                grid.options['color'] = default_colors
                
            return grid

        elif chart_type == 'line':
            c = Line(init_opts=init_opts)
            if colors: 
                c.set_colors(colors)
            else:
                c.set_colors(default_colors)
            c.add_xaxis(x_data)
            
            if isinstance(stack, str) and stack:
                 stack_name = stack
            else:
                 stack_name = 'stack1' if stack else None
            
            for col, vals in y_datasets.items():
                c.add_yaxis(
                    series_names.get(col, col), 
                    vals, 
                    label_opts=get_series_label_opts(col), 
                    stack=stack_name,
                    is_smooth=smooth,
                    is_step=is_step,
                    is_connect_nones=is_connect_nones,
                    symbol=symbol,
                    symbol_size=symbol_size,
                    areastyle_opts=areastyle_opts,
                    linestyle_opts=common_linestyle_opts,
                    markpoint_opts=series_markpoint,
                    markline_opts=series_markline,
                    itemstyle_opts=itemstyle_opts
                )
                
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                tooltip_opts=common_tooltip_opts,
                xaxis_opts=xaxis_opts,
                yaxis_opts=yaxis_opts,
                datazoom_opts=common_datazoom_opts,
                visualmap_opts=common_visualmap_opts,
                toolbox_opts=common_toolbox_opts,
                brush_opts=common_brush_opts
            )

            if color_by == 'data':
                c.set_series_opts(colorBy='data')

            grid = Grid(init_opts=init_opts)
            grid.add(c, grid_opts=common_grid_opts)
            
            # Ensure global colors are propagated to Grid
            if colors:
                grid.options['color'] = colors
            else:
                grid.options['color'] = default_colors
                
            return grid

        elif chart_type == 'pie':
            if y_cols:
                primary_y = y_cols[0]
                y_data = y_datasets[primary_y]
                pie_data = [list(z) for z in zip(x_data, y_data)]
                
                pie_lbl_opts = get_series_label_opts(primary_y, default_fmt="{b}: {c}")
                
                c = Pie(init_opts=init_opts)
                if colors: 
                    c.set_colors(colors)
                else:
                    c.set_colors(default_colors)
                
                radius = ["40%", "75%"] if radius_type == 'ring' else ["0%", "75%"]
                rosetype_val = rosetype if rosetype in ['radius', 'area'] else None
                
                # Center parsing
                center_list = ["50%", "50%"]
                if pie_center:
                    parts = str(pie_center).split(',')
                    if len(parts) == 2:
                        center_list = [p.strip() for p in parts]

                c.add(series_names.get(primary_y, primary_y), pie_data, radius=radius, center=center_list, rosetype=rosetype_val, label_opts=pie_lbl_opts, itemstyle_opts=itemstyle_opts)
                c.set_global_opts(
                    title_opts=common_title_opts,
                    legend_opts=common_legend_opts,
                    tooltip_opts=common_tooltip_opts,
                    visualmap_opts=common_visualmap_opts,
                    toolbox_opts=common_toolbox_opts
                )
                if color_by == 'data':
                     c.set_series_opts(colorBy='data')

        elif chart_type == 'scatter':
            c = Scatter(init_opts=init_opts)
            if colors: 
                c.set_colors(colors)
            else:
                c.set_colors(default_colors)
            
            # Handle symbol_size (support JS function)
            if isinstance(symbol_size, str) and symbol_size.strip().startswith('function') and JS_CODE_MARKER not in symbol_size:
                 symbol_size = f"{JS_CODE_MARKER}{symbol_size}{JS_CODE_MARKER}"

            is_scatter_matrix = kwargs.get('y_axis_type') == 'category'
            
            if is_scatter_matrix:
                # Matrix Mode (Punch Card)
                # Note: Do NOT use c.add_xaxis(x_data) here, as it forces 1-to-1 mapping with series data.
                # We must also initialize _xaxis_data to empty list to satisfy Scatter._parse_data check
                # and bypass auto-zip logic.
                c._xaxis_data = []
                
                # Instead, we inject x_data into xaxis_opts.
                if xaxis_opts:
                    # Refactor: Create a fresh AxisOpts for Matrix mode to avoid mutation issues
                    # We copy relevant properties from the original xaxis_opts but force type="category"
                    # This avoids the .opts['type'] hack and potential side effects
                    
                    # Extract original opts dictionary
                    orig_opts = xaxis_opts.opts
                    
                    # Create new opts with forced type and data
                    # We must preserve style options like axislabel_opts, splitline_opts etc.
                    # Pyecharts AxisOpts stores everything in self.opts.
                    # We can clone the dict and update it.
                    new_opts = orig_opts.copy()
                    new_opts['type'] = 'category'
                    new_opts['data'] = x_data
                    
                    # Remove 'type_' key if it exists (artifact of previous updates or init)
                    if 'type_' in new_opts:
                        del new_opts['type_']
                        
                    # Re-wrap in AxisOpts? No, AxisOpts just dumps opts.
                    # But we need to assign it back to xaxis_opts variable OR use a new variable.
                    # Since we pass xaxis_opts to set_global_opts later, we should update the variable.
                    # But xaxis_opts is an object.
                    # We can create a new object and inject the opts.
                    # But AxisOpts doesn't accept a full dict in init.
                    # So we have to rely on the fact that Pyecharts objects are just wrappers around .opts
                    
                    # Safer approach: Create new AxisOpts with explicit parameters matching the original
                    # This is verbose but safe.
                    # However, xaxis_opts was created with many params (lines 1045-1064).
                    # Copying them all is hard to maintain.
                    
                    # Middle ground: Use the clone strategy but cleaner.
                    # We modify the object's internal state but via a clean replacement of the dict?
                    # No, that's still mutation.
                    
                    # Let's create a NEW object that mimics the old one but with overrides.
                    # Actually, since we are inside create_chart, xaxis_opts is local.
                    # Replacing the variable `xaxis_opts` with a new object is fine.
                    # But how to create it with all the same styles?
                    
                    # We can use the .update() method properly IF we trust it.
                    # But the user specifically asked for "different types via if judgment assignment".
                    
                    # Let's try to modify the dictionary directly but robustly, 
                    # OR create a new wrapper that outputs the modified dict.
                    
                    # Let's stick to the direct dictionary modification but cleaner, 
                    # ensuring we remove conflicting keys like 'type_'.
                    xaxis_opts.opts['type'] = 'category'
                    xaxis_opts.opts['data'] = x_data
                    if 'type_' in xaxis_opts.opts:
                        del xaxis_opts.opts['type_']
                        
                scatter_data = []
                for j, col in enumerate(y_cols):
                     vals = y_datasets.get(col, [])
                     for i, val in enumerate(vals):
                          if val is not None:
                              scatter_data.append([i, j, val])
                
                if yaxis_opts:
                    # Ensure Y-axis is also category type with correct data
                    yaxis_opts.opts['type'] = 'category'
                    yaxis_opts.opts['data'] = y_cols
                    if 'type_' in yaxis_opts.opts:
                        del yaxis_opts.opts['type_']
                
                # 1. Fix Series Name: Use user alias if available, otherwise "数值" or generic name
                # The user sees 'Monday' because we were picking y_cols[0] (which is a dimension in Pivot mode).
                # We should try to use the value column's alias.
                s_name = "数值"
                if y_cols:
                    # In matrix mode, y_cols are the categories on Y-axis.
                    # The actual series name should represent the metric being visualized.
                    # We check if there's a mapped name for the value column.
                    if value_col:
                        # value_col might be a string (col name)
                        s_name = series_names.get(value_col, value_col) if isinstance(value_col, str) else "数值"
                    else:
                        s_name = "数值"
                
                # 2. Fix Symbol Size: Default to dynamic sizing if user didn't specify custom size
                # If symbol_size is missing or generic default (10), use dynamic sizing based on value
                sym_size_val = kwargs.get('symbol_size')
                min_symbol_size = kwargs.get('min_symbol_size', 5)
                max_symbol_size = kwargs.get('max_symbol_size', 20) # Default max size if not specified
                
                # Calculate max value for scaling if needed
                # We need to scan all values in scatter_data to find the max value for normalization
                max_data_val = 1
                if scatter_data:
                    # scatter_data items are [i, j, val]
                    vals = [d[2] for d in scatter_data if isinstance(d[2], (int, float))]
                    if vals:
                        max_data_val = max(vals)
                if max_data_val == 0: max_data_val = 1

                if sym_size_val is None or str(sym_size_val).strip() == '10':
                     # Use value directly as size but ensure minimum visibility AND maximum limit.
                     # We use a simple linear scaling: (val / max_val) * max_symbol_size
                     # But we also ensure it's at least min_symbol_size.
                     # However, if max_symbol_size is very large, this might be too small for small values.
                     # Let's support two modes? Or just simple clamping?
                     # User request: "Overall bubble display proportion" or "Max display range".
                     # Scaling is safer.
                     # Note: symbolSize callback receives (value, params), where value is [x, y, z]
                     # We pass max_data_val into the JS function string.
                     symbol_size = JsCode(f"function (val) {{ try {{ if (!val || val.length < 3) return {min_symbol_size}; var size = (val[2] / {max_data_val}) * {max_symbol_size}; return Math.max(size, {min_symbol_size}); }} catch(e) {{ return {min_symbol_size}; }} }}")
                
                # 3. Fix Labels: Default to Show if not explicitly disabled
                # If 'label_show' is False (default) or missing, force it to True for Matrix mode
                # so users see data immediately as requested.
                if not kwargs.get('label_show'):
                    label_show = True
                
                # Matrix Label Fix: If no custom formatter is provided (or it's just the default {c}),
                # default to showing value (index 2). Otherwise standard label might show index or nothing.
                matrix_lbl_opts = lbl_opts
                is_default_fmt = label_formatter == "{c}"
                
                if label_show and (not label_formatter or is_default_fmt):
                    # Check if there is a specific format for the value column
                    val_fmt_entry = None
                    if value_col:
                        # Reuse the logic from get_tooltip_formatter to find format config
                         if value_col in series_formats:
                             val_fmt_entry = {'type': series_formats[value_col], 'suffix': series_suffixes.get(value_col, '')}
                    
                    # Construct JS formatter
                    # If we have biFormatter (assumed available in frontend), use it.
                    # Otherwise fallback to simple value.
                    if val_fmt_entry:
                        fmt_type = val_fmt_entry['type']
                        suffix = val_fmt_entry['suffix']
                        # We need to be careful with quotes in f-string
                        # Compact JS to avoid issues with newlines
                        js_fmt = f"function(p){{ try {{ var val = (p && p.data && p.data.length > 2) ? p.data[2] : null; if (val === null) return ''; if (window.biFormatter && window.biFormatter.format) {{ return window.biFormatter.format(val, '{fmt_type}') + '{suffix}'; }} return val; }} catch (e) {{ return (p && p.data && p.data.length > 2) ? p.data[2] : ''; }} }}"
                        formatter_code = JsCode(js_fmt)
                    else:
                        formatter_code = JsCode("function(p){return (p && p.data && p.data.length > 2) ? p.data[2] : '';}")

                    matrix_lbl_opts = opts.LabelOpts(
                        is_show=True,
                        position=label_position,
                        formatter=formatter_code
                    )

                c.add_yaxis(
                    s_name,
                    scatter_data,
                    label_opts=matrix_lbl_opts,
                    symbol=symbol,
                    symbol_size=symbol_size,
                    itemstyle_opts=itemstyle_opts
                )
            else:
                c.add_xaxis(x_data)
                for col, vals in y_datasets.items():
                    c.add_yaxis(
                        series_names.get(col, col), 
                        vals, 
                        label_opts=get_series_label_opts(col), 
                        symbol=symbol,
                        symbol_size=symbol_size,
                        markpoint_opts=series_markpoint,
                        markline_opts=series_markline,
                        itemstyle_opts=itemstyle_opts
                    )
                
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                tooltip_opts=common_tooltip_opts,
                xaxis_opts=xaxis_opts,
                yaxis_opts=yaxis_opts,
                datazoom_opts=common_datazoom_opts,
                visualmap_opts=common_visualmap_opts,
                toolbox_opts=common_toolbox_opts,
                brush_opts=common_brush_opts
            )
            
            if color_by == 'data':
                c.set_series_opts(colorBy='data')

            grid = Grid(init_opts=init_opts)
            grid.add(c, grid_opts=common_grid_opts)
            
            # Ensure global colors are propagated to Grid
            if colors:
                grid.options['color'] = colors
            else:
                grid.options['color'] = default_colors
                
            return grid
            
        elif chart_type == 'radar':
            # Simplified Radar
            all_vals = []
            for vals in y_datasets.values():
                all_vals.extend(vals)
            max_val = max(all_vals) if all_vals else 100
            
            schema = [
                opts.RadarIndicatorItem(name=x, max_=max_val) for x in x_data
            ]
            
            c = Radar(init_opts=init_opts)
            if colors: 
                c.set_colors(colors)
            else:
                c.set_colors(default_colors)
            c.add_schema(
                schema=schema, 
                shape=radar_shape,
                splitline_opt=opts.SplitLineOpts(is_show=splitline_show),
                splitarea_opt=opts.SplitAreaOpts(is_show=splitarea_show, areastyle_opts=opts.AreaStyleOpts(opacity=1))
            )
            
            for col, vals in y_datasets.items():
                c.add(
                    series_names.get(col, col), 
                    [vals], 
                    label_opts=get_series_label_opts(col), 
                    areastyle_opts=areastyle_opts,
                    linestyle_opts=common_linestyle_opts,
                    symbol=symbol,
                    symbol_size=symbol_size
                )
                
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                tooltip_opts=common_tooltip_opts,
                toolbox_opts=common_toolbox_opts
            )
            
        elif chart_type == 'funnel':
            if y_cols:
                primary_y = y_cols[0]
                y_data = y_datasets[primary_y]
                funnel_data = [list(z) for z in zip(x_data, y_data)]
                c = Funnel(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add(
                    series_names.get(primary_y, "Funnel"),
                    funnel_data,
                    gap=2,
                    sort_=sort_,
                    label_opts=get_series_label_opts(primary_y)
                )
                c.set_global_opts(
                    title_opts=common_title_opts,
                    legend_opts=common_legend_opts,
                    visualmap_opts=common_visualmap_opts,
                    tooltip_opts=common_tooltip_opts,
                    toolbox_opts=common_toolbox_opts
                )
            
        elif chart_type == 'gauge':
            if y_cols:
                primary_y = y_cols[0]
                vals = y_datasets[primary_y]
                val = vals[0] if vals else 0
                name = x_data[0] if x_data else primary_y
                
                gauge_lbl_opts = lbl_opts
                if not label_formatter:
                    gauge_lbl_opts = opts.LabelOpts(formatter="{value}", is_show=label_show)
                    
                c = Gauge(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add(
                    series_name=series_names.get(name, name),
                    data_pair=[(series_names.get(name, name), val)],
                    min_=min_,
                    max_=max_,
                    split_number=split_number,
                    radius=radius,
                    start_angle=start_angle,
                    end_angle=end_angle,
                    detail_label_opts=get_series_label_opts(name),
                )
                c.set_global_opts(
                    title_opts=common_title_opts,
                    legend_opts=common_legend_opts, 
                    tooltip_opts=common_tooltip_opts,
                    toolbox_opts=common_toolbox_opts
                )

        elif chart_type == 'heatmap':
            heatmap_data = []
            # Use y_datasets which handles both Standard and Pivot modes correctly
            # y_datasets[col] is a list of values corresponding to x_data
            for j, col in enumerate(y_cols):
                vals = y_datasets.get(col, [])
                for i, val in enumerate(vals):
                    heatmap_data.append([i, j, val])
            
            c = HeatMap(init_opts=init_opts)
            if colors: c.set_colors(colors)
            c.add_xaxis(x_data)
            
            # HeatMap requires Y-axis to be category type with series names
            # We must override the default 'value' type derived from global config
            if yaxis_opts:
                # Use direct dictionary modification to avoid potential Pyecharts update() issues
                # and align with other charts' safety patterns.
                yaxis_opts.opts['type'] = 'category'
                yaxis_opts.opts['data'] = y_cols
                if 'type_' in yaxis_opts.opts:
                    del yaxis_opts.opts['type_']
                
            # Determine Series Name
            # Use the value column name (and its display name) if available
            s_name = "Series"
            if y_cols:
                col = y_cols[0]
                s_name = series_names.get(col, col)

            c.add_yaxis(
                s_name,
                y_cols,
                heatmap_data,
                label_opts=lbl_opts,
            )
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                visualmap_opts=common_visualmap_opts,
                tooltip_opts=common_tooltip_opts,
                xaxis_opts=xaxis_opts,
                yaxis_opts=yaxis_opts,
                toolbox_opts=common_toolbox_opts
            )
            
            grid = Grid(init_opts=init_opts)
            grid.add(c, grid_opts=common_grid_opts)
            
            # Ensure global colors are propagated to Grid
            if colors:
                grid.options['color'] = colors
            else:
                grid.options['color'] = default_colors
                
            return grid

        elif chart_type == 'calendar':
            if y_cols:
                primary_y = y_cols[0]
                y_data = y_datasets[primary_y]
                # Data should be list of [date, value]
                calendar_data = [[x_data[i], y_data[i]] for i in range(len(x_data))]
                
                c = Calendar(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add(
                    series_name=series_names.get(primary_y, primary_y),
                    yaxis_data=calendar_data,
                    calendar_opts=opts.CalendarOpts(
                        range_=calendar_range,
                        daylabel_opts=opts.CalendarDayLabelOpts(name_map="cn"),
                        monthlabel_opts=opts.CalendarMonthLabelOpts(name_map="cn"),
                        yearlabel_opts=opts.CalendarYearLabelOpts(is_show=False)
                    ),
                    label_opts=get_series_label_opts(primary_y)
                )
                c.set_global_opts(
                    title_opts=common_title_opts,
                    visualmap_opts=common_visualmap_opts,
                    legend_opts=common_legend_opts,
                    tooltip_opts=common_tooltip_opts,
                    toolbox_opts=common_toolbox_opts
                )

        elif chart_type == 'graph':
            if y_cols:
                target_col = y_cols[0]
                val_col = y_cols[1] if len(y_cols) > 1 else None
                
                nodes = set()
                links = []
                for row in data:
                    src = str(row.get(x_col, ''))
                    tgt = str(row.get(target_col, ''))
                    if src: nodes.add(src)
                    if tgt: nodes.add(tgt)
                    
                    val = to_number(row.get(val_col, 1), val_col) if val_col else 1
                    links.append(opts.GraphLink(source=src, target=tgt, value=val))
                
                nodes_data = [opts.GraphNode(name=n, symbol_size=symbol_size, symbol=symbol) for n in nodes]
                
                c = Graph(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add(
                    series_names.get(target_col, target_col),
                    nodes_data,
                    links,
                    layout=layout,
                    gravity=gravity,
                    repulsion=repulsion,
                    edge_length=edge_length,
                    label_opts=get_series_label_opts(target_col)
                )
                c.set_global_opts(
                    title_opts=common_title_opts,
                    toolbox_opts=common_toolbox_opts,
                    tooltip_opts=common_tooltip_opts
                )

        elif chart_type == 'liquid':
            if y_cols:
                primary_y = y_cols[0]
                y_data = y_datasets[primary_y]
                
                # If multiple data points exist (e.g. from Dimension breakdown), 
                # we sum them up to get a single value for the Liquid chart.
                # This handles the case where user selects a Dimension but wants a single Liquid ball.
                # Use safe sum to handle None values
                clean_y_data = [v for v in y_data if v is not None and isinstance(v, (int, float))]
                val = sum(clean_y_data) if clean_y_data else 0
                
                liquid_data = []
                
                # Logic to normalize value to 0-1 if it looks like percentage (0-100)
                # But if value is > 100, we keep it as is.
                # If value is 5000, it will just fill the container.
                if val > 1 and val <= 100:
                    liquid_data.append(val / 100.0)
                else:
                    liquid_data.append(val)
                
                # Ensure we have at least one value
                if not liquid_data:
                    liquid_data = [0.5]
                
                c = Liquid(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add(
                    series_names.get(primary_y, "Liquid"), 
                    liquid_data,
                    is_outline_show=is_outline_show,
                    shape=liquid_shape,
                    is_animation=is_liquid_animation,
                    label_opts=get_series_label_opts(primary_y)
                )
                c.set_global_opts(title_opts=common_title_opts, tooltip_opts=common_tooltip_opts)

        elif chart_type == 'parallel':
            schema = [opts.ParallelAxisOpts(dim=i, name=col) for i, col in enumerate(y_cols)]
            p_data = []
            for row in data:
                item = [to_number(row.get(col, 0), col) for col in y_cols]
                p_data.append(item)
                
            c = Parallel(init_opts=init_opts)
            if colors: c.set_colors(colors)
            c.add_schema(schema)
            c.add(
                series_names.get("Series", "Series"), 
                p_data, 
                linestyle_opts=common_linestyle_opts,
                itemstyle_opts=itemstyle_opts
            )
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                toolbox_opts=common_toolbox_opts,
                tooltip_opts=common_tooltip_opts
            )

        elif chart_type == 'pictorial_bar' or chart_type == 'pictorialbar':
            c = PictorialBar(init_opts=init_opts)
            if colors: c.set_colors(colors)
            c.add_xaxis(x_data)
            
            stack_name = 'stack1' if stack else None
            
            for col, vals in y_datasets.items():
                c.add_yaxis(
                    series_names.get(col, col), 
                    vals, 
                    label_opts=get_series_label_opts(col), 
                    symbol=symbol,
                    symbol_size=symbol_size,
                    symbol_repeat=symbol_repeat,
                    symbol_margin=symbol_margin,
                    is_symbol_clip=symbol_clip
                )
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                tooltip_opts=common_tooltip_opts,
                xaxis_opts=xaxis_opts,
                yaxis_opts=yaxis_opts,
                toolbox_opts=common_toolbox_opts
            )
            
            grid = Grid(init_opts=init_opts)
            grid.add(c, grid_opts=common_grid_opts)

            # Ensure global colors are propagated to Grid
            if colors:
                grid.options['color'] = colors
            else:
                grid.options['color'] = default_colors
            
            return grid

        elif chart_type == 'sankey':
            if len(y_cols) < 1:
                return None
                
            source_col = x_col
            target_col = y_cols[0]
            value_col = y_cols[1] if len(y_cols) > 1 else None
            
            nodes = set()
            links = []
            
            # Sankey Specific
            node_align = kwargs.get('node_align', 'justify')
            orient = kwargs.get('orient', 'horizontal')
            
            for row in data:
                s = str(row.get(source_col, ''))
                t = str(row.get(target_col, ''))
                v = float(row.get(value_col, 1)) if value_col else 1
                
                nodes.add(s)
                nodes.add(t)
                links.append({"source": s, "target": t, "value": v})
                
            sankey_nodes = [{"name": n} for n in nodes]
            
            c = Sankey(init_opts=init_opts)
            if colors: c.set_colors(colors)
            c.add(
                series_name=series_names.get(primary_y, primary_y),
                nodes=sankey_nodes,
                links=links,
                linestyle_opt=opts.LineStyleOpts(opacity=0.2, curve=0.5, color="source"),
                label_opts=get_series_label_opts(primary_y),
                node_align=node_align,
                orient=orient
            )
            c.set_global_opts(
                title_opts=common_title_opts,
                legend_opts=common_legend_opts,
                tooltip_opts=common_tooltip_opts,
                toolbox_opts=common_toolbox_opts
            )

        elif chart_type == 'map':
             if y_cols:
                primary_y = y_cols[0]
                y_data = y_datasets[primary_y]
                map_data = [list(z) for z in zip(x_data, y_data)]
                map_type = kwargs.get('map_type', 'china')
                
                c = Map(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add(
                    series_name=series_names.get(primary_y, primary_y),
                    data_pair=map_data,
                    maptype=map_type,
                    label_opts=get_series_label_opts(primary_y)
                )
                c.set_global_opts(
                    title_opts=common_title_opts,
                    legend_opts=common_legend_opts,
                    visualmap_opts=common_visualmap_opts,
                    tooltip_opts=common_tooltip_opts,
                    toolbox_opts=common_toolbox_opts
                )

        elif chart_type == 'table':
            table = Table()
            headers = [x_col] + y_cols if x_col else y_cols
            rows = []
            for row in data:
                r = []
                if x_col:
                    if isinstance(x_col, list):
                        r.append("-".join([str(row.get(c, '')) for c in x_col]))
                    else:
                        r.append(str(row.get(x_col, '')))
                for col in y_cols:
                    r.append(row.get(col, ''))
                rows.append(r)
            table.add(headers, rows)
            
            # Table Title Styling
            t_style = {"color": title_color, "font-size": f"{title_size}px"}
            s_style = {"color": subtitle_color, "font-size": f"{subtitle_size}px"}
            
            table.set_global_opts(
                title_opts=opts.ComponentTitleOpts(
                    title=title, 
                    subtitle=subtitle,
                    title_style=t_style,
                    subtitle_style=s_style
                )
            )
            return table

        elif chart_type == 'grid':
            grid = Grid(init_opts=init_opts)
            
            # Check for dual-axis/overlap conditions
            series_axis = kwargs.get('series_axis', {})
            has_right_axis = any(v == 'right' for v in series_axis.values())
            
            if grid_type == 'multi_yaxis' or overlap_type in ['bar_line', 'line_scatter'] or has_right_axis:
                if len(y_cols) < 1:
                    return None
                
                series_types = kwargs.get('series_types', {})
                
                # 1. Identify Left and Right Axis Columns
                left_cols = []
                right_cols = []
                
                if series_axis or has_right_axis:
                     for col in y_cols:
                        if series_axis.get(col) == 'right':
                            right_cols.append(col)
                        else:
                            left_cols.append(col)
                else:
                    # Legacy: First col left, others right
                    left_cols = [y_cols[0]]
                    right_cols = y_cols[1:]
                
                # 2. Initialize Container Charts
                bar_chart = Bar()
                bar_chart.add_xaxis(x_data)
                
                line_chart = Line()
                line_chart.add_xaxis(x_data)

                scatter_chart = Scatter()
                scatter_chart.add_xaxis(x_data)
                
                has_bar = False
                has_line = False
                has_scatter = False
                
                # 3. Add Series to respective charts
                # Helper to add series
                def add_series(cols, axis_index):
                    nonlocal has_bar, has_line, has_scatter
                    default_stype = kwargs.get('default_series_type', 'bar')
                    
                    # Prepare stack name
                    stack_name = 'stack1' if stack else None

                    for col in cols:
                        # Try to get type by column name, then by series name (display name), then default
                        s_name = series_names.get(col, col)
                        stype = series_types.get(col) or series_types.get(s_name, default_stype)
                        
                        # Check if user explicitly set line, or if overlap_type forced it (legacy)
                        if grid_type == 'multi_yaxis' and not series_types and axis_index == 1:
                             stype = 'line' # Legacy behavior for multi_yaxis without explicit types
                        
                        if stype == 'line':
                            line_chart.add_yaxis(
                                series_name=series_names.get(col, col),
                                y_axis=y_datasets[col],
                                yaxis_index=axis_index,
                                label_opts=get_series_label_opts(col),
                                z=10,
                                is_smooth=smooth,
                                is_step=is_step,
                                is_connect_nones=is_connect_nones,
                                symbol=symbol,
                                symbol_size=symbol_size,
                                markpoint_opts=series_markpoint,
                                markline_opts=series_markline,
                                itemstyle_opts=itemstyle_opts,
                                areastyle_opts=areastyle_opts,
                                linestyle_opts=common_linestyle_opts
                            )
                            has_line = True
                        elif stype == 'scatter':
                            scatter_chart.add_yaxis(
                                series_name=series_names.get(col, col),
                                y_axis=y_datasets[col],
                                yaxis_index=axis_index,
                                label_opts=get_series_label_opts(col),
                                symbol=symbol,
                                symbol_size=symbol_size,
                                markpoint_opts=series_markpoint,
                                markline_opts=series_markline,
                                itemstyle_opts=itemstyle_opts
                            )
                            has_scatter = True
                        else:
                            bar_chart.add_yaxis(
                                series_name=series_names.get(col, col),
                                y_axis=y_datasets[col],
                                yaxis_index=axis_index,
                                label_opts=get_series_label_opts(col),
                                z=0,
                                stack=stack_name,
                                gap=bar_gap,
                                category_gap=category_gap,
                                bar_width=bar_width,
                                bar_max_width=bar_max_width,
                                bar_min_width=bar_min_width,
                                markpoint_opts=series_markpoint,
                                markline_opts=series_markline,
                                itemstyle_opts=itemstyle_opts
                            )
                            has_bar = True

                add_series(left_cols, 0)
                add_series(right_cols, 1)
                
                # 4. Determine Base Chart and Overlap
                base = None
                if has_bar:
                    base = bar_chart
                    if has_line:
                        base.overlap(line_chart)
                    if has_scatter:
                        base.overlap(scatter_chart)
                elif has_line:
                    base = line_chart
                    if has_scatter:
                        base.overlap(scatter_chart)
                elif has_scatter:
                    base = scatter_chart
                else:
                    return None

                # Apply colors and color_by to base chart
                if colors:
                    base.set_colors(colors)
                
                if color_by == 'data':
                    base.set_series_opts(colorBy='data')
                
                # 5. Configure Axes
                # Primary Axis (Index 0)
                y_name = kwargs.get('y_axis_name') or (series_names.get(left_cols[0], left_cols[0]) if left_cols else "")
                y_min = kwargs.get('y_axis_min')
                y_max = kwargs.get('y_axis_max')
                if y_min == '': y_min = None
                if y_max == '': y_max = None
                
                y_label_size = kwargs.get('y_axis_label_size', 12)
                y_label_color = kwargs.get('y_axis_label_color', '#5793f3')
                y_fmt = kwargs.get('y_axis_formatter', '{value}')
                y_suffix = kwargs.get('y_axis_suffix', '')
                y_splitline = kwargs.get('y_splitline_show', True)

                if y_suffix and '{value}' in y_fmt:
                     y_fmt = y_fmt.replace('{value}', f'{{value}}{y_suffix}')
                elif y_suffix:
                     y_fmt = f"{{value}}{y_suffix}"

                yaxis_opts = opts.AxisOpts(
                    name=y_name,
                    type_="value",
                    min_=y_min,
                    max_=y_max,
                    position="left",
                    grid_index=0,
                    axisline_opts=opts.AxisLineOpts(
                        linestyle_opts=opts.LineStyleOpts(color=y_label_color)
                    ),
                    axislabel_opts=opts.LabelOpts(
                        formatter=y_fmt,
                        font_size=y_label_size,
                        color=y_label_color
                    ),
                    splitline_opts=opts.SplitLineOpts(is_show=y_splitline)
                )
                
                base.set_global_opts(
                    title_opts=common_title_opts,
                    legend_opts=common_legend_opts,
                    tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="cross", formatter=tooltip_formatter),
                    xaxis_opts=xaxis_opts,
                    yaxis_opts=yaxis_opts,
                    datazoom_opts=common_datazoom_opts,
                    toolbox_opts=common_toolbox_opts
                )
                
                # Secondary Axis (Index 1) - Added via extend_axis
                if right_cols:
                    y2_name = kwargs.get('y2_axis_name') or (series_names.get(right_cols[0], right_cols[0]) if right_cols else "")
                    y2_min = kwargs.get('y2_axis_min')
                    y2_max = kwargs.get('y2_axis_max')
                    
                    # Ensure None if empty or invalid
                    if y2_min == '': y2_min = None
                    if y2_max == '': y2_max = None
                    y2_label_size = kwargs.get('y2_axis_label_size', 12)
                    y2_label_color = kwargs.get('y2_axis_label_color', '#d14a61') 
                    y2_fmt = kwargs.get('y2_axis_formatter', '{value}')
                    y2_suffix = kwargs.get('y2_axis_suffix', '')
                    y2_splitline = kwargs.get('y2_splitline_show', False)

                    if y2_suffix and '{value}' in y2_fmt:
                         y2_fmt = y2_fmt.replace('{value}', f'{{value}}{y2_suffix}')
                    elif y2_suffix:
                         y2_fmt = f"{{value}}{y2_suffix}"

                    base.extend_axis(
                        yaxis=opts.AxisOpts(
                            name=y2_name,
                            type_="value",
                            min_=y2_min,
                            max_=y2_max,
                            position="right",
                            grid_index=0,
                            axisline_opts=opts.AxisLineOpts(
                                linestyle_opts=opts.LineStyleOpts(color=y2_label_color)
                            ),
                            axislabel_opts=opts.LabelOpts(
                                formatter=y2_fmt,
                                font_size=y2_label_size,
                                color=y2_label_color
                            ),
                            splitline_opts=opts.SplitLineOpts(is_show=y2_splitline)
                        )
                    )
                
                # Manually inject grid options to avoid Grid component resetting yAxisIndex for dual-axis charts
                # This ensures that series assigned to index 1 (right axis) keep their assignment
                # Use user-defined grid_right if available, otherwise default logic
                default_right = "20%" if right_cols else "5%"
                final_grid_right = grid_pos_right if grid_pos_right else default_right
                
                base.options['grid'] = opts.GridOpts(
                    pos_left=grid_pos_left, 
                    pos_right=final_grid_right,
                    pos_top=grid_pos_top,
                    pos_bottom=grid_pos_bottom
                )
                return base
                
            elif grid_type in ['vertical', 'horizontal']:
                mid = len(y_cols) // 2
                if mid == 0: mid = 1
                group1 = y_cols[:mid]
                group2 = y_cols[mid:]
                
                c1 = Bar()
                c1.add_xaxis(x_data)
                for col in group1:
                    c1.add_yaxis(
                        series_names.get(col, col), 
                        y_datasets[col], 
                        label_opts=get_series_label_opts(col),
                        bar_width=bar_width,
                        bar_max_width=bar_max_width,
                        bar_min_width=bar_min_width,
                        itemstyle_opts=itemstyle_opts
                    )
                c1.set_global_opts(title_opts=opts.TitleOpts(title="Group 1"), legend_opts=opts.LegendOpts(pos_top="5%"), tooltip_opts=common_tooltip_opts)
                if colors: c1.set_colors(colors)
                if color_by == 'data': c1.set_series_opts(colorBy='data')
                
                c2 = Line()
                c2.add_xaxis(x_data)
                for col in group2:
                    c2.add_yaxis(series_names.get(col, col), y_datasets[col], label_opts=get_series_label_opts(col))
                c2.set_global_opts(title_opts=opts.TitleOpts(title="Group 2", pos_top="50%"), legend_opts=opts.LegendOpts(pos_top="50%"), tooltip_opts=common_tooltip_opts)
                
                if grid_type == 'vertical':
                    grid.add(c1, grid_opts=opts.GridOpts(pos_bottom="60%"))
                    grid.add(c2, grid_opts=opts.GridOpts(pos_top="60%"))
                else:
                    # Horizontal split simulation
                    grid.add(c1, grid_opts=opts.GridOpts(pos_right="55%"))
                    grid.add(c2, grid_opts=opts.GridOpts(pos_left="55%"))
                
                # Ensure global colors are propagated to Grid if not set on sub-charts
                if colors:
                    grid.options['color'] = colors

                return grid
            
            else:
                # Basic
                c = Bar(init_opts=init_opts)
                if colors: c.set_colors(colors)
                c.add_xaxis(x_data)
                for col in y_cols:
                    c.add_yaxis(
                        series_names.get(col, col), 
                        y_datasets[col], 
                        label_opts=get_series_label_opts(col),
                        bar_width=bar_width,
                        bar_max_width=bar_max_width,
                        bar_min_width=bar_min_width,
                        itemstyle_opts=itemstyle_opts
                    )
                c.set_global_opts(
                    title_opts=common_title_opts,
                    legend_opts=common_legend_opts,
                    xaxis_opts=xaxis_opts,
                    yaxis_opts=yaxis_opts,
                    tooltip_opts=common_tooltip_opts
                )
                if color_by == 'data':
                    c.set_series_opts(colorBy='data')

                grid.add(c, grid_opts=opts.GridOpts(
                    pos_left=grid_pos_left, 
                    pos_right=grid_pos_right,
                    pos_top=grid_pos_top,
                    pos_bottom=grid_pos_bottom
                ))
                
                if colors:
                    grid.options['color'] = colors
                    
                return grid

        return c
