# backend/items/serializers.py
from rest_framework import serializers
from .models import Item
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)


class ItemSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'item_class', 'user', 'title', 'description', 'type',
            'location', 'latitude', 'longitude', 'contact', 'image_url', 'image', 'created_at', 'time', 'is_resolved'
        ]
        read_only_fields = ('user', 'created_at')

    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:  # 确保有 request 上下文
                return request.build_absolute_uri(obj.image.url)
            return f"http://10.122.238.99:8000{obj.image.url}"
        return None

    def get_contact(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.contact  # 登录用户返回完整联系方式
        return obj.contact[:3] + "***" if obj.contact else ""  # 匿名用户打码处理

    def validate(self, data):
        if not data or (
                'location' not in data and
                'latitude' not in data and
                'longitude' not in data
        ):
            return data  # 直接通过验证

        """校验 location 和坐标至少提供一个"""
        location = data.get('location', '').strip()
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not location and not (latitude and longitude):
            raise serializers.ValidationError({
                "non_field_errors": ["请至少提供地点描述或在地图上选点。"]
            })
        return data

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
        contact = validated_data.get('contact')  # 确保从验证数据中提取
        instance = super().create(validated_data)  # 创建 Item
        if contact:
            instance.contact = contact
            instance.save()
        logger.debug(f"创建物品: ID={instance.id}, Contact='{instance.contact}'")  # 调试日志
        return instance


class MatchSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            'id', 'title', 'type', 'item_class', 'location',
            'contact', 'image_url', 'created_at', 'is_resolved', 'description', 'time'
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
