from django.db import models
from django.contrib.auth.models import User


class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="关联用户")
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
    location = models.CharField(max_length=50, verbose_name="地点")
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