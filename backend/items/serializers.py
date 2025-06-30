# backend/items/serializers.py
from rest_framework import serializers
from .models import Item

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'user', 'title', 'description', 'type', 'location', 'contact', 'image', 'created_at', 'is_resolved']
        read_only_fields = ['id', 'user', 'created_at']  # 用户和创建时间自动填充，禁止前端修改

    # 验证图片大小（可选）
    def validate_image(self, value):
        if value.size > 5 * 1024 * 1024:  # 限制5MB
            raise serializers.ValidationError("图片大小不能超过5MB")
        return value