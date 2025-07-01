from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Item
from .views import ItemViewSet
import logging

# 配置日志（可选，用于调试）
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Item)
def auto_match_on_item_create(sender, instance, created, **kwargs):
    """
    当新物品创建时自动触发匹配检查
    """
    if created:  # 仅对新创建的物品处理
        try:
            viewset = ItemViewSet()
            matches = viewset.find_matches(instance)
            logger.info(f"Item {instance.id} 创建成功，找到 {matches.count()} 个匹配项")

            # 这里可以后续扩展通知逻辑
            # 例如：将匹配结果存入数据库或调用推送服务

        except Exception as e:
            logger.error(f"物品 {instance.id} 匹配失败: {str(e)}")