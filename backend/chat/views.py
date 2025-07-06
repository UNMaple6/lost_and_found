from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.pagination import PageNumberPagination
from .models import ChatRoom, ChatMessage
from .serializers import (
    ChatRoomSerializer,
    ChatMessageSerializer,
    ChatRoomCreateSerializer
)
from rest_framework import serializers

User = get_user_model()

class StandardResultsPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 100

class ChatRoomList(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_serializer_class(self):
        return ChatRoomCreateSerializer if self.request.method == 'POST' else ChatRoomSerializer

    def get_queryset(self):
        return self.request.user.chat_rooms.all().prefetch_related(
            'participants',
            'messages__user',
            'messages__recipient'
        ).order_by('-messages__created_at')
    def create(self, request, *args, **kwargs):
        try:
            return super().create(request, *args, **kwargs)
        except serializers.ValidationError as e:
            return Response(
                {"error": str(e.detail) if hasattr(e, 'detail') else str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "创建聊天室失败", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    '''def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        headers = self.get_success_headers(serializer.data)
        return Response(
            ChatRoomSerializer(instance, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )'''

class ChatRoomDetail(generics.RetrieveDestroyAPIView):
    serializer_class = ChatRoomSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'name'

    def get_queryset(self):
        return ChatRoom.objects.filter(
            participants=self.request.user
        )

    def perform_destroy(self, instance):
        if instance.creator != self.request.user:
            return Response(
                {"error": "只有创建者可以解散聊天室"},
                status=status.HTTP_403_FORBIDDEN
            )
        instance.delete()

class MessageList(generics.ListAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsPagination

    def get_queryset(self):
        room = get_object_or_404(
            ChatRoom,
            name=self.kwargs['room_name'],
            participants=self.request.user
        )
        return ChatMessage.objects.filter(
            room=room
        ).select_related(
            'user',
            'recipient',
            'room'
        ).order_by('-created_at')

class MessageCreate(generics.CreateAPIView):
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        room = get_object_or_404(
            ChatRoom,
            name=serializer.validated_data['room']['name'],
            participants=self.request.user
        )
        recipient = room.participants.exclude(id=self.request.user.id).first()
        
        serializer.save(
            user=self.request.user,
            recipient=recipient,
            room=room
        )

class MessageMarkRead(generics.UpdateAPIView):
    queryset = ChatMessage.objects.filter(is_read=False)
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        message = self.get_object()
        if message.recipient != request.user:
            return Response(
                {"error": "只能标记自己收到的消息为已读"},
                status=status.HTTP_403_FORBIDDEN
            )
        message.is_read = True
        message.save()
        return Response({"status": "marked as read"})

# 在 views.py 中添加以下内容
class RoomMarkAllRead(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, room_name):
        room = get_object_or_404(
            ChatRoom,
            name=room_name,
            participants=request.user
        )
        
        # 更新所有未读消息
        updated = ChatMessage.objects.filter(
            room=room,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
        
        return Response({
            "status": "success",
            "message": f"{updated}All messages marked as read."
        }, status=status.HTTP_200_OK)
