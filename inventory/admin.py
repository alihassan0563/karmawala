from django.contrib import admin
from .models import Category, Product, Order, OrderItem, Notification, Sale

# Admin branding
admin.site.site_header = "KarmaWala Administration"
admin.site.site_title = "KarmaWala Admin"
admin.site.index_title = "KarmaWala Admin"

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    search_fields = ('name',)
    list_display = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'sku', 'category', 'size', 'color', 'price', 'stock', 'reorder_threshold', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku', 'color')
    autocomplete_fields = ('category',)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('get_subtotal',)
    
    def get_subtotal(self, obj):
        if obj and obj.pk:
            return f"₨{obj.subtotal:,.0f}"
        return "₨0"
    get_subtotal.short_description = "Subtotal"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_phone', 'status', 'total_amount', 'item_count', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone', 'customer_email')
    readonly_fields = ('order_number', 'total_amount', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'status', 'total_amount', 'created_at', 'updated_at')
        }),
        ('Customer Details', {
            'fields': ('customer_name', 'customer_email', 'customer_phone', 'customer_address')
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'get_subtotal')
    list_filter = ('created_at',)
    search_fields = ('order__order_number', 'product__name', 'product__sku')
    
    def get_subtotal(self, obj):
        return f"₨{obj.subtotal:,.0f}"
    get_subtotal.short_description = "Subtotal"

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at',)
    
    actions = ['mark_as_read', 'mark_as_unread']
    
    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)
        self.message_user(request, f'{queryset.count()} notifications marked as read.')
    mark_as_read.short_description = "Mark selected notifications as read"
    
    def mark_as_unread(self, request, queryset):
        queryset.update(is_read=False)
        self.message_user(request, f'{queryset.count()} notifications marked as unread.')
    mark_as_unread.short_description = "Mark selected notifications as unread"

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'unit_price', 'total_amount', 'created_at', 'created_by')
    list_filter = ('created_at', 'created_by')
    search_fields = ('product__name', 'product__sku')
    autocomplete_fields = ('product',)