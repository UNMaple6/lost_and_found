from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Item, MatchNotification
import logging
from datetime import timedelta
from django.db import transaction

logger = logging.getLogger(__name__)


def find_matches(instance, opposite_type):
    """独立匹配函数"""
    try:
        queryset = Item.objects.filter(
            type=opposite_type,
            item_class=instance.item_class,
            is_resolved=False
        ).exclude(user=instance.user)

        logger.debug(f"匹配查询SQL: {str(queryset.query)}")

        # 地点模糊匹配
        if instance.location:
            queryset = queryset.filter(location__icontains=instance.location)

        # 时间范围过滤（7天内）
        if instance.time:
            queryset = queryset.filter(
                time__range=[
                    instance.time - timedelta(days=7),
                    instance.time + timedelta(days=7)
                ]
            )
        return queryset
    except Exception as e:
        logger.error(f"匹配失败: {str(e)}", exc_info=True)
        return Item.objects.none()


'''@receiver(post_save, sender=Item)
def auto_match_and_notify(sender, instance, created, **kwargs):
    """物品保存后的自动匹配和通知信号"""
    if not created:
        return

    # 只处理新创建的拾取物品(FOUND)来匹配丢失物品(LOST)
    if instance.type != 'FOUND':
        return

    def notify_matches():
        # 重新从数据库加载最新数据，确保获取最新的contact信息
        try:
            # 查找匹配的丢失物品
            matches = find_matches(instance, opposite_type='LOST')
            if not matches.exists():
                logger.debug(f"无匹配丢失物品（拾物ID:{instance.id}）")
                return

            logger.info(f"找到 {matches.count()} 个匹配的丢失物品")

            for lost_item in matches:
                # 重新从数据库加载丢失物品，确保获取最新数据
                fresh_lost_item = Item.objects.get(pk=lost_item.pk)

                # 获取联系方式
                contact = Item.objects.filter(pk=fresh_lost_item.pk).values_list('contact', flat=True).first()
                if not contact:
                    logger.warning(f"物品ID {fresh_lost_item.id} 未设置联系方式，跳过通知")
                    continue

                logger.debug(f"准备通知失主，物品ID: {fresh_lost_item.id}, 联系方式: {recipient}")

                # 检查是否已经通知过
                if MatchNotification.objects.filter(
                        lost_item=fresh_lost_item,
                        found_item=instance
                ).exists():
                    logger.info(f"已通知过失主 {recipient}，跳过")
                    continue

                subject = "【物品匹配提醒】可能找到了您丢失的物品！"
                message = f"""
                您好！

                有用户发布了与您丢失的物品匹配的招领信息：
                - 物品类型: {fresh_lost_item.get_item_class_display()}
                - 地点: {fresh_lost_item.location}
                - 描述: {fresh_lost_item.description}

                请尽快登录系统确认：http://127.0.0.1:8000/api/items/{fresh_lost_item.id}/matches/
                """

                try:
                    send_mail(
                        subject=subject,
                        message=message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[recipient],
                        fail_silently=False,
                    )
                    logger.info(f"邮件发送成功：{recipient}")

                    # 记录通知历史
                    MatchNotification.objects.create(
                        lost_item=fresh_lost_item,
                        found_item=instance,
                        notified_at=timezone.now()
                    )

                except Exception as e:
                    logger.error(f"邮件发送失败（物品 {instance.id} → {recipient}）: {str(e)}", exc_info=True)

        except Exception as e:
            logger.error(f"通知处理过程中发生错误: {str(e)}", exc_info=True)

    # 使用事务提交后执行
    transaction.on_commit(notify_matches)'''

@receiver(post_save, sender=Item)
def auto_match_and_notify(sender, instance, created, **kwargs):
    if not created or instance.type != 'FOUND':
        return

    matches = find_matches(instance, opposite_type='LOST')
    if not matches.exists():
        logger.debug(f"无匹配丢失物品（拾物ID:{instance.id}）")
        return

    logger.info(f"找到 {matches.count()} 个匹配的丢失物品")
    for lost_item in matches:
        # 关键修改：优先使用 lost_item.contact 作为收件人
        recipient = lost_item.contact  # 前端填写的联系方式
        if not recipient:
            # 如果 contact 为空，尝试从 User 模型获取
            recipient = lost_item.user.email
            if not recipient:
                logger.warning(f"用户 {lost_item.user} 未设置邮箱，跳过通知")
                continue

        logger.info(f"准备通知失主，联系方式: {recipient}")

        if MatchNotification.objects.filter(
            lost_item=lost_item,
            found_item=instance
        ).exists():
            logger.info(f"已通知过失主 {recipient}，跳过")
            continue

        subject = "【物品匹配提醒】可能找到了您丢失的物品！"
        message = f"""
        您好！

        有用户发布了与您丢失的物品匹配的招领信息：
        - 物品类型: {lost_item.get_item_class_display()}
        - 地点: {lost_item.location}
        - 描述: {lost_item.description}

        请尽快登录系统确认：http://10.122.197.122:8000/api/items/{lost_item.id}/matches/
        """

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],  # 使用 contact 或 user.email
                fail_silently=False,
            )
            logger.info(f"邮件发送成功：{recipient}")
            MatchNotification.objects.create(
                lost_item=lost_item,
                found_item=instance,
                notified_at=timezone.now()
            )
        except Exception as e:
            logger.error(f"邮件发送失败（物品 {instance.id} → {recipient}）: {str(e)}", exc_info=True)
