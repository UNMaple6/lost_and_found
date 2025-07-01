# backend/items/serializers.py
from rest_framework import serializers
from .models import Item
from django.contrib.auth.models import User

class ItemSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'item_class', 'user', 'title', 'description', 'type',
            'location', 'contact', 'image_url','image', 'created_at', 'time', 'is_resolved'
        ]
        read_only_fields = ('user', 'created_at')

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:  # 确保有 request 上下文
                return request.build_absolute_uri(obj.image.url)
            return f"http://10.122.238.99:8000{obj.image.url}"
        return None
    
    def validate_item_class(self, value):
        valid_classes = [choice[0] for choice in Item.ItemClass.choices]
        if value not in valid_classes:
            raise serializers.ValidationError(
                f"物品类别必须是以下之一：{', '.join(valid_classes)}"
            )
        return value

    def validate_time(self, value):
        if value is not None:
            try:
                from datetime import datetime
                if isinstance(value, str):
                    datetime.strptime(value, "%Y-%m-%d")
            except ValueError:
                raise serializers.ValidationError("日期格式必须为 YYYY-MM-DD")
        return value

    def create(self, validated_data):
        # 自动关联当前用户（从请求上下文中获取）
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class MatchSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'title', 'type', 'item_class', 'location',
            'contact', 'image_url', 'created_at', 'is_resolved'
        ]

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return f"http://10.122.238.99:8000{obj.image.url}"
        return None

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("用户名已存在")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user