from rest_framework import serializers
from .models import Category, Product

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    inventory_value = serializers.ReadOnlyField()
    low_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'category', 'category_name', 'size', 'color',
            'price', 'cost', 'stock', 'reorder_threshold', 'is_active',
            'created_at', 'updated_at', 'inventory_value', 'low_stock'
        ]
        read_only_fields = ['created_at', 'updated_at']
