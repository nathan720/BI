from django import forms
from django.contrib.auth.models import User
from core.data_source.models import DataSource
from core.dataset.models import DataSet
from core.reporting.models import Report, ReportDirectory
from core.auth.models import SysRole, SysMenu

class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep unchanged'}), required=False)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_active', 'is_superuser']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_superuser': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class SysRoleForm(forms.ModelForm):
    class Meta:
        model = SysRole
        fields = ['name', 'description', 'menus']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'menus': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        }

class SysMenuForm(forms.ModelForm):
    class Meta:
        model = SysMenu
        fields = ['name', 'code', 'parent', 'path', 'icon', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'path': forms.TextInput(attrs={'class': 'form-control'}),
            'icon': forms.TextInput(attrs={'class': 'form-control'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class DataSourceForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Leave blank to keep unchanged'}), required=False)

    class Meta:
        model = DataSource
        fields = ['name', 'db_type', 'host', 'port', 'username', 'password', 'db_name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'db_type': forms.Select(attrs={'class': 'form-select'}),
            'host': forms.TextInput(attrs={'class': 'form-control'}),
            'port': forms.NumberInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'db_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        datasource = super().save(commit=False)
        if self.cleaned_data['password']:
            datasource.password = self.cleaned_data['password']
        if commit:
            datasource.save()
        return datasource

class DataSetForm(forms.ModelForm):
    class Meta:
        model = DataSet
        fields = ['name', 'datasource', 'sql_script']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'datasource': forms.Select(attrs={'class': 'form-select'}),
            'sql_script': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'font-family': 'monospace'}),
        }

class ReportDirectoryForm(forms.ModelForm):
    class Meta:
        model = ReportDirectory
        fields = ['name', 'parent', 'sort_order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'parent': forms.Select(attrs={'class': 'form-select'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['name', 'code', 'platform', 'is_visible', 'description', 'external_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'platform': forms.Select(attrs={'class': 'form-select'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input', 'role': 'switch'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'external_url': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '可选：输入外部链接 (例如 http://example.com)'}),
        }

