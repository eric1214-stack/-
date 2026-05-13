"""
資料庫模型 - 食品資料
"""

from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func

db = SQLAlchemy()

class FoodItem(db.Model):
    """食品資料模型"""
    id = db.Column(db.Integer, primary_key=True)
    barcode = db.Column(db.String(50), index=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    expiry_date = db.Column(db.Date, nullable=False)
    batch_number = db.Column(db.String(50))
    image_path = db.Column(db.String(255))
    notes = db.Column(db.Text)
    # 新增食品分類欄位
    category = db.Column(db.String(50), default='其他')
    # 新增數量欄位
    quantity = db.Column(db.Float, default=1.0)
    # 新增單位欄位
    unit = db.Column(db.String(20), default='個')
    # 超商庫存管理欄位
    storage_location = db.Column(db.String(50), default='E1')  # 架位編號
    storage_condition = db.Column(db.String(20), default='常溫')  # 儲存條件
    inbound_date = db.Column(db.DateTime, default=datetime.now)  # 入庫時間
    item_status = db.Column(db.String(20), default='在庫')  # 商品狀態
    ai_check_status = db.Column(db.String(20), default='Pass')  # AI辨識狀態
    unit_price = db.Column(db.Float, default=0.0)  # 單位價格
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 食品分類選項
    CATEGORIES = [
        '乳製品', '肉類', '海鮮', '蔬菜', '水果', 
        '飲料', '零食', '烘焙', '調味料', '冷凍食品', '其他'
    ]
    
    # 常用單位選項
    UNITS = [
        '個', '包', '瓶', '罐', '盒', '袋', 
        '公斤', '公克', '毫升', '升', '份', '其他'
    ]
    
    @property
    def days_remaining(self):
        """計算剩餘天數"""
        if not self.expiry_date:
            return None
        
        today = date.today()
        delta = self.expiry_date - today
        return delta.days
    
    @property
    def status(self):
        """取得狀態"""
        days = self.days_remaining
        
        if days is None:
            return "unknown"
        elif days < 0:
            return "expired"
        elif days == 0:
            return "today"
        elif days <= 30:
            return "soon"
        else:
            return "normal"
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'barcode': self.barcode,
            'name': self.name,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'batch_number': self.batch_number,
            'image_path': self.image_path,
            'notes': self.notes,
            'category': self.category,
            'quantity': self.quantity,
            'unit': self.unit,
            'storage_location': self.storage_location,
            'storage_condition': self.storage_condition,
            'inbound_date': self.inbound_date.strftime('%Y-%m-%d %H:%M:%S') if self.inbound_date else None,
            'item_status': self.item_status,
            'ai_check_status': self.ai_check_status,
            'unit_price': self.unit_price,
            'days_remaining': self.days_remaining,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
