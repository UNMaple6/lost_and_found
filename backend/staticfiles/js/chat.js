$(document).ready(function () {
    // --- 1. 初始化和身份验证 ---
    const token = localStorage.getItem('token');
    const myUserId = localStorage.getItem('userId'); // 【假设】登录时已存储用户ID

    if (!token || !myUserId) {
        alert('认证信息不完整，请重新登录！');
        window.location.href = 'login.html';
        return;
    }

    const urlParams = new URLSearchParams(window.location.search);
    const roomName = urlParams.get('room');

    if (!roomName) {
        alert('未指定聊天室！');
        window.location.href = 'personal-center.html';
        return;
    }

    const messagesContainer = $('#messages-container');
    const messageInput = $('#message-input');
    const sendButton = $('#send-button');

    let socket = null;

    // --- 2. 封装函数 ---

    // 滚动到聊天记录底部
    function scrollToBottom() {
        messagesContainer.scrollTop(messagesContainer[0].scrollHeight);
    }
    // 创建并添加一条消息气泡
    function addMessageBubble(message) {
        const isSentByMe = message.sender.id.toString() === myUserId;
        const bubbleClass = isSentByMe ? 'message-sent' : 'message-received';
        const timestamp = new Date(message.timestamp).toLocaleString();

        const messageHtml = `
            <div class="message-bubble ${bubbleClass}">
                <div>${message.content}</div>
                <div class="message-meta text-end">${timestamp}</div>
            </div>
        `;
        messagesContainer.append(messageHtml);
    }
    // --- 3. 加载历史消息 ---
    function loadHistory() {
        $.ajax({
            url: `${API_BASE_URL}/api/rooms/${roomName}/messages/`,
            type: 'GET',
            headers: { 'Authorization': 'Token ' + token },
            success: function (response) {
                $('#loading-history').hide();
                // 假设 response.results 是消息数组，且按时间顺序排列
                let messages = response.results || response;
                // 在渲染之前，确保消息数组是按时间戳升序排列的（从旧到新）
                // Array.sort() 会原地修改数组
                messages.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));

                messages.forEach(addMessageBubble);
                scrollToBottom(); // 加载完历史记录后滚动到底部
                // 加载完历史记录后，在本地记录这个房间已被查看
                markRoomAsRead(roomName); 
                // 加载完历史记录后，再连接WebSocket
                connectWebSocket();
            },
            error: function () {
                $('#loading-history').text('加载历史消息失败。').addClass('text-danger');
            }
        });
    }
    function markRoomAsRead(roomNameToMark) {
        // 确保使用当前token进行调用
        const currentToken = localStorage.getItem('token');
        if (!currentToken) {
            console.error('无法标记为已读：缺少认证令牌');
            return;
        }
        
        console.log(`正在将房间 ${roomNameToMark} 标记为已读...`);
        $.ajax({
            url: `${API_BASE_URL}/api/rooms/${roomNameToMark}/mark_as_read/`,
            type: 'POST',
            headers: { 'Authorization': 'Token ' + currentToken },
            success: function (response) {
                console.log(`房间 ${roomNameToMark} 已成功标记为已读。`, response);
            },
            error: function (xhr, status, error) {
                console.error(`标记房间 ${roomNameToMark} 为已读失败:`, status, error);
            }
        });
    }
    // --- 4. WebSocket 逻辑 ---
    function connectWebSocket() {
        // 使用 ws:// 或 wss:// (安全连接)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${wsProtocol}${API_BASE_URL.split('//')[1]}/ws/chat/${roomName}/?token=${token}`;

        socket = new WebSocket(wsUrl);

        socket.onopen = function () {
            console.log('WebSocket连接成功！');
            sendButton.prop('disabled', false);
        };

        socket.onmessage = function (e) {
            const data = JSON.parse(e.data);
            console.log("收到新消息:", data);

            // 根据后端返回的格式处理消息
            if (data.type === 'chat_message') {
                addMessageBubble(data);
                scrollToBottom();
            }
        };

        socket.onclose = function (e) {
            console.error('WebSocket连接关闭', e);
            sendButton.prop('disabled', true);
            let reason = '连接已断开。';
            if (e.code === 4001) reason = '认证失败，请重新登录。';
            if (e.code === 4003) reason = '无权访问此聊天室。';
            messagesContainer.append(`<p class="text-center text-danger">${reason}</p>`);
        };

        socket.onerror = function (e) {
            console.error('WebSocket发生错误', e);
            messagesContainer.append('<p class="text-center text-danger">连接发生错误。</p>');
        };
    }

    // --- 5. 事件绑定 ---
    function sendMessage() {
        const content = messageInput.val().trim();
        if (content && socket && socket.readyState === WebSocket.OPEN) {
            // 构建符合API文档的消息体
            socket.send(JSON.stringify({
                type: 'chat_message',
                content: content,
            }));
            messageInput.val('');
        }
    }

    sendButton.on('click', sendMessage);
    messageInput.on('keypress', function (e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // --- 6. 页面启动 ---
    // 在页面加载时立即标记房间为已读
    markRoomAsRead(roomName);
    
    // 定义一个函数来设置标题
    function setChatTitle() {
        $.ajax({
            url: `${API_BASE_URL}/api/rooms/${roomName}/`, // 使用我们之前约定好的详情接口
            type: 'GET',
            headers: { 'Authorization': 'Token ' + token },
            success: function (room) {
                if (room && room.other_participant && room.other_participant.username) {
                    $('#chat-title').text(`与 ${room.other_participant.username} 的对话`);
                    console.log(`聊天室标题设置为: 与 ${room.other_participant.username} 的对话`);
                } else {
                    $('#chat-title').text('聊天室');
                }
            },
            error: function () {
                $('#chat-title').text('获取聊天信息失败');
            }
        });
    }

    loadHistory();
    setChatTitle();
});
