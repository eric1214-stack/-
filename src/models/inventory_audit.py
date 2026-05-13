"""
資料庫模型 - 庫存盤點報表
"""

from datetime import datetime
from src.models.food_item import db
import json

class InventoryAudit(db.Model):
    """庫存盤點報表模型"""
    __tablename__ = 'inventory_audit'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 報表基本信息
    report_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    report_type = db.Column(db.String(50), nullable=False)  # '日報表', '週報表', '月報表'
    
    # 核心統計數據
    total_items = db.Column(db.Integer, default=0)
    in_stock_items = db.Column(db.Integer, default=0)
    sold_items = db.Column(db.Integer, default=0)
    removed_items = db.Column(db.Integer, default=0)
    expired_items = db.Column(db.Integer, default=0)
    expiring_soon_items = db.Column(db.Integer, default=0)
    total_sales_amount = db.Column(db.Float, default=0.0)
    
    # 詳細數據（JSON格式）
    raw_data = db.Column(db.Text) # 儲存原始統計數據的JSON字符串
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        """轉換為字典"""
        return {
            'report_id': self.id,
            'report_date': self.report_date.strftime('%Y-%m-%d'),
            'report_type': self.report_type,
            'total_items': self.total_items,
            'inventory_total': self.in_stock_items, # for frontend
            'expired_items': self.expired_items,
            'expiring_items': self.expiring_soon_items,
            'anomaly_count': self.expired_items + self.expiring_soon_items, # for frontend
            'total_sales': self.total_sales_amount, # for frontend
            'raw_data': json.loads(self.raw_data) if self.raw_data else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

