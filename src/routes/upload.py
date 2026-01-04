"""
圖片上傳與辨識API路由
"""

import os
import uuid
import json
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from src.models.recognition.food_recognition import FoodRecognitionSystem
from src.models.food_item import db, FoodItem
from src.models.inventory_record import InventoryRecord
from src.routes.operation_log_api import log_operation

# 創建藍圖
upload_bp = Blueprint('upload', __name__)

# 初始化辨識系統
recognition_system = FoodRecognitionSystem()

# 允許的圖片格式
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

def allowed_file(filename):
    """檢查檔案是否為允許的格式"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@upload_bp.route('/api/upload', methods=['POST'])
def upload_images():
    """
    批量上傳圖片API
    接收多個圖片檔案，返回每個圖片的上傳結果
    """
    # 檢查是否有檔案上傳
    if 'files[]' not in request.files:
        return jsonify({'error': '沒有上傳檔案'}), 400
    
    files = request.files.getlist('files[]')
    
    # 檢查是否有選擇檔案
    if not files or files[0].filename == '':
        return jsonify({'error': '沒有選擇檔案'}), 400
    
    # 準備結果列表
    results = []
    
    # 創建上傳目錄
    upload_folder = os.path.join(current_app.static_folder, 'uploads')
    os.makedirs(upload_folder, exist_ok=True)
    
    # 處理每個上傳的檔案
    for file in files:
        if file and allowed_file(file.filename):
            # 安全地獲取檔案名
            filename = secure_filename(file.filename)
            
            # 生成唯一的檔案名以避免衝突
            unique_filename = f"{uuid.uuid4()}_{filename}"
            file_path = os.path.join(upload_folder, unique_filename)
            
            # 保存檔案
            file.save(file_path)
            
            # 構建結果
            result = {
                'success': True,
                'original_filename': filename,
                'saved_filename': unique_filename,
                'image_path': f"/static/uploads/{unique_filename}"
            }
            
            # 添加到結果列表
            results.append(result)
        else:
            # 不支援的檔案類型
            results.append({
                'success': False,
                'original_filename': file.filename,
                'error': '不支援的檔案類型'
            })
    
    # 返回所有結果
    return jsonify({'results': results})

@upload_bp.route('/api/recognize', methods=['POST'])
def recognize_images():
    """
    批量辨識圖片API
    接收圖片路徑列表，返回每個圖片的辨識結果
    """
    # 獲取請求數據
    data = request.json
    
    if not data or 'images' not in data:
        return jsonify({'error': '沒有提供圖片路徑'}), 400
    
    image_paths = data['images']
    
    if not image_paths:
        return jsonify({'error': '圖片路徑列表為空'}), 400
    
    # 準備絕對路徑列表
    absolute_paths = []
    for image_path in image_paths:
        # 確保路徑是絕對路徑
        if image_path.startswith('/static/'):
            absolute_path = os.path.join(current_app.root_path, image_path.lstrip('/'))
        else:
            absolute_path = image_path
        absolute_paths.append(absolute_path)
    
    # 使用批量處理方法，保持原始順序
    results = recognition_system.process_images_batch(absolute_paths)
    
    # 確保結果與原始圖片路徑對應
    for i, result in enumerate(results):
        result['image_path'] = image_paths[i]
    
    # 返回所有結果
    return jsonify({'results': results})

@upload_bp.route('/api/delete-image', methods=['POST'])
def delete_image():
    """
    刪除圖片API
    接收圖片路徑，刪除對應的圖片檔案
    """
    # 獲取請求數據
    data = request.json
    
    if not data or 'image_path' not in data:
        return jsonify({'error': '沒有提供圖片路徑'}), 400
    
    image_path = data['image_path']
    
    # 確保路徑是絕對路徑
    if image_path.startswith('/static/'):
        absolute_path = os.path.join(current_app.root_path, image_path.lstrip('/'))
    else:
        absolute_path = image_path
    
    # 檢查檔案是否存在
    if not os.path.exists(absolute_path):
        return jsonify({'error': '圖片不存在'}), 404
    
    try:
        # 刪除檔案
        os.remove(absolute_path)
        
        # 如果有關聯的食品資料，更新圖片路徑為空
        food_items = FoodItem.query.filter_by(image_path=image_path).all()
        for item in food_items:
            item.image_path = None
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': '圖片已成功刪除'})
    except Exception as e:
        return jsonify({'error': f'刪除圖片時發生錯誤: {str(e)}'}), 500

@upload_bp.route('/api/save-food', methods=['POST'])
def save_food():
    """
    保存食品資料API
    接收食品資料，新增或更新資料庫記錄
    """
    # 獲取請求數據
    data = request.json
    
    if not data:
        return jsonify({'error': '沒有提供食品資料'}), 400
    
    try:
        # 檢查是否為更新操作
        is_new_item = False
        old_quantity = None
        
        if 'id' in data and data['id']:
            # 更新現有記錄
            food_item = FoodItem.query.get(data['id'])
            if not food_item:
                return jsonify({'error': f"找不到ID為{data['id']}的食品記錄"}), 404
            old_quantity = food_item.quantity
        else:
            # 新增記錄
            food_item = FoodItem()
            is_new_item = True
            old_quantity = 0
        
        # 更新資料
        food_item.barcode = data.get('barcode')
        food_item.name = data.get('name')
        
        # 處理日期格式
        if 'expiry_date' in data and data['expiry_date']:
            try:
                food_item.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': '無效的日期格式，請使用YYYY-MM-DD'}), 400
        elif is_new_item:
            # 新增時如果沒有提供日期，使用今天
            food_item.expiry_date = datetime.now().date()
        
        food_item.batch_number = data.get('batch_number')
        food_item.image_path = data.get('image_path')
        food_item.notes = data.get('notes')
        
        # 新增欄位：分類、數量、單位
        food_item.category = data.get('category', '其他')
        
        # 處理數量，確保為浮點數
        try:
            if 'quantity' in data and data['quantity']:
                food_item.quantity = float(data['quantity'])
            elif is_new_item:
                food_item.quantity = 1.0
        except (ValueError, TypeError):
            food_item.quantity = 1.0 if is_new_item else (old_quantity or 1.0)
            
        food_item.unit = data.get('unit', '個')
        
        # 新增欄位：儲存環境、單價、儲存位置
        food_item.storage_condition = data.get('storage_condition', '常溫')
        
        # 處理單價，確保為浮點數
        try:
            if 'unit_price' in data and data['unit_price']:
                food_item.unit_price = float(data['unit_price'])
            elif is_new_item:
                food_item.unit_price = 0.0
        except (ValueError, TypeError):
            food_item.unit_price = 0.0
        
        food_item.storage_location = data.get('storage_location', '')
        
        # 如果沒有設置狀態，設置默認狀態
        if is_new_item and not food_item.item_status:
            food_item.item_status = '在庫'
        if is_new_item and not food_item.ai_check_status:
            food_item.ai_check_status = 'Pass'
        
        # 保存到資料庫
        db.session.add(food_item)
        db.session.flush()  # 先獲取 ID
        
        # 如果是新增食品，自動創建對應的入庫記錄
        if is_new_item:
            quantity = food_item.quantity or 1.0
            record = InventoryRecord.create_inbound_record(
                food_item_id=food_item.id,
                barcode=food_item.barcode or '',
                product_name=food_item.name,
                category=food_item.category,
                quantity=quantity,
                unit=food_item.unit,
                unit_price=food_item.unit_price or 0.0,
                storage_location=food_item.storage_location or '',
                storage_condition=food_item.storage_condition or '常溫',
                expiry_date=food_item.expiry_date,
                operator='system',
                notes=f'從主頁新增食品：{food_item.notes or ""}',
                operation_type='purchase'
            )
            db.session.add(record)
            
            # 記錄操作日誌
            log_operation(
                operation_type='create',
                module='food_item',
                action_description=f'新增食品並創建入庫記錄: {food_item.name}, 數量: {quantity} {food_item.unit}',
                object_type='FoodItem',
                object_id=food_item.id,
                object_name=food_item.name,
                new_value={'quantity': quantity, 'record_id': record.id},
                status='success'
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '食品資料已成功保存',
            'food_item': food_item.to_dict(),
            'inventory_record_created': is_new_item
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'保存食品資料時發生錯誤: {str(e)}'}), 500

@upload_bp.route('/api/delete-food/<int:food_id>', methods=['DELETE'])
def delete_food(food_id):
    """
    刪除食品資料API
    接收食品ID，刪除對應的資料庫記錄
    """
    try:
        # 查找記錄
        food_item = FoodItem.query.get(food_id)
        
        if not food_item:
            return jsonify({'error': f"找不到ID為{food_id}的食品記錄"}), 404
        
        # 刪除記錄
        db.session.delete(food_item)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '食品資料已成功刪除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'刪除食品資料時發生錯誤: {str(e)}'}), 500

@upload_bp.route("/api/foods/delete", methods=["POST"])
def delete_multiple_foods():
    """
    批量刪除食品資料API
    接收食品ID列表，刪除對應的資料庫記錄
    """
    data = request.json
    if not data or "ids" not in data or not isinstance(data["ids"], list):
        return jsonify({"error": "請提供有效的食品ID列表"}), 400

    food_ids_to_delete = data["ids"]
    deleted_count = 0
    errors = []

    try:
        for food_id in food_ids_to_delete:
            # 確保 ID 是整數
            try:
                food_id = int(food_id)
            except ValueError:
                errors.append(f"無效的食品ID: {food_id}")
                continue

            food_item = FoodItem.query.get(food_id)
            if food_item:
                db.session.delete(food_item)
                deleted_count += 1
            else:
                errors.append(f"找不到ID為{food_id}的食品記錄")
        
        db.session.commit()
        
        if errors:
            # 即使有錯誤，也返回 200，並在訊息中說明
            return jsonify({"success": False, "message": f"部分食品刪除失敗: {', '.join(errors)}", "deleted_count": deleted_count}), 200
        else:
            return jsonify({"success": True, "message": f"成功刪除{deleted_count}個食品項目"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": f"批量刪除食品資料時發生錯誤: {str(e)}"}), 500

@upload_bp.route("/api/foods", methods=["GET"])
def get_food_list():
    """
    獲取食品列表API
    返回所有食品資料
    """
    try:
        # 查詢所有記錄
        food_items = FoodItem.query.all()
        
        # 轉換為字典列表
        result = [item.to_dict() for item in food_items]
        
        return jsonify({
            'success': True,
            'food_items': result
        })
    except Exception as e:
        return jsonify({'error': f'獲取食品列表時發生錯誤: {str(e)}'}), 500

@upload_bp.route('/api/expiring-food', methods=['GET'])
def get_expiring_food():
    """
    獲取即將到期食品列表API
    返回30天內到期的食品資料以及已過期的食品
    """
    try:
        from datetime import timedelta
        
        # 計算30天後的日期
        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        # 查詢30天內到期的記錄以及已過期的記錄
        # 移除 FoodItem.expiry_date >= today 條件，使已過期食品也能顯示
        food_items = FoodItem.query.filter(
            FoodItem.expiry_date <= thirty_days_later
        ).order_by(FoodItem.expiry_date).all()
        
        # 轉換為字典列表
        result = [item.to_dict() for item in food_items]
        
        return jsonify({
            'success': True,
            'food_items': result
        })
    except Exception as e:
        return jsonify({'error': f'獲取即將到期食品列表時發生錯誤: {str(e)}'}), 500

@upload_bp.route('/api/food-stats', methods=['GET'])
def get_food_stats():
    """
    獲取食品統計數據API
    返回總食品數量、即將到期數量和已過期數量
    """
    try:
        from datetime import timedelta
        
        # 計算當前日期和30天後的日期
        today = datetime.now().date()
        thirty_days_later = today + timedelta(days=30)
        
        # 查詢總食品數量
        total_count = FoodItem.query.count()
        
        # 查詢即將到期數量（30天內到期且未過期，含今天）
        expiring_count = FoodItem.query.filter(
            FoodItem.expiry_date >= today,
            FoodItem.expiry_date <= thirty_days_later
        ).count()
        
        # 查詢已過期數量
        expired_count = FoodItem.query.filter(
            FoodItem.expiry_date < today
        ).count()
        
        # 按分類統計數量
        category_stats = db.session.query(
            FoodItem.category, 
            db.func.count(FoodItem.id)
        ).group_by(FoodItem.category).all()
        
        category_counts = {category: count for category, count in category_stats}
        
        return jsonify({
            'success': True,
            'stats': {
                'total_count': total_count,
                'expiring_count': expiring_count,
                'expired_count': expired_count,
                'category_counts': category_counts
            }
        })
    except Exception as e:
        return jsonify({'error': f'獲取食品統計數據時發生錯誤: {str(e)}'}), 500
