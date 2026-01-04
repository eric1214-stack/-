"""
資料庫模型 - 庫存預警設定
"""

from datetime import datetime
from src.models.food_item import db

class InventoryAlert(db.Model):
    """庫存預警設定模型"""
    __tablename__ = 'inventory_alert'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 商品信息
    product_name = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(50), index=True)
    category = db.Column(db.String(50))
    
    # 預警設定
    min_quantity = db.Column(db.Float, default=10.0)  # 最低庫存量
    alert_threshold = db.Column(db.Float, default=5.0)  # 預警閾值（低於此值時發出警告）
    reorder_quantity = db.Column(db.Float, default=50.0)  # 建議補貨量
    
    # 預警狀態
    is_active = db.Column(db.Boolean, default=True)  # 是否啟用預警
    alert_status = db.Column(db.String(20), default='normal')  # normal/warning/critical
    last_alert_time = db.Column(db.DateTime)  # 上次預警時間
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 預警狀態常數
    STATUS_NORMAL = 'normal'  # 正常
    STATUS_WARNING = 'warning'  # 預警（低於最低庫存）
    STATUS_CRITICAL = 'critical'  # 緊急（低於預警閾值）
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'product_name': self.product_name,
            'barcode': self.barcode,
            'category': self.category,
            'min_quantity': self.min_quantity,
            'alert_threshold': self.alert_threshold,
            'reorder_quantity': self.reorder_quantity,
            'is_active': self.is_active,
            'alert_status': self.alert_status,
            'last_alert_time': self.last_alert_time.strftime('%Y-%m-%d %H:%M:%S') if self.last_alert_time else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class InventoryAlertLog(db.Model):
    """庫存預警日誌模型"""
    __tablename__ = 'inventory_alert_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 預警信息
    alert_id = db.Column(db.Integer, db.ForeignKey('inventory_alert.id'), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    barcode = db.Column(db.String(50))
    
    # 庫存信息
    current_quantity = db.Column(db.Float)
    min_quantity = db.Column(db.Float)
    alert_threshold = db.Column(db.Float)
    
    # 預警級別
    alert_level = db.Column(db.String(20))  # warning/critical
    alert_message = db.Column(db.Text)
    
    # 狀態
    is_resolved = db.Column(db.Boolean, default=False)  # 是否已解決
    resolved_at = db.Column(db.DateTime)  # 解決時間
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'alert_id': self.alert_id,
            'product_name': self.product_name,
            'barcode': self.barcode,
            'current_quantity': self.current_quantity,
            'min_quantity': self.min_quantity,
            'alert_threshold': self.alert_threshold,
            'alert_level': self.alert_level,
            'alert_message': self.alert_message,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
