import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from asgiref.sync import sync_to_async
from .models import ChatRoom, ChatMessage
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

import logging
logger = logging.getLogger(__name__)

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # 从URL参数或headers中获取token
        token = self.scope.get('query_string', b'').decode().split('token=')[-1].split('&')[0]
        if not token:
            # 尝试从headers获取
            headers = dict(self.scope['headers'])
            if b'authorization' in headers:
                auth_header = headers[b'authorization'].decode()
                if auth_header.startswith('Token '):
                    token = auth_header[6:]

        logger.info(f"WebSocket连接尝试 - Token: {token}")

        if token:
            try:
                # 关键修改：直接使用自定义用户模型验证
                from rest_framework.authtoken.models import Token
                from django.contrib.auth import get_user_model
                User = get_user_model()
            
                # 同步方式执行查询
                def sync_get_user():
                    try:
                        token_obj = Token.objects.select_related('user').get(key=token)
                        return User.objects.get(id=token_obj.user_id)  # 直接通过ID获取自定义用户
                    except (Token.DoesNotExist, User.DoesNotExist):
                        return None

                self.scope['user'] = await sync_to_async(sync_get_user)()
            
                if not self.scope['user']:
                    raise ValueError("Invalid token or user")

                logger.info(f"用户认证成功: {self.scope['user'].username}")

            except Exception as e:
                logger.error(f"Token验证失败: {str(e)}")
                await self.close(code=4001)
                return


        if not self.scope.get("user") or not self.scope["user"].is_authenticated:
            logger.error("用户未认证")
            await self.close(code=4001)
            return

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        logger.info(f"尝试加入房间: {self.room_name}")

        if not await self.room_access_check():
            logger.error(f"用户无权访问房间: {self.room_name}")
            await self.close(code=4003)
            return

        await self.accept()
        await self.channel_layer.group_add(
            self.room_name,
            self.channel_name
        )
        logger.info(f"用户 {self.scope['user'].username} 成功加入房间 {self.room_name}")

    @sync_to_async
    def room_access_check(self):
        try:
            return ChatRoom.objects.filter(
                name=self.room_name,
                participants=self.scope["user"]
            ).exists()
        except Exception as e:
            logger.error(f"房间访问检查失败: {e}")
            return False

    async def disconnect(self, close_code):
        if hasattr(self, 'room_name'):
            await self.channel_layer.group_discard(
                self.room_name,
                self.channel_name
            )
            logger.info(f"用户断开连接，关闭代码: {close_code}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data['type'] != 'chat_message':
                raise ValueError("Invalid message type")

            message = await self.save_message(data['content'])
            await self.channel_layer.group_send(
                self.room_name,
                {
                    "type": "chat.message",
                    "message": {
                        "id": message.id,
                        "type": "chat_message",
                        "sender": {
                            "id": self.scope["user"].id,
                            "username": self.scope["user"].username
                        },
                        "recipient": {
                            "id": message.recipient.id,
                            "username": message.recipient.username
                        },
                        "content": message.content,
                        "timestamp": message.created_at.isoformat(),
                        "is_read": False,
                        "room": self.room_name
                    }
                }
            )
        except Exception as e:
            logger.error(f"消息处理错误: {e}")
            await self.send(json.dumps({
                "type": "error",
                "message": str(e)
            }))

    @sync_to_async
    def save_message(self, content):
        try:
            room = ChatRoom.objects.get(name=self.room_name)
            recipient = room.participants.exclude(id=self.scope["user"].id).first()
            message = ChatMessage.objects.create(
                room=room,
                content=content,
                user=self.scope["user"],
                recipient=recipient
            )
            logger.info(f"消息保存成功: {message.id}")
            return message
        except Exception as e:
            logger.error(f"消息保存失败: {e}")
            raise

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['message']))
