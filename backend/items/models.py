#backend/items/models
from django.db import models
from django.contrib.auth.models import User
from django.conf import settings


class Item(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # 动态引用自定义用户模型
        on_delete=models.CASCADE
    )
    title = models.CharField(max_length=100, verbose_name="物品标题")
    description = models.TextField(blank=True, verbose_name="描述")

    # 物品类别选择项
    class ItemClass(models.TextChoices):
        ELECTRONICS = "电子产品", "电子产品"
        CERTIFICATE = "证件卡片", "证件卡片"
        STUDY = "学习用品", "学习用品"
        LIVING = "生活用品", "生活用品"
        OTHERS = "其他", "其他"

    item_class = models.CharField(
        max_length=20,
        choices=ItemClass.choices,
        default=ItemClass.OTHERS,
        verbose_name="物品类别",
        help_text="必须是：电子产品、证件卡片、学习用品、生活用品、其他"
    )

    type = models.CharField(
        max_length=10,
        choices=[('LOST', '失物'), ('FOUND', '招领')],
        verbose_name="类型"
    )
    location = models.CharField(max_length=50, blank=True, verbose_name="地点描述")  # 改为可选
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="纬度")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="经度")
    contact = models.CharField(max_length=100, verbose_name="联系方式")
    image = models.ImageField(upload_to='item_images/', blank=True, null=True, verbose_name="图片")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    is_resolved = models.BooleanField(default=False, verbose_name="是否已解决")

    # 修改 time 字段为 DateField（仅日期）
    time = models.DateField(
        verbose_name="事件日期",
        null=True,
        blank=True,
        help_text="格式：YYYY-MM-DD（可选）"
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "物品"
        verbose_name_plural = "物品"


# 新增模型：记录匹配通知历史（避免重复发送邮件）
class MatchNotification(models.Model):
    lost_item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='notifications_received',
        verbose_name="丢失物品"
    )
    found_item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='notifications_sent',
        verbose_name="拾取物品"
    )
    notified_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="通知时间"
    )

    class Meta:
        verbose_name = "匹配通知记录"
        verbose_name_plural = "匹配通知记录"
        unique_together = ('lost_item', 'found_item')  # 确保同一对匹配只通知一次

    def __str__(self):
        return f"{self.lost_item} ↔ {self.found_item} (通知于 {self.notified_at})"
