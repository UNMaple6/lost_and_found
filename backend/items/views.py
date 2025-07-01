from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action, api_view, permission_classes
from .models import Item
from .serializers import ItemSerializer, UserSerializer
from django.http import HttpResponse
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate

def home(request):
    return HttpResponse("Hello, World! 这是根路径 / 的响应，来自 item 应用。")

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all().order_by('-created_at')
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.user != request.user:
            return Response({"error": "无权删除他人发布的物品"}, status=status.HTTP_403_FORBIDDEN)
        self.perform_destroy(instance)
        return Response({"message": "物品删除成功"}, status=status.HTTP_200_OK)

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

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        item = self.get_object()
        if item.user != request.user:
            return Response({"error": "无权操作他人发布的信息"}, status=status.HTTP_403_FORBIDDEN)
        item.is_resolved = True
        item.save()
        return Response({"message": "状态已更新为已解决"})

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        Token.objects.create(user=user)
        return Response({
            'message': '注册成功',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login(request):
    username = request.data.get('username')
    password = request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_id': user.id
        }, status=status.HTTP_200_OK)
    return Response(
        {'error': '用户名或密码错误'},
        status=status.HTTP_401_UNAUTHORIZED
    )