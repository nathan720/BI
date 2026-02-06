import os
import sys
import django

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')
django.setup()

from django.contrib.auth.models import User
from core.auth.models import SysRole, SysMenu, SysDataPermission
from apps.admin.organization.models import Department, Post
from apps.admin.user_management.models import UserProfile

def init_menus():
    print("Initializing Menus...")
    
    menus = [
        # Data Center
        {'name': '数据中心', 'code': 'data_center', 'path': '#', 'icon': 'database', 'sort': 10, 'children': [
            {'name': '数据连接', 'code': 'data_conn', 'path': '/datasource', 'icon': 'link', 'sort': 10},
            {'name': '数据集管理', 'code': 'dataset_mgt', 'path': '/dataset', 'icon': 'table', 'sort': 20},
        ]},
        
        # Report Center
        {'name': '报表中心', 'code': 'report_center', 'path': '#', 'icon': 'bar-chart', 'sort': 20, 'children': [
            {'name': '报表展示', 'code': 'report_view', 'path': '/report/analysis', 'icon': 'eye', 'sort': 10},
            {'name': '报表设计', 'code': 'report_design_mgt', 'path': '/report/manage', 'icon': 'pencil-square', 'sort': 15},
            {'name': '目录管理', 'code': 'report_dir', 'path': '/report/directory', 'icon': 'folder', 'sort': 20},
        ]},
        
        # Mobile
        {'name': '移动平台', 'code': 'mobile_platform', 'path': '/mobile', 'icon': 'mobile', 'sort': 30, 'children': []},
        
        # System Management
        {'name': '系统管理', 'code': 'sys_mgt', 'path': '/system', 'icon': 'setting', 'sort': 90, 'children': [
            {'name': '用户管理', 'code': 'user_mgt', 'path': '/system/user', 'icon': 'user', 'sort': 10},
            {'name': '权限管理', 'code': 'perm_mgt', 'path': '/system/permission', 'icon': 'lock', 'sort': 20},
            {'name': '菜单管理', 'code': 'menu_mgt', 'path': '/system/menu', 'icon': 'menu', 'sort': 30},
            {'name': '定时调度', 'code': 'scheduler', 'path': '/system/scheduler', 'icon': 'clock', 'sort': 40},
            {'name': '操作日志', 'code': 'audit_log', 'path': '/system/log', 'icon': 'file', 'sort': 50},
        ]}
    ]

    for m in menus:
        menu_obj, created = SysMenu.objects.update_or_create(
            code=m['code'],
            defaults={
                'name': m['name'],
                'path': m['path'],
                'icon': m['icon'],
                'sort_order': m.get('sort', 0),
                'parent': None  # Ensure it is root
            }
        )
        action = "Created" if created else "Updated"
        print(f"{action} Menu: {m['name']}")
        
        for child in m.get('children', []):
            SysMenu.objects.update_or_create(
                code=child['code'],
                defaults={
                    'name': child['name'],
                    'parent': menu_obj,
                    'path': child['path'],
                    'icon': child['icon'],
                    'sort_order': child.get('sort', 0)
                }
            )
            print(f"  Processed Child Menu: {child['name']}")

def init_roles():
    print("Initializing Roles...")
    admin_role, _ = SysRole.objects.get_or_create(name='Administrator', defaults={'description': 'System Administrator'})
    user_role, _ = SysRole.objects.get_or_create(name='General User', defaults={'description': 'Normal User'})
    
    # Assign all menus to Admin
    all_menus = SysMenu.objects.all()
    admin_role.menus.set(all_menus)
    print("Assigned all menus to Administrator")

def init_users():
    print("Initializing Users...")
    if not User.objects.filter(username='admin').exists():
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Created Superuser: admin / admin123")
    else:
        print("Superuser admin already exists")

def main():
    try:
        init_menus()
        init_roles()
        init_users()
        print("Initialization Complete!")
    except Exception as e:
        print(f"Error during initialization: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
