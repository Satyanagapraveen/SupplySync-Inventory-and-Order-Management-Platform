from rest_framework import serializers
from .models import Category
from drf_spectacular.utils import extend_schema_field


class CategorySerializer(serializers.ModelSerializer):
    category_code = serializers.CharField(required=False, allow_blank=True)
    class Meta:
        model = Category
        fields = ['id', 'category_code', 'name', 'description', 'parent_category', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

@extend_schema_field('apps.categoried.serializers.CategorySerializer(many=True)')
@extend_schema_field(serializers.ListField(child=serializers.DictField()))
class CategoryTreeSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'category_code', 'name', 'description', 'children']

    def get_children(self, obj):
        if obj.children.exists():
            children_queryset = obj.children.all()
            return CategoryTreeSerializer(children_queryset, many=True).data
        return []