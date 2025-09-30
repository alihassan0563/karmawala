from django import forms
from .models import Product, Category, Order, OrderItem

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'sku', 'category', 'size', 'color', 'price', 'cost', 'stock', 'reorder_threshold', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., Cotton Casual Shirt, Denim Jeans, Leather Jacket'
            }),
            'sku': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., SHT-001, JNS-BLU-M, JKT-LTR-L'
            }),
            'size': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., S, M, L, XL, 32, 34, EU42'
            }),
            'color': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., Blue, Black, White, Navy, Red'
            }),
            'price': forms.NumberInput(attrs={
                'step': '0.01', 
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 2500.00'
            }),
            'cost': forms.NumberInput(attrs={
                'step': '0.01', 
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 1800.00 (optional)'
            }),
            'stock': forms.NumberInput(attrs={
                'min': 0, 
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 25'
            }),
            'reorder_threshold': forms.NumberInput(attrs={
                'min': 0, 
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 5 (alert when stock ≤ this)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
            }),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., Formal Shirts, Winter Jackets, Sports Shoes'
            }),
            'description': forms.Textarea(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Brief description of this category and what products it includes...'
            }),
        }

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['customer_name', 'customer_email', 'customer_phone', 'customer_address', 'status', 'notes']
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., Ahmed Khan, Muhammad Ali'
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., customer@email.com (optional)'
            }),
            'customer_phone': forms.TextInput(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 03001234567'
            }),
            'customer_address': forms.Textarea(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Complete delivery address with city and postal code'
            }),
            'status': forms.Select(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 2,
                'placeholder': 'Internal notes about this order (optional)'
            }),
        }

class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['product', 'quantity', 'unit_price']
        widgets = {
            'product': forms.Select(attrs={
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'quantity': forms.NumberInput(attrs={
                'min': 1,
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., 2'
            }),
            'unit_price': forms.NumberInput(attrs={
                'step': '0.01',
                'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Price per unit'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show active products
        self.fields['product'].queryset = Product.objects.filter(is_active=True, stock__gt=0)
        # Auto-populate unit price from product price
        if not self.instance.pk and 'product' in self.data:
            try:
                product_id = int(self.data['product'])
                product = Product.objects.get(id=product_id)
                self.fields['unit_price'].initial = product.price
            except (ValueError, Product.DoesNotExist):
                pass

# Formset for handling multiple order items
OrderItemFormSet = forms.inlineformset_factory(
    Order, 
    OrderItem, 
    form=OrderItemForm,
    extra=1,  # Start with 1 empty form
    min_num=1,  # Require at least 1 item
    validate_min=True,
    can_delete=True
)

# Simple form for quick sales to reduce stock
class SellForm(forms.Form):
    product = forms.ModelChoiceField(
        queryset=Product.objects.filter(is_active=True, stock__gt=0),
        widget=forms.Select(attrs={
            'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'input w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'e.g., 1'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        quantity = cleaned_data.get('quantity')
        if product and quantity and product.stock < quantity:
            self.add_error('quantity', f'Only {product.stock} in stock for {product.name}.')
        return cleaned_data