"""
條碼資料庫管理API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.food_item import db
from src.models.barcode_product import BarcodeProduct
from src.routes.operation_log_api import log_operation

barcode_api_bp = Blueprint('barcode_api', __name__, url_prefix='/api/barcode')

# ==================== 條碼查詢 ====================

@barcode_api_bp.route('/search', methods=['GET'])
def search_barcode():
    """按條碼搜尋商品"""
    try:
        barcode = request.args.get('barcode', '').strip()
        
        if not barcode:
            return jsonify({'success': False, 'error': '條碼不能為空'}), 400
        
        product = BarcodeProduct.query.filter_by(barcode=barcode, is_active=True).first()
        
        if not product:
            return jsonify({'success': False, 'error': '條碼不存在或已停用'}), 404
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_api_bp.route('/list', methods=['GET'])
def get_products():
    """獲取條碼商品列表"""
    try:
        # 獲取篩選參數
        category = request.args.get('category', 'all')
        search = request.args.get('search', '')
        is_active = request.args.get('is_active', 'true')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 構建查詢
        query = BarcodeProduct.query
        
        # 分類篩選
        if category != 'all':
            query = query.filter_by(category=category)
        
        # 搜尋篩選
        if search:
            query = query.filter(
                (BarcodeProduct.barcode.contains(search)) |
                (BarcodeProduct.product_name.contains(search))
            )
        
        # 狀態篩選
        if is_active == 'true':
            query = query.filter_by(is_active=True)
        elif is_active == 'false':
            query = query.filter_by(is_active=False)
        
        # 按更新時間倒序排列
        query = query.order_by(BarcodeProduct.updated_at.desc())
        
        # 分頁
        paginated = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'products': [product.to_dict() for product in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@barcode_api_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """獲取單個商品詳情"""
    try:
        product = BarcodeProduct.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        return jsonify({
            'success': True,
            'product': product.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 條碼新增 ====================

@barcode_api_bp.route('/create', methods=['POST'])
def create_product():
    """新增條碼商品"""
    try:
        data = request.get_json()
        
        # 驗證必要字段
        required_fields = ['barcode', 'product_name', 'category', 'unit_price']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'success': False, 'error': f'缺少必要字段: {field}'}), 400
        
        # 檢查條碼是否已存在
        existing = BarcodeProduct.query.filter_by(barcode=data['barcode']).first()
        if existing:
            return jsonify({'success': False, 'error': '條碼已存在'}), 400
        
        # 創建新商品
        product = BarcodeProduct(
            barcode=data['barcode'],
            product_name=data['product_name'],
            category=data['category'],
            unit_price=float(data['unit_price']),
            storage_condition=data.get('storage_condition', '常溫'),
            description=data.get('description', ''),
            is_active=True
        )
        
        db.session.add(product)
        db.session.commit()
        
        # 記錄操作日誌
        log_operation(
            operation_type='create',
            module='barcode_database',
            action_description=f'新延條碼商品: {data["product_name"]}',
            object_type='BarcodeProduct',
            object_id=product.id,
            object_name=data['product_name'],
            new_value=product.to_dict(),
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': '商品已新延',
            'product': product.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        log_operation(
            operation_type='create',
            module='barcode_database',
            action_description='新延條碼商品失敗',
            status='failure',
            error_message=str(e)
        )
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 條碼更新 ====================

@barcode_api_bp.route('/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """更新條碼商品"""
    try:
        product = BarcodeProduct.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        data = request.get_json()
        
        # 更新允許的字段
        if 'product_name' in data:
            product.product_name = data['product_name']
        if 'category' in data:
            product.category = data['category']
        if 'unit_price' in data:
            product.unit_price = float(data['unit_price'])
        if 'storage_condition' in data:
            product.storage_condition = data['storage_condition']
        if 'description' in data:
            product.description = data['description']
        if 'is_active' in data:
            product.is_active = bool(data['is_active'])
        
        product.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '商品已更新',
            'product': product.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 條碼刪除 ====================

@barcode_api_bp.route('/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """刪除條碼商品（軟刪除）"""
    try:
        product = BarcodeProduct.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'error': '商品不存在'}), 404
        
        # 軟刪除 - 標記為停用
        product.is_active = False
        product.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '商品已刪除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 批量操作 ====================

@barcode_api_bp.route('/batch-import', methods=['POST'])
def batch_import():
    """批量導入條碼商品"""
    try:
        data = request.get_json()
        
        if not isinstance(data.get('products'), list):
            return jsonify({'success': False, 'error': '產品列表格式不正確'}), 400
        
        products_list = data['products']
        created_count = 0
        updated_count = 0
        errors = []
        
        for idx, item in enumerate(products_list):
            try:
                # 驗證必要字段
                if not all(k in item for k in ['barcode', 'product_name', 'category', 'unit_price']):
                    errors.append(f"第 {idx + 1} 行：缺少必要字段")
                    continue
                
                # 檢查條碼是否已存在
                existing = BarcodeProduct.query.filter_by(barcode=item['barcode']).first()
                
                if existing:
                    # 更新現有商品
                    existing.product_name = item['product_name']
                    existing.category = item['category']
                    existing.unit_price = float(item['unit_price'])
                    existing.storage_condition = item.get('storage_condition', '常溫')
                    existing.description = item.get('description', '')
                    existing.is_active = True
                    existing.updated_at = datetime.now()
                    updated_count += 1
                else:
                    # 創建新商品
                    product = BarcodeProduct(
                        barcode=item['barcode'],
                        product_name=item['product_name'],
                        category=item['category'],
                        unit_price=float(item['unit_price']),
                        storage_condition=item.get('storage_condition', '常溫'),
                        description=item.get('description', ''),
                        is_active=True
                    )
                    db.session.add(product)
                    created_count += 1
            except Exception as e:
                errors.append(f"第 {idx + 1} 行：{str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'導入完成：新增 {created_count} 項，更新 {updated_count} 項',
            'created': created_count,
            'updated': updated_count,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 統計 ====================

@barcode_api_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """獲取條碼資料庫統計"""
    try:
        total_products = BarcodeProduct.query.count()
        active_products = BarcodeProduct.query.filter_by(is_active=True).count()
        inactive_products = BarcodeProduct.query.filter_by(is_active=False).count()
        
        # 按分類統計
        category_stats = {}
        for product in BarcodeProduct.query.filter_by(is_active=True).all():
            category = product.category
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
        
        return jsonify({
            'success': True,
            'statistics': {
                'total_products': total_products,
                'active_products': active_products,
                'inactive_products': inactive_products,
                'category_stats': category_stats
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
