# backend\chat\urls.py
from django.urls import path
from . import views
from .views import RoomMarkAllRead

urlpatterns = [
    path('rooms/', views.ChatRoomList.as_view()),
    path('rooms/<str:name>/', views.ChatRoomDetail.as_view()),
    path('rooms/<str:room_name>/messages/', views.MessageList.as_view()),
    path('messages/', views.MessageCreate.as_view()),
    path('messages/<int:pk>/mark_read/', views.MessageMarkRead.as_view()),
    path('rooms/<str:room_name>/mark_as_read/', RoomMarkAllRead.as_view(), name='room-mark-read'),
]
