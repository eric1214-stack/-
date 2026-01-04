"""
盤點報表API - 使用統一的FoodItem表
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, date
from src.models.food_item import db, FoodItem
from src.models.inventory_record import InventoryRecord

reports_api_bp = Blueprint('reports_api', __name__, url_prefix='/api/reports')

# ==================== 報表生成 ====================

@reports_api_bp.route('/daily', methods=['POST'])
def generate_daily_report():
    """生成日報表"""
    try:
        report_date = request.json.get('report_date', date.today().isoformat())
        
        # 統計當日數據
        all_items = FoodItem.query.all()
        
        total_items = len(all_items)
        in_stock = len([i for i in all_items if i.item_status == '在庫'])
        sold = len([i for i in all_items if i.item_status == '已售'])
        removed = len([i for i in all_items if i.item_status == '下架'])
        
        today = date.today()
        expired = len([i for i in all_items if i.expiry_date < today and i.item_status == '在庫'])
        expiring_soon = len([i for i in all_items if today <= i.expiry_date <= today + timedelta(days=30) and i.item_status == '在庫'])
        
        return jsonify({
            'success': True,
            'report': {
                'report_date': report_date,
                'report_type': '日報表',
                'inventory_summary': {
                    'total_items': total_items,
                    'in_stock': in_stock,
                    'sold': sold,
                    'removed': removed
                },
                'anomaly_summary': {
                    'expired_items': expired,
                    'expiring_items': expiring_soon,
                    'total_anomalies': expired + expiring_soon
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_api_bp.route('/weekly', methods=['POST'])
def generate_weekly_report():
    """生成週報表"""
    try:
        # 統計過去7天數據
        all_items = FoodItem.query.all()
        
        total_items = len(all_items)
        in_stock = len([i for i in all_items if i.item_status == '在庫'])
        sold = len([i for i in all_items if i.item_status == '已售'])
        
        today = date.today()
        expired = len([i for i in all_items if i.expiry_date < today and i.item_status == '在庫'])
        
        # 按分類統計
        categories = {}
        for item in all_items:
            cat = item.category or '其他'
            if cat not in categories:
                categories[cat] = {'count': 0, 'quantity': 0}
            categories[cat]['count'] += 1
            categories[cat]['quantity'] += item.quantity
        
        return jsonify({
            'success': True,
            'report': {
                'report_type': '週報表',
                'period': f'{(today - timedelta(days=7)).isoformat()} 至 {today.isoformat()}',
                'inventory_summary': {
                    'total_items': total_items,
                    'in_stock': in_stock,
                    'sold': sold
                },
                'category_breakdown': [
                    {'category': cat, 'count': data['count'], 'quantity': data['quantity']}
                    for cat, data in categories.items()
                ],
                'anomaly_summary': {
                    'expired_items': expired
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_api_bp.route('/monthly', methods=['POST'])
def generate_monthly_report():
    """生成月報表"""
    try:
        # 統計過去30天數據
        all_items = FoodItem.query.all()
        
        total_items = len(all_items)
        in_stock = len([i for i in all_items if i.item_status == '在庫'])
        sold = len([i for i in all_items if i.item_status == '已售'])
        
        today = date.today()
        expired = len([i for i in all_items if i.expiry_date < today and i.item_status == '在庫'])
        
        # 按分類統計
        categories = {}
        for item in all_items:
            cat = item.category or '其他'
            if cat not in categories:
                categories[cat] = {'count': 0, 'quantity': 0, 'sales': 0}
            categories[cat]['count'] += 1
            categories[cat]['quantity'] += item.quantity
            if item.item_status == '已售':
                categories[cat]['sales'] += item.unit_price * item.quantity
        
        return jsonify({
            'success': True,
            'report': {
                'report_type': '月報表',
                'period': f'{(today - timedelta(days=30)).isoformat()} 至 {today.isoformat()}',
                'inventory_summary': {
                    'total_items': total_items,
                    'in_stock': in_stock,
                    'sold': sold
                },
                'category_breakdown': [
                    {
                        'category': cat,
                        'count': data['count'],
                        'quantity': data['quantity'],
                        'sales': data['sales']
                    }
                    for cat, data in categories.items()
                ],
                'anomaly_summary': {
                    'expired_items': expired
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 報表查詢 ====================

@reports_api_bp.route('/list', methods=['GET'])
def get_reports_list():
    """獲取報表列表"""
    try:
        today = date.today()
        
        # 獲取所有商品
        all_items = FoodItem.query.all()
        
        # 計算庫存統計
        total_items = len(all_items)
        total_quantity = sum(item.quantity for item in all_items if item.quantity)
        expired_items = len([i for i in all_items if i.expiry_date and i.expiry_date < today and i.item_status == '在庫'])
        expiring_items = len([i for i in all_items if i.expiry_date and today <= i.expiry_date <= today + timedelta(days=30) and i.item_status == '在庫'])
        
        # 計算總銷售額
        sales_records = InventoryRecord.query.filter_by(operation_type='銷售').all()
        total_sales_amount = sum(r.total_amount for r in sales_records if r.total_amount)
        
        # 因為沒有報表歷史記錄，這裡我們創建一個即時的總覽報表
        summary_report = {
            'report_id': 1,
            'report_date': today.isoformat(),
            'report_type': '總覽報表',
            'total_items': total_items,
            'total_quantity': total_quantity,
            'expired_items': expired_items,
            'expiring_items': expiring_items,
            'total_sales_amount': total_sales_amount
        }
        
        return jsonify({
            'success': True,
            'reports': [summary_report]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 庫存統計 ====================

@reports_api_bp.route('/inventory-stats', methods=['GET'])
def get_inventory_stats():
    """獲取庫存統計"""
    try:
        all_items = FoodItem.query.all()
        today = date.today()
        
        # 按狀態統計
        status_breakdown = {}
        for item in all_items:
            status = item.item_status
            if status not in status_breakdown:
                status_breakdown[status] = 0
            status_breakdown[status] += 1
        
        # 按儲存條件統計
        condition_breakdown = {}
        for item in all_items:
            condition = item.storage_condition
            if condition not in condition_breakdown:
                condition_breakdown[condition] = 0
            condition_breakdown[condition] += 1
        
        # 按架位統計
        location_breakdown = {}
        for item in all_items:
            location = item.storage_location
            if location not in location_breakdown:
                location_breakdown[location] = 0
            location_breakdown[location] += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total_items': len(all_items),
                'by_status': [{'status': k, 'count': v} for k, v in status_breakdown.items()],
                'by_condition': [{'condition': k, 'count': v} for k, v in condition_breakdown.items()],
                'by_location': [{'location': k, 'count': v} for k, v in location_breakdown.items()]
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
