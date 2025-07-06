from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from .models import Item
from .serializers import ItemSerializer, UserSerializer
from django.http import HttpResponse
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
import hashlib
from django.contrib.auth.models import User
import jieba
from django.db.models import Q  # 确保导入 Q 对象
from .serializers import MatchSerializer
import logging
from chat.models import User
from django.db.models.functions import Concat
from django.db.models import Value, CharField


jieba.initialize()
logger = logging.getLogger(__name__)

def home(request):
    return HttpResponse("Hello, World! 这是根路径 / 的响应，来自 item 应用。")

class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    # 动态权限控制：不同动作不同权限
    permission_classes_by_action = {
        'list': [permissions.AllowAny],  # 所有人可查看列表
        'retrieve': [permissions.AllowAny],  # 所有人可查看详情
        'create': [permissions.IsAuthenticated],  # 仅登录用户可创建
        'update': [permissions.IsAuthenticated],  # 仅登录用户可修改
        'partial_update': [permissions.IsAuthenticated],
        'destroy': [permissions.IsAuthenticated],  # 仅登录用户可删除
        'resolve': [permissions.IsAuthenticated],  # 仅登录用户可标记为已解决
    }

    def get_permissions(self):
        try:
            # 根据当前动作返回对应的权限类
            return [permission() for permission in self.permission_classes_by_action[self.action]]
        except KeyError:
            # 默认权限（通常不会执行到这里）
            return [permission() for permission in self.permission_classes]

    def get_queryset(self):
        queryset = Item.objects.all().order_by('-created_at')

        # 1. 按文字描述筛选（原有逻辑）
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(item_class__icontains=search_query) |
                Q(location__icontains=search_query) |
                Q(time__icontains=search_query)
            )

        # 2. 按坐标范围筛选（新增逻辑）
        lat = self.request.query_params.get('lat')  # 中心点纬度
        lon = self.request.query_params.get('lon')  # 中心点经度
        radius = self.request.query_params.get('radius', '0.0002')  # 默认范围：0.01度（约1公里） 20米

        if lat and lon:
            try:
                lat = float(lat)
                lon = float(lon)
                radius = float(radius)
                # 筛选出坐标在 [lat ± radius] 和 [lon ± radius] 范围内的物品
                queryset = queryset.filter(
                    latitude__gte=lat - radius,
                    latitude__lte=lat + radius,
                    longitude__gte=lon - radius,
                    longitude__lte=lon + radius,
                )
            except (ValueError, TypeError):
                pass  # 参数无效时忽略筛选

        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def find_matches(self, item):
        """简单的匹配算法"""
        opposite_type = 'FOUND' if item.type == 'LOST' else 'LOST'

        # 基本匹配条件：相反类型 + 相同分类 + 未解决
        queryset = Item.objects.filter(
            type=opposite_type,
            item_class=item.item_class,
            is_resolved=False
        ).exclude(user=item.user)  # 排除自己发布的

        # 关键词匹配（从标题和描述中提取关键词）
        keywords = self.extract_keywords(item.title) + self.extract_keywords(item.description)

        # 如果没有关键词，返回空列表
        if not keywords:
            return queryset.none()

        # 对每个关键词进行过滤
        for keyword in keywords:
            queryset = queryset.filter(
                Q(title__icontains=keyword) |
                Q(description__icontains=keyword)
            )

        # 按创建时间排序并限制数量
        matches = queryset.order_by('-created_at').distinct()[:5]

        # 调试日志
        logger = logging.getLogger(__name__)
        logger.debug(f"物品 {item.id} 的匹配结果: {[m.id for m in matches]}")

        return matches

    def extract_keywords(self, text):
        """从文本中提取关键词"""
        if not text:
            return []
        # 使用jieba进行中文分词
        return [word for word in jieba.cut_for_search(text) if len(word) > 1]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"error": "无权删除他人发布的物品"}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response({"message": "物品删除成功"}, status=status.HTTP_200_OK)

    #模糊搜索，主页的搜索
    def list(self, request):
        queryset = self.get_queryset()
        search_query = request.query_params.get('search', None)

        if search_query:
            # 分别匹配 title 或 description，用 OR 组合
            queryset = queryset.filter(
                Q(title__icontains=search_query) |  # 匹配 title
                Q(description__icontains=search_query)  # 匹配 description
            )

            # 地理位置过滤（保持不变）
            lat = request.query_params.get('lat')
            lon = request.query_params.get('lon')
            radius = request.query_params.get('radius', '0.0002')
            if lat and lon:
                try:
                    lat, lon, radius = float(lat), float(lon), float(radius)
                    queryset = queryset.filter(
                        latitude__gte=lat - radius,
                        latitude__lte=lat + radius,
                        longitude__gte=lon - radius,
                        longitude__lte=lon + radius,
                    )
                except (ValueError, TypeError):
                    pass

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        # 1. 获取当前物品实例
        instance = self.get_object()

        # 2. 权限检查：仅允许物品发布者修改
        if instance.user != request.user:
            return Response({"error": "无权修改他人发布的信息"}, status=status.HTTP_403_FORBIDDEN)

        # 3. 执行部分更新（DRF 默认支持部分更新）
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 4. 返回更新后的完整物品对象
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        item = self.get_object()
        if item.user != request.user:
            return Response({"error": "无权操作他人发布的信息"}, status=status.HTTP_403_FORBIDDEN)
        item.is_resolved = True
        item.save()
        return Response({"message": "状态已更新为已解决"})

    @action(detail=False, methods=['get'])
    def mine(self, request):
        # 仅返回当前用户发布的物品
        queryset = Item.objects.filter(user=request.user).order_by('-created_at')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def matches(self, request, pk=None):
        # 新增的匹配查询接口
        item = self.get_object()
        matches = self.find_matches(item)
        serializer = MatchSerializer(matches, many=True, context={'request': request})
        return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    username = request.data.get('username')
    raw_password = request.data.get('password')

    if not username or not raw_password:
        return Response({'error': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    # 1. 计算SHA-1哈希值
    hashed_password = hashlib.sha1(raw_password.encode('utf-8')).hexdigest()

    # 2. 检查用户名是否已存在
    if User.objects.filter(username=username).exists():
        return Response({'error': '用户名已存在'}, status=status.HTTP_400_BAD_REQUEST)

    # 3. 创建用户（直接存储SHA-1哈希值）
    try:
        user = User.objects.create(
            username=username,
            password=hashed_password  # 直接存储哈希值
        )
        Token.objects.create(user=user)
        return Response({
            'message': '注册成功',
            'user':{ 'id':user.id,'username':username}
        }, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get('username')
    raw_password = request.data.get('password')

    if not username or not raw_password:
        return Response({'error': '用户名和密码不能为空'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        # 1. 获取用户
        user = User.objects.get(username=username)

        # 2. 计算输入密码的SHA-1哈希值
        hashed_input = hashlib.sha1(raw_password.encode('utf-8')).hexdigest()

        # 3. 验证哈希值是否匹配
        if hashed_input == user.password:  # 直接比较哈希值
            token, _ = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user':{ 'id':user.id,'username':username}
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)