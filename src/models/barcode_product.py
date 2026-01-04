"""
資料庫模型 - 條碼商品資料庫
"""

from datetime import datetime
from src.models.food_item import db

class BarcodeProduct(db.Model):
    """條碼商品資料庫模型"""
    __tablename__ = 'barcode_product'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 條碼信息
    barcode = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # 商品信息
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    
    # 價格信息
    unit_price = db.Column(db.Float, default=0.0)
    
    # 儲存條件
    storage_condition = db.Column(db.String(20), default='常溫')  # 常溫/冷藏/冷凍
    
    # 商品描述
    description = db.Column(db.Text)
    
    # 狀態
    is_active = db.Column(db.Boolean, default=True)
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 分類常數
    CATEGORIES = [
        '乳製品', '肉類', '海鮮', '蔬菜', '水果', 
        '飲料', '零食', '烘焙', '調味料', '冷凍食品', '其他'
    ]
    
    # 儲存條件常數
    STORAGE_CONDITIONS = ['常溫', '冷藏', '冷凍']
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'barcode': self.barcode,
            'product_name': self.product_name,
            'category': self.category,
            'unit_price': self.unit_price,
            'storage_condition': self.storage_condition,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
