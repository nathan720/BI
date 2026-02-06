import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings.dev')
django.setup()

from core.reporting.models import ReportDirectory, Report

def create_report_directories():
    print("Creating Report Directories...")
    
    # Root Level
    finance, _ = ReportDirectory.objects.get_or_create(name='财务报表', defaults={'sort_order': 10})
    sales, _ = ReportDirectory.objects.get_or_create(name='销售报表', defaults={'sort_order': 20})
    ops, _ = ReportDirectory.objects.get_or_create(name='运营报表', defaults={'sort_order': 30})
    
    # Level 2 - Finance
    fin_monthly, _ = ReportDirectory.objects.get_or_create(name='月度财报', parent=finance, defaults={'sort_order': 1})
    fin_quarterly, _ = ReportDirectory.objects.get_or_create(name='季度财报', parent=finance, defaults={'sort_order': 2})
    
    # Level 2 - Sales
    sales_north, _ = ReportDirectory.objects.get_or_create(name='华北区', parent=sales, defaults={'sort_order': 1})
    sales_south, _ = ReportDirectory.objects.get_or_create(name='华南区', parent=sales, defaults={'sort_order': 2})
    
    # Level 3 - Sales North
    sales_beijing, _ = ReportDirectory.objects.get_or_create(name='北京分公司', parent=sales_north, defaults={'sort_order': 1})
    
    print("Directories created.")
    
    # Assign existing reports
    reports = Report.objects.all()
    for r in reports:
        if '财务' in r.name:
            r.directory = fin_monthly
        elif '经营' in r.name:
            r.directory = ops
        else:
            r.directory = sales_beijing # Default for others
        r.save()
        
    print("Reports assigned.")

if __name__ == '__main__':
    create_report_directories()