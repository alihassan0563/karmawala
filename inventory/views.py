from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum, F
from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import uuid

from .models import Product, Category, Order, OrderItem, Notification, Sale
from .forms import ProductForm, CategoryForm, OrderForm, OrderItemFormSet, SellForm

@login_required
def dashboard(request):
    total_products = Product.objects.filter(is_active=True).count()
    total_stock = Product.objects.aggregate(s=Sum('stock'))['s'] or 0
    inventory_value = Product.objects.aggregate(v=Sum(F('price') * F('stock')))['v'] or Decimal('0.00')
    low_stock_count = Product.objects.filter(reorder_threshold__gt=0, stock__lte=F('reorder_threshold')).count()

    low_stock_items = Product.objects.filter(reorder_threshold__gt=0, stock__lte=F('reorder_threshold')).order_by('stock')[:10]
    recent_items = Product.objects.order_by('-created_at')[:10]
    
    # Order statistics
    pending_orders = Order.objects.filter(status='pending').count()
    recent_orders = Order.objects.order_by('-created_at')[:5]
    
    # Unread notifications
    unread_notifications = Notification.objects.filter(is_read=False).order_by('-created_at')[:5]

    # Sales summary for dashboard (guard if table not migrated yet)
    try:
        total_sales_count = Sale.objects.count()
        total_sales_amount = Sale.objects.aggregate(v=Sum('total_amount'))['v'] or Decimal('0.00')
        recent_sales = Sale.objects.select_related('product').order_by('-created_at')[:5]
    except Exception:
        total_sales_count = 0
        total_sales_amount = Decimal('0.00')
        recent_sales = []

    return render(request, 'dashboard.html', {
        'total_products': total_products,
        'total_stock': total_stock,
        'inventory_value': inventory_value,
        'low_stock_count': low_stock_count,
        'low_stock_items': low_stock_items,
        'recent_items': recent_items,
        'pending_orders': pending_orders,
        'recent_orders': recent_orders,
        'unread_notifications': unread_notifications,
        'total_sales_count': total_sales_count,
        'total_sales_amount': total_sales_amount,
        'recent_sales': recent_sales,
    })

@login_required
def create_category_ajax(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            
            if not name:
                return JsonResponse({'success': False, 'error': 'Category name is required'})
            
            # Check if category already exists
            if Category.objects.filter(name__iexact=name).exists():
                return JsonResponse({'success': False, 'error': 'Category with this name already exists'})
            
            # Create new category
            category = Category.objects.create(name=name, description=description)
            
            return JsonResponse({
                'success': True,
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'description': category.description
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def create_order_ajax(request):
    """AJAX endpoint for creating orders (for external systems or customer interface)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Generate unique order number
            order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
            
            # Create order
            order = Order.objects.create(
                order_number=order_number,
                customer_name=data.get('customer_name'),
                customer_email=data.get('customer_email', ''),
                customer_phone=data.get('customer_phone'),
                customer_address=data.get('customer_address'),
            )
            
            # Add order items
            total_amount = Decimal('0.00')
            for item_data in data.get('items', []):
                product = get_object_or_404(Product, id=item_data['product_id'])
                quantity = int(item_data['quantity'])
                
                # Check stock availability
                if product.stock < quantity:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Insufficient stock for {product.name}. Available: {product.stock}, Requested: {quantity}'
                    })
                
                order_item = OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    unit_price=product.price
                )
                total_amount += order_item.subtotal
            
            # Update order total
            order.total_amount = total_amount
            order.save()
            
            return JsonResponse({
                'success': True,
                'order': {
                    'order_number': order.order_number,
                    'total_amount': str(order.total_amount),
                    'status': order.status
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def mark_notification_read(request, notification_id):
    """Mark a notification as read"""
    try:
        notification = get_object_or_404(Notification, id=notification_id)
        notification.is_read = True
        notification.save()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def sell(request):
    """Simple sell page to reduce stock for a selected product"""
    if request.method == 'POST':
        form = SellForm(request.POST)
        if form.is_valid():
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity']

            # Reduce stock safely
            if product.reduce_stock(quantity):
                # Optional: create a notification for stock update/low stock
                if product.low_stock:
                    Notification.objects.create(
                        type='low_stock',
                        title=f'Low Stock Alert: {product.name}',
                        message=f'{product.name} is now at {product.stock} units (threshold: {product.reorder_threshold})',
                        product=product
                    )
                # Record the sale
                Sale.objects.create(
                    product=product,
                    quantity=quantity,
                    unit_price=product.price,
                    total_amount=product.price * quantity,
                    created_by=request.user if request.user.is_authenticated else None
                )
                return render(request, 'sell.html', {
                    'form': SellForm(),
                    'success_message': f'Sold {quantity} x {product.name}. Remaining stock: {product.stock}.',
                })
            else:
                form.add_error('quantity', f'Insufficient stock. Available: {product.stock}.')
    else:
        form = SellForm()

    return render(request, 'sell.html', {'form': form})

class SalesListView(LoginRequiredMixin, ListView):
    model = Sale
    template_name = 'sales_list.html'
    context_object_name = 'sales'
    paginate_by = 20

    def get_queryset(self):
        qs = Sale.objects.select_related('product').order_by('-created_at')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page_sales = list(context['sales'])
        page_total_amount = sum((s.total_amount for s in page_sales), Decimal('0.00'))
        page_items_sold = sum((s.quantity for s in page_sales), 0)
        context['page_total_amount'] = page_total_amount
        context['page_items_sold'] = page_items_sold
        return context

class SaleDeleteView(LoginRequiredMixin, DeleteView):
    model = Sale
    template_name = 'sale_confirm_delete.html'
    success_url = reverse_lazy('sales-list')

class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category').order_by('name')
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(color__icontains=search)
            )
        
        # Category filter
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        
        # Stock status filter
        stock_status = self.request.GET.get('stock_status')
        if stock_status == 'low_stock':
            qs = qs.filter(reorder_threshold__gt=0, stock__lte=F('reorder_threshold'))
        elif stock_status == 'out_of_stock':
            qs = qs.filter(stock=0)
        elif stock_status == 'in_stock':
            qs = qs.filter(stock__gt=0)
        
        return qs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all().order_by('name')
        return context

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = Order.objects.prefetch_related('items__product').order_by('-created_at')
        
        # Status filter
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        
        # Search functionality
        search = self.request.GET.get('search')
        if search:
            qs = qs.filter(
                Q(order_number__icontains=search) |
                Q(customer_name__icontains=search) |
                Q(customer_phone__icontains=search)
            )
        
        return qs

class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        qs = Notification.objects.order_by('-created_at')
        
        # Filter by type
        notification_type = self.request.GET.get('type')
        if notification_type:
            qs = qs.filter(type=notification_type)
        
        # Filter by read status
        is_read = self.request.GET.get('is_read')
        if is_read == 'unread':
            qs = qs.filter(is_read=False)
        elif is_read == 'read':
            qs = qs.filter(is_read=True)
        
        return qs

class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'product_detail.html'
    context_object_name = 'product'

class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('product-list')

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'product_form.html'
    success_url = reverse_lazy('product-list')

class ProductDeleteView(LoginRequiredMixin, DeleteView):
    model = Product
    template_name = 'product_confirm_delete.html'
    success_url = reverse_lazy('product-list')

class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category_form.html'
    success_url = reverse_lazy('category-list')

class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'category_form.html'
    success_url = reverse_lazy('category-list')

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'category_confirm_delete.html'
    success_url = reverse_lazy('category-list')

class OrderCreateView(LoginRequiredMixin, CreateView):
    model = Order
    form_class = OrderForm
    template_name = 'order_form.html'
    success_url = reverse_lazy('order-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = OrderItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        # Generate unique order number
        form.instance.order_number = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            # Calculate total amount
            self.object.calculate_total()
            
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    form_class = OrderForm
    template_name = 'order_form.html'
    success_url = reverse_lazy('order-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['formset'] = OrderItemFormSet(self.request.POST, instance=self.object)
        else:
            context['formset'] = OrderItemFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        formset = context['formset']
        
        if formset.is_valid():
            self.object = form.save()
            formset.instance = self.object
            formset.save()
            
            # Recalculate total amount
            self.object.calculate_total()
            
            return super().form_valid(form)
        else:
            return self.render_to_response(self.get_context_data(form=form))

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'order_detail.html'
    context_object_name = 'order'