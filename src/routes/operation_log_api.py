"""
操作日誌審計系統API路由
"""

from datetime import datetime, timedelta, date
from flask import Blueprint, request, jsonify
from src.models.food_item import db
from src.models.operation_log import OperationLog, OperationLogSummary
import json

# 創建藍圖
operation_log_bp = Blueprint('operation_log', __name__)


def get_client_ip():
    """獲取客戶端IP"""
    if request.headers.getlist("X-Forwarded-For"):
        return request.headers.getlist("X-Forwarded-For")[0]
    return request.remote_addr


def log_operation(operation_type, module, action_description, object_type=None, 
                 object_id=None, object_name=None, old_value=None, new_value=None,
                 user_id=None, user_name=None, status='success', error_message=None):
    """
    記錄操作日誌
    """
    try:
        log = OperationLog(
            operation_type=operation_type,
            module=module,
            action_description=action_description,
            object_type=object_type,
            object_id=object_id,
            object_name=object_name,
            old_value=json.dumps(old_value) if old_value else None,
            new_value=json.dumps(new_value) if new_value else None,
            user_id=user_id or 'system',
            user_name=user_name or '系統',
            user_ip=get_client_ip(),
            status=status,
            error_message=error_message
        )
        
        db.session.add(log)
        db.session.commit()
        
        # 更新摘要
        update_summary(operation_type, module, status)
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f'記錄操作日誌失敗: {str(e)}')
        return False


def update_summary(operation_type, module, status):
    """更新操作日誌摘要"""
    try:
        today = date.today()
        summary = OperationLogSummary.query.filter_by(log_date=today).first()
        
        if not summary:
            summary = OperationLogSummary(log_date=today)
            db.session.add(summary)
        
        # 更新總數
        summary.total_operations += 1
        if status == 'success':
            summary.successful_operations += 1
        else:
            summary.failed_operations += 1
        
        # 按操作類型統計
        if operation_type == 'create':
            summary.create_count += 1
        elif operation_type == 'update':
            summary.update_count += 1
        elif operation_type == 'delete':
            summary.delete_count += 1
        elif operation_type == 'view':
            summary.view_count += 1
        elif operation_type == 'export':
            summary.export_count += 1
        elif operation_type == 'import':
            summary.import_count += 1
        elif operation_type == 'search':
            summary.search_count += 1
        
        # 按模塊統計（支持多種模塊名稱格式）
        if module:
            module_lower = module.lower()
            if 'food' in module_lower or module_lower == 'food_item':
                summary.food_operations += 1
            elif 'inventory' in module_lower or module_lower == 'inventory_record':
                summary.inventory_operations += 1
            elif 'barcode' in module_lower:
                summary.barcode_operations += 1
            elif 'alert' in module_lower:
                summary.alert_operations += 1
        
        summary.updated_at = datetime.now()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'更新摘要失敗: {str(e)}')


@operation_log_bp.route('/api/operation-logs', methods=['GET'])
def get_operation_logs():
    """
    獲取操作日誌列表
    """
    try:
        # 獲取查詢參數
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        operation_type = request.args.get('operation_type', None)
        module = request.args.get('module', None)
        status = request.args.get('status', None)
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        # 構建查詢
        query = OperationLog.query
        
        if operation_type:
            query = query.filter_by(operation_type=operation_type)
        if module:
            query = query.filter_by(module=module)
        if status:
            query = query.filter_by(status=status)
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(OperationLog.created_at >= start)
            except:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(OperationLog.created_at < end)
            except:
                pass
        
        # 分頁
        paginated = query.order_by(
            OperationLog.created_at.desc()
        ).paginate(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in paginated.items],
            'total': paginated.total,
            'pages': paginated.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'error': f'獲取操作日誌失敗: {str(e)}'}), 500


@operation_log_bp.route('/api/operation-logs/summary', methods=['GET'])
def get_operation_summary():
    """
    獲取操作日誌摘要
    """
    try:
        # 獲取查詢參數
        days = request.args.get('days', 7, type=int)  # 過去N天
        
        start_date = date.today() - timedelta(days=days)
        summaries = OperationLogSummary.query.filter(
            OperationLogSummary.log_date >= start_date
        ).order_by(
            OperationLogSummary.log_date.desc()
        ).all()
        
        return jsonify({
            'success': True,
            'summaries': [s.to_dict() for s in summaries],
            'total': len(summaries)
        })
    except Exception as e:
        return jsonify({'error': f'獲取摘要失敗: {str(e)}'}), 500


@operation_log_bp.route('/api/operation-logs/statistics', methods=['GET'])
def get_operation_statistics():
    """
    獲取操作統計信息
    """
    try:
        # 按操作類型統計
        operation_stats = db.session.query(
            OperationLog.operation_type,
            db.func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.operation_type).all()
        
        # 按模塊統計
        module_stats = db.session.query(
            OperationLog.module,
            db.func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.module).all()
        
        # 按狀態統計
        status_stats = db.session.query(
            OperationLog.status,
            db.func.count(OperationLog.id).label('count')
        ).group_by(OperationLog.status).all()
        
        # 過去7天的日趨勢
        seven_days_ago = datetime.now() - timedelta(days=7)
        daily_stats = db.session.query(
            db.func.date(OperationLog.created_at).label('date'),
            db.func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.created_at >= seven_days_ago
        ).group_by(
            db.func.date(OperationLog.created_at)
        ).order_by('date').all()
        
        # 最常操作的對象
        top_objects = db.session.query(
            OperationLog.object_name,
            db.func.count(OperationLog.id).label('count')
        ).filter(
            OperationLog.object_name.isnot(None)
        ).group_by(OperationLog.object_name).order_by(
            db.func.count(OperationLog.id).desc()
        ).limit(10).all()
        
        return jsonify({
            'success': True,
            'operation_stats': [
                {'type': op, 'count': count} for op, count in operation_stats
            ],
            'module_stats': [
                {'module': mod, 'count': count} for mod, count in module_stats
            ],
            'status_stats': [
                {'status': st, 'count': count} for st, count in status_stats
            ],
            'daily_stats': [
                {'date': str(d), 'count': count} for d, count in daily_stats
            ],
            'top_objects': [
                {'name': name, 'count': count} for name, count in top_objects
            ]
        })
    except Exception as e:
        return jsonify({'error': f'獲取統計失敗: {str(e)}'}), 500


@operation_log_bp.route('/api/operation-logs/today', methods=['GET'])
def get_today_summary():
    """
    獲取今天的操作摘要（直接從 OperationLog 表計算）
    """
    try:
        today = date.today()
        tomorrow = today + timedelta(days=1)
        
        # 直接從 OperationLog 表計算今天的統計
        today_logs = OperationLog.query.filter(
            OperationLog.created_at >= datetime.combine(today, datetime.min.time()),
            OperationLog.created_at < datetime.combine(tomorrow, datetime.min.time())
        ).all()
        
        total_operations = len(today_logs)
        successful_operations = len([log for log in today_logs if log.status == 'success'])
        failed_operations = len([log for log in today_logs if log.status == 'failure'])
        
        # 同時更新或創建 OperationLogSummary（用於歷史記錄）
        summary = OperationLogSummary.query.filter_by(log_date=today).first()
        if not summary:
            summary = OperationLogSummary(log_date=today)
            db.session.add(summary)
        
        # 更新摘要數據
        summary.total_operations = total_operations
        summary.successful_operations = successful_operations
        summary.failed_operations = failed_operations
        summary.updated_at = datetime.now()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'summary': {
                'total_operations': total_operations,
                'successful_operations': successful_operations,
                'failed_operations': failed_operations,
                'log_date': today.strftime('%Y-%m-%d')
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'獲取今日摘要失敗: {str(e)}'}), 500


@operation_log_bp.route('/api/operation-logs/cleanup', methods=['POST'])
def cleanup_old_logs():
    """
    清理舊日誌（保留N天內的日誌）
    """
    try:
        days = request.json.get('days', 90) if request.json else 90
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 刪除舊日誌
        deleted_count = OperationLog.query.filter(
            OperationLog.created_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'已刪除 {deleted_count} 條舊日誌',
            'deleted_count': deleted_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'清理日誌失敗: {str(e)}'}), 500


@operation_log_bp.route('/api/operation-logs/export', methods=['GET'])
def export_logs():
    """
    導出操作日誌（CSV格式）
    """
    try:
        import csv
        from io import StringIO
        
        # 獲取查詢參數
        start_date = request.args.get('start_date', None)
        end_date = request.args.get('end_date', None)
        
        # 構建查詢
        query = OperationLog.query
        
        if start_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                query = query.filter(OperationLog.created_at >= start)
            except:
                pass
        
        if end_date:
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                query = query.filter(OperationLog.created_at < end)
            except:
                pass
        
        logs = query.order_by(OperationLog.created_at.desc()).all()
        
        # 創建CSV
        output = StringIO()
        writer = csv.writer(output)
        
        # 寫入頭部
        writer.writerow([
            '操作類型', '模塊', '操作描述', '對象類型', '對象ID', '對象名稱',
            '用戶ID', '用戶名稱', '用戶IP', '狀態', '時間'
        ])
        
        # 寫入數據
        for log in logs:
            writer.writerow([
                log.operation_type,
                log.module,
                log.action_description,
                log.object_type,
                log.object_id,
                log.object_name,
                log.user_id,
                log.user_name,
                log.user_ip,
                log.status,
                log.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return {
            'success': True,
            'data': output.getvalue(),
            'count': len(logs)
        }
    except Exception as e:
        return jsonify({'error': f'導出失敗: {str(e)}'}), 500
