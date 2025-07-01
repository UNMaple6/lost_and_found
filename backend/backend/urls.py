from django.contrib import admin
from django.urls import path, include  # 添加 include
from items import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/items/', views.ItemViewSet.as_view({
        'get': 'list',
        'post': 'create',
    })),
    path('api/items/<int:pk>/', views.ItemViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    })),
    path('api/items/<int:pk>/delete/', views.ItemViewSet.as_view({
        'delete': 'delete_item',
    })),
    # 新增注册和登录接口
    path('api/register/', views.register, name='register'),
    path('api/login/', views.login, name='login'),
    # 根路径测试接口
    path('', views.home, name='home'),
]