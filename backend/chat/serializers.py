from rest_framework import serializers
from .models import ChatRoom, ChatMessage
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']

class ChatMessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(source='user', read_only=True)
    recipient = UserSerializer(read_only=True)
    room = serializers.CharField(source='room.name', read_only=True)
    timestamp = serializers.DateTimeField(source='created_at', read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'room',
            'sender',
            'recipient',
            'content',
            'timestamp',
            'is_read'
        ]
        read_only_fields = fields

class ChatRoomSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    def get_other_participant(self, obj):
        current_user = self.context['request'].user
        other_user = obj.participants.exclude(id=current_user.id).first()
        return UserSerializer(other_user, context=self.context).data if other_user else None

    def get_unread_count(self, obj):
        return obj.messages.filter(
            recipient=self.context['request'].user,
            is_read=False
        ).count()

    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'id': last_msg.id,
                'content': last_msg.content,
                'sender': UserSerializer(last_msg.user).data,
                'timestamp': last_msg.created_at.isoformat(),
                'is_read': last_msg.is_read
            }
        return None

    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'other_participant',
            'unread_count',
            'last_message'
        ]
        read_only_fields = fields

class ChatRoomCreateSerializer(serializers.Serializer):
    participant_usernames = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="包含目标用户名的数组（未来支持多人聊天）"
    )

    def validate_participant_usernames(self, value):
        if len(value) != 1:
            raise serializers.ValidationError("当前仅支持1对1聊天")
        return value

    def create(self, validated_data):
        current_user = self.context['request'].user
        target_username = validated_data['participant_usernames'][0]
        
        try:
            target_user = User.objects.get(username=target_username)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                "error": f"用户 {target_username} 不存在",
                "code": "user_not_found"
            })

        # 生成标准房间名（按ID排序）
        user1_id, user2_id = sorted([current_user.id, target_user.id])
        room_name = f"private_{user1_id}_{user2_id}"

        # Get or Create逻辑
        room, created = ChatRoom.objects.get_or_create(
            name=room_name,
            defaults={'creator': current_user}
        )

        if created:
            room.participants.add(current_user, target_user)
        return room

    def to_representation(self, instance):
        return ChatRoomSerializer(instance, context=self.context).data
'''from rest_framework import serializers
from .models import ChatRoom, ChatMessage
from django.contrib.auth import get_user_model
from items.serializers import ItemSerializer 

User = get_user_model()
''
class ChatMessageSerializer(serializers.ModelSerializer):
    # 新增：添加发送者详细信息字段
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)  # 新增字段
    
    class Meta:
        model = ChatMessage
        fields = [
            'id', 
            'room_id', 
            'room_name',  # 新增字段
            'user_id', 
            'username', 
            'content', 
            'created_at',
            'is_read'
        ]
        read_only_fields = ['created_at', 'user_id', 'username']  # 明确所有只读字段''
class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='user.username', read_only=True)
    recipient_name = serializers.CharField(source='recipient.username', read_only=True)
    room_name = serializers.CharField(source='room.name', read_only=True)

    recipient_name_input = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'room_id',
            'room_name',
            'sender_name',
            'recipient_name',
            'recipient_name_input',
            'content',
            'created_at',
            'is_read'
        ]
        read_only_fields = ['created_at', 'is_read']
    def create(self, validated_data):
        # 从 validated_data 中提取 recipient_name_input 并转换为 User 对象
        recipient_name = validated_data.pop('recipient_name_input')
        recipient = get_object_or_404(User, username=recipient_name)
        
        # 调用父类方法保存数据
        return super().create({
            **validated_data,
            'recipient': recipient
        })
        

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']  # 可根据需要扩展字段

class ChatRoomSerializer(serializers.ModelSerializer):
    other_participant = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    def get_other_participant(self, obj):
        current_user = self.context['request'].user
        return UserSerializer(
            obj.participants.exclude(id=current_user.id).first(),
            context=self.context
        ).data

    def get_unread_count(self, obj):
        return obj.messages.filter(
            recipient=self.context['request'].user,
            is_read=False
        ).count()
    
    class Meta:
        model = ChatRoom
        fields = [
            'id',
            'name',
            'participants',
            'created_at',
            'latest_message',
            #'related_item'
        ]
        read_only_fields = fields

    def get_latest_message(self, obj):
        latest_msg = obj.messages.order_by('-created_at').first()
        if latest_msg:
            return {
                'id': latest_msg.id,
                'content': latest_msg.content,
                'sender_id': latest_msg.user.id,
                'sender_name': latest_msg.user.username,
                'timestamp': latest_msg.created_at.isoformat()
            }
        return None

# 专门用于创建聊天室的序列化器
class ChatRoomCreateSerializer(serializers.ModelSerializer):
    participant_usernames = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=True
    )

    class Meta:
        model = ChatRoom
        fields = ['name', 'participant_usernames']
        ''extra_kwargs = {
            'related_item': {'required': False}
        }''
''
    def create(self, validated_data):
        usernames = validated_data.pop('participant_usernames')
        room = ChatRoom.objects.create(**validated_data)
        
        # 添加参与者
        users = User.objects.filter(username__in=usernames)
        room.participants.add(*users)
        
        # 确保创建者也在房间中
        if self.context['request'].user not in room.participants.all():
            room.participants.add(self.context['request'].user)
            
        return room''
    # serializers.py - ChatRoomCreateSerializer 修改
    def create(self, validated_data):
        target_user = User.objects.get(username=validated_data['participant_usernames'][0])
        current_user = self.context['request'].user
    
        # 生成标准房间名（按ID排序）
        user1_id, user2_id = sorted([current_user.id, target_user.id])
        room_name = f"private_{user1_id}_{user2_id}"
    
        # Get or Create逻辑
        room, created = ChatRoom.objects.get_or_create(
            name=room_name,
            defaults={'creator': current_user}
        )
    
        if created:
            room.participants.add(current_user, target_user)
        return room
'''
