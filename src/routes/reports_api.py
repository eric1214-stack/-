"""
盤點報表API - 使用統一的FoodItem表
"""

import json
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, date
from src.models.food_item import db, FoodItem
from src.models.inventory_record import InventoryRecord
from src.models.inventory_audit import InventoryAudit

reports_api_bp = Blueprint('reports_api', __name__, url_prefix='/api/reports')

# ==================== 報表生成 ====================

@reports_api_bp.route('/daily', methods=['POST'])
def generate_daily_report():
    """生成日報表並存檔"""
    try:
        report_date_str = request.json.get('report_date', date.today().isoformat())
        report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()

        all_items = FoodItem.query.all()
        
        total_items = len(all_items)
        in_stock = len([i for i in all_items if i.item_status == '在庫'])
        sold = len([i for i in all_items if i.item_status == '已售'])
        removed = len([i for i in all_items if i.item_status == '下架'])
        
        expired = len([i for i in all_items if i.expiry_date and i.expiry_date < report_date and i.item_status == '在庫'])
        expiring_soon = len([i for i in all_items if i.expiry_date and report_date <= i.expiry_date <= report_date + timedelta(days=30) and i.item_status == '在庫'])
        
        sales_records = InventoryRecord.query.filter(
            InventoryRecord.operation_type.in_(['sale', '銷售']),
            db.func.date(InventoryRecord.record_date) == report_date
        ).all()
        total_sales = sum(r.total_price for r in sales_records if r.total_price is not None)

        report_data = {
            'report_date': report_date.isoformat(),
            'report_type': '日報表',
            'inventory_summary': {'total_items': total_items, 'in_stock': in_stock, 'sold': sold, 'removed': removed},
            'anomaly_summary': {'expired_items': expired, 'expiring_items': expiring_soon, 'total_anomalies': expired + expiring_soon},
            'sales_summary': {'total_sales': total_sales}
        }

        new_audit = InventoryAudit(
            report_date=report_date,
            report_type='日報表',
            total_items=total_items,
            in_stock_items=in_stock,
            sold_items=sold,
            removed_items=removed,
            expired_items=expired,
            expiring_soon_items=expiring_soon,
            total_sales_amount=total_sales,
            raw_data=json.dumps(report_data)
        )
        
        db.session.add(new_audit)
        db.session.commit()
        
        return jsonify({'success': True, 'report': new_audit.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_api_bp.route('/weekly', methods=['POST'])
def generate_weekly_report():
    """生成週報表並存檔"""
    try:
        today = date.today()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)

        all_items = FoodItem.query.all()
        
        total_items = len(all_items)
        in_stock = len([i for i in all_items if i.item_status == '在庫'])
        
        # Weekly specific stats
        sold_records_weekly = InventoryRecord.query.filter(
            InventoryRecord.operation_type.in_(['sale', '銷售']),
            db.func.date(InventoryRecord.record_date).between(start_of_week, end_of_week)
        ).all()
        sold_weekly = sum(r.quantity for r in sold_records_weekly)
        total_sales_weekly = sum(r.total_price for r in sold_records_weekly if r.total_price is not None)

        expired = len([i for i in all_items if i.expiry_date and i.expiry_date < today and i.item_status == '在庫'])
        
        report_data = {
            'report_type': '週報表',
            'period': f'{start_of_week.isoformat()} 至 {end_of_week.isoformat()}',
            'inventory_summary': {'total_items': total_items, 'in_stock': in_stock, 'sold': sold_weekly},
            'sales_summary': {'total_sales': total_sales_weekly},
            'anomaly_summary': {'expired_items': expired}
        }

        new_audit = InventoryAudit(
            report_date=today,
            report_type='週報表',
            total_items=total_items,
            in_stock_items=in_stock,
            sold_items=sold_weekly,
            expired_items=expired,
            total_sales_amount=total_sales_weekly,
            raw_data=json.dumps(report_data)
        )
        
        db.session.add(new_audit)
        db.session.commit()
        
        return jsonify({'success': True, 'report': new_audit.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@reports_api_bp.route('/monthly', methods=['POST'])
def generate_monthly_report():
    """生成月報表並存檔"""
    try:
        today = date.today()
        start_of_month = today.replace(day=1)
        
        all_items = FoodItem.query.all()
        
        total_items = len(all_items)
        in_stock = len([i for i in all_items if i.item_status == '在庫'])

        sold_records_monthly = InventoryRecord.query.filter(
            InventoryRecord.operation_type.in_(['sale', '銷售']),
            db.func.date(InventoryRecord.record_date) >= start_of_month
        ).all()
        sold_monthly = sum(r.quantity for r in sold_records_monthly)
        total_sales_monthly = sum(r.total_price for r in sold_records_monthly if r.total_price is not None)

        expired = len([i for i in all_items if i.expiry_date and i.expiry_date < today and i.item_status == '在庫'])
        
        report_data = {
            'report_type': '月報表',
            'period': f'{start_of_month.isoformat()} 至 {today.isoformat()}',
            'inventory_summary': {'total_items': total_items, 'in_stock': in_stock, 'sold': sold_monthly},
            'sales_summary': {'total_sales': total_sales_monthly},
            'anomaly_summary': {'expired_items': expired}
        }
        
        new_audit = InventoryAudit(
            report_date=today,
            report_type='月報表',
            total_items=total_items,
            in_stock_items=in_stock,
            sold_items=sold_monthly,
            expired_items=expired,
            total_sales_amount=total_sales_monthly,
            raw_data=json.dumps(report_data)
        )
        
        db.session.add(new_audit)
        db.session.commit()
        
        return jsonify({'success': True, 'report': new_audit.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 報表查詢 ====================

@reports_api_bp.route('/list', methods=['GET'])
def get_reports_list():
    """獲取歷史報表列表"""
    try:
        reports = InventoryAudit.query.order_by(InventoryAudit.report_date.desc()).all()
        
        return jsonify({
            'success': True,
            'reports': [r.to_dict() for r in reports]
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
