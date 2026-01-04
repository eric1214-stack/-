"""
入庫/出庫記錄管理API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta, date
from src.models.food_item import db, FoodItem
from src.models.inventory_record import InventoryRecord
from src.routes.operation_log_api import log_operation

inventory_record_bp = Blueprint('inventory_record', __name__, url_prefix='/api/inventory-records')

# ==================== 記錄查詢 ====================

@inventory_record_bp.route('/list', methods=['GET'])
def get_records():
    """獲取入庫/出庫記錄列表"""
    try:
        # 獲取篩選參數
        record_type = request.args.get('record_type', 'all')  # all, inbound, outbound
        operation_type = request.args.get('operation_type', 'all')
        category = request.args.get('category', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 構建查詢
        query = InventoryRecord.query
        
        # 記錄類型篩選
        if record_type != 'all':
            query = query.filter_by(record_type=record_type)
        
        # 操作類型篩選
        if operation_type != 'all':
            query = query.filter_by(operation_type=operation_type)
        
        # 分類篩選
        if category != 'all':
            query = query.filter_by(category=category)
        
        # 日期範圍篩選
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryRecord.record_date >= start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(InventoryRecord.record_date < end_datetime)
        
        # 按時間倒序排列
        query = query.order_by(InventoryRecord.record_date.desc())
        
        # 分頁
        paginated = query.paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'records': [record.to_dict() for record in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_record_bp.route('/<int:record_id>', methods=['GET'])
def get_record(record_id):
    """獲取單個記錄詳情"""
    try:
        record = InventoryRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': '記錄不存在'}), 404
        
        return jsonify({
            'success': True,
            'record': record.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 記錄創建 ====================

@inventory_record_bp.route('/create-inbound', methods=['POST'])
def create_inbound_record():
    """創建入庫記錄"""
    try:
        data = request.get_json()
        
        # 驗證必要字段
        required_fields = ['product_name', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                return jsonify({'success': False, 'error': f'缺少必要字段: {field}'}), 400
        
        # 安全地轉換數值字段
        try:
            quantity = float(data['quantity'])
            if quantity <= 0:
                return jsonify({'success': False, 'error': '數量必須大於0'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '數量格式錯誤，必須為數字'}), 400
        
        try:
            unit_price = float(data['unit_price'])
            if unit_price < 0:
                return jsonify({'success': False, 'error': '單價不能為負數'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '單價格式錯誤，必須為數字'}), 400
        
        food_item_id = data.get('food_item_id')
        barcode = data.get('barcode', '')
        operator = data.get('operator', 'system')
        operation_type = data.get('operation_type', 'purchase')
        
        # 查找或創建 FoodItem
        food_item = None
        is_new_item = False
        
        if food_item_id:
            food_item = FoodItem.query.get(food_item_id)
        elif barcode:
            food_item = FoodItem.query.filter_by(barcode=barcode).first()
        
        # 如果找不到 FoodItem，創建新的
        if not food_item:
            food_item = FoodItem(
                name=data['product_name'],
                barcode=barcode if barcode else None,
                category=data.get('category', '其他'),
                quantity=quantity,
                unit=data.get('unit', '個'),
                storage_location=data.get('storage_location', ''),
                storage_condition=data.get('storage_condition', '常溫'),
                unit_price=unit_price,
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else datetime.now().date(),
                item_status='在庫',
                ai_check_status='Pass'
            )
            db.session.add(food_item)
            db.session.flush()  # 獲取 ID 但不提交
            food_item_id = food_item.id
            is_new_item = True
            old_quantity = 0
        else:
            # 如果找到 FoodItem，更新庫存數量
            old_quantity = food_item.quantity or 0
            food_item.quantity = old_quantity + quantity
            # 更新其他可能變更的字段
            if data.get('storage_location'):
                food_item.storage_location = data['storage_location']
            if data.get('storage_condition'):
                food_item.storage_condition = data['storage_condition']
            if data.get('unit_price') is not None:
                try:
                    food_item.unit_price = float(data['unit_price'])
                except (ValueError, TypeError):
                    pass  # 如果轉換失敗，保持原值
            if data.get('expiry_date'):
                food_item.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            food_item.updated_at = datetime.now()
            # 確保 food_item_id 與記錄一致
            food_item_id = food_item.id
        
        # 創建記錄
        record = InventoryRecord.create_inbound_record(
            food_item_id=food_item_id,
            barcode=barcode,
            product_name=data['product_name'],
            category=data.get('category', '其他'),
            quantity=quantity,
            unit=data.get('unit', '個'),
            unit_price=unit_price,
            storage_location=data.get('storage_location', ''),
            storage_condition=data.get('storage_condition', '常溫'),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            operator=operator,
            notes=data.get('notes', ''),
            operation_type=operation_type
        )
        
        db.session.add(record)
        db.session.commit()
        
        # 記錄操作日誌（包含詳細信息）
        operation_type_name = {
            'purchase': '採購入庫',
            'return': '退貨入庫',
            'adjustment': '調整入庫'
        }.get(operation_type, '入庫')
        
        log_description = f'{operation_type_name}: {data["product_name"]}, 數量: +{quantity} {data.get("unit", "個")}'
        if food_item and old_quantity is not None:
            log_description += f', 庫存: {old_quantity} → {food_item.quantity}'
        
        log_operation(
            operation_type='create',
            module='inventory_record',
            action_description=log_description,
            object_type='InventoryRecord',
            object_id=record.id,
            object_name=data['product_name'],
            old_value={'quantity': old_quantity} if old_quantity is not None else None,
            new_value={'quantity': food_item.quantity if food_item else None, 'record': record.to_dict()},
            user_name=operator,
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': '入庫記錄已創建',
            'record': record.to_dict(),
            'food_item_updated': food_item is not None,
            'new_quantity': food_item.quantity if food_item else None
        }), 201
    except Exception as e:
        db.session.rollback()
        log_operation(
            operation_type='create',
            module='inventory_record',
            action_description='創建入庫記錄失敗',
            status='failure',
            error_message=str(e),
            user_name=data.get('operator', 'system')
        )
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_record_bp.route('/create-outbound', methods=['POST'])
def create_outbound_record():
    """創建出庫記錄"""
    try:
        data = request.get_json()
        
        # 驗證必要字段
        required_fields = ['product_name', 'quantity', 'unit_price']
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                return jsonify({'success': False, 'error': f'缺少必要字段: {field}'}), 400
        
        # 安全地轉換數值字段
        try:
            quantity = float(data['quantity'])
            if quantity <= 0:
                return jsonify({'success': False, 'error': '數量必須大於0'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '數量格式錯誤，必須為數字'}), 400
        
        try:
            unit_price = float(data['unit_price'])
            if unit_price < 0:
                return jsonify({'success': False, 'error': '單價不能為負數'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '單價格式錯誤，必須為數字'}), 400
        
        try:
            discount_rate = float(data.get('discount_rate', 0))
            if discount_rate < 0 or discount_rate > 1:
                return jsonify({'success': False, 'error': '折扣率必須在0-1之間'}), 400
        except (ValueError, TypeError):
            discount_rate = 0.0
        
        food_item_id = data.get('food_item_id')
        barcode = data.get('barcode', '')
        operator = data.get('operator', 'system')
        operation_type = data.get('operation_type', 'sale')
        
        # 查找 FoodItem
        food_item = None
        is_new_item = False
        
        if food_item_id:
            food_item = FoodItem.query.get(food_item_id)
        elif barcode:
            food_item = FoodItem.query.filter_by(barcode=barcode).first()
        
        # 如果找不到 FoodItem，創建新的（出庫時創建新商品的情況較少，但為了同步還是要創建）
        if not food_item:
            # 出庫時創建新商品，初始數量為0，然後扣除
            food_item = FoodItem(
                name=data['product_name'],
                barcode=barcode if barcode else None,
                category=data.get('category', '其他'),
                quantity=0,  # 新商品初始數量為0
                unit=data.get('unit', '個'),
                storage_location=data.get('storage_location', ''),
                storage_condition=data.get('storage_condition', '常溫'),
                unit_price=unit_price,
                expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else datetime.now().date(),
                item_status='已售',  # 出庫時創建的商品直接標記為已售
                ai_check_status='Pass'
            )
            db.session.add(food_item)
            db.session.flush()  # 獲取 ID 但不提交
            food_item_id = food_item.id
            is_new_item = True
            old_quantity = 0
            # 出庫時創建新商品，數量會是負數，但我們允許這種情況
        else:
            # 如果找到 FoodItem，檢查庫存並更新數量
            old_quantity = food_item.quantity or 0
            # 檢查庫存是否足夠
            if old_quantity < quantity:
                return jsonify({
                    'success': False,
                    'error': f'庫存不足：當前庫存 {old_quantity} {food_item.unit}，出庫數量 {quantity} {data.get("unit", "個")}'
                }), 400
            
            food_item.quantity = old_quantity - quantity
            # 如果庫存為0，可以選擇更新狀態
            if food_item.quantity <= 0:
                food_item.item_status = '已售'
            food_item.updated_at = datetime.now()
            # 確保 food_item_id 與記錄一致
            food_item_id = food_item.id
        
        # 創建記錄
        record = InventoryRecord.create_outbound_record(
            food_item_id=food_item_id,
            barcode=barcode,
            product_name=data['product_name'],
            category=data.get('category', '其他'),
            quantity=quantity,
            unit=data.get('unit', '個'),
            unit_price=unit_price,
            discount_rate=discount_rate,
            storage_location=data.get('storage_location', ''),
            storage_condition=data.get('storage_condition', '常溫'),
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None,
            operator=operator,
            notes=data.get('notes', ''),
            operation_type=operation_type
        )
        
        db.session.add(record)
        db.session.commit()
        
        # 記錄操作日誌（包含詳細信息）
        operation_type_name = {
            'sale': '銷售出庫',
            'damage': '損壞出庫',
            'expiry': '過期出庫',
            'adjustment': '調整出庫'
        }.get(operation_type, '出庫')
        
        log_description = f'{operation_type_name}: {data["product_name"]}, 數量: -{quantity} {data.get("unit", "個")}'
        if food_item and old_quantity is not None:
            log_description += f', 庫存: {old_quantity} → {food_item.quantity}'
        
        log_operation(
            operation_type='create',
            module='inventory_record',
            action_description=log_description,
            object_type='InventoryRecord',
            object_id=record.id,
            object_name=data['product_name'],
            old_value={'quantity': old_quantity} if old_quantity is not None else None,
            new_value={'quantity': food_item.quantity if food_item else None, 'record': record.to_dict()},
            user_name=operator,
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': '出庫記錄已創建',
            'record': record.to_dict(),
            'food_item_updated': food_item is not None,
            'new_quantity': food_item.quantity if food_item else None
        }), 201
    except Exception as e:
        db.session.rollback()
        log_operation(
            operation_type='create',
            module='inventory_record',
            action_description='創建出庫記錄失敗',
            status='failure',
            error_message=str(e),
            user_name=data.get('operator', 'system')
        )
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 記錄更新 ====================

@inventory_record_bp.route('/<int:record_id>', methods=['PUT'])
def update_record(record_id):
    """更新記錄"""
    try:
        record = InventoryRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': '記錄不存在'}), 404
        
        data = request.get_json()
        
        # 更新允許的字段
        if 'notes' in data:
            record.notes = data['notes']
        if 'status' in data:
            record.status = data['status']
        if 'operator' in data:
            record.operator = data['operator']
        
        record.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '記錄已更新',
            'record': record.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 記錄刪除 ====================

@inventory_record_bp.route('/<int:record_id>', methods=['DELETE'])
def delete_record(record_id):
    """刪除記錄（標記為已取消）"""
    try:
        record = InventoryRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': '記錄不存在'}), 404
        
        # 軟刪除 - 標記為已取消
        record.status = 'cancelled'
        record.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '記錄已刪除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== 統計分析 ====================

@inventory_record_bp.route('/statistics/summary', methods=['GET'])
def get_summary_statistics():
    """獲取統計摘要"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 構建查詢
        query = InventoryRecord.query.filter_by(status='completed')
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryRecord.record_date >= start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(InventoryRecord.record_date < end_datetime)
        
        # 計算統計數據
        inbound_records = query.filter_by(record_type='inbound').all()
        outbound_records = query.filter_by(record_type='outbound').all()
        
        inbound_quantity = sum(r.quantity for r in inbound_records)
        inbound_amount = sum(r.total_price for r in inbound_records)
        
        outbound_quantity = sum(r.quantity for r in outbound_records)
        outbound_amount = sum(r.total_price for r in outbound_records)
        
        return jsonify({
            'success': True,
            'summary': {
                'inbound': {
                    'count': len(inbound_records),
                    'quantity': inbound_quantity,
                    'amount': round(inbound_amount, 2)
                },
                'outbound': {
                    'count': len(outbound_records),
                    'quantity': outbound_quantity,
                    'amount': round(outbound_amount, 2)
                },
                'net_quantity': inbound_quantity - outbound_quantity,
                'net_amount': round(inbound_amount - outbound_amount, 2)
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_record_bp.route('/statistics/by-category', methods=['GET'])
def get_category_statistics():
    """按分類統計"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 構建查詢
        query = InventoryRecord.query.filter_by(status='completed')
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryRecord.record_date >= start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(InventoryRecord.record_date < end_datetime)
        
        records = query.all()
        
        # 按分類分組統計
        category_stats = {}
        for record in records:
            category = record.category or '其他'
            if category not in category_stats:
                category_stats[category] = {
                    'inbound_quantity': 0,
                    'inbound_amount': 0,
                    'outbound_quantity': 0,
                    'outbound_amount': 0
                }
            
            if record.record_type == 'inbound':
                category_stats[category]['inbound_quantity'] += record.quantity
                category_stats[category]['inbound_amount'] += record.total_price
            else:
                category_stats[category]['outbound_quantity'] += record.quantity
                category_stats[category]['outbound_amount'] += record.total_price
        
        # 計算淨值
        for category in category_stats:
            stats = category_stats[category]
            stats['net_quantity'] = stats['inbound_quantity'] - stats['outbound_quantity']
            stats['net_amount'] = round(stats['inbound_amount'] - stats['outbound_amount'], 2)
            stats['inbound_amount'] = round(stats['inbound_amount'], 2)
            stats['outbound_amount'] = round(stats['outbound_amount'], 2)
        
        return jsonify({
            'success': True,
            'statistics': category_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_record_bp.route('/statistics/by-operation', methods=['GET'])
def get_operation_statistics():
    """按操作類型統計"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 構建查詢
        query = InventoryRecord.query.filter_by(status='completed')
        
        if start_date:
            start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(InventoryRecord.record_date >= start_datetime)
        
        if end_date:
            end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(InventoryRecord.record_date < end_datetime)
        
        records = query.all()
        
        # 按操作類型分組統計
        operation_stats = {}
        for record in records:
            op_type = record.operation_type
            if op_type not in operation_stats:
                operation_stats[op_type] = {
                    'count': 0,
                    'quantity': 0,
                    'amount': 0
                }
            
            operation_stats[op_type]['count'] += 1
            operation_stats[op_type]['quantity'] += record.quantity
            operation_stats[op_type]['amount'] += record.total_price
        
        # 四捨五入金額
        for op_type in operation_stats:
            operation_stats[op_type]['amount'] = round(operation_stats[op_type]['amount'], 2)
        
        return jsonify({
            'success': True,
            'statistics': operation_stats
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_record_bp.route('/statistics/daily', methods=['GET'])
def get_daily_statistics():
    """按日期統計"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # 默認查詢最近30天
        if not end_date:
            end_date = date.today().strftime('%Y-%m-%d')
        if not start_date:
            start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # 構建查詢
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        
        query = InventoryRecord.query.filter_by(status='completed').filter(
            InventoryRecord.record_date >= start_datetime,
            InventoryRecord.record_date < end_datetime
        )
        
        records = query.all()
        
        # 按日期分組統計
        daily_stats = {}
        for record in records:
            day = record.record_date.strftime('%Y-%m-%d')
            if day not in daily_stats:
                daily_stats[day] = {
                    'inbound_quantity': 0,
                    'inbound_amount': 0,
                    'outbound_quantity': 0,
                    'outbound_amount': 0
                }
            
            if record.record_type == 'inbound':
                daily_stats[day]['inbound_quantity'] += record.quantity
                daily_stats[day]['inbound_amount'] += record.total_price
            else:
                daily_stats[day]['outbound_quantity'] += record.quantity
                daily_stats[day]['outbound_amount'] += record.total_price
        
        # 計算淨值並排序
        result = []
        for day in sorted(daily_stats.keys()):
            stats = daily_stats[day]
            result.append({
                'date': day,
                'inbound_quantity': stats['inbound_quantity'],
                'inbound_amount': round(stats['inbound_amount'], 2),
                'outbound_quantity': stats['outbound_quantity'],
                'outbound_amount': round(stats['outbound_amount'], 2),
                'net_quantity': stats['inbound_quantity'] - stats['outbound_quantity'],
                'net_amount': round(stats['inbound_amount'] - stats['outbound_amount'], 2)
            })
        
        return jsonify({
            'success': True,
            'statistics': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
