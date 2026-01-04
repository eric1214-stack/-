"""
資料庫模型 - 操作日誌審計
"""

from datetime import datetime
from src.models.food_item import db

class OperationLog(db.Model):
    """操作日誌模型"""
    __tablename__ = 'operation_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 操作信息
    operation_type = db.Column(db.String(50), nullable=False)  # 操作類型：create/update/delete/view/export
    module = db.Column(db.String(50))  # 模塊：food/inventory/barcode/alert等
    action_description = db.Column(db.String(255))  # 操作描述
    
    # 對象信息
    object_type = db.Column(db.String(50))  # 對象類型：FoodItem/InventoryRecord等
    object_id = db.Column(db.Integer)  # 對象ID
    object_name = db.Column(db.String(100))  # 對象名稱
    
    # 變更詳情
    old_value = db.Column(db.Text)  # 舊值（JSON格式）
    new_value = db.Column(db.Text)  # 新值（JSON格式）
    
    # 用戶信息
    user_id = db.Column(db.String(50))  # 用戶ID
    user_name = db.Column(db.String(100))  # 用戶名稱
    user_ip = db.Column(db.String(50))  # 用戶IP地址
    
    # 狀態信息
    status = db.Column(db.String(20), default='success')  # success/failure
    error_message = db.Column(db.Text)  # 錯誤信息（如果操作失敗）
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now, index=True)
    
    # 操作類型常數
    OPERATION_CREATE = 'create'  # 新增
    OPERATION_UPDATE = 'update'  # 編輯
    OPERATION_DELETE = 'delete'  # 刪除
    OPERATION_VIEW = 'view'  # 查看
    OPERATION_EXPORT = 'export'  # 導出
    OPERATION_IMPORT = 'import'  # 導入
    OPERATION_SEARCH = 'search'  # 搜尋
    
    # 狀態常數
    STATUS_SUCCESS = 'success'
    STATUS_FAILURE = 'failure'
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'operation_type': self.operation_type,
            'module': self.module,
            'action_description': self.action_description,
            'object_type': self.object_type,
            'object_id': self.object_id,
            'object_name': self.object_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'user_ip': self.user_ip,
            'status': self.status,
            'error_message': self.error_message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class OperationLogSummary(db.Model):
    """操作日誌摘要（用於快速統計）"""
    __tablename__ = 'operation_log_summary'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 日期
    log_date = db.Column(db.Date, unique=True, index=True)
    
    # 統計數據
    total_operations = db.Column(db.Integer, default=0)  # 總操作數
    successful_operations = db.Column(db.Integer, default=0)  # 成功操作數
    failed_operations = db.Column(db.Integer, default=0)  # 失敗操作數
    
    # 按操作類型統計
    create_count = db.Column(db.Integer, default=0)
    update_count = db.Column(db.Integer, default=0)
    delete_count = db.Column(db.Integer, default=0)
    view_count = db.Column(db.Integer, default=0)
    export_count = db.Column(db.Integer, default=0)
    import_count = db.Column(db.Integer, default=0)
    search_count = db.Column(db.Integer, default=0)
    
    # 按模塊統計
    food_operations = db.Column(db.Integer, default=0)
    inventory_operations = db.Column(db.Integer, default=0)
    barcode_operations = db.Column(db.Integer, default=0)
    alert_operations = db.Column(db.Integer, default=0)
    
    # 時間戳
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'log_date': self.log_date.strftime('%Y-%m-%d'),
            'total_operations': self.total_operations,
            'successful_operations': self.successful_operations,
            'failed_operations': self.failed_operations,
            'create_count': self.create_count,
            'update_count': self.update_count,
            'delete_count': self.delete_count,
            'view_count': self.view_count,
            'export_count': self.export_count,
            'import_count': self.import_count,
            'search_count': self.search_count,
            'food_operations': self.food_operations,
            'inventory_operations': self.inventory_operations,
            'barcode_operations': self.barcode_operations,
            'alert_operations': self.alert_operations,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
