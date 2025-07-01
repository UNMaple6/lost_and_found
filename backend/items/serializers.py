# backend/items/serializers.py
from rest_framework import serializers
from .models import Item
from django.contrib.auth.models import User

class ItemSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Item
        fields = [
            'id', 'item_class', 'user', 'title', 'description', 'type',
            'location', 'contact', 'image', 'created_at', 'time', 'is_resolved'
        ]
        read_only_fields = ('user', 'created_at')

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