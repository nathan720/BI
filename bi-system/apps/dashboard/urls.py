from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.index_view, name='dashboard_index'),
    
    # Specific system pages (override generic view)
    path('system/menu', views.menu_list_view, name='menu_list'),
    path('system/menu/create', views.menu_create_view, name='menu_create'),
    path('system/menu/edit/<int:pk>', views.menu_edit_view, name='menu_edit'),
    path('system/menu/delete/<int:pk>', views.menu_delete_view, name='menu_delete'),

    path('system/user', views.user_list_view, name='user_list'),
    path('system/user/create', views.user_create_view, name='user_create'),
    path('system/user/edit/<int:pk>', views.user_edit_view, name='user_edit'),
    path('system/user/detail/<int:pk>', views.user_detail_view, name='user_detail'),
    path('system/user/delete/<int:pk>', views.user_delete_view, name='user_delete'),

    path('system/permission', views.generic_view, name='permission_list'),
    path('system/permission/create', views.generic_view, name='role_create'),
    path('system/permission/edit/<int:pk>', views.generic_view, name='role_edit'),
    path('system/permission/delete/<int:pk>', views.generic_view, name='role_delete'),

    path('system/scheduler', views.generic_view, name='scheduler_list'),
    path('system/log', views.generic_view, name='log_list'),
    
    path('datasource', views.datasource_list_view, name='datasource_list'),
    path('datasource/create', views.datasource_create_view, name='datasource_create'),
    path('datasource/edit/<int:pk>', views.datasource_edit_view, name='datasource_edit'),
    path('datasource/delete/<int:pk>', views.datasource_delete_view, name='datasource_delete'),

    path('dataset', views.dataset_list_view, name='dataset_list'),
    path('dataset/create', views.dataset_create_view, name='dataset_create'),
    path('dataset/edit/<int:pk>', views.dataset_edit_view, name='dataset_edit'),
    path('dataset/preview', views.dataset_preview_view, name='dataset_preview'),

    path('mobile', views.mobile_index_view, name='mobile_index'),
    
    # Report views
    path('report', views.report_list_view, name='report_list'), # Default/Redirect
    path('report/analysis', views.report_analysis_view, name='report_analysis'),
    path('report/manage', views.report_manage_view, name='report_manage'),
    
    path('report/create', views.report_create_view, name='report_create'),
    path('report/edit/<int:report_id>', views.report_edit_view, name='report_edit'),
    path('report/design/<int:report_id>', views.report_design_view, name='report_design'),
    path('report/delete/<int:report_id>', views.report_delete_view, name='report_delete'),
    path('report/view/<int:report_id>', views.report_detail_view, name='report_detail'),
    
    # Report Directory views
    path('report/directory', views.report_directory_list_view, name='report_directory_list'),
    path('report/directory/create', views.report_directory_create_view, name='report_directory_create'),
    path('report/directory/edit/<int:pk>', views.report_directory_edit_view, name='report_directory_edit'),
    path('report/directory/delete/<int:pk>', views.report_directory_delete_view, name='report_directory_delete'),

    # API for Report Designer
    path('api/dataset/<int:dataset_id>/columns', views.api_get_dataset_columns, name='api_get_dataset_columns'),
    path('api/dataset/<int:dataset_id>/preview', views.api_preview_dataset_data, name='api_preview_dataset_data'),
    path('api/dataset/<int:dataset_id>/delete', views.api_delete_dataset, name='api_delete_dataset'),
    path('api/dataset/<int:dataset_id>/detail', views.api_get_dataset_detail, name='api_get_dataset_detail'),
    path('api/dataset/preview_sql', views.api_preview_sql, name='api_preview_sql'),
    path('api/report/<int:report_id>/save_config', views.api_save_report_config, name='api_save_report_config'),
    path('api/report/<int:report_id>/save_meta', views.api_save_report_meta, name='api_save_report_meta'),
    path('api/report/<int:report_id>/publish', views.api_publish_report, name='api_publish_report'),
    path('api/report/preview_chart', views.api_preview_chart, name='api_preview_chart'),
    path('api/dataset/create', views.api_create_dataset, name='api_create_dataset'),
    path('api/chart/configs', views.api_get_chart_configs, name='api_get_chart_configs'),
    path('api/report/directory/move', views.api_move_directory, name='api_move_directory'),
    path('api/report/external/create', views.api_create_external_link, name='api_create_external_link'),
    path('api/report/reorder', views.api_reorder_report, name='api_reorder_report'),
    path('api/report/create/template', views.api_create_report_from_template, name='api_create_report_from_template'),

    # API
    path('datasource/test/<int:datasource_id>', views.datasource_test_view, name='test_connection'),
    path('datasource/test_params', views.not_implemented_api_view, name='test_connection_params'),

    # Catch-all for other paths to render generic view
    # Using re_path to capture everything else
    re_path(r'^(?P<page_path>.*)/?$', views.generic_view, name='dashboard_page'),
]
