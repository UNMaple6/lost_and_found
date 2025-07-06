$(document).ready(function () {
    // API_BASE_URL 从 config.js 引入
    const token = localStorage.getItem('token');
    const username = localStorage.getItem('username');

    // --- 1. 身份验证 ---
    // 页面加载时立即检查token，没有则直接跳转到登录页
    if (!token) {
        alert('您尚未登录，请先登录！');
        window.location.href = 'login.html';
        return; // 阻止后续代码执行
    }
    // --- 【新增】和首页一样的未读消息数函数 ---
    function fetchUnreadCount() {
        $.ajax({
            url: API_BASE_URL + '/api/rooms/',
            type: 'GET',
            headers: { 'Authorization': 'Token ' + token },
            success: function (response) {
                let totalUnread = 0;
                // 检查API返回的格式，适配两种可能的数据结构
                const rooms = response.results || response;

                // 使用Set记录已处理的用户，避免重复计算
                const processedUsers = new Set();

                if (rooms && rooms.length > 0) {
                    rooms.forEach(room => {
                        // 如果这个房间没有对方用户信息，跳过
                        if (!room.other_participant) return;

                        const otherUsername = room.other_participant.username;
                        // 如果已经处理过这个用户的未读消息，跳过
                        if (processedUsers.has(otherUsername)) return;

                        // 记录这个用户已处理
                        processedUsers.add(otherUsername);
                        totalUnread += room.unread_count;
                    });
                }
                const unreadBadge = $('#unread-count-badge');
                if (totalUnread > 0) {
                    unreadBadge.text(totalUnread).show();
                } else {
                    unreadBadge.hide();
                }
            },
            error: function (xhr) {
                console.error('获取未读消息计数失败:', xhr.responseText);
            }
        });
    }
    // --- 【新增】动态填充导航栏 ---
    $('#nav-user-status').html(`
        <a href="message-list.html" class="btn btn-primary position-relative me-3">
            ✉️
            <span id="unread-count-badge" class="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger" style="display: none;"></span>
        </a>
        <span id="username-display" class="navbar-text me-3">欢迎, ${username}</span>
    `);
    // 在导航栏显示用户名
    $('#username-display').text(`欢迎, ${username}`);

    // --- 2. 加载并渲染“我发布的物品” ---
    function loadMyItems() {
        $('#loading-status').text('正在加载您的物品...').show();

        $.ajax({
            url: API_BASE_URL + '/api/items/mine/',
            type: 'GET',
            headers: {
                'Authorization': 'Token ' + token
            },
            success: function (items) {
                $('#loading-status').hide();
                renderMyItems(items);
            },
            error: function (xhr) {
                if (xhr.status === 401 || xhr.status === 403) {
                    alert('身份认证已过期，请重新登录。');
                    window.location.href = 'login.html';
                } else {
                    $('#loading-status').text('加载物品失败，请稍后重试或联系管理员。').addClass('text-danger');
                }
            }
        });
    }

    function renderMyItems(items) {
        const itemList = $('#my-item-list');
        itemList.empty(); // 清空旧数据

        if (!items || items.length === 0) {
            itemList.html('<p class="text-center text-muted">您还没有发布任何物品信息。</p>');
            return;
        }

        items.forEach(function (item) {
            const cardClass = item.type === 'LOST' ? 'border-danger' : 'border-success';

            const statusBadge = item.is_resolved
                ? '<span class="badge bg-success">已处理</span>' // 文字改为“已处理”更通用
                : '<span class="badge bg-warning">处理中</span>'; // 文字改为“处理中”更通用

            // ====================【合并点】: 从分支2引入typeBadge逻辑 ====================
            const typeBadge = item.type === 'LOST'
                ? '<span class="badge bg-danger">失物</span>'
                : '<span class="badge bg-info">拾物</span>';
            // ========================================================================

            let imageHtml = item.image_url ? `<img src="${item.image_url}" class="card-img-top" alt="${item.title}" style="max-height: 200px; object-fit: cover;">` : '';

            // ====================【合并点】: 更新cardHtml模板以包含typeBadge ====================
            const cardHtml = `
                <div class="col-md-6 col-lg-4 mb-4" id="item-card-${item.id}">
                    <div class="card h-100 ${cardClass}">
                        ${imageHtml}
                        <div class="card-body">
                            <!-- 这是分支2中新的标题布局 -->
                            <h5 class="card-title d-flex justify-content-between align-items-center">
                                <span class="text-truncate" title="${item.title}">${item.title}</span>
                                <div>
                                    ${statusBadge}
                                    <span class="ms-1">${typeBadge}</span>
                                </div>
                            </h5>
                            <h6 class="card-subtitle mb-2 text-muted">${item.item_class}</h6>
                            <p class="card-text">${item.description || '无'}</p>
                            <p class="card-text"><small class="text-muted">地点：${item.location || '无'}</small></p>
                            ${item.time ? `<p class="card-text"><small class="text-muted">日期：${item.time}</small></p>` : ''}
                        </div>
                        <div class="card-footer bg-transparent">
                            <a href="item-detail.html?id=${item.id}" class="btn btn-info btn-sm">详情</a>
                            <button class="btn btn-primary btn-sm edit-btn" data-id="${item.id}" data-bs-toggle="modal" data-bs-target="#editItemModal">编辑</button>
                            <button class="btn btn-danger btn-sm delete-btn" data-id="${item.id}">删除</button>
                            ${!item.is_resolved ? `<button class="btn btn-success btn-sm resolve-btn" data-id="${item.id}">标记已处理</button>` : ''}
                            <button class="btn btn-secondary btn-sm manual-match-btn" data-id="${item.id}">查找匹配</button>
                        </div>
                    </div>
                </div>
            `;
            // =============================================================================
            itemList.append(cardHtml);
        });
    }
    // 在 $(document).ready() 中，增加一个新函数调用


    // --- 3. 事件委托，处理所有按钮的点击事件 ---
    // 点击“查找匹配”按钮
    $('#my-item-list').on('click', '.manual-match-btn', function () {
        const itemId = $(this).data('id');
        // 直接跳转到我们已经做好的匹配结果页，并把当前物品ID传过去
        window.location.href = `match-results.html?id=${itemId}`;
    });
    // 点击“删除”按钮
    $('#my-item-list').on('click', '.delete-btn', function () {
        const itemId = $(this).data('id');
        if (confirm('您确定要删除这条信息吗？此操作不可恢复。')) {
            $.ajax({
                url: `${API_BASE_URL}/api/items/${itemId}/`,
                type: 'DELETE',
                headers: { 'Authorization': 'Token ' + token },
                success: function () {
                    alert('删除成功！');
                    $(`#item-card-${itemId}`).remove(); // 从页面上移除卡片
                },
                error: function () {
                    alert('删除失败，请稍后重试。');
                }
            });
        }
    });

    // 点击“标记为已找回”按钮
    $('#my-item-list').on('click', '.resolve-btn', function () {
        const itemId = $(this).data('id');
        $.ajax({
            url: `${API_BASE_URL}/api/items/${itemId}/`,
            type: 'PATCH',
            headers: { 'Authorization': 'Token ' + token },
            contentType: 'application/json',
            data: JSON.stringify({ is_resolved: true }),
            success: function () {
                alert('状态更新成功！');
                loadMyItems(); // 重新加载列表以更新状态
            },
            error: function (xhr) {//调试
                console.error("PATCH 请求失败，服务器响应:", xhr.responseJSON); // <--- 打印详细错误
                alert('状态更新失败，请稍后重试。');
            }
        });
    });

    // 点击“编辑”按钮，填充模态框
    let currentEditItemId = null; // 用于存储当前正在编辑的物品ID
    $('#my-item-list').on('click', '.edit-btn', function () {
        currentEditItemId = $(this).data('id');
        const card = $(this).closest('.card');
        const title = card.find('.card-title').clone().children().remove().end().text().trim();
        const item_class = card.find('.card-subtitle').text();
        const description = card.find('.card-text').first().text();
        const location = card.find('small:contains("地点")').text().replace('地点：', '');
        const time = card.find('small:contains("日期")').text().replace('日期：', '');

        $('#edit-title').val(title);
        $('#edit-item_class').val(item_class);
        $('#edit-description').val(description);
        $('#edit-location').val(location);
        $('#edit-time').val(time);
    });

    // 点击模态框中的“保存修改”按钮
    $('#save-changes-btn').on('click', function () {
        // --- 前端校验开始 (逻辑与publish.html类似) ---
        const title = $('#edit-title').val().trim();
        const location = $('#edit-location').val().trim();

        if (!title) {
            alert('物品名称不能为空！');
            return; // 阻止提交
        }
        if (title.length > 50) {
            alert('物品名称不能超过50个字符！');
            return; // 阻止提交
        }
        if (!location) {
            alert('地点不能为空！');
            return; // 阻止提交
        }
        // --- 前端校验结束 ---

        const updatedData = {
            title: $('#edit-title').val(),
            item_class: $('#edit-item_class').val(),
            description: $('#edit-description').val(),
            location: $('#edit-location').val(),
            time: $('#edit-time').val() || null, // 如果时间未填写，则发送null
        };
        // 移除值为null的字段，这样PATCH请求只会发送有值的字段
        Object.keys(updatedData).forEach(key => updatedData[key] == null && delete updatedData[key]);
        $.ajax({
            url: `${API_BASE_URL}/api/items/${currentEditItemId}/`,
            type: 'PATCH',
            headers: { 'Authorization': 'Token ' + token },
            contentType: 'application/json',
            data: JSON.stringify(updatedData),
            success: function () {
                alert('修改成功！');
                $('#editItemModal').modal('hide'); // 关闭模态框
                loadMyItems(); // 重新加载列表以显示最新数据
            },
            error: function (xhr) {
                // 处理后端返回的校验错误
                let errorMsg = '修改失败！\n';

                if (xhr.status === 400 && xhr.responseJSON) {
                    const errors = xhr.responseJSON;
                    for (const field in errors) {
                        errorMsg += `\n- ${field}: ${errors[field][0]}`;
                    }
                } else {
                    errorMsg += '未知错误，请稍后重试。';
                }
                alert(errorMsg.trim());
                //
            }
        });
    });

    // --- 4. 页面初始化 ---
    // 首次进入页面时加载数据
    loadMyItems();
    fetchUnreadCount(); // 调用新函数
});