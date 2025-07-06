from django.contrib import admin
from .models import ChatRoom, ChatMessage

# ChatRoom 管理员配置
@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'get_related_item')
    
    def get_related_item(self, obj):
        return str(obj.related_item) if obj.related_item else '-'
    get_related_item.short_description = 'Related Item'

# ChatMessage 管理员配置
@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'created_at', 'is_read')
