"""
銷售趨勢分析系統API路由
"""

from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify
from src.models.food_item import db
from src.models.inventory_record import InventoryRecord
import json

# 創建藍圖
sales_trend_bp = Blueprint('sales_trend', __name__)


@sales_trend_bp.route('/api/sales-trend/daily', methods=['GET'])
def get_daily_sales_trend():
    """
    獲取日銷售趨勢（過去N天）
    """
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # 查詢銷售記錄
        records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= start_date
        ).all()
        
        # 按日期分組統計
        daily_stats = {}
        for record in records:
            date_key = record.created_at.strftime('%Y-%m-%d')
            if date_key not in daily_stats:
                daily_stats[date_key] = {
                    'count': 0,
                    'amount': 0,
                    'discount': 0,
                    'quantity': 0
                }
            
            gross_amount = (record.quantity or 0) * (record.unit_price or 0)
            net_amount = record.total_price or 0
            discount_amount = gross_amount - net_amount

            daily_stats[date_key]['count'] += 1
            daily_stats[date_key]['amount'] += gross_amount
            daily_stats[date_key]['discount'] += discount_amount
            daily_stats[date_key]['quantity'] += record.quantity or 0
        
        # 轉換為列表格式
        result = []
        for date_str in sorted(daily_stats.keys()):
            stats = daily_stats[date_str]
            result.append({
                'date': date_str,
                'sales_count': stats['count'],
                'sales_amount': round(stats['amount'], 2),
                'discount': round(stats['discount'], 2),
                'net_amount': round(stats['amount'] - stats['discount'], 2),
                'quantity': stats['quantity']
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'total_days': len(result),
            'total_sales': sum(s['sales_amount'] for s in result),
            'average_daily_sales': round(sum(s['sales_amount'] for s in result) / len(result), 2) if result else 0
        })
    except Exception as e:
        return jsonify({'error': f'獲取日趨勢失敗: {str(e)}'}), 500


@sales_trend_bp.route('/api/sales-trend/weekly', methods=['GET'])
def get_weekly_sales_trend():
    """
    獲取週銷售趨勢（過去N週）
    """
    try:
        weeks = request.args.get('weeks', 12, type=int)
        start_date = datetime.now() - timedelta(weeks=weeks)
        
        # 查詢銷售記錄
        records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= start_date
        ).all()
        
        # 按週分組統計
        weekly_stats = {}
        for record in records:
            week_key = record.created_at.strftime('%Y-W%U')  # 年-週號
            if week_key not in weekly_stats:
                weekly_stats[week_key] = {
                    'count': 0,
                    'amount': 0,
                    'discount': 0,
                    'quantity': 0
                }
            
            gross_amount = (record.quantity or 0) * (record.unit_price or 0)
            net_amount = record.total_price or 0
            discount_amount = gross_amount - net_amount

            weekly_stats[week_key]['count'] += 1
            weekly_stats[week_key]['amount'] += gross_amount
            weekly_stats[week_key]['discount'] += discount_amount
            weekly_stats[week_key]['quantity'] += record.quantity or 0
        
        # 轉換為列表格式
        result = []
        for week_str in sorted(weekly_stats.keys()):
            stats = weekly_stats[week_str]
            result.append({
                'week': week_str,
                'sales_count': stats['count'],
                'sales_amount': round(stats['amount'], 2),
                'discount': round(stats['discount'], 2),
                'net_amount': round(stats['amount'] - stats['discount'], 2),
                'quantity': stats['quantity']
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'total_weeks': len(result),
            'total_sales': sum(s['sales_amount'] for s in result),
            'average_weekly_sales': round(sum(s['sales_amount'] for s in result) / len(result), 2) if result else 0
        })
    except Exception as e:
        return jsonify({'error': f'獲取週趨勢失敗: {str(e)}'}), 500


@sales_trend_bp.route('/api/sales-trend/monthly', methods=['GET'])
def get_monthly_sales_trend():
    """
    獲取月銷售趨勢（過去N月）
    """
    try:
        months = request.args.get('months', 12, type=int)
        start_date = datetime.now() - timedelta(days=30*months)
        
        # 查詢銷售記錄
        records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= start_date
        ).all()
        
        # 按月分組統計
        monthly_stats = {}
        for record in records:
            month_key = record.created_at.strftime('%Y-%m')
            if month_key not in monthly_stats:
                monthly_stats[month_key] = {
                    'count': 0,
                    'amount': 0,
                    'discount': 0,
                    'quantity': 0
                }
            
            gross_amount = (record.quantity or 0) * (record.unit_price or 0)
            net_amount = record.total_price or 0
            discount_amount = gross_amount - net_amount

            monthly_stats[month_key]['count'] += 1
            monthly_stats[month_key]['amount'] += gross_amount
            monthly_stats[month_key]['discount'] += discount_amount
            monthly_stats[month_key]['quantity'] += record.quantity or 0
        
        # 轉換為列表格式
        result = []
        for month_str in sorted(monthly_stats.keys()):
            stats = monthly_stats[month_str]
            result.append({
                'month': month_str,
                'sales_count': stats['count'],
                'sales_amount': round(stats['amount'], 2),
                'discount': round(stats['discount'], 2),
                'net_amount': round(stats['amount'] - stats['discount'], 2),
                'quantity': stats['quantity']
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'total_months': len(result),
            'total_sales': sum(s['sales_amount'] for s in result),
            'average_monthly_sales': round(sum(s['sales_amount'] for s in result) / len(result), 2) if result else 0
        })
    except Exception as e:
        return jsonify({'error': f'獲取月趨勢失敗: {str(e)}'}), 500


@sales_trend_bp.route('/api/sales-trend/category', methods=['GET'])
def get_category_sales_trend():
    """
    獲取按分類的銷售趨勢
    """
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # 查詢銷售記錄
        records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= start_date
        ).all()
        
        # 按分類分組統計
        category_stats = {}
        for record in records:
            category = record.category or '未分類'
            if category not in category_stats:
                category_stats[category] = {
                    'count': 0,
                    'amount': 0,
                    'discount': 0,
                    'quantity': 0
                }
            
            gross_amount = (record.quantity or 0) * (record.unit_price or 0)
            net_amount = record.total_price or 0
            discount_amount = gross_amount - net_amount

            category_stats[category]['count'] += 1
            category_stats[category]['amount'] += gross_amount
            category_stats[category]['discount'] += discount_amount
            category_stats[category]['quantity'] += record.quantity or 0
        
        # 轉換為列表格式並排序
        result = []
        for category in sorted(category_stats.keys(), key=lambda x: category_stats[x]['amount'], reverse=True):
            stats = category_stats[category]
            result.append({
                'category': category,
                'sales_count': stats['count'],
                'sales_amount': round(stats['amount'], 2),
                'discount': round(stats['discount'], 2),
                'net_amount': round(stats['amount'] - stats['discount'], 2),
                'quantity': stats['quantity'],
                'average_price': round(stats['amount'] / stats['quantity'], 2) if stats['quantity'] > 0 else 0
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'total_categories': len(result),
            'total_sales': sum(s['sales_amount'] for s in result)
        })
    except Exception as e:
        return jsonify({'error': f'獲取分類趨勢失敗: {str(e)}'}), 500


@sales_trend_bp.route('/api/sales-trend/top-products', methods=['GET'])
def get_top_products():
    """
    獲取銷售排行前N的商品
    """
    try:
        days = request.args.get('days', 30, type=int)
        limit = request.args.get('limit', 10, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # 查詢銷售記錄
        records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= start_date
        ).all()
        
        # 按商品分組統計
        product_stats = {}
        for record in records:
            product = record.product_name or '未知商品'
            if product not in product_stats:
                product_stats[product] = {
                    'count': 0,
                    'amount': 0,
                    'discount': 0,
                    'quantity': 0,
                    'category': record.category
                }
            
            gross_amount = (record.quantity or 0) * (record.unit_price or 0)
            net_amount = record.total_price or 0
            discount_amount = gross_amount - net_amount

            product_stats[product]['count'] += 1
            product_stats[product]['amount'] += gross_amount
            product_stats[product]['discount'] += discount_amount
            product_stats[product]['quantity'] += record.quantity or 0
        
        # 轉換為列表格式並排序
        result = []
        for product in sorted(product_stats.keys(), key=lambda x: product_stats[x]['amount'], reverse=True)[:limit]:
            stats = product_stats[product]
            result.append({
                'product_name': product,
                'category': stats['category'] or '未分類',
                'sales_count': stats['count'],
                'sales_amount': round(stats['amount'], 2),
                'discount': round(stats['discount'], 2),
                'net_amount': round(stats['amount'] - stats['discount'], 2),
                'quantity': stats['quantity'],
                'average_price': round(stats['amount'] / stats['quantity'], 2) if stats['quantity'] > 0 else 0
            })
        
        return jsonify({
            'success': True,
            'data': result,
            'total_products': len(result)
        })
    except Exception as e:
        return jsonify({'error': f'獲取排行失敗: {str(e)}'}), 500


@sales_trend_bp.route('/api/sales-trend/summary', methods=['GET'])
def get_sales_summary():
    """
    獲取銷售摘要統計
    """
    try:
        days = request.args.get('days', 30, type=int)
        start_date = datetime.now() - timedelta(days=days)
        
        # 查詢銷售記錄
        records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= start_date
        ).all()
        
        # 計算統計信息
        total_sales_count = len(records)
        total_gross_amount = 0
        total_discount_amount = 0
        total_net_amount = 0
        total_quantity = 0

        for record in records:
            gross_amount = (record.quantity or 0) * (record.unit_price or 0)
            net_amount = record.total_price or 0
            discount_amount = gross_amount - net_amount

            total_gross_amount += gross_amount
            total_discount_amount += discount_amount
            total_net_amount += net_amount
            total_quantity += (record.quantity or 0)
        
        # 計算平均值
        avg_transaction = round(total_gross_amount / total_sales_count, 2) if total_sales_count > 0 else 0
        avg_discount_rate = round((total_discount_amount / total_gross_amount * 100), 2) if total_gross_amount > 0 else 0
        
        return jsonify({
            'success': True,
            'summary': {
                'period_days': days,
                'total_sales': total_sales_count,
                'total_amount': round(total_gross_amount, 2), # This is Gross Amount
                'total_discount': round(total_discount_amount, 2),
                'net_amount': round(total_net_amount, 2),
                'total_quantity': total_quantity,
                'average_transaction': avg_transaction,
                'average_discount_rate': avg_discount_rate,
                'daily_average_sales': round(total_gross_amount / days, 2) if days > 0 else 0
            }
        })
    except Exception as e:
        return jsonify({'error': f'獲取摘要失敗: {str(e)}'}), 500


@sales_trend_bp.route('/api/sales-trend/comparison', methods=['GET'])
def get_period_comparison():
    """
    比較兩個時間段的銷售數據
    """
    try:
        # 當前期間
        current_days = request.args.get('current_days', 30, type=int)
        current_end = datetime.now()
        current_start = current_end - timedelta(days=current_days)
        
        # 對比期間
        compare_days = request.args.get('compare_days', 30, type=int)
        compare_end = current_start
        compare_start = compare_end - timedelta(days=compare_days)
        
        # 查詢當前期間銷售
        current_records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= current_start,
            InventoryRecord.created_at < current_end
        ).all()
        
        # 查詢對比期間銷售
        compare_records = InventoryRecord.query.filter(
            InventoryRecord.operation_type == 'sale',
            InventoryRecord.created_at >= compare_start,
            InventoryRecord.created_at < compare_end
        ).all()
        
        # 計算統計 (使用 gross amount)
        current_gross_amount = sum((r.quantity or 0) * (r.unit_price or 0) for r in current_records)
        compare_gross_amount = sum((r.quantity or 0) * (r.unit_price or 0) for r in compare_records)
        
        # 計算增長率
        growth_rate = 0
        if compare_gross_amount > 0:
            growth_rate = round(((current_gross_amount - compare_gross_amount) / compare_gross_amount * 100), 2)
        
        return jsonify({
            'success': True,
            'comparison': {
                'current_period': {
                    'days': current_days,
                    'sales_count': len(current_records),
                    'sales_amount': round(current_gross_amount, 2)
                },
                'compare_period': {
                    'days': compare_days,
                    'sales_count': len(compare_records),
                    'sales_amount': round(compare_gross_amount, 2)
                },
                'growth_rate': growth_rate,
                'difference': round(current_gross_amount - compare_gross_amount, 2)
            }
        })
    except Exception as e:
        return jsonify({'error': f'比較失敗: {str(e)}'}), 500
