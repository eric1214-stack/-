/**
 * 食品效期辨識與管理系統 - 前端互動腳本（完整修正版，含編輯功能修正）
 */
// 立即執行，確認腳本載入
console.log("食品效期辨識系統前端腳本已載入");

// 全域變數
let uploadedImages = [];
let recognitionResults = [];
let categoryChart = null;
let selectedItems = new Set(); // 儲存被選中的項目索引

// DOM 元素載入完成後執行
document.addEventListener('DOMContentLoaded', function () {
    console.log("DOM已完全載入，開始初始化系統");

    // DOM 元素
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const previewContainer = document.getElementById('previewContainer');
    const clearImagesBtn = document.getElementById('clearImagesBtn');
    const recognizeBtn = document.getElementById('recognizeBtn');
    const recognitionResultsDiv = document.getElementById('recognitionResults');
    const resultsContainer = document.getElementById('resultsContainer');
    const loadingOverlay = document.getElementById('loadingOverlay');
    const loadingMessage = document.getElementById('loadingMessage');
    const foodForm = document.getElementById('foodForm');
    const clearFormBtn = document.getElementById('clearFormBtn');
    const refreshExpiringBtn = document.getElementById('refreshExpiringBtn');
    const refreshAllBtn = document.getElementById('refreshAllBtn');
    const expiringTableBody = document.getElementById('expiringFoodList');
    const allTableBody = document.getElementById('allFoodList');
    const expiringEmptyMessage = document.getElementById('expiringEmptyMessage');
    const allEmptyMessage = document.getElementById('allEmptyMessage');
    const categoryFilterSelect = document.getElementById('categoryFilter');

    // 初始化頁面
    initPage();

    // 上傳區域點擊
    if (uploadArea) {
        uploadArea.addEventListener('click', function () {
            fileInput.click();
        });
    }

    // 檔案選擇
    if (fileInput) {
        fileInput.addEventListener('change', function () {
            if (this.files.length > 0) {
                handleFiles(this.files);
            }
        });
    }

    // 拖放事件
    if (uploadArea) {
        uploadArea.addEventListener('dragover', function (e) {
            e.preventDefault();
            uploadArea.classList.add('highlight');
        });

        uploadArea.addEventListener('dragleave', function () {
            uploadArea.classList.remove('highlight');
        });

        uploadArea.addEventListener('drop', function (e) {
            e.preventDefault();
            uploadArea.classList.remove('highlight');
            if (e.dataTransfer.files.length > 0) {
                handleFiles(e.dataTransfer.files);
            }
        });
    }

    // 清除圖片
    if (clearImagesBtn) {
        clearImagesBtn.addEventListener('click', function () {
            clearImages();
        });
    }

    // 執行辨識
    if (recognizeBtn) {
        recognizeBtn.addEventListener('click', function () {
            recognizeImages();
        });
    }

    // 清除表單
    if (clearFormBtn) {
        clearFormBtn.addEventListener('click', function () {
            clearForm();
        });
    }

    // 重新整理列表
    if (refreshExpiringBtn) {
        refreshExpiringBtn.addEventListener('click', function () {
            loadExpiringFoodList();
        });
    }

    if (refreshAllBtn) {
        refreshAllBtn.addEventListener('click', function () {
            loadAllFoodList();
        });
    }
    
    // 分類篩選事件
    if (categoryFilterSelect) {
        categoryFilterSelect.addEventListener('change', function() {
            console.log("分類篩選變更:", this.value);
            filterFoodListByCategory(this.value);
        });
    }

    /**
     * 初始化頁面
     */
    function initPage() {
        console.log("初始化頁面");
        // 設定 expiryDate 預設為今天
        const today = new Date();
        const formattedDate = today.toISOString().split('T')[0];
        const expiryDateInput = document.getElementById('expiryDate');
        if (expiryDateInput) expiryDateInput.value = formattedDate;

        // 載入列表與統計
        loadAllFoodList();       // 主要表格
        loadExpiringFoodList();  // 即將到期（30天內，未過期）
        updateDashboard();

        // 載入分類選單
        loadCategoryStats();

        // 綁定表單提交事件
        if (foodForm) {
            foodForm.addEventListener('submit', function(e) {
                e.preventDefault();
                saveFood();
            });
        }
    }

    /**
     * 處理上傳檔案
     */
    function handleFiles(files) {
        console.log("handleFiles:", files);
        // 驗證與限制
        const validTypes = ['image/jpeg', 'image/png', 'image/webp'];
        for (let i = 0; i < files.length; i++) {
            const f = files[i];
            if (!validTypes.includes(f.type)) {
                alert(`不支援的檔案類型: ${f.name}`);
                return;
            }
            if (f.size > 10 * 1024 * 1024) {
                alert(`檔案過大: ${f.name} (上限 10MB)`);
                return;
            }
        }

        showLoading('上傳圖片中...');

        const formData = new FormData();
        for (let i = 0; i < files.length; i++) {
            formData.append('files[]', files[i]);
        }

        fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        .then(resp => {
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return resp.json();
        })
        .then(data => {
            console.log('upload response', data);
            if (data.results && data.results.length) {
                data.results.forEach(r => {
                    if (r.success) {
                        uploadedImages.push({ path: r.image_path, filename: r.original_filename });
                    } else {
                        console.warn('upload failed for', r.original_filename, r.error);
                    }
                });
                updatePreview();
                updateButtonStatus();
            } else {
                alert('上傳失敗：伺服器回傳格式錯誤');
            }
            hideLoading();
        })
        .catch(err => {
            console.error('upload error', err);
            alert('上傳失敗: ' + err.message);
            hideLoading();
        });
    }

    /**
     * 更新圖片預覽
     */
    function updatePreview() {
        if (!previewContainer) return;
        previewContainer.innerHTML = '';
        if (uploadedImages.length === 0) {
            previewContainer.style.display = 'none';
            return;
        }
        previewContainer.style.display = 'flex';
        uploadedImages.forEach((img, idx) => {
            const wrap = document.createElement('div');
            wrap.className = 'preview-item';
            wrap.style.position = 'relative';
            wrap.style.width = '150px';

            const imageEl = document.createElement('img');
            imageEl.src = img.path;
            imageEl.alt = img.filename;
            imageEl.style.width = '150px';
            imageEl.style.height = '150px';
            imageEl.className = 'object-fit-cover rounded';

            const btn = document.createElement('button');
            btn.className = 'btn btn-sm btn-danger btn-remove';
            btn.style.position = 'absolute';
            btn.style.top = '4px';
            btn.style.right = '4px';
            btn.innerHTML = '<i class="bi bi-x-lg"></i>';
            btn.addEventListener('click', function () {
                removeImage(idx);
            });

            wrap.appendChild(imageEl);
            wrap.appendChild(btn);
            previewContainer.appendChild(wrap);
        });
    }

    /**
     * 移除單張圖片（前端列表 + 後端刪除）
     */
    function removeImage(index) {
        const toRemove = uploadedImages[index];
        if (!toRemove) return;
        // 立即從前端移除
        uploadedImages.splice(index, 1);
        updatePreview();
        updateButtonStatus();
        // 非同步通知後端刪除（不阻塞 UI）
        fetch('/api/delete-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image_path: toRemove.path })
        }).catch(err => console.warn('delete-image failed', err));
    }

    /**
     * 清除全部上傳圖片
     */
    function clearImages() {
        // 通知後端刪除並清空陣列
        uploadedImages.forEach(img => {
            fetch('/api/delete-image', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image_path: img.path })
            }).catch(() => {});
        });
        uploadedImages = [];
        updatePreview();
        updateButtonStatus();
    }

    /**
     * 根據是否有上傳圖片更新按鈕狀態
     */
    function updateButtonStatus() {
        const has = uploadedImages.length > 0;
        if (clearImagesBtn) clearImagesBtn.disabled = !has;
        if (recognizeBtn) recognizeBtn.disabled = !has;
    }

    /**
     * 呼叫後端辨識 API
     */
    function recognizeImages() {
        if (uploadedImages.length === 0) {
            alert('請先上傳圖片');
            return;
        }
        showLoading('辨識中...');
        const imagePaths = uploadedImages.map(i => i.path);
        fetch('/api/recognize', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ images: imagePaths })
        })
        .then(resp => {
            if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
            return resp.json();
        })
        .then(data => {
            console.log('recognize result', data);
            if (Array.isArray(data.results)) {
                recognitionResults = data.results;
                selectedItems.clear(); // 清空選擇狀態
                // 顯示至畫面
                displayRecognitionResults();
            } else {
                alert('辨識失敗：回傳格式錯誤');
            }
            hideLoading();
        })
        .catch(err => {
            console.error('recognize error', err);
            alert('辨識失敗: ' + err.message);
            hideLoading();
        });
    }

    /**
     * 顯示辨識結果（含條碼顯示和選擇框）
     */
    function displayRecognitionResults() {
        console.log("顯示辨識結果");
        
        if (resultsContainer && recognitionResultsDiv) {
            // 清空舊結果
            resultsContainer.innerHTML = '';
            
            // 顯示結果區塊
            recognitionResultsDiv.style.display = 'block';
            
            // 為每個結果創建卡片
            recognitionResults.forEach((result, index) => {
                const resultCard = document.createElement('div');
                resultCard.classList.add('card', 'mb-3', 'recognition-card');
                
                // 條碼顯示邏輯
                const barcodeDisplay = result.barcode ? 
                    `<p class="card-text"><strong>條碼:</strong> ${result.barcode}</p>` : 
                    `<p class="card-text"><strong>條碼:</strong> 未辨識到條碼</p>`;
                
                let cardBody = `
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-3">
                                <img src="${result.image_path}" class="img-fluid rounded" alt="食品圖片">
                            </div>
                            <div class="col-md-6">
                                <h5 class="card-title">${result.food_name || '無法辨識'}</h5>
                                <div class="row">
                                    <div class="col-md-6">
                                        <p class="card-text"><strong>到期日:</strong> ${result.expiry_date || '無法辨識'}</p>
                                        <p class="card-text"><strong>分類:</strong> ${result.category || '其他'}</p>
                                    </div>
                                    <div class="col-md-6">
                                        ${barcodeDisplay}
                                        <p class="card-text"><strong>數量:</strong> ${result.quantity || '1'} ${result.unit || '個'}</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="d-flex flex-column h-100 justify-content-between">
                                    <div class="form-check">
                                        <input class="form-check-input item-checkbox" type="checkbox" value="${index}" id="itemCheckbox${index}">
                                        <label class="form-check-label" for="itemCheckbox${index}">
                                            選擇此項目
                                        </label>
                                    </div>
                                    <div>
                                        <button class="btn btn-primary btn-sm btn-fill-form w-100 mb-2" data-index="${index}">填入表單</button>
                                        <button class="btn btn-outline-secondary btn-sm w-100 mb-1" onclick="fillSingleField(${index}, 'name')">僅用名稱</button>
                                        <button class="btn btn-outline-secondary btn-sm w-100 mb-1" onclick="fillSingleField(${index}, 'expiryDate')">僅用到期日</button>
                                        <button class="btn btn-outline-secondary btn-sm w-100" onclick="fillSingleField(${index}, 'barcode')">僅用條碼</button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                `;
                
                resultCard.innerHTML = cardBody;
                resultsContainer.appendChild(resultCard);
            });

            // 綁定選擇框事件
            document.querySelectorAll('.item-checkbox').forEach(checkbox => {
                checkbox.addEventListener('change', function() {
                    const index = parseInt(this.value);
                    if (this.checked) {
                        selectedItems.add(index);
                    } else {
                        selectedItems.delete(index);
                    }
                    updateMergeButtonState();
                });
            });

            // 綁定填入表單按鈕事件
            document.querySelectorAll('.btn-fill-form').forEach(btn => {
                btn.addEventListener('click', function() {
                    const index = parseInt(this.getAttribute('data-index'));
                    fillFormFromRecognition(index);
                });
            });

            // 更新合併按鈕狀態
            updateMergeButtonState();
        }
    }

    /**
     * 更新合併按鈕狀態
     */
    function updateMergeButtonState() {
        const mergeSelectedBtn = document.getElementById('mergeSelectedBtn');
        if (mergeSelectedBtn) {
            if (selectedItems.size > 0) {
                mergeSelectedBtn.disabled = false;
                mergeSelectedBtn.textContent = `合併選擇的項目 (${selectedItems.size})`;
            } else {
                mergeSelectedBtn.disabled = true;
                mergeSelectedBtn.textContent = '合併選擇的項目';
            }
        }
    }

    /**
     * 合併選擇的辨識結果
     */
    function mergeSelectedResults() {
        if (selectedItems.size === 0) {
            alert('請先選擇要合併的項目');
            return;
        }

        const selectedResults = Array.from(selectedItems).map(index => recognitionResults[index]);
        
        if (!confirm(`確定要將 ${selectedItems.size} 筆選擇的辨識結果加入食品清單？`)) {
            return;
        }

        showLoading("正在寫入選擇的食品清單...");

        let successCount = 0;
        let errorCount = 0;
        let currentIndex = 0;

        function saveNext() {
            if (currentIndex >= selectedResults.length) {
                // 全部完成
                console.log("選擇性合併完成，成功:", successCount, "失敗:", errorCount);
                
                // 清除已合併的項目
                selectedResults.forEach((result, index) => {
                    const originalIndex = Array.from(selectedItems)[index];
                    recognitionResults.splice(originalIndex, 1);
                });
                
                // 清空選擇狀態
                selectedItems.clear();
                
                // 更新UI
                displayRecognitionResults();
                updatePreview();
                updateButtonStatus();
                
                // 重新載入列表
                loadAllFoodList();
                loadExpiringFoodList();
                updateDashboard();
                
                hideLoading();
                
                // 顯示結果訊息
                if (errorCount === 0) {
                    alert(`✅ 所有 ${successCount} 筆選擇的辨識結果已成功加入食品清單！`);
                } else {
                    alert(`⚠️ 完成合併！成功: ${successCount} 筆，失敗: ${errorCount} 筆`);
                }
                return;
            }

            const result = selectedResults[currentIndex];
            console.log(`處理第 ${currentIndex + 1} 筆選擇的資料:`, result);

            const foodData = {
                id: '',
                name: result.food_name || '未命名食品',
                category: result.category || '其他',
                expiry_date: result.expiry_date || new Date().toISOString().split('T')[0],
                barcode: result.barcode || '',
                quantity: result.quantity || '1',
                unit: result.unit || '個',
                batch_number: result.batch_number || '',
                notes: result.notes || '',
                image_path: result.image_path || ''
            };

            // 更新載入訊息
            loadingMessage.textContent = `正在寫入選擇的食品清單... (${currentIndex + 1}/${selectedResults.length})`;

            fetch('/api/save-food', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(foodData)
            })
            .then(resp => {
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                return resp.json();
            })
            .then(data => {
                if (data.success) {
                    successCount++;
                    console.log(`第 ${currentIndex + 1} 筆選擇的資料保存成功`);
                } else {
                    errorCount++;
                    console.warn(`第 ${currentIndex + 1} 筆選擇的資料保存失敗:`, data.error);
                }
                currentIndex++;
                saveNext();
            })
            .catch(err => {
                console.error(`第 ${currentIndex + 1} 筆選擇的資料保存錯誤:`, err);
                errorCount++;
                currentIndex++;
                saveNext(); // 即使失敗也繼續
            });
        }

        saveNext();
    }

    /**
     * 填入單一欄位到表單
     */
    window.fillSingleField = function(index, fieldName) {
        const result = recognitionResults[index];
        if (!result) return;

        switch(fieldName) {
            case 'name':
                document.getElementById('name').value = result.food_name || '';
                break;
            case 'expiryDate':
                document.getElementById('expiryDate').value = result.expiry_date || '';
                break;
            case 'barcode':
                document.getElementById('barcode').value = result.barcode || '';
                break;
            case 'category':
                document.getElementById('category').value = result.category || '其他';
                break;
        }

        // 滾動到表單位置
        const foodForm = document.getElementById('foodForm');
        if (foodForm) {
            foodForm.scrollIntoView({ behavior: 'smooth' });
        }
        
        alert(`已將 ${getFieldDisplayName(fieldName)} 填入表單`);
    };

    /**
     * 取得欄位顯示名稱
     */
    function getFieldDisplayName(fieldName) {
        const fieldMap = {
            'name': '食品名稱',
            'expiryDate': '到期日',
            'barcode': '條碼',
            'category': '分類'
        };
        return fieldMap[fieldName] || fieldName;
    }

    /**
     * 將辨識結果填入表單（含條碼）
     * @param {number} index - 辨識結果的索引
     */
    function fillFormFromRecognition(index) {
        console.log("填入表單，索引:", index);
        
        const result = recognitionResults[index];
        
        if (result) {
            document.getElementById('foodId').value = '';
            document.getElementById('name').value = result.food_name || '';
            document.getElementById('expiryDate').value = result.expiry_date || '';
            document.getElementById('imagePath').value = result.image_path || '';
            document.getElementById('barcode').value = result.barcode || ''; // 填入條碼
            document.getElementById('quantity').value = result.quantity || '1';
            document.getElementById('unit').value = result.unit || '個';
            document.getElementById('batchNumber').value = result.batch_number || '';
            document.getElementById('notes').value = result.notes || '';
            
            // 自動選擇最接近的類別
            const category = result.category || '其他';
            const categorySelect = document.getElementById('category');
            
            // 檢查選項是否存在
            let optionExists = false;
            for (let i = 0; i < categorySelect.options.length; i++) {
                if (categorySelect.options[i].value === category) {
                    optionExists = true;
                    break;
                }
            }
            
            // 如果不存在，新增選項
            if (!optionExists) {
                const newOption = new Option(category, category, true, true);
                categorySelect.add(newOption);
            } else {
                categorySelect.value = category;
            }
            
            // 滾動到表單位置
            if (foodForm) {
                foodForm.scrollIntoView({ behavior: 'smooth' });
            }
        }
    }

    /**
     * 清除表單內容
     */
    function clearForm() {
        document.getElementById('foodId').value = '';
        document.getElementById('name').value = '';
        document.getElementById('category').value = '其他';
        document.getElementById('expiryDate').value = new Date().toISOString().split('T')[0];
        document.getElementById('barcode').value = '';
        document.getElementById('quantity').value = '1';
        document.getElementById('unit').value = '個';
        document.getElementById('batchNumber').value = '';
        document.getElementById('notes').value = '';
        document.getElementById('imagePath').value = '';
        document.getElementById('storageCondition').value = '常溫';
        document.getElementById('unitPrice').value = '';
        document.getElementById('storageLocation').value = '';
    }

    /**
     * 儲存食品資料（新增/編輯）- 修正版
     */
    function saveFood() {
        const foodId = document.getElementById('foodId').value;
        const foodData = {
            name: document.getElementById('name').value,
            category: document.getElementById('category').value,
            expiry_date: document.getElementById('expiryDate').value,
            barcode: document.getElementById('barcode').value,
            quantity: document.getElementById('quantity').value,
            unit: document.getElementById('unit').value,
            batch_number: document.getElementById('batchNumber').value,
            notes: document.getElementById('notes').value,
            image_path: document.getElementById('imagePath').value,
            storage_condition: document.getElementById('storageCondition').value,
            unit_price: parseFloat(document.getElementById('unitPrice').value) || 0,
            storage_location: document.getElementById('storageLocation').value
        };

        if (!foodData.name) {
            alert('請填寫食品名稱');
            return;
        }

        console.log("儲存食品資料:", foodData, "ID:", foodId);

        showLoading(foodId ? '更新中...' : '儲存中...');

        // 根據是否有ID決定是新增還是更新
        let url, method;
        if (foodId) {
            // 編輯模式 - 使用跟新增相同的端點，但將ID加入到資料中
            url = '/api/save-food';
            method = 'POST';
            foodData.id = foodId; // 重要：將ID加入到資料中
        } else {
            // 新增模式
            url = '/api/save-food';
            method = 'POST';
        }

        console.log("請求:", method, url, foodData);

        fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(foodData)
        })
        .then(response => {
            console.log("回應狀態:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("回應資料:", data);
            if (data.success) {
                alert(foodId ? '食品資料已更新！' : '食品資料已儲存！');
                clearForm();
                loadAllFoodList();
                loadExpiringFoodList();
                updateDashboard();
            } else {
                alert('儲存失敗: ' + (data.error || '未知錯誤'));
            }
            hideLoading();
        })
        .catch(error => {
            console.error('儲存食品失敗:', error);
            
            // 提供更詳細的錯誤處理
            if (error.message.includes('404')) {
                alert('API端點不存在。請確認後端伺服器正在運行，且 /api/save-food 端點可用。');
            } else {
                alert('儲存失敗: ' + error.message);
            }
            hideLoading();
        });
    }

    /**
     * 合併所有辨識結果（含條碼）
     */
    function mergeAllResults() {
        console.log("開始合併所有辨識結果", recognitionResults);
        
        if (!recognitionResults || recognitionResults.length === 0) {
            alert("目前沒有辨識結果可合併。請先上傳並執行 AI 辨識。");
            return;
        }

        if (!confirm(`確定要將 ${recognitionResults.length} 筆辨識結果加入食品清單？`)) {
            return;
        }

        showLoading("正在寫入食品清單...");
        console.log("開始寫入食品清單，數量:", recognitionResults.length);

        let successCount = 0;
        let errorCount = 0;
        let currentIndex = 0;

        function saveNext() {
            if (currentIndex >= recognitionResults.length) {
                // 全部完成
                console.log("合併完成，成功:", successCount, "失敗:", errorCount);
                
                // 清除辨識結果和圖片
                recognitionResults = [];
                uploadedImages = [];
                
                // 更新UI
                updatePreview();
                updateButtonStatus();
                
                // 重新載入列表
                loadAllFoodList();
                loadExpiringFoodList();
                updateDashboard();
                
                hideLoading();
                
                // 顯示結果訊息
                if (errorCount === 0) {
                    alert(`✅ 所有 ${successCount} 筆辨識結果已成功加入食品清單！`);
                } else {
                    alert(`⚠️ 完成合併！成功: ${successCount} 筆，失敗: ${errorCount} 筆`);
                }
                return;
            }

            const result = recognitionResults[currentIndex];
            console.log(`處理第 ${currentIndex + 1} 筆資料:`, result);

            const foodData = {
                id: '',
                name: result.food_name || '未命名食品',
                category: result.category || '其他',
                expiry_date: result.expiry_date || new Date().toISOString().split('T')[0],
                barcode: result.barcode || '', // 包含條碼
                quantity: result.quantity || '1',
                unit: result.unit || '個',
                batch_number: result.batch_number || '',
                notes: result.notes || '',
                image_path: result.image_path || ''
            };

            // 更新載入訊息
            loadingMessage.textContent = `正在寫入食品清單... (${currentIndex + 1}/${recognitionResults.length})`;

            fetch('/api/save-food', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(foodData)
            })
            .then(resp => {
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                return resp.json();
            })
            .then(data => {
                if (data.success) {
                    successCount++;
                    console.log(`第 ${currentIndex + 1} 筆保存成功`);
                } else {
                    errorCount++;
                    console.warn(`第 ${currentIndex + 1} 筆保存失敗:`, data.error);
                }
                currentIndex++;
                saveNext();
            })
            .catch(err => {
                console.error(`第 ${currentIndex + 1} 筆保存錯誤:`, err);
                errorCount++;
                currentIndex++;
                saveNext(); // 即使失敗也繼續
            });
        }

        saveNext();
    }

    /**
     * 載入即將到期食品（30天內，未過期）- 修正版（含備註欄位）
     */
    function loadExpiringFoodList() {
        console.log("載入即將到期食品列表（30天內）");
        
        fetch('/api/expiring-food')
            .then(resp => {
                if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
                return resp.json();
            })
            .then(data => {
                console.log("即將到期食品數據:", data);
                if (data.success) {
                    // 過濾掉已過期的食品，只顯示30天內但還未過期的
                    const expiringItems = data.food_items.filter(item => {
                        const expiry = new Date(item.expiry_date);
                        const today = new Date();
                        const diffDays = Math.ceil((expiry - today) / (1000 * 60 * 60 * 24));
                        return diffDays >= 0 && diffDays <= 30; // 0-30天內，未過期
                    });
                    
                    console.log("過濾後的即將到期食品:", expiringItems.length);
                    displayExpiringFoodList(expiringItems);
                } else {
                    console.error("獲取即將到期食品失敗:", data.error);
                }
            })
            .catch(err => {
                console.error('載入即將到期食品失敗:', err);
                if (expiringTableBody) {
                    expiringTableBody.innerHTML = `<tr><td colspan="8" class="text-center text-danger">載入失敗</td></tr>`;
                }
            });
    }

    /**
     * 專門顯示即將到期食品列表（30天內，未過期）- 修正版（全部黃色）
     */
    function displayExpiringFoodList(foodItems) {
        console.log("顯示即將到期食品列表（30天內），數量:", foodItems.length);
        
        if (!expiringTableBody) return;
        
        expiringTableBody.innerHTML = '';

        if (!foodItems || foodItems.length === 0) {
            if (expiringEmptyMessage) {
                expiringEmptyMessage.style.display = 'table-row';
                expiringEmptyMessage.innerHTML = '<td colspan="8" class="text-center">沒有即將到期的食品（30天內）</td>';
            }
            return;
        } else {
            if (expiringEmptyMessage) {
                expiringEmptyMessage.style.display = 'none';
            }
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        foodItems.forEach(item => {
            const row = document.createElement('tr');
            const expiry = new Date(item.expiry_date);
            expiry.setHours(0, 0, 0, 0);
            
            const diffTime = expiry - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            let statusBadge = '';
            
            // 即將到期列表：全部顯示黃色 badge
            if (diffDays === 0) {
                statusBadge = `<span class="badge bg-warning">今天到期</span>`;
            } else if (diffDays <= 30) {
                statusBadge = `<span class="badge bg-warning">剩餘 ${diffDays} 天</span>`;
            }
            
            row.innerHTML = `
                <td><strong>${item.name}</strong></td>
                <td>${item.category}</td>
                <td>${item.quantity} ${item.unit}</td>
                <td><strong>${item.expiry_date}</strong></td>
                <td>${item.batch_number || '-'}</td>
                <td>${item.notes || '-'}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-info btn-view" data-id="${item.id}">查看細項</button>
                    <button class="btn btn-sm btn-primary btn-edit" data-id="${item.id}">編輯</button>
                    <button class="btn btn-sm btn-danger btn-delete" data-id="${item.id}">刪除</button>
                </td>`;
            
            expiringTableBody.appendChild(row);
        });

        bindTableButtonEvents();
    }

    /**
     * 載入所有食品列表
     */
    function loadAllFoodList() {
        fetch('/api/foods')
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    displayAllFoodList(data.food_items);
                }
            })
            .catch(err => console.error('all list load error', err));
    }

    /**
     * 專門顯示所有食品列表 - 修正版（只有 badge 變色，無底色）
     */
    function displayAllFoodList(foodItems) {
        console.log("顯示所有食品列表，數量:", foodItems.length);
        
        if (!allTableBody) return;
        
        allTableBody.innerHTML = '';

        if (!foodItems || foodItems.length === 0) {
            if (allEmptyMessage) {
                allEmptyMessage.style.display = 'table-row';
            }
            return;
        } else {
            if (allEmptyMessage) {
                allEmptyMessage.style.display = 'none';
            }
        }

        const today = new Date();
        today.setHours(0, 0, 0, 0);

        foodItems.forEach(item => {
            const row = document.createElement('tr');
            const expiry = new Date(item.expiry_date);
            expiry.setHours(0, 0, 0, 0);
            
            const diffTime = expiry - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

            let statusBadge = '';
            
            // 只有 badge 變色，無 rowClass
            if (diffDays < 0) {
                // 已過期 - 紅色
                statusBadge = `<span class="badge bg-danger">已過期 ${Math.abs(diffDays)} 天</span>`;
            } else if (diffDays < 30) {
                // 0-29天 - 黃色
                statusBadge = `<span class="badge bg-warning">剩餘 ${diffDays} 天</span>`;
            } else {
                // 30天以上 - 綠色
                statusBadge = `<span class="badge bg-success">剩餘 ${diffDays} 天</span>`;
            }

            // 移除 row.className 設定，保持白色底色
            
            row.innerHTML = `
                <td>${item.name}</td>
                <td>${item.category}</td>
                <td>${item.quantity} ${item.unit}</td>
                <td>${item.expiry_date}</td>
                <td>${item.batch_number || ''}</td>
                <td>${item.notes || ''}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-info btn-view" data-id="${item.id}">查看細項</button>
                    <button class="btn btn-sm btn-primary btn-edit" data-id="${item.id}">編輯</button>
                    <button class="btn btn-sm btn-danger btn-delete" data-id="${item.id}">刪除</button>
                </td>`;
            
            allTableBody.appendChild(row);
        });

        bindTableButtonEvents();
    }

    /**
     * 綁定表格按鈕事件
     */
    function bindTableButtonEvents() {
        // 綁定編輯按鈕
        document.querySelectorAll('.btn-edit').forEach(btn => {
            btn.addEventListener('click', function() {
                const foodId = parseInt(this.getAttribute('data-id'));
                editFoodItem(foodId);
            });
        });

        // 綁定刪除按鈕
        document.querySelectorAll('.btn-delete').forEach(btn => {
            btn.addEventListener('click', function() {
                const foodId = parseInt(this.getAttribute('data-id'));
                deleteFoodItem(foodId);
            });
        });

        // 綁定查看細項按鈕（新增）
        document.querySelectorAll('.btn-view').forEach(btn => {
            btn.addEventListener('click', function() {
                const foodId = parseInt(this.getAttribute('data-id'));
                showFoodItemDetails(foodId);
            });
        });
    }

    /**
     * 顯示食品細項彈出視窗
     */
    function showFoodItemDetails(itemId) {
        // 從現有資料中找食品資料
        fetch('/api/foods')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const item = data.food_items.find(food => food.id == itemId);
                if (item) {
                    displayFoodDetailModal(item);
                } else {
                    throw new Error('找不到該食品資料');
                }
            } else {
                throw new Error(data.error || '獲取食品列表失敗');
            }
        })
        .catch(error => {
            console.error('獲取食品資料失敗:', error);
            alert('無法獲取食品詳細資料：' + error.message);
        });
    }

    /**
     * 顯示食品詳細資訊彈出視窗
     */
    function displayFoodDetailModal(item) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const expiry = new Date(item.expiry_date);
        expiry.setHours(0, 0, 0, 0);
        const diffTime = expiry - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

        const modalHtml = `
            <div class="modal fade" id="foodDetailModal" tabindex="-1" aria-labelledby="foodDetailModalLabel" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title" id="foodDetailModalLabel">食品詳細資訊</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            <div class="row mb-2">
                                <div class="col-4"><strong>名稱：</strong></div>
                                <div class="col-8">${item.name}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>條碼：</strong></div>
                                <div class="col-8">${item.barcode || '無'}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>分類：</strong></div>
                                <div class="col-8">${item.category}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>數量：</strong></div>
                                <div class="col-8">${item.quantity} ${item.unit}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>批號：</strong></div>
                                <div class="col-8">${item.batch_number || '無'}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>備註：</strong></div>
                                <div class="col-8">${item.notes || '無'}</div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>剩餘天數：</strong></div>
                                <div class="col-8">
                                    ${diffDays < 0 ? 
                                        `<span class="badge bg-danger">已過期 ${Math.abs(diffDays)} 天</span>` : 
                                        diffDays < 30 ? 
                                        `<span class="badge bg-warning">剩餘 ${diffDays} 天</span>` : 
                                        `<span class="badge bg-success">剩餘 ${diffDays} 天</span>`
                                    }
                                </div>
                            </div>
                            <div class="row mb-2">
                                <div class="col-4"><strong>到期日：</strong></div>
                                <div class="col-8">${item.expiry_date}</div>
                            </div>
                            ${item.image_path ? `
                            <div class="row mb-2">
                                <div class="col-4"><strong>圖片：</strong></div>
                                <div class="col-8">
                                    <img src="${item.image_path}" class="img-fluid rounded" alt="食品圖片" style="max-height: 200px;">
                                </div>
                            </div>` : ''}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">確定</button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        // 移除現有的 modal（如果存在）
        const existingModal = document.getElementById('foodDetailModal');
        if (existingModal) {
            existingModal.remove();
        }

        // 添加新的 modal 到 body
        document.body.insertAdjacentHTML('beforeend', modalHtml);

        // 顯示 modal
        const modal = new bootstrap.Modal(document.getElementById('foodDetailModal'));
        modal.show();

        // 當 modal 關閉時移除它
        document.getElementById('foodDetailModal').addEventListener('hidden.bs.modal', function () {
            this.remove();
        });
    }

    /**
     * 編輯食品 - 修正版（解決編輯問題）
     * @param {number} foodId - 食品ID
     */
    function editFoodItem(foodId) {
        console.log("編輯食品，ID:", foodId);
        
        showLoading('載入食品資料中...');
        
        // 直接從現有資料中找食品資料（避免API路徑問題）
        fetch('/api/foods')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP錯誤! 狀態: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // 從所有食品中找出對應ID的食品
                const item = data.food_items.find(food => food.id == foodId);
                if (item) {
                    fillFormWithFoodData(item);
                    hideLoading();
                } else {
                    throw new Error('找不到該食品資料');
                }
            } else {
                throw new Error(data.error || '獲取食品列表失敗');
            }
        })
        .catch(error => {
            console.error('獲取食品資料失敗:', error);
            alert('無法獲取食品資料：' + error.message);
            hideLoading();
        });
    }

    /**
     * 將食品資料填入表單 - 修正版
     */
    function fillFormWithFoodData(item) {
        console.log("填入食品資料:", item);
        
        // 確保所有欄位都有正確的值
        document.getElementById('foodId').value = item.id || '';
        document.getElementById('name').value = item.name || '';
        document.getElementById('category').value = item.category || '其他';
        document.getElementById('expiryDate').value = item.expiry_date || '';
        document.getElementById('barcode').value = item.barcode || '';
        document.getElementById('quantity').value = item.quantity || '1';
        document.getElementById('unit').value = item.unit || '個';
        document.getElementById('batchNumber').value = item.batch_number || '';
        document.getElementById('notes').value = item.notes || '';
        document.getElementById('imagePath').value = item.image_path || '';
        document.getElementById('storageCondition').value = item.storage_condition || '常溫';
        document.getElementById('unitPrice').value = item.unit_price || '';
        document.getElementById('storageLocation').value = item.storage_location || '';
        
        // 滾動到表單位置
        const foodForm = document.getElementById('foodForm');
        if (foodForm) {
            foodForm.scrollIntoView({ behavior: 'smooth' });
        }
        
        console.log("食品資料已成功填入表單，ID:", item.id);
    }

    /**
     * 刪除食品
     * @param {number} foodId - 食品ID
     */
    function deleteFoodItem(foodId) {
        console.log("刪除食品，ID:", foodId);
        
        if (confirm("確定要刪除此食品嗎？")) {
            fetch(`/api/delete-food/${foodId}`, {
                method: 'DELETE'
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP錯誤! 狀態: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert("食品已成功刪除");
                    
                    // 重新載入列表
                    loadExpiringFoodList();
                    loadAllFoodList();
                    
                    // 更新儀表板
                    updateDashboard();
                } else {
                    alert("刪除失敗: " + data.error);
                }
            })
            .catch(error => {
                console.error('刪除食品失敗:', error);
                alert('刪除食品失敗: ' + error.message);
            });
        }
    }

    /**
     * 儀表板更新
     */
    function updateDashboard() {
        fetch('/api/food-stats')
            .then(resp => resp.json())
            .then(data => {
                if (data.success) {
                    const totalFoodCount = document.getElementById('totalFoodCount');
                    const expiringCount = document.getElementById('expiring-count');
                    const expiredFoodCount = document.getElementById('expiredFoodCount');
                    
                    if (totalFoodCount) totalFoodCount.textContent = data.stats.total_count;
                    if (expiringCount) expiringCount.textContent = data.stats.expiring_count;
                    if (expiredFoodCount) expiredFoodCount.textContent = data.stats.expired_count;
                    
                    updateCategoryChart(data.stats.category_counts);
                }
            });
    }

    /**
     * 更新分類圓餅圖（固定顏色 + 防變形）
     */
    function updateCategoryChart(categoryCounts) {
        const chartElement = document.getElementById('categoryChart');
        if (!chartElement) return;
        
        const ctx = chartElement.getContext('2d');
        const labels = Object.keys(categoryCounts);
        const values = Object.values(categoryCounts);

        if (categoryChart) categoryChart.destroy();

        categoryChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: labels,
                datasets: [{
                    data: values,
                    backgroundColor: [
                        "#FF6384","#36A2EB","#FFCE56",
                        "#4BC0C0","#9966FF","#FF9F40",
                        "#C9CBCF","#5367FF","#28A745","#D28850"
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top" },
                    title: { display: true, text: "食品分類分佈" }
                }
            }
        });
    }

    /**
     * 顯示分類選單
     */
    function loadCategoryStats() {
        fetch('/api/food-stats')
            .then(resp => resp.json())
            .then(data => {
                if (data.success && categoryFilterSelect) {
                    const categories = Object.keys(data.stats.category_counts);
                    categoryFilterSelect.innerHTML = '<option value="all">所有類別</option>';
                    categories.forEach(c => {
                        const op = document.createElement('option');
                        op.value = c;
                        op.textContent = c;
                        categoryFilterSelect.appendChild(op);
                    });
                }
            });
    }

    /**
     * 根據分類篩選食品列表
     * @param {string} category - 要篩選的分類
     */
    function filterFoodListByCategory(category) {
        if (!allTableBody) return;
        
        const rows = allTableBody.querySelectorAll('tr');
        rows.forEach(row => {
            // 檢查是否為資料行
            if (row.querySelector('td')) {
                const rowCategory = row.cells[1].textContent; // 分類在第二個儲存格
                if (category === 'all' || rowCategory === category) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            }
        });
    }

    /**
     * 載入中樣式
     */
    function showLoading(msg) {
        if (loadingMessage) loadingMessage.textContent = msg;
        if (loadingOverlay) loadingOverlay.style.display = 'flex';
    }

    function hideLoading() {
        if (loadingOverlay) loadingOverlay.style.display = 'none';
    }
});

// ==================== 條碼掃描功能 ====================
let videoStream = null;
let barcodeDetector = null;

// 初始化條碼掃描
document.addEventListener('DOMContentLoaded', function() {
    const startScannerBtn = document.getElementById('startScannerBtn');
    const stopScannerBtn = document.getElementById('stopScannerBtn');
    const searchBarcodeBtn = document.getElementById('searchBarcodeBtn');
    const useBarcodeBtn = document.getElementById('useBarcodeBtn');
    const manualBarcode = document.getElementById('manualBarcode');

    if (startScannerBtn) {
        startScannerBtn.addEventListener('click', startScanner);
    }
    if (stopScannerBtn) {
        stopScannerBtn.addEventListener('click', stopScanner);
    }
    if (searchBarcodeBtn) {
        searchBarcodeBtn.addEventListener('click', searchBarcode);
    }
    if (useBarcodeBtn) {
        useBarcodeBtn.addEventListener('click', useBarcodeForStocking);
    }
    if (manualBarcode) {
        manualBarcode.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                searchBarcode();
            }
        });
    }

    // 初始化條碼檢測器
    if ('BarcodeDetector' in window) {
        try {
            barcodeDetector = new BarcodeDetector({
                formats: ['ean_13', 'ean_8', 'code_128', 'code_39', 'qr_code']
            });
        } catch (e) {
            console.log('條碼檢測器初始化失敗:', e);
        }
    }
});

// 開啟鏡頭掃描
async function startScanner() {
    const scannerContainer = document.getElementById('scannerContainer');
    const video = document.getElementById('video');
    const startBtn = document.getElementById('startScannerBtn');
    const stopBtn = document.getElementById('stopScannerBtn');
    const scannerStatus = document.getElementById('scannerStatus');

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'environment' }
        });
        
        videoStream = stream;
        video.srcObject = stream;
        scannerContainer.style.display = 'block';
        startBtn.disabled = true;
        stopBtn.disabled = false;
        scannerStatus.style.display = 'block';

        // 開始掃描
        scanBarcodeFromVideo();
    } catch (error) {
        console.error('無法訪問攝像頭:', error);
        alert('無法訪問攝像頭，請檢查權限設置');
    }
}

// 停止掃描
function stopScanner() {
    const scannerContainer = document.getElementById('scannerContainer');
    const startBtn = document.getElementById('startScannerBtn');
    const stopBtn = document.getElementById('stopScannerBtn');
    const scannerStatus = document.getElementById('scannerStatus');

    if (videoStream) {
        videoStream.getTracks().forEach(track => track.stop());
        videoStream = null;
    }

    scannerContainer.style.display = 'none';
    startBtn.disabled = false;
    stopBtn.disabled = true;
    scannerStatus.style.display = 'none';
}

// 從視頻流掃描條碼
async function scanBarcodeFromVideo() {
    const video = document.getElementById('video');
    
    if (!videoStream || !barcodeDetector) {
        return;
    }

    try {
        const barcodes = await barcodeDetector.detect(video);
        
        if (barcodes.length > 0) {
            const barcode = barcodes[0].rawValue;
            console.log('檢測到條碼:', barcode);
            
            // 停止掃描並顯示結果
            stopScanner();
            
            // 查詢條碼
            document.getElementById('manualBarcode').value = barcode;
            searchBarcode();
            return;
        }
    } catch (error) {
        console.log('掃描錯誤:', error);
    }

    // 繼續掃描
    if (videoStream) {
        requestAnimationFrame(scanBarcodeFromVideo);
    }
}

// 搜尋條碼
async function searchBarcode() {
    const barcode = document.getElementById('manualBarcode').value.trim();
    
    if (!barcode) {
        alert('請輸入條碼');
        return;
    }

    try {
        const response = await fetch(`/api/barcode/search?barcode=${encodeURIComponent(barcode)}`);
        const data = await response.json();

        const barcodeResult = document.getElementById('barcodeResult');
        const barcodeResultContent = document.getElementById('barcodeResultContent');

        if (data.success && (data.product || data.data)) {
            const product = data.product || data.data;
            barcodeResultContent.innerHTML = `
                <p><strong>商品名稱:</strong> ${product.product_name}</p>
                <p><strong>分類:</strong> ${product.category}</p>
                <p><strong>單價:</strong> $${product.unit_price}</p>
                <p><strong>儲存條件:</strong> ${product.storage_condition}</p>
                ${product.description ? `<p><strong>描述:</strong> ${product.description}</p>` : ''}
            `;
            barcodeResult.style.display = 'block';
            
            // 儲存條碼信息到全域變數
            window.currentBarcodeData = product;
        } else {
            barcodeResultContent.innerHTML = '<p style="color: #dc3545;">未找到該條碼的商品信息</p>';
            barcodeResult.style.display = 'block';
            window.currentBarcodeData = null;
        }
    } catch (error) {
        console.error('查詢條碼失敗:', error);
        alert('查詢條碼失敗，請重試');
    }
}

// 使用條碼進行入庫
function useBarcodeForStocking() {
    if (!window.currentBarcodeData) {
        alert('請先查詢有效的條碼');
        return;
    }

    const product = window.currentBarcodeData;
    
    // 填充表單
    document.getElementById('barcode').value = document.getElementById('manualBarcode').value;
    document.getElementById('name').value = product.product_name;
    document.getElementById('category').value = product.category;
    document.getElementById('storageCondition').value = product.storage_condition;
    document.getElementById('unitPrice').value = product.unit_price;
    document.getElementById('storageLocation').value = '';

    // 設定今天的日期為預設
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expiryDate').value = today;

    // 隱藏條碼結果
    document.getElementById('barcodeResult').style.display = 'none';

    // 滾動到表單
    document.getElementById('foodForm').scrollIntoView({ behavior: 'smooth' });
    
    alert('條碼信息已填充到表單，請完善其他信息後提交');
}
