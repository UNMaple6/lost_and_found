from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import ChatRoom

@receiver(post_save, sender=ChatRoom)
def add_default_participants(sender, instance, created, **kwargs):
    if created :#and instance.related_item:
        # 自动添加物品所有者和当前用户到聊天室
        #instance.participants.add(instance.related_item.user_id)
        print(f"New chat room created: {instance.name}")
