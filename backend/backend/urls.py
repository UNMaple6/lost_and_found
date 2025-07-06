from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from items.views import ItemViewSet, home, register, login
from rest_framework.routers import DefaultRouter
from django.urls import path, re_path

# 创建路由器并注册ItemViewSet
router = DefaultRouter()
router.register(r'api/items', ItemViewSet, basename='item')
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    
    # 添加前端路由
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    
    # 2. 为其他前端页面创建明确的路由
    path('index.html', TemplateView.as_view(template_name='index.html'), name='index'),
    path('login.html', TemplateView.as_view(template_name='login.html'), name='login'),
    path('publish.html', TemplateView.as_view(template_name='publish.html'), name='publish'),
    path('personal-center.html', TemplateView.as_view(template_name='personal-center.html'), name='personal-center'),
    path('item-detail.html', TemplateView.as_view(template_name='item-detail.html'), name='item-detail'),
    path('chat.html', TemplateView.as_view(template_name='chat.html'), name='chat'),
    path('message-list.html', TemplateView.as_view(template_name='message-list.html'), name='message-list'),
    path('match-results.html', TemplateView.as_view(template_name='match-results.html'), name='match-results'),
    path('', include(router.urls)),
    path('', home, name='home'),
    #path('api/items/',include('items.urls'))
    
    path('api/', include('chat.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
'''
urlpatterns = [
    path('admin/', admin.site.urls),
    # 包含自动生成的路由（包含list/create/retrieve/matches等所有动作）
    path('', include(router.urls)),

    # 其他独立路由
    path('api/register/', register, name='register'),
    path('api/login/', login, name='login'),
    path('', home, name='home'),

    path('api/', include('chat.urls')) ,  # 如果 chat/urls.py 存在
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
'''
