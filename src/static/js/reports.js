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
    
    // 刷新總覽數據按鈕
    document.getElementById('refreshReportsBtn').addEventListener('click', loadReportsList);
    
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
            updateQuickStatsFromGeneratedReport(data.report);
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
            updateQuickStatsFromGeneratedReport(data.report);
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
            updateQuickStatsFromGeneratedReport(data.report);
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
                if (allReports.length > 0) {
                    displayQuickStatsFromList(allReports[0]); // Display stats from the first report in the list
                } else {
                    // Reset quick stats if no reports
                    const invTotal = document.getElementById('statInventoryTotal');
                    const anomalyCount = document.getElementById('statAnomalyCount');
                    const totalSales = document.getElementById('statTotalSales');
                    if (invTotal) invTotal.textContent = '0';
                    if (anomalyCount) anomalyCount.textContent = '0';
                    if (totalSales) totalSales.textContent = '¥0.00';
                }
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
        allList.appendChild(createReportRow(report));
        
        if (report.report_type === '日報表') {
            dailyList.appendChild(createDailyReportRow(report));
            dailyCount++;
        } else if (report.report_type === '週報表') {
            weeklyList.appendChild(createWeeklyReportRow(report));
            weeklyCount++;
        } else if (report.report_type === '月報表') {
            monthlyList.appendChild(createMonthlyReportRow(report));
            monthlyCount++;
        }
    });
    
    // 更新徽章
    document.getElementById('allBadge').textContent = reports.length;
    document.getElementById('dailyBadge').textContent = dailyCount;
    document.getElementById('weeklyBadge').textContent = weeklyCount;
    document.getElementById('monthlyBadge').textContent = monthlyCount;
    
    // 更新空狀態
    document.getElementById('allEmpty').style.display = reports.length > 0 ? 'none' : 'block';
    document.getElementById('dailyEmpty').style.display = dailyCount > 0 ? 'none' : 'block';
    document.getElementById('weeklyEmpty').style.display = weeklyCount > 0 ? 'none' : 'block';
    document.getElementById('monthlyEmpty').style.display = monthlyCount > 0 ? 'none' : 'block';
}

/**
 * 建立通用報表行
 */
function createReportRow(report) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>${report.report_date}</td>
        <td><span class="badge bg-secondary">${report.report_type}</span></td>
        <td>${report.total_items}</td>
        <td>${report.inventory_total}</td>
        <td><span class="badge bg-danger">${report.expired_items}</span></td>
        <td><span class="badge bg-warning">${report.expiring_items}</span></td>
        <td>¥${(report.total_sales || 0).toFixed(2)}</td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="viewReport(${report.report_id})">
                <i class="bi bi-eye"></i> 查看
            </button>
        </td>
    `;
    return row;
}

/**
 * 建立日報表行
 */
function createDailyReportRow(report) {
    const row = document.createElement('tr');
    const sales_count = report.raw_data?.sales_summary?.total_sales_count || 0;
    row.innerHTML = `
        <td>${report.report_date}</td>
        <td>${report.total_items}</td>
        <td>${report.inventory_total}</td>
        <td>${sales_count}</td>
        <td>¥${(report.total_sales || 0).toFixed(2)}</td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="viewReport(${report.report_id})">
                <i class="bi bi-eye"></i> 查看
            </button>
        </td>
    `;
    return row;
}

/**
 * 建立週報表行
 */
function createWeeklyReportRow(report) {
    const row = document.createElement('tr');
    const sales_count = report.raw_data?.sales_summary?.total_sales_count || 0;
    row.innerHTML = `
        <td>${report.report_date}</td>
        <td>${report.total_items}</td>
        <td>${report.inventory_total}</td>
        <td>${sales_count}</td>
        <td>¥${(report.total_sales || 0).toFixed(2)}</td>
        <td>
            <button class="btn btn-sm btn-outline-primary" onclick="viewReport(${report.report_id})">
                <i class="bi bi-eye"></i> 查看
            </button>
        </td>
    `;
    return row;
}

/**
 * 建立月報表行
 */
function createMonthlyReportRow(report) {
    const row = document.createElement('tr');
    const sales_count = report.raw_data?.sales_summary?.total_sales_count || 0;
    row.innerHTML = `
        <td>${report.report_date}</td>
        <td>${report.total_items}</td>
        <td>${report.inventory_total}</td>
        <td>${sales_count}</td>
        <td>¥${(report.total_sales || 0).toFixed(2)}</td>
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
    const report = allReports.find(r => r.report_id === reportId);
    if (report) {
        currentReport = report;
        displayReportDetail(report);
        const modal = new bootstrap.Modal(document.getElementById('reportDetailModal'));
        modal.show();
    } else {
        alert('找不到報表詳情');
    }
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
                        <td>商品總數</td>
                        <td><strong>${report.total_items}</strong></td>
                    </tr>
                    <tr>
                        <td>在庫數量</td>
                        <td><strong>${report.inventory_total}</strong></td>
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
                </table>
            </div>
        </div>
        
        <div class="row">
            <div class="col-md-6">
                <h6>銷售統計</h6>
                <table class="table table-sm">
                    <tr>
                        <td>銷售額</td>
                        <td><strong>¥${(report.total_sales || 0).toFixed(2)}</strong></td>
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
    
    if (report.raw_data) {
        html += `<h6>原始數據</h6><pre><code>${JSON.stringify(report.raw_data, null, 2)}</code></pre>`;
    }

    document.getElementById('reportDetailContent').innerHTML = html;
}

/**
 * 顯示來自報表列表的快速統計 (總覽報表)
 * @param {object} report - 從 /api/reports/list 獲取的報表數據
 */
function displayQuickStatsFromList(report) {
    const invTotal = document.getElementById('statInventoryTotal');
    const anomalyCount = document.getElementById('statAnomalyCount');
    const totalSales = document.getElementById('statTotalSales');
    
    if (invTotal) invTotal.textContent = report.inventory_total || '0';
    if (anomalyCount) anomalyCount.textContent = report.anomaly_count || '0';
    if (totalSales) totalSales.textContent = `¥${(report.total_sales || 0).toFixed(2)}`;
}

/**
 * 更新快速統計，用於處理 generate*Report 函數返回的嵌套結構
 * @param {object} reportData - 從 /api/reports/daily, /api/reports/weekly, /api/reports/monthly 獲取的報表數據
 */
function updateQuickStatsFromGeneratedReport(reportData) {
    const invTotal = document.getElementById('statInventoryTotal');
    const anomalyCount = document.getElementById('statAnomalyCount');
    const totalSales = document.getElementById('statTotalSales');
    
    if (reportData.inventory_summary) { // 檢查是否是生成的報表，具有嵌套結構
        if (invTotal) invTotal.textContent = reportData.inventory_summary.total_quantity || '0';
        if (anomalyCount) anomalyCount.textContent = reportData.anomaly_summary.total_anomalies || '0';
        if (totalSales) totalSales.textContent = `¥${(reportData.sales_summary?.total_sales_amount || 0).toFixed(2)}`;
    } else { // 針對類似 /api/reports/list 返回的扁平結構
        if (invTotal) invTotal.textContent = reportData.inventory_total || '0';
        if (anomalyCount) anomalyCount.textContent = reportData.anomaly_count || '0';
        if (totalSales) totalSales.textContent = `¥${(reportData.total_sales || 0).toFixed(2)}`;
    }
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
    
    const report1 = allReports.find(r => r.report_id == report1Id);
    const report2 = allReports.find(r => r.report_id == report2Id);

    if (!report1 || !report2) {
        alert('找不到要對比的報表');
        return;
    }
    
    displayComparison(report1, report2);
}

/**
 * 顯示對比結果
 */
function displayComparison(report1, report2) {
    const changes = {
        items_change: report2.total_items - report1.total_items,
        items_change_rate: (report2.total_items / report1.total_items - 1) * 100,
        quantity_change: report2.inventory_total - report1.inventory_total,
        quantity_change_rate: (report2.inventory_total / report1.inventory_total - 1) * 100,
        sales_change: report2.total_sales - report1.total_sales,
        sales_change_rate: (report2.total_sales / report1.total_sales - 1) * 100,
    };
    
    let html = `
        <div class="row mb-3">
            <div class="col-md-6">
                <h6>報表1: ${report1.report_date} (${report1.report_type})</h6>
                <table class="table table-sm">
                    <tr><td>商品數</td><td>${report1.total_items}</td></tr>
                    <tr><td>庫存量</td><td>${report1.inventory_total}</td></tr>
                    <tr><td>銷售額</td><td>¥${(report1.total_sales || 0).toFixed(2)}</td></tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>報表2: ${report2.report_date} (${report2.report_type})</h6>
                <table class="table table-sm">
                    <tr><td>商品數</td><td>${report2.total_items}</td></tr>
                    <tr><td>庫存量</td><td>${report2.inventory_total}</td></tr>
                    <tr><td>銷售額</td><td>¥${(report2.total_sales || 0).toFixed(2)}</td></tr>
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
    csv += `庫存量,${currentReport.inventory_total}\n\n`;
    
    csv += '異常統計\n';
    csv += `過期商品,${currentReport.expired_items}\n`;
    csv += `即期商品,${currentReport.expiring_items}\n\n`;
    
    csv += '銷售統計\n';
    csv += `銷售額,${currentReport.total_sales}\n`;
    
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
