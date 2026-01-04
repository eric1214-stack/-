"""
藍牙顯示 API 路由模組
提供食品資訊的 RESTful API 端點，供第二螢幕透過藍牙網路訪問
"""

from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from src.models.food_item import FoodItem, db
import logging

# 創建藍牙 API 藍圖
bluetooth_api = Blueprint('bluetooth_api', __name__, url_prefix='/api')

# 設定日誌
logger = logging.getLogger(__name__)

def calculate_days_remaining(expiry_date):
    """計算距離到期日的剩餘天數"""
    if not expiry_date:
        return None
    
    today = datetime.now().date()
    if isinstance(expiry_date, str):
        expiry_date = datetime.strptime(expiry_date, '%Y-%m-%d').date()
    
    delta = expiry_date - today
    return delta.days

def get_food_status(days_remaining):
    """根據剩餘天數判斷食品狀態"""
    if days_remaining is None:
        return "未知"
    elif days_remaining < 0:
        return "已過期"
    elif days_remaining <= 7:
        return "即將到期"
    elif days_remaining <= 30:
        return "注意"
    else:
        return "正常"

def format_food_item(food_item):
    """將食品項目格式化為 JSON 格式"""
    days_remaining = calculate_days_remaining(food_item.expiry_date)
    status = get_food_status(days_remaining)
    
    return {
        "id": food_item.id,
        "name": food_item.name,
        "category": food_item.category,
        "expiry_date": food_item.expiry_date.strftime('%Y-%m-%d') if food_item.expiry_date else None,
        "quantity": food_item.quantity,
        "unit": food_item.unit,
        "barcode": food_item.barcode,
        "batch_number": food_item.batch_number,
        "notes": food_item.notes or "",
        "image_path": f"/static/uploads/{food_item.image_filename}" if food_item.image_filename else None,
        "days_remaining": days_remaining,
        "status": status
    }

@bluetooth_api.route('/food/all', methods=['GET'])
def get_all_food():
    """獲取所有食品列表"""
    try:
        # 查詢所有食品項目
        food_items = FoodItem.query.all()
        
        # 格式化數據
        formatted_items = [format_food_item(item) for item in food_items]
        
        # 按到期日排序（即將到期的在前）
        formatted_items.sort(key=lambda x: x['days_remaining'] if x['days_remaining'] is not None else float('inf'))
        
        logger.info(f"返回 {len(formatted_items)} 個食品項目")
        return jsonify(formatted_items)
        
    except Exception as e:
        logger.error(f"獲取所有食品時發生錯誤: {str(e)}")
        return jsonify({"error": "獲取食品列表失敗"}), 500

@bluetooth_api.route('/food/expiring', methods=['GET'])
def get_expiring_food():
    """獲取即將到期食品列表（30天內）"""
    try:
        # 獲取查詢參數，預設為30天
        days_threshold = request.args.get('days', 30, type=int)
        
        # 計算截止日期
        cutoff_date = datetime.now().date() + timedelta(days=days_threshold)
        
        # 查詢即將到期的食品
        food_items = FoodItem.query.filter(
            FoodItem.expiry_date <= cutoff_date,
            FoodItem.expiry_date >= datetime.now().date()
        ).all()
        
        # 格式化數據
        formatted_items = [format_food_item(item) for item in food_items]
        
        # 按到期日排序（最快到期的在前）
        formatted_items.sort(key=lambda x: x['days_remaining'] if x['days_remaining'] is not None else float('inf'))
        
        logger.info(f"返回 {len(formatted_items)} 個即將到期的食品項目（{days_threshold}天內）")
        return jsonify(formatted_items)
        
    except Exception as e:
        logger.error(f"獲取即將到期食品時發生錯誤: {str(e)}")
        return jsonify({"error": "獲取即將到期食品列表失敗"}), 500

@bluetooth_api.route('/food/expired', methods=['GET'])
def get_expired_food():
    """獲取已過期食品列表"""
    try:
        # 查詢已過期的食品
        food_items = FoodItem.query.filter(
            FoodItem.expiry_date < datetime.now().date()
        ).all()
        
        # 格式化數據
        formatted_items = [format_food_item(item) for item in food_items]
        
        # 按過期時間排序（最近過期的在前）
        formatted_items.sort(key=lambda x: x['days_remaining'] if x['days_remaining'] is not None else float('-inf'), reverse=True)
        
        logger.info(f"返回 {len(formatted_items)} 個已過期的食品項目")
        return jsonify(formatted_items)
        
    except Exception as e:
        logger.error(f"獲取已過期食品時發生錯誤: {str(e)}")
        return jsonify({"error": "獲取已過期食品列表失敗"}), 500

@bluetooth_api.route('/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """獲取儀表板統計數據"""
    try:
        # 計算總食品數量
        total_food_count = FoodItem.query.count()
        
        # 計算即將到期食品數量（30天內）
        cutoff_date = datetime.now().date() + timedelta(days=30)
        expiring_soon_count = FoodItem.query.filter(
            FoodItem.expiry_date <= cutoff_date,
            FoodItem.expiry_date >= datetime.now().date()
        ).count()
        
        # 計算已過期食品數量
        expired_count = FoodItem.query.filter(
            FoodItem.expiry_date < datetime.now().date()
        ).count()
        
        # 計算各類別食品分佈
        category_stats = db.session.query(
            FoodItem.category,
            db.func.count(FoodItem.id).label('count')
        ).group_by(FoodItem.category).all()
        
        category_distribution = [
            {"category": stat.category, "count": stat.count}
            for stat in category_stats
        ]
        
        # 組裝統計數據
        stats = {
            "total_food_count": total_food_count,
            "expiring_soon_count": expiring_soon_count,
            "expired_count": expired_count,
            "category_distribution": category_distribution
        }
        
        logger.info(f"返回儀表板統計數據: 總計 {total_food_count}, 即將到期 {expiring_soon_count}, 已過期 {expired_count}")
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"獲取儀表板統計數據時發生錯誤: {str(e)}")
        return jsonify({"error": "獲取統計數據失敗"}), 500

@bluetooth_api.route('/food/<int:food_id>', methods=['GET'])
def get_food_detail(food_id):
    """獲取特定食品的詳細資訊"""
    try:
        food_item = FoodItem.query.get_or_404(food_id)
        formatted_item = format_food_item(food_item)
        
        logger.info(f"返回食品詳細資訊: ID {food_id}")
        return jsonify(formatted_item)
        
    except Exception as e:
        logger.error(f"獲取食品詳細資訊時發生錯誤: {str(e)}")
        return jsonify({"error": "獲取食品詳細資訊失敗"}), 404

@bluetooth_api.route('/food/category/<category>', methods=['GET'])
def get_food_by_category(category):
    """根據類別獲取食品列表"""
    try:
        food_items = FoodItem.query.filter_by(category=category).all()
        formatted_items = [format_food_item(item) for item in food_items]
        
        # 按到期日排序
        formatted_items.sort(key=lambda x: x['days_remaining'] if x['days_remaining'] is not None else float('inf'))
        
        logger.info(f"返回類別 '{category}' 的 {len(formatted_items)} 個食品項目")
        return jsonify(formatted_items)
        
    except Exception as e:
        logger.error(f"根據類別獲取食品時發生錯誤: {str(e)}")
        return jsonify({"error": f"獲取類別 '{category}' 食品列表失敗"}), 500

@bluetooth_api.route('/health', methods=['GET'])
def health_check():
    """健康檢查端點"""
    return jsonify({
        "status": "healthy",
        "service": "食品效期管理系統藍牙 API",
        "timestamp": datetime.now().isoformat()
    })

# 錯誤處理
@bluetooth_api.errorhandler(404)
def not_found(error):
    return jsonify({"error": "資源未找到"}), 404

@bluetooth_api.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "內部伺服器錯誤"}), 500

