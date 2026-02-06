import os
import sys
import django
import random
from datetime import timedelta
from django.utils import timezone

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')
django.setup()

from core.auth.models import SysRole, SysMenu
from core.reporting.models import ScheduledTask, Report
from core.data_source.models import DataSource
from apps.admin.logging.audit_logs.models import AuditLog

def init_roles():
    print("Creating Demo Roles...")
    roles = [
        {'name': '数据分析师', 'desc': '负责报表制作和数据分析'},
        {'name': '业务经理', 'desc': '查看业务报表'},
        {'name': '审计员', 'desc': '查看系统日志'},
    ]
    for r in roles:
        SysRole.objects.get_or_create(name=r['name'], defaults={'description': r['desc']})

def init_reports():
    print("Creating Demo Reports...")
    reports = [
        {'name': '2025年度财务总览', 'code': 'rpt_fin_2025', 'platform': 'pc', 'desc': '展示年度收入、支出及利润趋势'},
        {'name': 'Q1销售业绩分析', 'code': 'rpt_sale_q1', 'platform': 'pc', 'desc': '各区域销售达成率排名'},
        {'name': '移动端-每日经营日报', 'code': 'rpt_mob_daily', 'platform': 'mobile', 'desc': '关键经营指标速览'},
        {'name': '库存周转率监控', 'code': 'rpt_inv_turnover', 'platform': 'pc', 'desc': '各仓库库存周转效率分析'},
    ]
    for r in reports:
        Report.objects.get_or_create(
            code=r['code'],
            defaults={
                'name': r['name'],
                'platform': r['platform'],
                'description': r['desc']
            }
        )

def init_tasks():
    print("Creating Demo Scheduled Tasks...")
    tasks = [
        {'name': '每日数据抽取', 'cron': '0 2 * * *', 'type': 'cache'},
        {'name': '发送CEO日报邮件', 'cron': '0 8 * * *', 'type': 'email'},
        {'name': '月度报表缓存刷新', 'cron': '0 0 1 * *', 'type': 'cache'},
    ]
    for t in tasks:
        ScheduledTask.objects.get_or_create(
            name=t['name'],
            defaults={
                'cron_expression': t['cron'],
                'task_type': t['type'],
                'next_run': timezone.now() + timedelta(days=1)
            }
        )

def init_logs():
    print("Creating Demo Audit Logs...")
    actions = ['LOGIN', 'QUERY', 'EXPORT', 'MODIFY']
    targets = ['财务报表', '用户管理', '数据连接配置', '销售分析']
    users = ['admin', 'zhangsan', 'lisi']
    
    # Check if we have enough logs, if not create some
    if AuditLog.objects.count() < 10:
        for i in range(20):
            AuditLog.objects.create(
                username=random.choice(users),
                action_type=random.choice(actions),
                target=random.choice(targets),
                detail=f"User performed operation on {random.choice(targets)}",
                ip_address=f"192.168.1.{random.randint(2, 254)}"
            )

def init_datasource():
    print("Creating Demo Data Source...")
    DataSource.objects.get_or_create(
        name='ERP生产库',
        defaults={
            'db_type': 'mssql',
            'host': '192.168.1.100',
            'username': 'readonly',
            'db_name': 'ERP_PROD'
        }
    )
    DataSource.objects.get_or_create(
        name='CRM营销库',
        defaults={
            'db_type': 'mysql',
            'host': '192.168.1.101',
            'username': 'marketing',
            'db_name': 'CRM_DB'
        }
    )

if __name__ == '__main__':
    try:
        init_roles()
        init_reports()
        init_tasks()
        init_logs()
        init_datasource()
        print("Demo Data Initialization Complete!")
    except Exception as e:
        print(f"Error: {e}")
