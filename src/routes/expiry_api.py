"""
即期品管理API - 使用統一的FoodItem表
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.food_item import db, FoodItem

expiry_api_bp = Blueprint('expiry_api', __name__, url_prefix='/api/expiry')

# ==================== 即期品清單 ====================

@expiry_api_bp.route('/list', methods=['GET'])
def get_expiry_list():
    """獲取即期品清單（按效期分類）"""
    try:
        today = datetime.now().date()
        
        # 查詢各類即期品
        critical = FoodItem.query.filter(
            FoodItem.expiry_date >= today,
            FoodItem.expiry_date <= today + timedelta(days=3),
            FoodItem.item_status == '在庫',
            FoodItem.quantity > 0
        ).all()
        
        urgent = FoodItem.query.filter(
            FoodItem.expiry_date > today + timedelta(days=3),
            FoodItem.expiry_date <= today + timedelta(days=7),
            FoodItem.item_status == '在庫',
            FoodItem.quantity > 0
        ).all()
        
        soon = FoodItem.query.filter(
            FoodItem.expiry_date > today + timedelta(days=7),
            FoodItem.expiry_date <= today + timedelta(days=30),
            FoodItem.item_status == '在庫',
            FoodItem.quantity > 0
        ).all()
        
        expired = FoodItem.query.filter(
            FoodItem.expiry_date < today,
            FoodItem.item_status == '在庫',
            FoodItem.quantity > 0
        ).all()
        
        return jsonify({
            'success': True,
            'expiry_list': {
                'critical': [item.to_dict() for item in critical],
                'urgent': [item.to_dict() for item in urgent],
                'soon': [item.to_dict() for item in soon],
                'expired': [item.to_dict() for item in expired]
            },
            'summary': {
                'critical_count': len(critical),
                'urgent_count': len(urgent),
                'soon_count': len(soon),
                'expired_count': len(expired),
                'total_expiring': len(critical) + len(urgent) + len(soon)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 折扣應用 ====================

@expiry_api_bp.route('/apply-discount', methods=['POST'])
def apply_discount():
    """應用折扣到即期品"""
    try:
        data = request.get_json()
        item_ids = data.get('item_ids', [])
        discount_rate = float(data.get('discount_rate', 0.3))
        
        if not item_ids:
            return jsonify({'success': False, 'error': '未指定商品'}), 400
        
        updated_items = []
        for item_id in item_ids:
            item = FoodItem.query.get(item_id)
            if item:
                # 記錄原始價格
                original_price = item.unit_price
                # 應用折扣
                item.unit_price = original_price * (1 - discount_rate)
                item.updated_at = datetime.now()
                updated_items.append({
                    'id': item.id,
                    'name': item.name,
                    'original_price': original_price,
                    'discounted_price': item.unit_price,
                    'discount_rate': discount_rate
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已應用折扣到 {len(updated_items)} 件商品',
            'updated_items': updated_items
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 下架過期商品 ====================

@expiry_api_bp.route('/remove-expired', methods=['POST'])
def remove_expired():
    """下架所有過期商品"""
    try:
        today = datetime.now().date()
        
        expired_items = FoodItem.query.filter(
            FoodItem.expiry_date <= today,
            FoodItem.item_status == '在庫'
        ).all()
        
        removed_count = 0
        for item in expired_items:
            item.item_status = '下架'
            item.updated_at = datetime.now()
            removed_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已下架 {removed_count} 件過期商品',
            'removed_count': removed_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 促銷活動 ====================

@expiry_api_bp.route('/promotion', methods=['POST'])
def create_promotion():
    """建立促銷活動"""
    try:
        data = request.get_json()
        item_ids = data.get('item_ids', [])
        discount_rate = float(data.get('discount_rate', 0.3))
        promotion_name = data.get('promotion_name', '即期品促銷')
        
        updated_items = []
        for item_id in item_ids:
            item = FoodItem.query.get(item_id)
            if item:
                original_price = item.unit_price
                item.unit_price = original_price * (1 - discount_rate)
                item.updated_at = datetime.now()
                updated_items.append({
                    'id': item.id,
                    'name': item.name,
                    'discount_rate': discount_rate
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'促銷活動「{promotion_name}」已建立',
            'promotion_name': promotion_name,
            'updated_count': len(updated_items),
            'updated_items': updated_items
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 銷售分析 ====================

@expiry_api_bp.route('/sales-analysis', methods=['GET'])
def sales_analysis():
    """分析即期品銷售效果"""
    try:
        # 統計過去7天的銷售
        seven_days_ago = datetime.now().date() - timedelta(days=7)
        
        # 統計已售出的商品（即期品）
        sold_items = FoodItem.query.filter(
            FoodItem.item_status == '已售',
            FoodItem.updated_at >= seven_days_ago
        ).all()
        
        total_discounted_sales = 0
        total_discounted_quantity = 0
        
        for item in sold_items:
            if item.unit_price > 0:
                total_discounted_sales += item.unit_price
                total_discounted_quantity += 1
        
        return jsonify({
            'success': True,
            'analysis': {
                'period': f'{seven_days_ago} 至 {datetime.now().date()}',
                'summary': {
                    'total_discounted_sales': total_discounted_sales,
                    'total_discounted_quantity': total_discounted_quantity,
                    'avg_discount_rate': 0.3 if total_discounted_quantity > 0 else 0
                }
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
