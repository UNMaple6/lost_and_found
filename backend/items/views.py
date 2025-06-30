# backend/items/views.py
from rest_framework import viewsets, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Item
from .serializers import ItemSerializer
from django.http import HttpResponse


def home(request):
    return HttpResponse("Hello, World! 这是根路径 / 的响应，来自 item 应用。")
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().order_by('-created_at')
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]  # 未登录只能读，登录后可写

    # 自动填充当前用户
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # 删除物品（仅允许发布者删除）
    @action(detail=True, methods=['delete'])
    def delete_item(self, request, pk=None):
        item = self.get_object()
        if item.user != request.user:
            return Response({"error": "无权删除他人发布的物品"}, status=403)
        item.delete()
        return Response({"message": "物品删除成功"}, status=200)

    # 示例：筛选接口（按类型和地点）
    def list(self, request):
        queryset = self.queryset
        type_filter = request.query_params.get('type')
        location_filter = request.query_params.get('location')
        if type_filter:
            queryset = queryset.filter(type=type_filter)
        if location_filter:
            queryset = queryset.filter(location__icontains=location_filter)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)




  