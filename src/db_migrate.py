"""
資料庫遷移腳本 - 新增分類、數量、單位欄位
"""

import os
import sys
import sqlite3
from datetime import datetime

def migrate_database():
    """執行資料庫遷移"""
    try:
        # 獲取資料庫路徑
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'food_expiry.db')
        
        # 檢查資料庫是否存在
        if not os.path.exists(db_path):
            print(f"資料庫不存在: {db_path}")
            return False
        
        # 連接資料庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查是否已有新欄位
        cursor.execute("PRAGMA table_info(food_item)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # 新增分類欄位
        if 'category' not in columns:
            cursor.execute("ALTER TABLE food_item ADD COLUMN category TEXT DEFAULT '其他'")
            print("已新增 category 欄位")
        
        # 新增數量欄位
        if 'quantity' not in columns:
            cursor.execute("ALTER TABLE food_item ADD COLUMN quantity REAL DEFAULT 1.0")
            print("已新增 quantity 欄位")
        
        # 新增單位欄位
        if 'unit' not in columns:
            cursor.execute("ALTER TABLE food_item ADD COLUMN unit TEXT DEFAULT '個'")
            print("已新增 unit 欄位")
        
        # 提交變更
        conn.commit()
        
        # 關閉連接
        conn.close()
        
        print("資料庫遷移完成")
        return True
    except Exception as e:
        print(f"資料庫遷移錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    migrate_database()
