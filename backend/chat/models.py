#backend/chat/models
from django.db import models
from django.conf import settings
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    custom_field = models.CharField(max_length=10, default='default')
    
    class Meta:
        db_table = 'chat_user'
        app_label = 'chat'
    '''    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='chat_user_set',
        blank=True,
        verbose_name='groups',
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='chat_user_set',
        blank=True,
        verbose_name='user permissions',
        help_text='Specific permissions for this user.',
    )'''

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True, db_index=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='chat_rooms'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    creator = models.ForeignKey(  # 新增字段，用于权限控制
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_rooms'
    )

    class Meta:
        db_table = 'chat_room'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['creator']),  # 新增索引
        ]
    
    def __str__(self):
        return self.name

    @classmethod
    def get_or_create_private(cls, user1, user2):
        """辅助方法：获取或创建私聊房间"""
        user1_id, user2_id = sorted([user1.id, user2.id])
        room_name = f"private_{user1_id}_{user2_id}"
        return cls.objects.get_or_create(
            name=room_name,
            defaults={'creator': user1}
        )

class ChatMessage(models.Model):
    room = models.ForeignKey(
        ChatRoom,
        on_delete=models.CASCADE,
        related_name='messages',
        db_index=True
    )
    content = models.TextField()
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_messages',
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        db_table = 'chat_message'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['room', 'created_at']),  # 新增索引，优化消息查询
        ]
    
    def __str__(self):
        return f"Msg[{self.id}] in {self.room.name}"
