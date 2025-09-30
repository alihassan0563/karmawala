from django.urls import path
from . import views

urlpatterns = [
    # Product URLs
    path('', views.ProductListView.as_view(), name='product-list'),
    path('sell/', views.sell, name='sell'),
    path('sales/', views.SalesListView.as_view(), name='sales-list'),
    path('sales/<int:pk>/delete/', views.SaleDeleteView.as_view(), name='sale-delete'),
    path('create/', views.ProductCreateView.as_view(), name='product-create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product-update'),
    path('<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product-delete'),
    
    # Order URLs
    path('orders/', views.OrderListView.as_view(), name='order-list'),
    path('orders/create/', views.OrderCreateView.as_view(), name='order-create'),
    path('orders/<int:pk>/', views.OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/edit/', views.OrderUpdateView.as_view(), name='order-update'),
    
    # Notification URLs
    path('notifications/', views.NotificationListView.as_view(), name='notification-list'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark-notification-read'),
    
    # AJAX URLs
    path('ajax/create-category/', views.create_category_ajax, name='create-category-ajax'),
    path('ajax/create-order/', views.create_order_ajax, name='create-order-ajax'),
]
