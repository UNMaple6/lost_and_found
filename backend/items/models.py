# backend/items/models.py
from django.db import models
from django.contrib.auth.models import User

class Item(models.Model):
    TYPE_CHOICES = [
        ('LOST', '失物'),
        ('FOUND', '招领'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)  # 关联用户
    title = models.CharField(max_length=100)  # 物品标题
    description = models.TextField(blank=True)  # 描述
    type = models.CharField(max_length=10, choices=TYPE_CHOICES)  # 类型
    location = models.CharField(max_length=50)  # 地点
    contact = models.CharField(max_length=100)  # 联系方式
    image = models.ImageField(upload_to='item_images/', blank=True, null=True)  # 图片
    created_at = models.DateTimeField(auto_now_add=True)  # 创建时间
    is_resolved = models.BooleanField(default=False)  # 是否已解决

    def __str__(self):
        return self.title