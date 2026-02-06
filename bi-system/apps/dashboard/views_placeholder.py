from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Q
from .models import Report, ReportDirectory, DataSet, DataSource
from .forms import ReportForm
from .utils.query_executor import QueryExecutor, resolve_dataset_sql
from .utils.data_processing import aggregate_data
import json
import os
import time
from django.conf import settings

def get_menus():
    # Helper to get menus (mock or real)
    # Since we saw it used in the code, we assume it exists in this file or imported.
    # Based on previous read, it was imported or defined.
    # It was defined in the file (I didn't read the top, but used in code).
    # Wait, I need to be careful not to overwrite the existing file content blindly.
    # I should use SearchReplace for specific functions.
    pass

# ... existing code ...
