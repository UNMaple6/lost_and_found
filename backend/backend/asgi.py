import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from django.urls import path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 必须在最前面设置环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()
# 初始化Django
django_asgi_app = get_asgi_application()

# 延迟导入以避免循环依赖
from chat.consumers import ChatConsumer



# WebSocket路由配置
websocket_urlpatterns = [
    path('ws/chat/<str:room_name>/', ChatConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    
    
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
