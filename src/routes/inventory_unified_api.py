"""
統一的庫存管理API - 使用FoodItem作為唯一的數據源
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from src.models.food_item import db, FoodItem

inventory_unified_bp = Blueprint('inventory_unified', __name__, url_prefix='/api/inventory')

# ==================== 庫存查詢 ====================

@inventory_unified_bp.route('/items', methods=['GET'])
def get_inventory_items():
    """獲取庫存項目列表（支援篩選）"""
    try:
        # 獲取篩選參數
        status = request.args.get('status', 'all')  # all, in_stock, sold, removed, expired
        category = request.args.get('category', 'all')
        storage_location = request.args.get('storage_location', 'all')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 構建查詢
        query = FoodItem.query
        
        # 狀態篩選
        if status != 'all':
            query = query.filter_by(item_status=status)
        
        # 分類篩選
        if category != 'all':
            query = query.filter_by(category=category)
        
        # 架位篩選
        if storage_location != 'all':
            query = query.filter_by(storage_location=storage_location)
        
        # 分頁
        paginated = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'items': [item.to_dict() for item in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_unified_bp.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    """獲取單個項目詳情"""
    try:
        item = FoodItem.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        return jsonify({
            'success': True,
            'item': item.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 商品編輯 ====================

@inventory_unified_bp.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    """更新商品信息"""
    try:
        item = FoodItem.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        data = request.get_json()
        
        # 更新允許的欄位
        if 'name' in data:
            item.name = data['name']
        if 'barcode' in data:
            item.barcode = data['barcode']
        if 'storage_location' in data:
            item.storage_location = data['storage_location']
        if 'storage_condition' in data:
            item.storage_condition = data['storage_condition']
        if 'item_status' in data:
            item.item_status = data['item_status']
        if 'ai_check_status' in data:
            item.ai_check_status = data['ai_check_status']
        if 'unit_price' in data:
            item.unit_price = float(data['unit_price'])
        if 'quantity' in data:
            item.quantity = float(data['quantity'])
        if 'category' in data:
            item.category = data['category']
        
        item.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '商品已更新',
            'item': item.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 銷售結帳 ====================

@inventory_unified_bp.route('/checkout', methods=['POST'])
def checkout():
    """銷售結帳"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = float(data.get('quantity', 1))

        # Check if item_id is a number or a string
        if isinstance(item_id, int):
            item = FoodItem.query.get(item_id)
        else:
            item = FoodItem.query.filter_by(barcode=item_id).first()
        
        if not item:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        # 檢查是否過期
        if item.status == 'expired':
            return jsonify({
                'success': False,
                'error': '商品已過期，無法銷售',
                'item_id': item_id
            }), 400
        
        # 檢查庫存
        if item.quantity < quantity:
            return jsonify({
                'success': False,
                'error': f'庫存不足，當前庫存: {item.quantity}',
                'item_id': item_id
            }), 400
        
        # 計算折扣
        discount_rate = 0
        if item.status == 'soon':  # 即期品
            discount_rate = 0.3  # 30% 折扣
        
        # 計算銷售金額
        unit_price = item.unit_price or 0
        original_amount = unit_price * quantity
        discount_amount = original_amount * discount_rate
        final_amount = original_amount - discount_amount
        
        # 更新庫存
        item.quantity -= quantity
        if item.quantity == 0:
            item.item_status = '已售'
        item.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '結帳成功',
            'item_id': item_id,
            'quantity': quantity,
            'unit_price': unit_price,
            'original_amount': original_amount,
            'discount_rate': discount_rate,
            'discount_amount': final_amount,
            'remaining_quantity': item.quantity,
            'is_expiring_soon': item.status == 'soon'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 即期品管理 ====================

@inventory_unified_bp.route('/expiring-items', methods=['GET'])
def get_expiring_items():
    """獲取即期品清單（30天內）"""
    try:
        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        items = FoodItem.query.filter(
            FoodItem.expiry_date <= thirty_days_later,
            FoodItem.expiry_date > today,
            FoodItem.item_status == '在庫'
        ).all()
        
        return jsonify({
            'success': True,
            'items': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_unified_bp.route('/expired-items', methods=['GET'])
def get_expired_items():
    """獲取過期商品清單"""
    try:
        today = datetime.now().date()
        
        items = FoodItem.query.filter(
            FoodItem.expiry_date < today,
            FoodItem.item_status == '在庫'
        ).all()
        
        return jsonify({
            'success': True,
            'items': [item.to_dict() for item in items],
            'count': len(items)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 統計信息 ====================

@inventory_unified_bp.route('/stats', methods=['GET'])
def get_stats():
    """獲取庫存統計數據"""
    try:
        total_items = FoodItem.query.count()
        in_stock = FoodItem.query.filter_by(item_status='在庫').count()
        expiring_soon = FoodItem.query.filter(
            FoodItem.expiry_date <= datetime.now().date() + timedelta(days=30),
            FoodItem.expiry_date > datetime.now().date(),
            FoodItem.item_status == '在庫'
        ).count()
        expired = FoodItem.query.filter(
            FoodItem.expiry_date < datetime.now().date(),
            FoodItem.item_status == '在庫'
        ).count()
        
        # 按分類統計
        categories = db.session.query(
            FoodItem.category,
            db.func.count(FoodItem.id).label('count')
        ).group_by(FoodItem.category).all()
        
        # 按架位統計
        locations = db.session.query(
            FoodItem.storage_location,
            db.func.count(FoodItem.id).label('count')
        ).group_by(FoodItem.storage_location).all()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_items': total_items,
                'in_stock': in_stock,
                'expiring_soon': expiring_soon,
                'expired': expired
            },
            'by_category': [{'category': cat, 'count': count} for cat, count in categories],
            'by_location': [{'location': loc, 'count': count} for loc, count in locations]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 架位管理 ====================

@inventory_unified_bp.route('/locations', methods=['GET'])
def get_locations():
    """獲取所有架位"""
    try:
        locations = db.session.query(
            FoodItem.storage_location,
            FoodItem.storage_condition,
            db.func.count(FoodItem.id).label('item_count'),
            db.func.sum(FoodItem.quantity).label('total_quantity')
        ).group_by(FoodItem.storage_location, FoodItem.storage_condition).all()
        
        result = []
        for loc, condition, count, qty in locations:
            result.append({
                'location': loc,
                'condition': condition,
                'item_count': count,
                'total_quantity': qty or 0
            })
        
        return jsonify({
            'success': True,
            'locations': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 下架/退貨 ====================

@inventory_unified_bp.route('/remove-item', methods=['POST'])
def remove_item():
    """下架商品"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        reason = data.get('reason', '其他')
        
        item = FoodItem.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        item.item_status = '下架'
        item.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'商品已下架（原因：{reason}）',
            'item_id': item_id
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_unified_bp.route('/return-item', methods=['POST'])
def return_item():
    """退貨"""
    try:
        data = request.get_json()
        item_id = data.get('item_id')
        quantity = float(data.get('quantity', 1))
        reason = data.get('reason', '其他')
        
        item = FoodItem.query.get(item_id)
        if not item:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        # 恢復庫存
        item.quantity += quantity
        item.item_status = '在庫'
        item.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'商品已退貨，恢復庫存 {quantity} 個',
            'item_id': item_id,
            'new_quantity': item.quantity
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
