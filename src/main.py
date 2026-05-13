"""
主程式入口點
"""

import sys
import os

# 將專案根目錄添加到 sys.path
# 這使得無論從哪裡執行，都可以正確解析 'src' 模組
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import logging
from datetime import datetime
from flask import Flask, render_template, send_from_directory, make_response, Response, send_file  
from flask_sqlalchemy import SQLAlchemy  
from flask_cors import CORS  
from src.models.food_item import db
from src.models.inventory_audit import InventoryAudit
from src.routes.upload import upload_bp
from src.routes.bluetooth_api import bluetooth_api
from src.routes.inventory_unified_api import inventory_unified_bp
from src.routes.inventory_pages import inventory_pages_bp
from src.routes.expiry_api import expiry_api_bp
from src.routes.reports_api import reports_api_bp
from src.routes.inventory_record_api import inventory_record_bp
from src.routes.barcode_api import barcode_api_bp
from src.routes.inventory_alert_api import inventory_alert_bp
from src.routes.operation_log_api import operation_log_bp
from src.routes.report_export_api import report_export_bp
from src.routes.sales_trend_api import sales_trend_bp

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(lineno)d - %(message)s')
logger = logging.getLogger('food_expiry_system')

# 創建Flask應用
app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))

# 啟用 CORS
CORS(app)

# 配置資料庫
# 使用絕對路徑來確保資料庫路徑的明確性
# 由於 main.py 在 src 目錄下，需要往上兩層才能到專案根目錄
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
database_path = os.path.join(project_root, 'instance', 'food_expiry.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 設定 Gemini API Key
app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', 'YOUR_GEMINI_API_KEY')

# 確保 instance 目錄存在
instance_dir = os.path.dirname(database_path)
os.makedirs(instance_dir, exist_ok=True)

# 初始化資料庫
db.init_app(app)

# 確保資料庫表存在並創建
with app.app_context():
    db.create_all()
    logger.info("資料庫表已確保存在或已創建")
    logger.info(f"資料庫檔案路徑: {database_path}") # 印出實際使用的資料庫路徑

# 註冊藍圖

@app.teardown_appcontext
def shutdown_session(exception=None):
    """確保在請求結束時移除資料庫會話，避免資源鎖定"""
    db.session.remove()

app.register_blueprint(upload_bp)
app.register_blueprint(bluetooth_api)
app.register_blueprint(inventory_unified_bp)
app.register_blueprint(inventory_pages_bp)
app.register_blueprint(expiry_api_bp)
app.register_blueprint(reports_api_bp)
app.register_blueprint(inventory_record_bp)
app.register_blueprint(barcode_api_bp)
app.register_blueprint(inventory_alert_bp)
app.register_blueprint(operation_log_bp)
app.register_blueprint(report_export_bp)
app.register_blueprint(sales_trend_bp)



# 主頁路由
@app.route('/')
def index():
    # 為靜態資源生成一個版本戳記，例如當前時間戳
    cache_buster = datetime.now().strftime('%Y%m%d%H%M%S')
    html = render_template('index.html', cache_buster=cache_buster)
    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8' # 明確設定 charset
    return response

# 靜態文件路由
@app.route('/static/<path:path>')
def serve_static(path):
    response = send_from_directory(app.static_folder, path)
    # 根據檔案類型設定正確的 Content-Type
    if path.endswith('.css'):
        response.headers['Content-Type'] = 'text/css; charset=utf-8'
    elif path.endswith('.js'):
        response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    return response

# 主程式入口
if __name__ == '__main__':
    # 確保上傳目錄存在
    os.makedirs(os.path.join(app.static_folder, 'uploads'), exist_ok=True)
    
    # 啟動應用
    app.run(host='0.0.0.0', port=5005, debug=True)
