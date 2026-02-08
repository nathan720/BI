from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib.auth.models import User
from core.auth.models import SysMenu, SysRole
from core.data_source.models import DataSource
from core.reporting.models import ScheduledTask, Report, ReportDirectory
from apps.admin.logging.audit_logs.models import AuditLog
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from apps.dashboard.forms import DataSourceForm, DataSetForm, ReportForm, UserForm, SysRoleForm, SysMenuForm, ReportDirectoryForm
from core.dataset.models import DataSet
from core.dataset.executor import QueryExecutor
from core.data_source.connector import DBConnector
from core.reporting.charts import ChartFactory
import json
import time
import importlib
import os
import re
from django.conf import settings

def resolve_dataset_sql(sql_script, depth=0, params=None):
    """
    Recursively resolve {{ dataset:ID }} and {{ param:KEY }} placeholders in SQL.
    """
    if not sql_script:
        return sql_script
    if depth > 5: # Prevent infinite recursion
        return sql_script
        
    if params is None:
        params = {}
        
    # 1. Resolve Parameters {{ param:key }}
    def replace_param(match):
        key = match.group(1)
        val = params.get(key)
        
        if val is None:
            return ""
            
        # Handle list/tuple (Multi-select)
        if isinstance(val, (list, tuple)):
            # If items are strings, wrap in quotes
            formatted_items = []
            for item in val:
                if isinstance(item, str):
                    formatted_items.append(f"'{item}'")
                else:
                    formatted_items.append(str(item))
            return ",".join(formatted_items)
            
        return str(val)

    param_pattern = r'\{\{\s*param:(\w+)\s*\}\}'
    sql_script = re.sub(param_pattern, replace_param, sql_script)

    # 2. Resolve Datasets {{ dataset:ID }}
    pattern = r'\{\{\s*dataset:(\d+)\s*\}\}'
    
    def replace_match(match):
        dataset_id = match.group(1)
        try:
            dataset = DataSet.objects.get(pk=dataset_id)
            # Recursively resolve the child dataset's SQL first, passing params down
            child_sql = resolve_dataset_sql(dataset.sql_script, depth + 1, params)
            # Wrap in subquery
            return f"({child_sql})"
        except DataSet.DoesNotExist:
            return match.group(0) # Keep as is if not found
            
    return re.sub(pattern, replace_match, sql_script)

def get_menus():
    # Get all menus
    all_menus = SysMenu.objects.all().order_by('sort_order')
    
    # Build tree
    menu_tree = []
    parent_map = {}
    
    # First pass: identify parents and children
    for menu in all_menus:
        if menu.parent is None:
            item = {'menu': menu, 'children': []}
            menu_tree.append(item)
            parent_map[menu.id] = item
            
    # Second pass: assign children
    for menu in all_menus:
        if menu.parent_id and menu.parent_id in parent_map:
            parent_map[menu.parent_id]['children'].append(menu)
            
    return menu_tree

def get_report_file_path(report_code):
    return os.path.join(settings.BASE_DIR, 'reports', f'{report_code}.json')

def load_report_from_file(report):
    try:
        file_path = get_report_file_path(report.code)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading report file: {e}")
    return None

def scan_local_reports():
    """
    Deprecated: Local scanning caused duplicate reports because it treated every file as a new report
    if a report with that EXACT code didn't exist, ignoring that users might have created manual reports
    with different codes but same content.
    
    If we enable this, we must ensure it links to existing reports or updates them, not create new ones blindly.
    For now, disable to prevent "Unclassified" duplicates.
    """
    pass
    # reports_dir = os.path.join(settings.BASE_DIR, 'reports')
    # if not os.path.exists(reports_dir):
    #     return
    #     
    # for filename in os.listdir(reports_dir):
    #     if filename.endswith('.json'):
    #         code = filename[:-5]
    #         if not Report.objects.filter(code=code).exists():
    #             Report.objects.create(
    #                 name=code,
    #                 code=code,
    #                 description="Imported from local file",
    #                 platform='pc',
    #                 is_visible=True
    #             )

@login_required(login_url='/admin/login/')
def index_view(request):
    menus = get_menus()
    context = {
        'menus': menus,
        'title': '首页',
        'content_title': '仪表盘首页'
    }
    return render(request, 'dashboard/index.html', context)

# --- Data Source Views ---

@login_required(login_url='/admin/login/')
def datasource_list_view(request):
    menus = get_menus()
    datasources = DataSource.objects.all().order_by('-created_at')
    context = {
        'menus': menus,
        'datasources': datasources,
        'title': '数据源管理',
        'content_title': '数据源列表'
    }
    return render(request, 'dashboard/datasource/list.html', context)

@login_required(login_url='/admin/login/')
def datasource_create_view(request):
    menus = get_menus()
    if request.method == 'POST':
        form = DataSourceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '数据源创建成功')
            return redirect('datasource_list')
    else:
        form = DataSourceForm()
    
    context = {
        'menus': menus,
        'form': form,
        'title': '数据源管理',
        'content_title': '新增数据源'
    }
    return render(request, 'dashboard/datasource/form.html', context)

@login_required(login_url='/admin/login/')
def datasource_edit_view(request, pk):
    menus = get_menus()
    datasource = get_object_or_404(DataSource, pk=pk)
    if request.method == 'POST':
        form = DataSourceForm(request.POST, instance=datasource)
        if form.is_valid():
            form.save()
            messages.success(request, '数据源更新成功')
            return redirect('datasource_list')
    else:
        form = DataSourceForm(instance=datasource)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '数据源管理',
        'content_title': f'编辑数据源: {datasource.name}'
    }
    return render(request, 'dashboard/datasource/form.html', context)

@login_required(login_url='/admin/login/')
def datasource_test_view(request, pk):
    datasource = get_object_or_404(DataSource, pk=pk)
    try:
        conn = DBConnector(datasource)
        conn.connect()
        conn.close()
        messages.success(request, '连接测试成功')
    except Exception as e:
        messages.error(request, f'连接测试失败: {str(e)}')
    return redirect('datasource_list')

@login_required(login_url='/admin/login/')
def datasource_delete_view(request, pk):
    datasource = get_object_or_404(DataSource, pk=pk)
    datasource.delete()
    messages.success(request, '数据源已删除')
    return redirect('datasource_list')

# --- Dataset Views ---

@login_required(login_url='/admin/login/')
def dataset_list_view(request):
    menus = get_menus()
    # Only show datasets that are NOT report-specific (Data Center datasets)
    datasets = DataSet.objects.filter(is_report_specific=False).order_by('-created_at')
    context = {
        'menus': menus,
        'datasets': datasets,
        'title': '数据集管理',
        'content_title': '数据集列表'
    }
    return render(request, 'dashboard/dataset/list.html', context)

@login_required(login_url='/admin/login/')
def dataset_create_view(request):
    menus = get_menus()
    if request.method == 'POST':
        form = DataSetForm(request.POST)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.is_report_specific = False # Explicitly set as Data Center dataset
            dataset.save()
            messages.success(request, '数据集创建成功')
            return redirect('dataset_list')
    else:
        form = DataSetForm()
    
    context = {
        'menus': menus,
        'form': form,
        'title': '数据集管理',
        'content_title': '新增数据集'
    }
    return render(request, 'dashboard/dataset/form.html', context)

@login_required(login_url='/admin/login/')
def dataset_edit_view(request, pk):
    menus = get_menus()
    dataset = get_object_or_404(DataSet, pk=pk)
    if request.method == 'POST':
        form = DataSetForm(request.POST, instance=dataset)
        if form.is_valid():
            form.save()
            messages.success(request, '数据集更新成功')
            return redirect('dataset_list')
    else:
        form = DataSetForm(instance=dataset)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '数据集管理',
        'content_title': f'编辑数据集: {dataset.name}'
    }
    return render(request, 'dashboard/dataset/form.html', context)

@login_required(login_url='/admin/login/')
def dataset_preview_view(request, pk):
    menus = get_menus()
    dataset = get_object_or_404(DataSet, pk=pk)
    columns = []
    data = []
    error = None
    
    try:
        resolved_sql = resolve_dataset_sql(dataset.sql_script)
        columns, data = QueryExecutor.execute(dataset.datasource, resolved_sql, limit=100)
    except Exception as e:
        error = str(e)
        
    context = {
        'menus': menus,
        'dataset': dataset,
        'columns': columns,
        'data': data,
        'error': error,
        'title': '数据集管理',
        'content_title': f'预览数据集: {dataset.name}'
    }
    return render(request, 'dashboard/dataset/preview.html', context)

@login_required(login_url='/admin/login/')
def api_delete_dataset(request, pk):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
        
    try:
        dataset = get_object_or_404(DataSet, pk=pk)
        dataset.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# --- System Management Views ---

@login_required(login_url='/admin/login/')
def menu_list_view(request):
    menus = get_menus() # For sidebar
    all_menus = SysMenu.objects.all().order_by('sort_order')
    context = {
        'menus': menus,
        'all_menus': all_menus,
        'title': '目录管理',
        'content_title': '系统菜单管理'
    }
    return render(request, 'dashboard/system/menu_list.html', context)

@login_required(login_url='/admin/login/')
def menu_create_view(request):
    menus = get_menus()
    if request.method == 'POST':
        form = SysMenuForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '菜单创建成功')
            return redirect('menu_list')
    else:
        form = SysMenuForm()
    
    context = {
        'menus': menus,
        'form': form,
        'title': '目录管理',
        'content_title': '新增菜单'
    }
    return render(request, 'dashboard/system/menu_form.html', context)

@login_required(login_url='/admin/login/')
def menu_edit_view(request, pk):
    menus = get_menus()
    menu = get_object_or_404(SysMenu, pk=pk)
    if request.method == 'POST':
        form = SysMenuForm(request.POST, instance=menu)
        if form.is_valid():
            form.save()
            messages.success(request, '菜单更新成功')
            return redirect('menu_list')
    else:
        form = SysMenuForm(instance=menu)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '目录管理',
        'content_title': f'编辑菜单: {menu.name}'
    }
    return render(request, 'dashboard/system/menu_form.html', context)

@login_required(login_url='/admin/login/')
def menu_delete_view(request, pk):
    menu = get_object_or_404(SysMenu, pk=pk)
    menu.delete()
    messages.success(request, '菜单已删除')
    return redirect('menu_list')

@login_required(login_url='/admin/login/')
def user_list_view(request):
    menus = get_menus()
    users = User.objects.all().order_by('-date_joined')
    context = {
        'menus': menus,
        'users': users,
        'title': '用户管理',
        'content_title': '系统用户管理'
    }
    return render(request, 'dashboard/system/user_list.html', context)

@login_required(login_url='/admin/login/')
def user_create_view(request):
    menus = get_menus()
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '用户创建成功')
            return redirect('user_list')
    else:
        form = UserForm()
    
    context = {
        'menus': menus,
        'form': form,
        'title': '用户管理',
        'content_title': '新增用户'
    }
    return render(request, 'dashboard/system/user_form.html', context)

@login_required(login_url='/admin/login/')
def user_edit_view(request, pk):
    menus = get_menus()
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, '用户更新成功')
            return redirect('user_list')
    else:
        form = UserForm(instance=user)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '用户管理',
        'content_title': f'编辑用户: {user.username}'
    }
    return render(request, 'dashboard/system/user_form.html', context)

@login_required(login_url='/admin/login/')
def user_detail_view(request, pk):
    menus = get_menus()
    user = get_object_or_404(User, pk=pk)
    context = {
        'menus': menus,
        'user_obj': user,
        'title': '用户管理',
        'content_title': f'用户详情: {user.username}'
    }
    return render(request, 'dashboard/system/user_detail.html', context)

@login_required(login_url='/admin/login/')
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)
    user.delete()
    messages.success(request, '用户已删除')
    return redirect('user_list')

# --- Mobile Views ---

@login_required(login_url='/admin/login/')
def mobile_index_view(request):
    menus = get_menus()
    
    # Simple dashboard for mobile
    # Get total sales etc. (Mock data for now)
    
    context = {
        'menus': menus,
        'title': '移动平台',
        'content_title': '移动端入口'
    }
    return render(request, 'dashboard/mobile/index.html', context)

# --- Report Views ---

def build_directory_tree():
    """
    Helper to build directory tree
    """
    all_dirs = list(ReportDirectory.objects.all().order_by('sort_order', 'id'))
    dir_map = {d.id: d for d in all_dirs}
    root_nodes = []
    
    for d in all_dirs:
        d.children_dirs = []
        
    for d in all_dirs:
        if d.parent_id and d.parent_id in dir_map:
            dir_map[d.parent_id].children_dirs.append(d)
        else:
            root_nodes.append(d)
            
    return root_nodes

@login_required(login_url='/admin/login/')
def report_list_view(request):
    return redirect('report_analysis')

@login_required(login_url='/admin/login/')
def report_analysis_view(request):
    # Redirect to first published report
    first_report = Report.objects.filter(status='published', is_visible=True, platform='pc').order_by('sort_order', '-created_at').first()
    
    if first_report:
        return redirect('report_detail', report_id=first_report.id)
        
    return _report_list_base(request, mode='view', title='报表展示', url_name='report_analysis')

@login_required(login_url='/admin/login/')
def report_manage_view(request):
    # scan_local_reports() # Disable auto-import to prevent duplicates
    return _report_list_base(request, mode='design', title='报表设计', url_name='report_manage')

def _report_list_base(request, mode='view', title='报表展示', url_name='report_list'):
    menus = get_menus()
    
    dir_id = request.GET.get('dir')
    current_dir = None
    
    if dir_id:
        try:
            current_dir = ReportDirectory.objects.get(pk=dir_id)
            # Filter using M2M field
            reports = Report.objects.filter(directories=current_dir)
            content_title = current_dir.name
        except (ValueError, ReportDirectory.DoesNotExist):
            reports = Report.objects.all()
            content_title = '所有报表'
    else:
        # Show all reports
        # Use distinct() because if filtering by directories logic changes, duplicates might appear
        reports = Report.objects.all().distinct()
        content_title = '所有报表'
        
    if mode == 'view':
        reports = reports.filter(status='published', is_visible=True, platform='pc')
        
    reports = reports.order_by('sort_order', '-created_at')
        
    directory_tree = build_directory_tree()
    
    # Form for Create Report Modal (only needed in design mode)
    form = None
    all_directories = None
    if mode == 'design':
        initial_data = {}
        if dir_id:
            initial_data['directories'] = [dir_id]
        form = ReportForm(initial=initial_data)
        all_directories = ReportDirectory.objects.all().order_by('name')
    
    context = {
        'menus': menus,
        'reports': reports,
        'directory_tree': directory_tree,
        'current_dir_id': int(dir_id) if dir_id and dir_id.isdigit() else None,
        'title': title,
        'content_title': content_title,
        'mode': mode,
        'base_url': url_name,
        'form': form,
        'all_directories': all_directories
    }
    return render(request, 'dashboard/report/view.html', context)

@login_required(login_url='/admin/login/')
def report_create_view(request):
    menus = get_menus()
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save()
            messages.success(request, '报表创建成功')
            return redirect('report_design', report_id=report.id)
    else:
        initial_data = {}
        if request.GET.get('code'):
            initial_data['code'] = request.GET.get('code')
            # Also set name to code by default if provided
            initial_data['name'] = request.GET.get('code')
        
        if request.GET.get('directory_id'):
            initial_data['directories'] = [request.GET.get('directory_id')]
            
        form = ReportForm(initial=initial_data)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '报表展示',
        'content_title': '新建报表'
    }
    return render(request, 'dashboard/report/form.html', context)

@login_required(login_url='/admin/login/')
def report_edit_view(request, report_id):
    menus = get_menus()
    report = get_object_or_404(Report, pk=report_id)
    
    if request.method == 'POST':
        form = ReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, '报表更新成功')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('report_manage')
    else:
        form = ReportForm(instance=report)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '报表设计',
        'content_title': f'编辑报表: {report.name}'
    }
    return render(request, 'dashboard/report/form.html', context)

from apps.dashboard.utils.data_processing import aggregate_data

def _get_report_render_data(report, params=None):
    report_data = []
    charts_data = []
    error = None
    visual_error = None
    has_visual_charts = False
    config = None
    
    if params is None:
        params = {}
    
    # 1. Fetch Data (Legacy/Table Mode)
    for dataset in report.datasets.all():
        try:
            resolved_sql = resolve_dataset_sql(dataset.sql_script, params=params)
            columns, data = QueryExecutor.execute(dataset.datasource, resolved_sql)
            report_data.append({
                'dataset_name': dataset.name,
                'columns': columns,
                'data': data
            })
        except Exception as e:
            report_data.append({
                'dataset_name': dataset.name,
                'error': f'Execution failed: {e}'
            })
            error = str(e)

    # 2. Process Visual Configuration
    config = load_report_from_file(report)
    if not config and report.template_config and report.template_config != '{}':
        try:
            config = json.loads(report.template_config)
        except Exception:
            config = None

    if config:
        try:
            charts = config.get('charts', [])
            if charts:
                has_visual_charts = True
                
                for chart in charts:
                    dataset_id = chart.get('dataset_id')
                    
                    # Flatten chart config into entry
                    chart_entry = chart.copy()
                    chart_entry.update({
                        'title': chart.get('title', '未命名图表'),
                        'type': chart.get('type', 'bar'),
                        'config': chart, # Keep reference
                        'error': None,
                        'data': [],
                        'columns': []
                    })
                    
                    # Check for static data first (common in templates)
                    has_static_data = False
                    if chart.get('data') or chart.get('source'):
                        has_static_data = True
                    elif chart.get('pyecharts_options'):
                        has_static_data = True
                    elif chart.get('series'):
                        # Check if any series has data
                        for s in chart.get('series', []):
                            if isinstance(s, dict) and s.get('data'):
                                has_static_data = True
                                break
                    elif chart.get('dataset'):
                        ds = chart.get('dataset')
                        if isinstance(ds, dict) and ds.get('source'):
                            has_static_data = True
                        elif isinstance(ds, list):
                             for d in ds:
                                 if isinstance(d, dict) and d.get('source'):
                                     has_static_data = True
                                     break

                    if has_static_data:
                         # If static data exists, we don't strictly need a dataset
                         # But if dataset_id is explicitly invalid, we might still warn?
                         # For now, if static data is present, we prioritize it and skip dataset validation error
                         pass
                    elif not dataset_id:
                        chart_entry['error'] = '需绑定数据集'
                        charts_data.append(chart_entry)
                        continue
                    else:
                        # Process Dataset Logic
                        # Try to find dataset in report's bound datasets first
                        target_dataset = report.datasets.filter(pk=dataset_id).first()
                        
                        # If not found in bound datasets, try global lookup (for imported reports or loose coupling)
                        if not target_dataset:
                            target_dataset = DataSet.objects.filter(pk=dataset_id).first()
                            
                        if not target_dataset:
                            # If dataset is missing but chart has no static data, then it's an error
                            chart_entry['error'] = '数据集未找到'
                            charts_data.append(chart_entry)
                            continue
                            
                        try:
                            chart_filters = chart.get('filters', [])
                            resolved_sql = resolve_dataset_sql(target_dataset.sql_script, params=params)
                            columns, data = QueryExecutor.execute(target_dataset.datasource, resolved_sql, filters=chart_filters)
                            
                            # Convert to list of dicts for aggregation
                            data_dicts = [dict(zip(columns, row)) for row in data]
                            
                            processed_data = aggregate_data(
                                data_dicts,
                                chart.get('x_axis'),
                                chart.get('y_axis'),
                                chart.get('aggregation', chart.get('aggregate', 'none')),
                                chart.get('series_col')
                            )
                            
                            chart_entry['data'] = processed_data
                            chart_entry['columns'] = columns
                            
                        except Exception as e:
                            chart_entry['error'] = f'查询失败: {str(e)}'
                            charts_data.append(chart_entry)
                            continue

                    # Generate Pyecharts Options
                    try:
                        # If static options exist, prioritize them and skip generation
                        if chart.get('pyecharts_options'):
                            chart_entry['pyecharts_options'] = chart.get('pyecharts_options')
                        # If we have data (either static or processed), create chart
                        # Note: processed_data might be empty if query failed, but error is set
                        elif chart_entry.get('error'):
                            pass 
                        else:
                            # Use static data if processed_data is empty but static data exists
                            chart_data = chart_entry.get('data')
                            if not chart_data and (chart.get('data') or chart.get('source')):
                                chart_data = chart.get('data') or chart.get('source')
                                
                            # Prepare kwargs by excluding explicitly passed arguments to avoid "multiple values" error
                            chart_kwargs = chart.copy()
                            # Clean up all potential parameter aliases from kwargs
                            for k in ['type', 'title', 'data', 'x_axis', 'y_axis', 'series_col', 
                                     'category_col', 'value_col', 'x_col', 'y_col']:
                                chart_kwargs.pop(k, None)
                                
                            # Resolve axis columns with fallbacks
                            x_axis_val = chart.get('x_axis') or chart.get('category_col') or chart.get('x_col')
                            y_axis_val = chart.get('y_axis') or chart.get('value_col') or chart.get('y_col')
                                
                            chart_obj = ChartFactory.create_chart(
                                chart_type=chart.get('type', 'bar'),
                                title=chart.get('title', '未命名图表'),
                                data=chart_data,
                                category_col=x_axis_val,
                                value_col=y_axis_val,
                                series_col=chart.get('series_col'),
                                **chart_kwargs
                            )
                            if chart_obj:
                                if chart_obj.__class__.__name__ == 'Table':
                                    chart_entry['table_html'] = chart_obj.render_embed()
                                else:
                                    chart_entry['pyecharts_options'] = ChartFactory.dump_options(chart_obj)
                    except Exception as e:
                        print(f"Pyecharts generation failed: {e}")
                        if not chart_entry.get('error'):
                             chart_entry['error'] = f"图表生成失败: {str(e)}"
                        
                    charts_data.append(chart_entry)
            
        except Exception as e:
            visual_error = str(e)
            
    return {
        'report_data': report_data,
        'charts_data': charts_data,
        'error': error,
        'visual_error': visual_error,
        'config': config,
        'has_visual_charts': has_visual_charts
    }

@login_required(login_url='/admin/login/')
def report_detail_view(request, report_id):
    menus = get_menus()
    report = get_object_or_404(Report, pk=report_id)
    
    # Extract query params
    params = request.GET.dict()
    
    # Process Report Parameters for UI
    report_params = []
    try:
        # Prioritize template_config, then file_config (legacy)
        config_source = None
        if report.template_config and len(report.template_config) > 5:
            config_source = json.loads(report.template_config)
        else:
            config_source = load_report_from_file(report)
            
        if config_source and 'params' in config_source:
            raw_params = config_source['params']
            for p in raw_params:
                # Inject current value
                p['current_value'] = params.get(p['key'], p.get('default', ''))
                
                # Fetch dynamic options if configured
                if p.get('type') == 'select' and p.get('source_type') == 'dataset' and p.get('dataset_id'):
                    try:
                        ds = DataSet.objects.get(pk=p['dataset_id'])
                        # Execute SQL with current params (allows cascading)
                        resolved_sql = resolve_dataset_sql(ds.sql_script, params=params)
                        cols, data = QueryExecutor.execute(ds.datasource, resolved_sql)
                        
                        label_field = p.get('label_field')
                        value_field = p.get('value_field') or label_field
                        
                        # Find indices
                        label_idx = cols.index(label_field) if label_field and label_field in cols else 0
                        value_idx = cols.index(value_field) if value_field and value_field in cols else label_idx
                        
                        # Build options string
                        opts = []
                        seen = set()
                        for row in data:
                            val = str(row[value_idx])
                            lbl = str(row[label_idx])
                            if val not in seen:
                                seen.add(val)
                                # Simple sanitization
                                safe_val = val.replace(',', '').replace(':', '')
                                safe_lbl = lbl.replace(',', '').replace(':', '')
                                opts.append(f"{safe_val}:{safe_lbl}")
                        
                        p['options'] = ",".join(opts)
                    except Exception as e:
                        print(f"Error fetching options for {p.get('key')}: {e}")
                        
                report_params.append(p)
                
            # If params not in request, apply defaults to 'params' dict passed to SQL resolution
            for p in report_params:
                if p['key'] not in params and p.get('default'):
                     params[p['key']] = p['default']
                     
    except Exception as e:
        print(f"Error parsing report params: {e}")

    # Render Data
    render_context = _get_report_render_data(report, params=params)
    
    # Build Tree for Sidebar (Viewer Mode)
    all_dirs = list(ReportDirectory.objects.all().order_by('sort_order', 'id'))
    dir_map = {d.id: d for d in all_dirs}
    root_nodes = []
    
    # Fetch Reports
    all_reports = Report.objects.filter(status='published', is_visible=True, platform='pc').order_by('sort_order', '-created_at')
    report_map = {}
    for r in all_reports:
        d_id = r.directory_id if r.directory_id else 0
        if d_id not in report_map:
            report_map[d_id] = []
        report_map[d_id].append(r)
        
    # Populate Dirs
    for d in all_dirs:
        d.children_dirs = []
        d.reports_list = report_map.get(d.id, [])
        # Determine if active (expanded)
        d.is_expanded = False
        # If current report is in this directory or sub-directory... logic is complex, simplify:
        # Just expand if it's the direct parent
        if report.directory_id == d.id:
            d.is_expanded = True
            
    # Build Tree Structure
    for d in all_dirs:
        if d.parent_id and d.parent_id in dir_map:
            dir_map[d.parent_id].children_dirs.append(d)
            # Propagate expansion up
            if d.is_expanded:
                dir_map[d.parent_id].is_expanded = True
        else:
            root_nodes.append(d)
            
    # Filter for 'test' directory if requested
    filtered_roots = [n for n in root_nodes if n.name == 'test']
    if filtered_roots:
        root_nodes = filtered_roots
            
    root_reports = report_map.get(0, [])
    
    context = {
        'menus': menus,
        'report': report,
        'report_data': render_context['report_data'],
        'charts_data': render_context['charts_data'],
        'error': render_context['error'],
        'title': '报表展示',
        'content_title': report.name,
        'config': render_context['config'],
        'visual_error': render_context['visual_error'],
        'has_visual_charts': render_context['has_visual_charts'],
        
        # Sidebar Context
        'directory_tree': root_nodes,
        # 'root_reports': root_reports, # User requested to hide root reports in viewer sidebar
        'current_report_id': report.id,
        'report_params': report_params
    }
    return render(request, 'dashboard/report/detail.html', context)

@login_required(login_url='/admin/login/')
def report_delete_view(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    report.delete()
    messages.success(request, '报表已删除')
    return redirect('report_manage')

@login_required(login_url='/admin/login/')
def report_design_view(request, report_id):
    menus = get_menus()
    report = get_object_or_404(Report, pk=report_id)
    
    # Load from file if exists, BUT prioritize DB template_config if it has content (user edits)
    # Only use file_config if DB config is empty/default
    file_config = load_report_from_file(report)
    
    # Check if DB has valid config (more than just empty JSON)
    db_has_content = False
    if report.template_config and len(report.template_config) > 5:
        try:
             db_json = json.loads(report.template_config)
             if db_json and isinstance(db_json, dict) and db_json.get('charts'):
                 db_has_content = True
        except:
             pass

    if file_config and not db_has_content:
        report.template_config = json.dumps(file_config)
    
    # Logic to include referenced datasets
    datasets = list(report.datasets.all())
    
    # Determine config to scan for dataset references
    config_source = file_config
    if not config_source and report.template_config and report.template_config != '{}':
        try:
            config_source = json.loads(report.template_config)
        except Exception:
            pass

    if config_source:
        charts = config_source.get('charts', [])
        extra_ids = set()
        for chart in charts:
            did = chart.get('dataset_id')
            if did:
                try:
                    extra_ids.add(int(did))
                except ValueError:
                    pass
        
        existing_ids = set(d.id for d in datasets)
        missing_ids = extra_ids - existing_ids
        if missing_ids:
            extra_datasets = DataSet.objects.filter(id__in=missing_ids)
            datasets.extend(list(extra_datasets))
    
    # Combine global datasets and linked/referenced datasets for display
    all_datasets_map = {d.id: d for d in DataSet.objects.filter(is_report_specific=False)}
    for d in datasets:
        all_datasets_map[d.id] = d
    
    all_datasets_list = sorted(all_datasets_map.values(), key=lambda x: x.name)

    context = {
        'menus': menus,
        'report': report,
        'datasets': datasets,
        'all_datasets': all_datasets_list, # Unified list: Global + Linked Report Specific
        'data_sources': DataSource.objects.all(),
        'directories': ReportDirectory.objects.all().order_by('parent', 'sort_order'),
        'title': '报表展示',
        'content_title': f'设计报表: {report.name}'
    }
    return render(request, 'dashboard/report/design.html', context)

@login_required(login_url='/admin/login/')
def api_save_report_config(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
        
    try:
        report = get_object_or_404(Report, pk=report_id)
        data = json.loads(request.body)
        
        # Save config
        report.template_config = json.dumps(data)
        report.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_save_report_meta(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
        
    try:
        report = get_object_or_404(Report, pk=report_id)
        data = json.loads(request.body)
        
        # Update meta fields
        if 'name' in data:
            report.name = data['name']
        if 'description' in data:
            report.description = data['description']
        if 'is_visible' in data:
            report.is_visible = data['is_visible']
        if 'platform' in data:
            report.platform = data['platform']
        if 'external_url' in data:
            report.external_url = data['external_url']
        if 'template_path' in data:
            # template_path is essentially the code (filename without ext)
            # or relative path. For simplicity, we assume code = template_filename_no_ext
            # Security check similar to create_from_template
            tp = data['template_path']
            # tp is e.g. "foo/bar.json"
            base_dir = os.path.join(settings.BASE_DIR, 'reports')
            full_path = os.path.normpath(os.path.join(base_dir, tp))
            if not full_path.startswith(os.path.normpath(base_dir)):
                 return JsonResponse({'success': False, 'message': 'Invalid template path'})
                 
            # Extract code from filename
            filename = os.path.basename(tp)
            base_code = os.path.splitext(filename)[0]
            code = base_code
            
            # Ensure uniqueness to prevent constraint violation
            # If code exists (and not self), append timestamp
            if Report.objects.filter(code=code).exclude(pk=report.id).exists():
                 code = f"{base_code}_{int(time.time())}"
            
            report.code = code
            
            # Optionally reload config? For now, we just update reference.
            # If user wants to reset config, they might need another action.
            # But usually changing template implies using that template's structure.
            # However, api_create_report_from_template sets template_config from file.
            # Should we do the same here?
            # Yes, if template changes, we likely want to load that template.
            if os.path.exists(full_path):
                 with open(full_path, 'r', encoding='utf-8') as f:
                     config = json.load(f)
                     report.template_config = json.dumps(config)

        if 'directory_id' in data:
            dir_id = data['directory_id']
            if dir_id:
                report.directory = ReportDirectory.objects.get(pk=dir_id)
            else:
                report.directory = None
                
        if 'directories' in data:
            dir_ids = data['directories']
            if isinstance(dir_ids, list):
                report.directories.set(dir_ids)
                
        report.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_get_dataset_columns(request, dataset_id):
    try:
        dataset = get_object_or_404(DataSet, pk=dataset_id)
        resolved_sql = resolve_dataset_sql(dataset.sql_script)
        columns, _ = QueryExecutor.execute(dataset.datasource, resolved_sql, limit=1)
        return JsonResponse({'success': True, 'columns': columns})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_create_dataset(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
        
    try:
        data = json.loads(request.body)
        name = data.get('name')
        datasource_id = data.get('datasource_id')
        sql_script = data.get('sql_script')
        dataset_id = data.get('id')
        
        datasource = get_object_or_404(DataSource, pk=datasource_id)
        
        if dataset_id:
            # Update existing
            dataset = get_object_or_404(DataSet, pk=dataset_id)
            dataset.name = name
            dataset.datasource = datasource
            dataset.sql_script = sql_script
            dataset.save()
        else:
            # Create new
            dataset = DataSet.objects.create(
                    name=name,
                    datasource=datasource,
                    sql_script=sql_script,
                    is_report_specific=True
                )
            
            # If report_id is provided, associate it
            report_id = data.get('report_id')
            if report_id:
                report = Report.objects.get(pk=report_id)
                report.datasets.add(dataset)
            
        return JsonResponse({
            'success': True, 
            'dataset': {
                'id': dataset.id,
                'name': dataset.name,
                'datasource_name': datasource.name
            }
        })
    except IntegrityError as e:
        if 'unique constraint' in str(e).lower() or 'duplicate key' in str(e).lower():
             return JsonResponse({'success': False, 'message': f'数据集名称 "{name}" 已存在，请使用其他名称'})
        return JsonResponse({'success': False, 'message': '数据库完整性错误: ' + str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

# --- Report Directory Views ---

def get_report_templates(base_path):
    """
    Recursively scan the reports directory and return a tree structure.
    """
    templates = []
    if not os.path.exists(base_path):
        return templates

    try:
        # List all items in the directory
        with os.scandir(base_path) as entries:
            # Sort entries: directories first, then files
            sorted_entries = sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower()))
            
            for entry in sorted_entries:
                item = {
                    'name': entry.name,
                    'path': entry.path,
                    'rel_path': os.path.relpath(entry.path, settings.BASE_DIR),
                    'type': 'dir' if entry.is_dir() else 'file'
                }
                
                if entry.is_dir():
                    # Recursive call for directories
                    children = get_report_templates(entry.path)
                    item['children'] = children
                    # Only add directory if it's not empty or we want to show empty dirs
                    # Let's show all dirs to match file explorer behavior
                    templates.append(item)
                elif entry.is_file() and (entry.name.endswith('.json') or entry.name.endswith('.js')):
                    # Only include supported template files
                    templates.append(item)
                    
    except PermissionError:
        pass # Skip folders we can't access
        
    return templates

@login_required(login_url='/admin/login/')
def report_directory_list_view(request):
    menus = get_menus()
    
    # 0. Get Report Templates from disk
    reports_dir = os.path.join(settings.BASE_DIR, 'reports')
    report_templates = get_report_templates(reports_dir)
    
    # 1. Get all directories
    all_dirs = list(ReportDirectory.objects.all().order_by('sort_order', 'id'))
    dir_map = {d.id: d for d in all_dirs}
    
    # 2. Get all reports
    all_reports = Report.objects.all().order_by('sort_order', 'created_at')
    
    # 3. Initialize children and reports lists
    for d in all_dirs:
        d.children_dirs = []
        d.reports_list = []
        
    # 4. Build directory hierarchy and assign reports
    root_nodes = []
    
    # Build Dir Tree
    for d in all_dirs:
        if d.parent_id and d.parent_id in dir_map:
            dir_map[d.parent_id].children_dirs.append(d)
        else:
            root_nodes.append(d)
            
    # Assign Reports
    orphan_reports = []
    for r in all_reports:
        if r.directory_id and r.directory_id in dir_map:
            dir_map[r.directory_id].reports_list.append(r)
        else:
            # Filter out published reports from Unclassified list
            if r.status != 'published':
                orphan_reports.append(r)
    
    # Flatten tree for dropdown - Fix indentation
    flat_dirs = []
    def flatten(nodes, level=0):
        for node in nodes:
            flat_dirs.append({
                'id': node.id,
                'name': node.name,
                'display_name': ('　' * level + '└─ ' + node.name) if level > 0 else node.name,
                'level': level
            })
            if node.children_dirs:
                flatten(node.children_dirs, level + 1)
    
    flatten(root_nodes)
    
    context = {
        'menus': menus,
        'directory_tree': root_nodes,
        'flat_dirs': flat_dirs,
        'orphan_reports': orphan_reports,
        'report_templates': report_templates,
        'title': '报表目录',
        'content_title': '报表目录管理'
    }
    return render(request, 'dashboard/report/directory_manage.html', context)

@login_required(login_url='/admin/login/')
def report_directory_create_view(request):
    menus = get_menus()
    next_url = request.GET.get('next', 'report_directory_list')
    
    if request.method == 'POST':
        form = ReportDirectoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, '目录创建成功')
            return redirect(next_url)
    else:
        form = ReportDirectoryForm()
    
    context = {
        'menus': menus,
        'form': form,
        'title': '报表目录',
        'content_title': '新建报表目录'
    }
    return render(request, 'dashboard/report/directory_form.html', context)

@login_required(login_url='/admin/login/')
def report_directory_edit_view(request, pk):
    menus = get_menus()
    next_url = request.GET.get('next', 'report_directory_list')
    directory = get_object_or_404(ReportDirectory, pk=pk)
    
    if request.method == 'POST':
        form = ReportDirectoryForm(request.POST, instance=directory)
        if form.is_valid():
            form.save()
            messages.success(request, '目录更新成功')
            return redirect(next_url)
    else:
        form = ReportDirectoryForm(instance=directory)
    
    context = {
        'menus': menus,
        'form': form,
        'title': '报表目录',
        'content_title': f'编辑目录: {directory.name}'
    }
    return render(request, 'dashboard/report/directory_form.html', context)

@login_required(login_url='/admin/login/')
def report_directory_delete_view(request, pk):
    directory = get_object_or_404(ReportDirectory, pk=pk)
    directory.delete()
    messages.success(request, '目录已删除')
    return redirect('report_directory_list')

@login_required(login_url='/admin/login/')
def api_move_directory(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        directory_id = data.get('directory_id')
        target_parent_id = data.get('target_parent_id')
        
        directory = get_object_or_404(ReportDirectory, pk=directory_id)
        
        if target_parent_id:
            target_parent = get_object_or_404(ReportDirectory, pk=target_parent_id)
            # Prevent circular reference
            parent = target_parent
            while parent:
                if parent.id == directory.id:
                    return JsonResponse({'success': False, 'message': 'Cannot move directory into itself or its children'})
                parent = parent.parent
            directory.parent = target_parent
        else:
            directory.parent = None
            
        directory.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_reorder_report(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        report_id = data.get('report_id')
        direction = data.get('direction') # 'up' or 'down'
        
        report = get_object_or_404(Report, pk=report_id)
        
        # Determine query set based on whether it has a directory or not
        if report.directory:
            siblings = Report.objects.filter(directory=report.directory)
        else:
            siblings = Report.objects.filter(directory__isnull=True)
            
        siblings = siblings.order_by('sort_order', 'id')
        
        current_index = -1
        sibling_list = list(siblings)
        for i, r in enumerate(sibling_list):
            if r.id == report.id:
                current_index = i
                break
                
        if current_index == -1:
             return JsonResponse({'success': False, 'message': 'Report not found in list'})
             
        swap_with = None
        if direction == 'up' and current_index > 0:
            swap_with = sibling_list[current_index - 1]
        elif direction == 'down' and current_index < len(sibling_list) - 1:
            swap_with = sibling_list[current_index + 1]
            
        if swap_with:
            # Swap sort_order
            if report.sort_order == swap_with.sort_order:
                # If equal, nudge to break tie
                if direction == 'up':
                    report.sort_order -= 1
                else:
                    report.sort_order += 1
            else:
                report.sort_order, swap_with.sort_order = swap_with.sort_order, report.sort_order
                
            report.save()
            swap_with.save()
            
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_create_external_link(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        name = data.get('name')
        url = data.get('url')
        directory_id = data.get('directory_id')
        
        if not name or not url:
            return JsonResponse({'success': False, 'message': 'Name and URL are required'})
        
        directory = None
        if directory_id:
            try:
                directory = ReportDirectory.objects.get(pk=directory_id)
            except ReportDirectory.DoesNotExist:
                return JsonResponse({'success': False, 'message': 'Directory not found'})
        
        # Create Report
        # Store URL in description
        report = Report.objects.create(
            name=name,
            code=f"external_{int(time.time())}", 
            directory=directory,
            description=url, 
            platform='pc',
            is_visible=True,
            status='published' # Assume published
        )
            
        return JsonResponse({
            'success': True, 
            'report_id': report.id
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_create_report_from_template(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        directory_id = data.get('directory_id')
        template_path = data.get('template_path')
        name = data.get('name')
        
        if not directory_id or not template_path or not name:
            return JsonResponse({'success': False, 'message': 'Missing parameters'})
            
        try:
            directory = ReportDirectory.objects.get(pk=directory_id)
        except ReportDirectory.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Directory not found'})
            
        # Security check: ensure path is within reports directory
        # template_path is relative to reports/ e.g. "bar.json" or "subdir/foo.json"
        base_dir = os.path.join(settings.BASE_DIR, 'reports')
        # Join and normalize
        full_path = os.path.normpath(os.path.join(base_dir, template_path))
        
        # Check if it starts with base_dir to prevent directory traversal
        if not full_path.startswith(os.path.normpath(base_dir)):
             return JsonResponse({'success': False, 'message': 'Invalid template path'})
             
        if not os.path.exists(full_path):
            return JsonResponse({'success': False, 'message': 'Template file not found'})
            
        with open(full_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
            
        # Generate code
        code = f"report_{int(time.time())}_{os.path.basename(template_path).split('.')[0]}"
        
        report = Report.objects.create(
            name=name,
            code=code,
            directory=directory,
            template_config=template_content,
            platform='pc',
            is_visible=True,
            status='published'
        )
        
        return JsonResponse({'success': True, 'report_id': report.id})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def generic_view(request, *args, **kwargs):
    menus = get_menus()
    context = {
        'menus': menus,
        'title': '通用页面',
        'content_title': '功能开发中'
    }
    return render(request, 'dashboard/generic.html', context)

@login_required(login_url='/admin/login/')
def api_preview_sql(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
        
    try:
        data = json.loads(request.body)
        datasource_id = data.get('datasource_id')
        content = data.get('content')
        
        if not datasource_id or not content:
             return JsonResponse({'success': False, 'message': 'Missing parameters'})
             
        datasource = get_object_or_404(DataSource, pk=datasource_id)
        
        resolved_sql = resolve_dataset_sql(content)
        columns, data = QueryExecutor.execute(datasource, resolved_sql, limit=100)
        
        # Convert to list of dicts for frontend table rendering
        data_dicts = [dict(zip(columns, row)) for row in data]
        
        return JsonResponse({
            'success': True,
            'columns': columns,
            'data': data_dicts
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_get_dataset_detail(request, dataset_id):
    try:
        dataset = get_object_or_404(DataSet, pk=dataset_id)
        return JsonResponse({
            'success': True,
            'dataset': {
                'id': dataset.id,
                'name': dataset.name,
                'datasource_id': dataset.datasource.id if dataset.datasource else None,
                'sql_script': dataset.sql_script
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_preview_dataset_data(request, dataset_id):
    try:
        dataset = get_object_or_404(DataSet, pk=dataset_id)
        resolved_sql = resolve_dataset_sql(dataset.sql_script)
        columns, data = QueryExecutor.execute(dataset.datasource, resolved_sql, limit=100)
        
        # Convert to list of dicts for frontend table rendering
        data_dicts = [dict(zip(columns, row)) for row in data]
        
        return JsonResponse({
            'success': True,
            'columns': columns,
            'data': data_dicts
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_publish_report(request, report_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})
        
    try:
        report = get_object_or_404(Report, pk=report_id)
        data = json.loads(request.body)
        action = data.get('action')
        
        if action == 'publish':
            report.status = 'published'
        elif action == 'unpublish':
            report.status = 'draft'
        
        report.save()
        return JsonResponse({'success': True, 'status': report.status})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

@login_required(login_url='/admin/login/')
def api_preview_chart(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid method'})

    try:
        import time
        start_time = time.time()
        
        data = json.loads(request.body)
        # data IS the chart config object from frontend
        params = data.get('params', {})
        
        dataset_id = data.get('dataset_id')
        if not dataset_id:
             return JsonResponse({'success': False, 'message': 'Missing dataset_id'})
              
        dataset = get_object_or_404(DataSet, pk=dataset_id)
        
        resolved_sql = resolve_dataset_sql(dataset.sql_script, params=params)
        filters = data.get('filters', [])
        
        sql_execution_time = time.time()
        columns, db_data = QueryExecutor.execute(dataset.datasource, resolved_sql, limit=1000, filters=filters)
        sql_execution_end = time.time()
        
        df_data = [dict(zip(columns, row)) for row in db_data]
        
        # Use data as chart_config
        chart_config = data
        
        x_axis = chart_config.get('x_axis') or chart_config.get('category_col') or chart_config.get('x_col')
        y_axis = chart_config.get('y_axis') or chart_config.get('value_col') or chart_config.get('y_col')
        series_col = chart_config.get('series_col')
        aggregation = chart_config.get('aggregation') or chart_config.get('aggregate') or 'none'
        
        aggregation_start = time.time()
        processed_data = aggregate_data(df_data, x_axis, y_axis, aggregation, series_col)
        aggregation_end = time.time()
        
        total_time = time.time() - start_time
        print(f"API Preview Chart Execution Time:")
        print(f"Total: {total_time:.2f}s")
        print(f"SQL Execution: {sql_execution_end - sql_execution_time:.2f}s")
        print(f"Data Aggregation: {aggregation_end - aggregation_start:.2f}s")
        print(f"Data Rows: {len(db_data)}")
        
        clean_config = chart_config.copy()
        for k in ['type', 'title', 'data', 'x_axis', 'y_axis', 'series_col', 'dataset_id', 'id', 'category_col', 'value_col', 'x_col', 'y_col']:
            clean_config.pop(k, None)
            
        chart_obj = ChartFactory.create_chart(
            chart_type=chart_config.get('type', 'bar'),
            title=chart_config.get('title', '预览图表'),
            data=processed_data,
            category_col=x_axis,
            value_col=y_axis,
            series_col=series_col,
            **clean_config
        )
        
        response_data = {
            'success': True,
            'options': ChartFactory.dump_options(chart_obj)
        }
        
        # If table chart, provide raw data for frontend rendering
        if chart_config.get('type') == 'table':
             # processed_data should be list of dicts from aggregate_data
             if processed_data and isinstance(processed_data, list):
                  cols = []
                  if len(processed_data) > 0 and isinstance(processed_data[0], dict):
                      cols = list(processed_data[0].keys())
                  
                  response_data['data'] = {
                      'columns': cols,
                      'rows': processed_data
                  }
        
        return JsonResponse(response_data)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})

def not_implemented_api_view(request, *args, **kwargs):
    return JsonResponse({'success': False, 'message': 'API not implemented yet'})

from apps.dashboard.utils.chart_config_loader import load_chart_configs

@login_required(login_url='/admin/login/')
def api_get_chart_configs(request):
    try:
        # Load configs dynamically from charts_parameter.json using the loader
        configs = load_chart_configs()
        return JsonResponse({'success': True, 'configs': configs})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})
