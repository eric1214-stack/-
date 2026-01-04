"""
資料庫初始化腳本 - 創建資料庫與表結構
"""

import os
import sys
import sqlite3
from datetime import datetime

def initialize_database():
    """初始化資料庫"""
    try:
        # 確保instance目錄存在
        instance_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance')
        os.makedirs(instance_dir, exist_ok=True)
        
        # 獲取資料庫路徑
        db_path = os.path.join(instance_dir, 'food_expiry.db')
        
        # 連接資料庫（如果不存在會自動創建）
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 創建食品資料表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS food_item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT,
            name TEXT NOT NULL,
            expiry_date DATE NOT NULL,
            batch_number TEXT,
            image_path TEXT,
            notes TEXT,
            category TEXT DEFAULT '其他',
            quantity REAL DEFAULT 1.0,
            unit TEXT DEFAULT '個',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # 創建索引
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_barcode ON food_item (barcode)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expiry_date ON food_item (expiry_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON food_item (category)')
        
        # 提交變更
        conn.commit()
        
        # 關閉連接
        conn.close()
        
        print(f"資料庫初始化完成: {db_path}")
        return True
    except Exception as e:
        print(f"資料庫初始化錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    initialize_database()
