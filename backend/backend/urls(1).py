from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from items.views import ItemViewSet, home, register, login
from rest_framework.routers import DefaultRouter

# 创建路由器并注册ItemViewSet
router = DefaultRouter()
router.register(r'api/items', ItemViewSet, basename='item')

urlpatterns = [
    path('admin/', admin.site.urls),
    # 包含自动生成的路由（包含list/create/retrieve/matches等所有动作）
    path('', include(router.urls)),

    # 其他独立路由
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('', home, name='home'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)