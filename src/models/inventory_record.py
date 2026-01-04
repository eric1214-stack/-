"""
資料庫模型 - 入庫/出庫記錄
"""

from datetime import datetime
from sqlalchemy import func
from src.models.food_item import db

class InventoryRecord(db.Model):
    """入庫/出庫記錄模型"""
    __tablename__ = 'inventory_record'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 基本信息
    record_type = db.Column(db.String(20), nullable=False)  # 'inbound' 或 'outbound'
    operation_type = db.Column(db.String(50), nullable=False)  # 'purchase', 'return', 'sale', 'damage', 'expiry', 'adjustment'
    
    # 商品信息
    food_item_id = db.Column(db.Integer, db.ForeignKey('food_item.id'), nullable=True)
    barcode = db.Column(db.String(50), index=True)
    product_name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    
    # 數量和單位
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), default='個')
    
    # 價格信息
    unit_price = db.Column(db.Float, default=0.0)
    total_price = db.Column(db.Float, default=0.0)
    discount_rate = db.Column(db.Float, default=0.0)  # 折扣率 (0-1)
    
    # 庫存位置
    storage_location = db.Column(db.String(50))
    storage_condition = db.Column(db.String(20))  # 常溫/冷藏/冷凍
    
    # 時間信息
    expiry_date = db.Column(db.Date)
    record_date = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # 操作人員
    operator = db.Column(db.String(50), default='system')
    
    # 備註
    notes = db.Column(db.Text)
    
    # 狀態
    status = db.Column(db.String(20), default='completed')  # 'pending', 'completed', 'cancelled'
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    # 記錄類型常數
    RECORD_TYPES = {
        'inbound': '入庫',
        'outbound': '出庫'
    }
    
    # 操作類型常數
    OPERATION_TYPES = {
        'purchase': '進貨',
        'return': '退貨',
        'sale': '銷售',
        'damage': '損壞',
        'expiry': '過期',
        'adjustment': '盤點調整'
    }
    
    # 狀態常數
    STATUSES = {
        'pending': '待確認',
        'completed': '已完成',
        'cancelled': '已取消'
    }
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'record_type': self.record_type,
            'record_type_name': self.RECORD_TYPES.get(self.record_type, self.record_type),
            'operation_type': self.operation_type,
            'operation_type_name': self.OPERATION_TYPES.get(self.operation_type, self.operation_type),
            'food_item_id': self.food_item_id,
            'barcode': self.barcode,
            'product_name': self.product_name,
            'category': self.category,
            'quantity': self.quantity,
            'unit': self.unit,
            'unit_price': self.unit_price,
            'total_price': self.total_price,
            'discount_rate': self.discount_rate,
            'storage_location': self.storage_location,
            'storage_condition': self.storage_condition,
            'expiry_date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else None,
            'record_date': self.record_date.strftime('%Y-%m-%d %H:%M:%S'),
            'operator': self.operator,
            'notes': self.notes,
            'status': self.status,
            'status_name': self.STATUSES.get(self.status, self.status),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    
    @staticmethod
    def create_inbound_record(food_item_id, barcode, product_name, category, quantity, unit, 
                             unit_price, storage_location, storage_condition, expiry_date, 
                             operator='system', notes='', operation_type='purchase'):
        """創建入庫記錄"""
        record = InventoryRecord(
            record_type='inbound',
            operation_type=operation_type,
            food_item_id=food_item_id,
            barcode=barcode,
            product_name=product_name,
            category=category,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_price=quantity * unit_price,
            storage_location=storage_location,
            storage_condition=storage_condition,
            expiry_date=expiry_date,
            operator=operator,
            notes=notes,
            status='completed'
        )
        return record
    
    @staticmethod
    def create_outbound_record(food_item_id, barcode, product_name, category, quantity, unit,
                              unit_price, discount_rate, storage_location, storage_condition,
                              expiry_date, operator='system', notes='', operation_type='sale'):
        """創建出庫記錄"""
        total_price = quantity * unit_price * (1 - discount_rate)
        record = InventoryRecord(
            record_type='outbound',
            operation_type=operation_type,
            food_item_id=food_item_id,
            barcode=barcode,
            product_name=product_name,
            category=category,
            quantity=quantity,
            unit=unit,
            unit_price=unit_price,
            total_price=total_price,
            discount_rate=discount_rate,
            storage_location=storage_location,
            storage_condition=storage_condition,
            expiry_date=expiry_date,
            operator=operator,
            notes=notes,
            status='completed'
        )
        return record
