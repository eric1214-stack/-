/**
 * 盤點報表系統 - JavaScript邏輯
 */

// 全局變數
let allReports = [];
let currentReport = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadReportsList();
});

/**
 * 初始化應用
 */
function initializeApp() {
    console.log('初始化盤點報表應用...');
}

/**
 * 設置事件監聽器
 */
function setupEventListeners() {
    // 報表生成按鈕
    document.getElementById('generateDailyBtn').addEventListener('click', generateDailyReport);
    document.getElementById('generateWeeklyBtn').addEventListener('click', generateWeeklyReport);
    document.getElementById('generateMonthlyBtn').addEventListener('click', generateMonthlyReport);
    
    // 報表對比
    document.getElementById('compareBtn').addEventListener('click', compareReports);
    
    // 報表操作
    document.getElementById('printReportBtn').addEventListener('click', printReport);
    document.getElementById('exportReportBtn').addEventListener('click', exportReport);
}

/**
 * 生成日報表
 */
function generateDailyReport() {
    showLoading('生成日報表中...');
    
    fetch('/api/reports/daily', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            alert('日報表已生成');
            loadReportsList();
            displayQuickStats(data.report);
        } else {
            alert('生成報表失敗: ' + (data.error || '未知錯誤'));
        }
    })
    .catch(error => {
        hideLoading();
        alert('生成報表失敗: ' + error.message);
    });
}

/**
 * 生成週報表
 */
function generateWeeklyReport() {
    showLoading('生成週報表中...');
    
    fetch('/api/reports/weekly', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            alert('週報表已生成');
            loadReportsList();
            displayQuickStats(data.report);
        } else {
            alert('生成報表失敗: ' + (data.error || '未知錯誤'));
        }
    })
    .catch(error => {
        hideLoading();
        alert('生成報表失敗: ' + error.message);
    });
}

/**
 * 生成月報表
 */
function generateMonthlyReport() {
    showLoading('生成月報表中...');
    
    fetch('/api/reports/monthly', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            alert('月報表已生成');
            loadReportsList();
            displayQuickStats(data.report);
        } else {
            alert('生成報表失敗: ' + (data.error || '未知錯誤'));
        }
    })
    .catch(error => {
        hideLoading();
        alert('生成報表失敗: ' + error.message);
    });
}

/**
 * 載入報表列表
 */
function loadReportsList() {
    showLoading('載入報表列表中...');
    
    fetch('/api/reports/list?limit=20')
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                allReports = data.reports;
                updateReportsList(data.reports);
                updateComparisonSelects(data.reports);
            } else {
                alert('載入報表失敗: ' + (data.error || '未知錯誤'));
            }
        })
        .catch(error => {
            hideLoading();
            alert('載入報表失敗: ' + error.message);
        });
}

/**
 * 更新報表列表顯示
 */
function updateReportsList(reports) {
    const allList = document.getElementById('allReportsList');
    const dailyList = document.getElementById('dailyReportsList');
    const weeklyList = document.getElementById('weeklyReportsList');
    const monthlyList = document.getElementById('monthlyReportsList');
    
    // 清空列表
    allList.innerHTML = '';
    dailyList.innerHTML = '';
    weeklyList.innerHTML = '';
    monthlyList.innerHTML = '';
    
    // 統計各類型報表
    let dailyCount = 0, weeklyCount = 0, monthlyCount = 0;
    
    reports.forEach(report => {
        const row = createReportRow(report);
        allList.appendChild(row);
        
        if (report.report_type === '日報表') {
            dailyList.appendChild(createReportRow(report));
            dailyCount++;
        } else if (report.report_type === '週報表') {
            weeklyList.appendChild(createReportRow(report));
            weeklyCount++;
        } else if (report.report_type === '月報表') {
            monthlyList.appendChild(createReportRow(report));
            monthlyCount++;
        }
    });
    
    // 更新徽章
    document.getElementById('allBadge').textContent = reports.length;
    document.getElementById('dailyBadge').textContent = dailyCount;
    document.getElementById('weeklyBadge').textContent = weeklyCount;
    document.getElementById('monthlyBadge').textContent = monthlyCount;
    
    // 更新空狀態
    document.getElementById('allEmpty').classList.toggle('hidden-element', reports.length > 0);
    document.getElementById('dailyEmpty').classList.toggle('hidden-element', dailyCount > 0);
    document.getElementById('weeklyEmpty').classList.toggle('hidden-element', weeklyCount > 0);
    document.getElementById('monthlyEmpty').classList.toggle('hidden-element', monthlyCount > 0);
}

/**
 * 建立報表行
 */
function createReportRow(report) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${report.report_date}</td>
        <td><span class="badge bg-secondary">${report.report_type}</span></td>
        <td>${report.total_items}</td>
        <td>${report.total_quantity}</td>
        <td><span class="badge bg-danger">${report.expired_items}</span></td>
        <td><span class="badge bg-warning">${report.expiring_items}</span></td>
        <td>¥${(report.total_sales_amount || 0).toFixed(2)}</td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="viewReport(${report.report_id})">
                <i class="bi bi-eye"></i> 查看
            </button>
        </td>
    `;
    return row;
}

/**
 * 查看報表詳情
 */
function viewReport(reportId) {
    showLoading('載入報表詳情中...');
    
    fetch(`/api/reports/${reportId}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                currentReport = data.report;
                displayReportDetail(data.report);
                
                // 顯示模態框
                const modal = new bootstrap.Modal(document.getElementById('reportDetailModal'));
                modal.show();
            } else {
                alert('載入報表失敗: ' + (data.error || '未知錯誤'));
            }
        })
        .catch(error => {
            hideLoading();
            alert('載入報表失敗: ' + error.message);
        });
}

/**
 * 顯示報表詳情
 */
function displayReportDetail(report) {
    document.getElementById('reportDetailTitle').textContent = `${report.report_type} - ${report.report_date}`;
    
    let html = `
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>庫存統計</h6>
                <table class="table table-sm">
                    <tr>
                        <td>商品數</td>
                        <td><strong>${report.total_items}</strong></td>
                    </tr>
                    <tr>
                        <td>庫存量</td>
                        <td><strong>${report.total_quantity}</strong></td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>異常統計</h6>
                <table class="table table-sm">
                    <tr>
                        <td>過期商品</td>
                        <td><span class="badge bg-danger">${report.expired_items}</span></td>
                    </tr>
                    <tr>
                        <td>即期商品</td>
                        <td><span class="badge bg-warning">${report.expiring_items}</span></td>
                    </tr>
                    <tr>
                        <td>折扣商品</td>
                        <td><span class="badge bg-info">${report.discounted_items}</span></td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <h6>銷售統計</h6>
                <table class="table table-sm">
                    <tr>
                        <td>銷售筆數</td>
                        <td><strong>${report.total_sales_count}</strong></td>
                    </tr>
                    <tr>
                        <td>銷售數量</td>
                        <td><strong>${report.total_sales_quantity}</strong></td>
                    </tr>
                    <tr>
                        <td>銷售額</td>
                        <td><strong>¥${(report.total_sales_amount || 0).toFixed(2)}</strong></td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>報表資訊</h6>
                <table class="table table-sm">
                    <tr>
                        <td>報表日期</td>
                        <td>${report.report_date}</td>
                    </tr>
                    <tr>
                        <td>報表類型</td>
                        <td>${report.report_type}</td>
                    </tr>
                    <tr>
                        <td>生成時間</td>
                        <td>${report.created_at}</td>
                    </tr>
                </table>
            </div>
        </div>
    `;
    
    document.getElementById('reportDetailContent').innerHTML = html;
}

/**
 * 顯示快速統計
 */
function displayQuickStats(report) {
    let html = `
        <div class="row g-2">
            <div class="col-6">
                <div class="p-2 bg-light rounded">
                    <strong>商品數</strong>
                    <div class="h6">${report.inventory_summary.total_items}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="p-2 bg-light rounded">
                    <strong>庫存量</strong>
                    <div class="h6">${report.inventory_summary.total_quantity}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="p-2 bg-light rounded">
                    <strong>銷售額</strong>
                    <div class="h6">¥${(report.sales_summary?.total_sales_amount || 0).toFixed(2)}</div>
                </div>
            </div>
            <div class="col-6">
                <div class="p-2 bg-light rounded">
                    <strong>異常數</strong>
                    <div class="h6">${report.anomaly_summary.total_anomalies}</div>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('quickStats').innerHTML = html;
}

/**
 * 更新對比下拉選單
 */
function updateComparisonSelects(reports) {
    const select1 = document.getElementById('compareReport1');
    const select2 = document.getElementById('compareReport2');
    
    // 清空選項
    select1.innerHTML = '<option value="">選擇報表...</option>';
    select2.innerHTML = '<option value="">選擇報表...</option>';
    
    // 添加選項
    reports.forEach(report => {
        const option1 = document.createElement('option');
        option1.value = report.report_id;
        option1.textContent = `${report.report_date} - ${report.report_type}`;
        select1.appendChild(option1);
        
        const option2 = document.createElement('option');
        option2.value = report.report_id;
        option2.textContent = `${report.report_date} - ${report.report_type}`;
        select2.appendChild(option2);
    });
}

/**
 * 對比報表
 */
function compareReports() {
    const report1Id = document.getElementById('compareReport1').value;
    const report2Id = document.getElementById('compareReport2').value;
    
    if (!report1Id || !report2Id) {
        alert('請選擇兩個報表');
        return;
    }
    
    if (report1Id === report2Id) {
        alert('請選擇不同的報表');
        return;
    }
    
    showLoading('對比報表中...');
    
    fetch(`/api/reports/compare?report1_id=${report1Id}&report2_id=${report2Id}`)
        .then(response => response.json())
        .then(data => {
            hideLoading();
            
            if (data.success) {
                displayComparison(data.comparison);
            } else {
                alert('對比失敗: ' + (data.error || '未知錯誤'));
            }
        })
        .catch(error => {
            hideLoading();
            alert('對比失敗: ' + error.message);
        });
}

/**
 * 顯示對比結果
 */
function displayComparison(comparison) {
    const report1 = comparison.report1;
    const report2 = comparison.report2;
    const changes = comparison.changes;
    
    let html = `
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>報表1: ${report1.report_date}</h6>
                <table class="table table-sm">
                    <tr>
                        <td>商品數</td>
                        <td>${report1.total_items}</td>
                    </tr>
                    <tr>
                        <td>庫存量</td>
                        <td>${report1.total_quantity}</td>
                    </tr>
                    <tr>
                        <td>銷售額</td>
                        <td>¥${(report1.total_sales_amount || 0).toFixed(2)}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>報表2: ${report2.report_date}</h6>
                <table class="table table-sm">
                    <tr>
                        <td>商品數</td>
                        <td>${report2.total_items}</td>
                    </tr>
                    <tr>
                        <td>庫存量</td>
                        <td>${report2.total_quantity}</td>
                    </tr>
                    <tr>
                        <td>銷售額</td>
                        <td>¥${(report2.total_sales_amount || 0).toFixed(2)}</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-12">
                <h6>變化對比</h6>
                <table class="table table-sm">
                    <tr>
                        <td>商品數變化</td>
                        <td>
                            ${changes.items_change > 0 ? '+' : ''}${changes.items_change}
                            <span class="badge ${changes.items_change > 0 ? 'bg-success' : changes.items_change < 0 ? 'bg-danger' : 'bg-secondary'}">
                                ${changes.items_change_rate > 0 ? '+' : ''}${changes.items_change_rate.toFixed(2)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>庫存量變化</td>
                        <td>
                            ${changes.quantity_change > 0 ? '+' : ''}${changes.quantity_change}
                            <span class="badge ${changes.quantity_change > 0 ? 'bg-success' : changes.quantity_change < 0 ? 'bg-danger' : 'bg-secondary'}">
                                ${changes.quantity_change_rate > 0 ? '+' : ''}${changes.quantity_change_rate.toFixed(2)}%
                            </span>
                        </td>
                    </tr>
                    <tr>
                        <td>銷售額變化</td>
                        <td>
                            ${(changes.sales_change || 0) > 0 ? '+' : ''}¥${(changes.sales_change || 0).toFixed(2)}
                            <span class="badge ${changes.sales_change > 0 ? 'bg-success' : changes.sales_change < 0 ? 'bg-danger' : 'bg-secondary'}">
                                ${(changes.sales_change_rate || 0) > 0 ? '+' : ''}${(changes.sales_change_rate || 0).toFixed(2)}%
                            </span>
                        </td>
                    </tr>
                </table>
            </div>
        </div>
    `;
    
    document.getElementById('comparisonResult').innerHTML = html;
}

/**
 * 列印報表
 */
function printReport() {
    if (!currentReport) {
        alert('請先選擇報表');
        return;
    }
    
    window.print();
}

/**
 * 匯出報表
 */
function exportReport() {
    if (!currentReport) {
        alert('請先選擇報表');
        return;
    }
    
    // 構建CSV內容
    let csv = '報表資訊\n';
    csv += `報表日期,${currentReport.report_date}\n`;
    csv += `報表類型,${currentReport.report_type}\n`;
    csv += `生成時間,${currentReport.created_at}\n\n`;
    
    csv += '庫存統計\n';
    csv += `商品數,${currentReport.total_items}\n`;
    csv += `庫存量,${currentReport.total_quantity}\n\n`;
    
    csv += '異常統計\n';
    csv += `過期商品,${currentReport.expired_items}\n`;
    csv += `即期商品,${currentReport.expiring_items}\n`;
    csv += `折扣商品,${currentReport.discounted_items}\n\n`;
    
    csv += '銷售統計\n';
    csv += `銷售筆數,${currentReport.total_sales_count}\n`;
    csv += `銷售數量,${currentReport.total_sales_quantity}\n`;
    csv += `銷售額,${currentReport.total_sales_amount}\n`;
    
    // 下載CSV
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `報表_${currentReport.report_date}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

/**
 * 顯示載入中
 */
function showLoading(message = '載入中...') {
    document.getElementById('loadingMessage').textContent = message;
    document.getElementById('loadingOverlay').classList.remove('hidden-element');
}

/**
 * 隱藏載入中
 */
function hideLoading() {
    document.getElementById('loadingOverlay').classList.add('hidden-element');
}
