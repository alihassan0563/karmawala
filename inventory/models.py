from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Product(models.Model):
    SIZES = [
        ('XS', 'XS'), ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL'),
        ('EU40', 'EU 40'), ('EU41', 'EU 41'), ('EU42', 'EU 42'), ('EU43', 'EU 43'), ('EU44', 'EU 44'),
    ]

    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    size = models.CharField(max_length=10, blank=True)
    color = models.CharField(max_length=50, blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=0, help_text='Alert when stock ≤ this value')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['name']),
        ]
        ordering = ['name']
        unique_together = [('name', 'sku')]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    @property
    def inventory_value(self):
        return self.price * self.stock

    @property
    def low_stock(self):
        return self.reorder_threshold and self.stock <= self.reorder_threshold

    def reduce_stock(self, quantity):
        """Reduce stock by quantity and return True if successful"""
        if self.stock >= quantity:
            self.stock -= quantity
            self.save()
            return True
        return False

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    order_number = models.CharField(max_length=20, unique=True)
    customer_name = models.CharField(max_length=200)
    customer_email = models.EmailField(blank=True)
    customer_phone = models.CharField(max_length=20)
    customer_address = models.TextField()
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    notes = models.TextField(blank=True, help_text='Internal notes for this order')

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order {self.order_number} - {self.customer_name}"

    def save(self, *args, **kwargs):
        # Ensure a unique order number is assigned when creating via admin or elsewhere
        if not self.order_number:
            # Generate a unique order number
            while True:
                candidate = f"ORD-{uuid.uuid4().hex[:8].upper()}"
                if not type(self).objects.filter(order_number=candidate).exists():
                    self.order_number = candidate
                    break
        super().save(*args, **kwargs)

    def calculate_total(self):
        """Calculate and update total amount"""
        total = sum(item.subtotal for item in self.items.all())
        self.total_amount = total
        self.save()
        return total

    @property
    def item_count(self):
        return sum(item.quantity for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['order', 'product']

    def __str__(self):
        return f"{self.quantity}x {self.product.name} in {self.order.order_number}"

    @property
    def subtotal(self):
        if self.quantity is not None and self.unit_price is not None:
            return self.quantity * self.unit_price
        return 0

    def save(self, *args, **kwargs):
        # Set unit price from product if not provided
        if not self.unit_price and self.product:
            self.unit_price = self.product.price
        super().save(*args, **kwargs)

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('new_order', 'New Order'),
        ('low_stock', 'Low Stock Alert'),
        ('order_status', 'Order Status Update'),
        ('stock_update', 'Stock Update'),
    ]

    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    # Optional references
    order = models.ForeignKey(Order, on_delete=models.CASCADE, null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_type_display()}: {self.title}"

# Signal handlers for automatic notifications and stock management
@receiver(post_save, sender=Order)
def create_order_notification(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            type='new_order',
            title=f'New Order #{instance.order_number}',
            message=f'New order from {instance.customer_name} for ₨{instance.total_amount}',
            order=instance
        )

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sales')
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Sale: {self.quantity}x {self.product.name} @ {self.unit_price}"

@receiver(post_save, sender=OrderItem)
def process_order_item(sender, instance, created, **kwargs):
    if created:
        # Reduce stock automatically
        if instance.product.reduce_stock(instance.quantity):
            # Check if stock is now low
            if instance.product.low_stock:
                Notification.objects.create(
                    type='low_stock',
                    title=f'Low Stock Alert: {instance.product.name}',
                    message=f'{instance.product.name} is now at {instance.product.stock} units (threshold: {instance.product.reorder_threshold})',
                    product=instance.product
                )
        else:
            # Not enough stock - create notification
            Notification.objects.create(
                type='stock_update',
                title=f'Insufficient Stock: {instance.product.name}',
                message=f'Order #{instance.order.order_number} requires {instance.quantity} units but only {instance.product.stock} available',
                order=instance.order,
                product=instance.product
            )