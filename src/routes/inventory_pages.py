"""
超商庫存管理系統 - 頁面路由
"""

from flask import Blueprint, render_template, make_response
from datetime import datetime

# 創建藍圖
inventory_pages_bp = Blueprint('inventory_pages', __name__)


@inventory_pages_bp.route('/inventory')
def inventory_page():
    """庫存管理頁面 - 優化版"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('inventory_optimized.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/inventory/legacy')
def inventory_legacy_page():
    """庫存管理頁面 - 原始版本"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('inventory_unified.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/expiry-management')
def expiry_management_page():
    """即期品管理系統頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('expiry_management.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/reports')
def reports_page():
    """盤點報表系統頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('reports.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/inventory-records')
def inventory_records_page():
    """入庫/出庫記錄管理頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('inventory_records.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/barcode-database')
def barcode_database_page():
    """條碼資料庫管理頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('barcode_database.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/barcode-scanner')
def barcode_scanner_page():
    """條碼掃描頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('barcode_scanner.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/inventory-alerts')
def inventory_alerts_page():
    """庫存預警頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('inventory_alerts.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/operation-logs')
def operation_logs_page():
    """操作日誌審計頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('operation_logs.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/report-export')
def report_export_page():
    """報表導出頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('report_export.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response


@inventory_pages_bp.route('/sales-trend')
def sales_trend_page():
    """銷售趨勢分析頁面"""
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('sales_trend.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    return response
