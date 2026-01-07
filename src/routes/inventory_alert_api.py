"""
庫存預警系統API路由
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from src.models.food_item import db, FoodItem
from src.models.inventory_alert import InventoryAlert, InventoryAlertLog
from src.routes.operation_log_api import log_operation

# 創建藍圖
inventory_alert_bp = Blueprint('inventory_alert', __name__)


@inventory_alert_bp.route('/api/inventory-alerts', methods=['GET'])
def get_all_alerts():
    """
    獲取所有庫存預警設定
    """
    try:
        alerts = InventoryAlert.query.all()
        return jsonify({
            'success': True,
            'alerts': [alert.to_dict() for alert in alerts],
            'total': len(alerts)
        })
    except Exception as e:
        return jsonify({'error': f'獲取預警設定失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/<int:alert_id>', methods=['GET'])
def get_alert(alert_id):
    """
    獲取單個庫存預警設定
    """
    try:
        alert = InventoryAlert.query.get(alert_id)
        if not alert:
            return jsonify({'error': '預警設定不存在'}), 404
        
        return jsonify({
            'success': True,
            'alert': alert.to_dict()
        })
    except Exception as e:
        return jsonify({'error': f'獲取預警設定失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/create', methods=['POST'])
def create_alert():
    """
    創建庫存預警設定
    """
    try:
        data = request.json
        
        # 檢查必填欄位
        if not data.get('product_name'):
            return jsonify({'error': '商品名稱不能為空'}), 400
        
        # 檢查是否已存在
        existing = InventoryAlert.query.filter_by(
            product_name=data['product_name']
        ).first()
        
        if existing:
            return jsonify({'error': '該商品的預警設定已存在'}), 400
        
        # 創建新預警設定
        alert = InventoryAlert(
            product_name=data['product_name'],
            barcode=data.get('barcode'),
            category=data.get('category'),
            min_quantity=float(data.get('min_quantity', 10.0)),
            alert_threshold=float(data.get('alert_threshold', 5.0)),
            reorder_quantity=float(data.get('reorder_quantity', 50.0)),
            is_active=data.get('is_active', True)
        )
        
        db.session.add(alert)
        db.session.commit()
        
        # 記錄操作日誌
        log_operation(
            operation_type='create',
            module='inventory_alert',
            action_description=f'創建庫存預警: {data["product_name"]}',
            object_type='InventoryAlert',
            object_id=alert.id,
            object_name=data['product_name'],
            new_value=alert.to_dict(),
            status='success'
        )
        
        return jsonify({
            'success': True,
            'message': '預警設定已創建',
            'alert': alert.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        log_operation(
            operation_type='create',
            module='inventory_alert',
            action_description='創建庫存預警失敗',
            status='failure',
            error_message=str(e)
        )
        return jsonify({'error': f'創建預警設定失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/<int:alert_id>/update', methods=['POST'])
def update_alert(alert_id):
    """
    更新庫存預警設定
    """
    try:
        alert = InventoryAlert.query.get(alert_id)
        if not alert:
            return jsonify({'error': '預警設定不存在'}), 404
        
        data = request.json
        
        # 更新欄位
        if 'product_name' in data:
            alert.product_name = data['product_name']
        if 'barcode' in data:
            alert.barcode = data['barcode']
        if 'category' in data:
            alert.category = data['category']
        if 'min_quantity' in data:
            alert.min_quantity = float(data['min_quantity'])
        if 'alert_threshold' in data:
            alert.alert_threshold = float(data['alert_threshold'])
        if 'reorder_quantity' in data:
            alert.reorder_quantity = float(data['reorder_quantity'])
        if 'is_active' in data:
            alert.is_active = data['is_active']
        
        alert.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '預警設定已更新',
            'alert': alert.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新預警設定失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/<int:alert_id>/delete', methods=['DELETE'])
def delete_alert(alert_id):
    """
    刪除庫存預警設定
    """
    try:
        alert = InventoryAlert.query.get(alert_id)
        if not alert:
            return jsonify({'error': '預警設定不存在'}), 404
        
        db.session.delete(alert)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '預警設定已刪除'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'刪除預警設定失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/check', methods=['POST'])
def check_inventory_alerts():
    """
    檢查所有庫存預警
    返回當前需要預警的商品列表
    """
    try:
        alerts = InventoryAlert.query.filter_by(is_active=True).all()
        triggered_alerts = []
        
        for alert in alerts:
            # 查詢該商品的當前庫存
            food_items = FoodItem.query.filter_by(
                name=alert.product_name
            ).all()
            
            current_quantity = sum(item.quantity for item in food_items)
            
            # 判斷預警狀態
            alert_status = InventoryAlert.STATUS_NORMAL
            alert_level = None
            
            if current_quantity <= alert.alert_threshold:
                alert_status = InventoryAlert.STATUS_CRITICAL
                alert_level = 'critical'
            elif current_quantity <= alert.min_quantity:
                alert_status = InventoryAlert.STATUS_WARNING
                alert_level = 'warning'
            
            # 如果狀態改變，更新預警設定
            old_alert_status = alert.alert_status # 儲存舊的預警狀態

            # 總是更新 alert.alert_status 以反映當前狀態
            alert.alert_status = alert_status

            # 如果處於預警狀態 (非正常)，則更新最後預警時間
            if alert_level:
                alert.last_alert_time = datetime.now()
                
            # 只有當預警狀態發生變化且處於非正常狀態時才記錄預警日誌
            if alert_status != old_alert_status and alert_level:
                log = InventoryAlertLog(
                    alert_id=alert.id,
                    product_name=alert.product_name,
                    barcode=alert.barcode,
                    current_quantity=current_quantity,
                    min_quantity=alert.min_quantity,
                    alert_threshold=alert.alert_threshold,
                    alert_level=alert_level,
                    alert_message=f"{alert.product_name}庫存不足！當前庫存：{current_quantity}，最低庫存：{alert.min_quantity}"
                )
                db.session.add(log)

            
            # 添加到觸發列表
            if alert_level:
                triggered_alerts.append({
                    'alert': alert.to_dict(),
                    'current_quantity': current_quantity,
                    'alert_level': alert_level,
                    'reorder_quantity': alert.reorder_quantity
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'triggered_alerts': triggered_alerts,
            'total_triggered': len(triggered_alerts)
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'檢查預警失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/status', methods=['GET'])
def get_alerts_status():
    """
    獲取預警狀態摘要
    """
    try:
        # 統計各級別預警數量
        critical_count = InventoryAlert.query.filter_by(
            is_active=True,
            alert_status=InventoryAlert.STATUS_CRITICAL
        ).count()
        
        warning_count = InventoryAlert.query.filter_by(
            is_active=True,
            alert_status=InventoryAlert.STATUS_WARNING
        ).count()
        
        normal_count = InventoryAlert.query.filter_by(
            is_active=True,
            alert_status=InventoryAlert.STATUS_NORMAL
        ).count()
        
        # 獲取最近的預警日誌
        recent_logs = InventoryAlertLog.query.filter_by(
            is_resolved=False
        ).order_by(
            InventoryAlertLog.created_at.desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'status': {
                'critical': critical_count,
                'warning': warning_count,
                'normal': normal_count,
                'total': critical_count + warning_count + normal_count
            },
            'recent_alerts': [log.to_dict() for log in recent_logs]
        })
    except Exception as e:
        return jsonify({'error': f'獲取預警狀態失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/logs', methods=['GET'])
def get_alert_logs():
    """
    獲取預警日誌
    """
    try:
        # 獲取查詢參數
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        is_resolved = request.args.get('is_resolved', None)
        alert_level = request.args.get('alert_level', None)
        
        # 構建查詢
        query = InventoryAlertLog.query
        
        if is_resolved is not None:
            query = query.filter_by(is_resolved=is_resolved == 'true')
        
        if alert_level:
            query = query.filter_by(alert_level=alert_level)
        
        # 分頁
        paginated = query.order_by(
            InventoryAlertLog.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': f'獲取預警日誌失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/logs/<int:log_id>/resolve', methods=['POST'])
def resolve_alert_log(log_id):
    """
    標記預警日誌為已解決
    """
    try:
        log = InventoryAlertLog.query.get(log_id)
        if not log:
            return jsonify({'error': '預警日誌不存在'}), 404
        
        log.is_resolved = True
        log.resolved_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '預警已標記為已解決',
            'log': log.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'標記預警失敗: {str(e)}'}), 500


@inventory_alert_bp.route('/api/inventory-alerts/statistics', methods=['GET'])
def get_alert_statistics():
    """
    獲取預警統計信息
    """
    try:
        # 按商品分類統計
        category_stats = db.session.query(
            InventoryAlert.category,
            db.func.count(InventoryAlert.id).label('count')
        ).group_by(InventoryAlert.category).all()
        
        # 按預警級別統計
        level_stats = db.session.query(
            InventoryAlertLog.alert_level,
            db.func.count(InventoryAlertLog.id).label('count')
        ).group_by(InventoryAlertLog.alert_level).all()
        
        # 過去7天的預警趨勢
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_stats = db.session.query(
            db.func.date(InventoryAlertLog.created_at).label('date'),
            db.func.count(InventoryAlertLog.id).label('count')
        ).filter(
            InventoryAlertLog.created_at >= seven_days_ago
        ).group_by(
            db.func.date(InventoryAlertLog.created_at)
        ).all()
        
        return jsonify({
            'success': True,
            'category_stats': [
                {'category': cat, 'count': count} for cat, count in category_stats
            ],
            'level_stats': [
                {'level': level, 'count': count} for level, count in level_stats
            ],
            'daily_stats': [
                {'date': str(date), 'count': count} for date, count in daily_stats
            ]
        })
    except Exception as e:
        return jsonify({'error': f'獲取統計信息失敗: {str(e)}'}), 500
