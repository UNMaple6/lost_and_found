from django.apps import AppConfig

class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat'

    def ready(self):
        # 检查用户模型是否正确加载
        from django.contrib.auth import get_user_model
        User = get_user_model()
        assert User.__name__ == 'User', "用户模型未正确加载"
        
        # 导入信号处理器（如果有）
        import chat.signals  # 确保chat/signals.py存在
        
        # 注册模型到admin（如果需要）
        from django.db.models.signals import post_migrate
        from django.contrib import admin
        from django.contrib.auth.admin import UserAdmin
        
        def register_model(sender, **kwargs):
            if not admin.site.is_registered(User):
                admin.site.register(User, UserAdmin)
        
        post_migrate.connect(register_model, sender=self)
