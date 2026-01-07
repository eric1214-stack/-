/**
 * 庫存管理系統 - 優化版
 * 包含加載動畫、實時搜尋、性能優化等功能
 */

let currentItems = [];
let filteredItems = [];
let editingItemId = null;
let searchTimeout;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    loadInventoryData();
    setupEventListeners();
    setupAutoRefresh();
});

/**
 * 設置事件監聽器
 */
function setupEventListeners() {
    // 篩選和搜尋
    document.getElementById('statusFilter')?.addEventListener('change', applyFilters);
    document.getElementById('categoryFilter')?.addEventListener('change', applyFilters);
    document.getElementById('searchInput')?.addEventListener('input', debounceSearch);
    
    // 標籤頁點擊時，直接觸發總的篩選函數
    document.querySelectorAll('[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('shown.bs.tab', applyFilters);
    });
}

/**
 * 防抖搜尋
 */
function debounceSearch() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
        applyFilters();
    }, 300);
}

/**
 * 加載庫存數據
 */
function loadInventoryData() {
    showLoading(true);
    
    fetch('/api/inventory/items')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                currentItems = data.items || [];
                applyFilters();
                updateStatistics();
                populateFilters();
            } else {
                showError(data.error || '加載數據失敗');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError('網絡錯誤，請重試');
        })
        .finally(() => {
            showLoading(false);
        });
}

/**
 * 應用所有篩選條件，包括下拉菜單、搜索和活動標籤頁
 */
function applyFilters() {
    // 獲取當前活動標籤頁的ID
    const activeTabEl = document.querySelector('.nav-tabs .nav-link.active');
    const tabId = activeTabEl ? activeTabEl.id : 'allTab';

    const statusFilter = document.getElementById('statusFilter')?.value || 'all';
    const categoryFilter = document.getElementById('categoryFilter')?.value || 'all';
    const searchText = document.getElementById('searchInput')?.value.toLowerCase() || '';
    
    filteredItems = currentItems.filter(item => {
        // 1. 通用篩選（下拉菜單和搜索）
        const matchStatusDropdown = statusFilter === 'all' || item.item_status === statusFilter;
        const matchCategory = categoryFilter === 'all' || item.category === categoryFilter;
        const matchSearch = !searchText || 
            item.name.toLowerCase().includes(searchText) ||
            (item.barcode && item.barcode.toLowerCase().includes(searchText));

        if (!matchStatusDropdown || !matchCategory || !matchSearch) {
            return false;
        }

        // 2. 根據活動標籤頁進行特定篩選
        switch (tabId) {
            case 'inStockTab':
                return item.item_status === '在庫';
            
            case 'expiringTab':
                // 即期: 7天內到期（含今天），且狀態為在庫
                return item.days_remaining >= 0 && item.days_remaining <= 7 && item.item_status === '在庫';
            
            case 'expiredTab':
                // 過期: 日期已過，或狀態為"下架"
                return item.days_remaining < 0 || item.item_status === '下架';
            
            case 'allTab':
            default:
                // "全部" 標籤頁不應用額外的特定篩選
                return true;
        }
    });
    
    renderItemsTable();
}

/**
 * 更新統計數據
 */
function updateStatistics() {
    const stats = {
        total: currentItems.length,
        inStock: currentItems.filter(i => i.item_status === '在庫').length,
        expiring: currentItems.filter(i => i.days_remaining >= 0 && i.days_remaining <= 30).length,
        expired: currentItems.filter(i => i.days_remaining < 0).length
    };
    
    document.getElementById('totalItems').textContent = stats.total;
    document.getElementById('inStockItems').textContent = stats.inStock;
    document.getElementById('expiringItems').textContent = stats.expiring;
    document.getElementById('expiredItems').textContent = stats.expired;
}

/**
 * 填充分類篩選下拉菜單
 */
function populateFilters() {
    const categorySelect = document.getElementById('categoryFilter');
    if (!categorySelect) return;

    // 從商品數據中提取不重複且有效的分類，並排序
    const categories = [...new Set(currentItems.map(item => item.category).filter(cat => cat))];
    categories.sort();

    const previouslySelected = categorySelect.value;
    categorySelect.innerHTML = '<option value="all">全部分類</option>'; // 保留"全部分類"

    categories.forEach(category => {
        const option = document.createElement('option');
        option.value = category;
        option.textContent = category;
        categorySelect.appendChild(option);
    });

    // 如果之前選中的分類仍然存在，則恢復選擇
    if (categorySelect.querySelector(`option[value="${previouslySelected}"]`)) {
        categorySelect.value = previouslySelected;
    }
}

/**
 * 渲染商品表格
 */
function renderItemsTable() {
    const tbody = document.getElementById('itemsTableBody');
    if (!tbody) return;
    
    if (filteredItems.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">沒有找到符合條件的商品</td></tr>';
        return;
    }
    
    tbody.innerHTML = filteredItems.map(item => {
        const statusBadge = getStatusBadge(item);
        const expiryWarning = getExpiryWarning(item);
        
        return `
            <tr>
                <td>${item.name}</td>
                <td>${item.barcode || '-'}</td>
                <td>${item.category}</td>
                <td>${item.storage_location}</td>
                <td>${item.quantity}</td>
                <td>$${item.unit_price?.toFixed(2) || '0.00'}</td>
                <td>${statusBadge}</td>
                <td>${expiryWarning}</td>
                <td>
                    <button class="btn btn-sm btn-primary" onclick="editItem(${item.id})">
                        <i class="bi bi-pencil"></i> 編輯
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="deleteItem(${item.id})">
                        <i class="bi bi-trash"></i> 刪除
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

/**
 * 獲取狀態徽章
 */
function getStatusBadge(item) {
    const statusColors = {
        '在庫': 'success',
        '已售': 'secondary',
        '下架': 'warning',
        '過期': 'danger'
    };
    
    const color = statusColors[item.item_status] || 'secondary';
    return `<span class="badge bg-${color}">${item.item_status}</span>`;
}

/**
 * 獲取效期警告
 */
function getExpiryWarning(item) {
    const daysRemaining = item.days_remaining;
    
    if (daysRemaining < 0) {
        return `<span class="badge bg-danger">已過期 ${Math.abs(daysRemaining)} 天</span>`;
    } else if (daysRemaining <= 3) {
        return `<span class="badge bg-danger">緊急 ${daysRemaining} 天</span>`;
    } else if (daysRemaining <= 7) {
        return `<span class="badge bg-warning">即期 ${daysRemaining} 天</span>`;
    } else if (daysRemaining <= 30) {
        return `<span class="badge bg-info">注意 ${daysRemaining} 天</span>`;
    }
    
    return `<span class="badge bg-success">${daysRemaining} 天</span>`;
}

/**
 * 編輯商品
 */
function editItem(itemId) {
    const item = currentItems.find(i => i.id === itemId);
    if (!item) return;
    
    editingItemId = itemId;
    
    // 填充表單
    document.getElementById('editItemName').value = item.name;
    document.getElementById('editItemBarcode').value = item.barcode || '';
    document.getElementById('editItemLocation').value = item.storage_location;
    document.getElementById('editItemCondition').value = item.storage_condition;
    document.getElementById('editItemPrice').value = item.unit_price || 0;
    document.getElementById('editItemStatus').value = item.item_status;
    
    // 顯示模態框
    const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
    modal.show();
}

/**
 * 保存編輯
 */
function saveEdit() {
    if (editingItemId === null) return;
    
    const updateData = {
        storage_location: document.getElementById('editItemLocation').value,
        storage_condition: document.getElementById('editItemCondition').value,
        unit_price: parseFloat(document.getElementById('editItemPrice').value),
        item_status: document.getElementById('editItemStatus').value
    };
    
    showLoading(true);
    
    fetch(`/api/inventory/items/${editingItemId}`, {
        method: 'PUT',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(updateData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('商品已更新');
            loadInventoryData();
            bootstrap.Modal.getInstance(document.getElementById('editItemModal')).hide();
            editingItemId = null;
        } else {
            showError(data.error || '更新失敗');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('網絡錯誤');
    })
    .finally(() => {
        showLoading(false);
    });
}

/**
 * 刪除商品
 */
function deleteItem(itemId) {
    if (!confirm('確定要刪除此商品嗎？')) return;
    
    showLoading(true);
    
    fetch(`/api/inventory/items/${itemId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess('商品已刪除');
            loadInventoryData();
        } else {
            showError(data.error || '刪除失敗');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('網絡錯誤');
    })
    .finally(() => {
        showLoading(false);
    });
}

/**
 * 銷售結帳
 */
function checkout() {
    const checkoutItemIdElement = document.getElementById('checkoutItemId');
    const checkoutQuantityElement = document.getElementById('checkoutQuantity');

    if (!checkoutItemIdElement) {
        showError('商品ID輸入框未找到');
        return;
    }
    if (!checkoutQuantityElement) {
        showError('數量輸入框未找到');
        return;
    }

    const itemId = parseInt(checkoutItemIdElement.value);
    const quantity = parseInt(checkoutQuantityElement.value);
    
    if (isNaN(itemId) || !quantity || quantity <= 0) {
        showError('請輸入有效的商品ID和數量');
        return;
    }
    
    showLoading(true);
    
    fetch('/api/inventory/checkout', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({item_id: itemId, quantity: quantity})
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showSuccess(`結帳成功！金額: $${data.final_amount}`);
            if (data.is_expiring_soon) {
                showWarning('此商品即期，已自動應用折扣');
            }
            loadInventoryData();
            document.getElementById('checkoutItemId').value = '';
            document.getElementById('checkoutQuantity').value = '';
        } else {
            showError(data.error || '結帳失敗');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showError('網絡錯誤');
    })
    .finally(() => {
        showLoading(false);
    });
}

/**
 * 設置自動刷新
 */
function setupAutoRefresh() {
    // 每5分鐘自動刷新一次數據
    setInterval(() => {
        loadInventoryData();
    }, 5 * 60 * 1000);
}

/**
 * 顯示加載動畫
 */
function showLoading(show) {
    const loader = document.getElementById('loadingSpinner');
    if (loader) {
        loader.style.display = show ? 'flex' : 'none';
    }
}

/**
 * 顯示成功提示
 */
function showSuccess(message) {
    showAlert(message, 'success');
}

/**
 * 顯示錯誤提示
 */
function showError(message) {
    showAlert(message, 'danger');
}

/**
 * 顯示警告提示
 */
function showWarning(message) {
    showAlert(message, 'warning');
}

/**
 * 通用提示函數
 */
function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container-fluid');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // 3秒後自動關閉
        setTimeout(() => {
            alertDiv.remove();
        }, 3000);
    }
}
