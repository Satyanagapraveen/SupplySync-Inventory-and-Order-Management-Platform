from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsAdminUser
from .models import Category
from .serializers import CategorySerializer, CategoryTreeSerializer
from .services import create_category, get_category_tree

class CategoryListCreateView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = create_category(serializer.validated_data)
        response_serializer = self.get_serializer(category)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class CategoryTreeView(generics.ListAPIView):
    serializer_class = CategoryTreeSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return get_category_tree()