from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from inventory.api import CategoryViewSet, ProductViewSet
from inventory.views import dashboard

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='api-categories')
router.register(r'products', ProductViewSet, basename='api-products')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('', dashboard, name='dashboard'),
    path('products/', include('inventory.urls')),

    path('api/', include(router.urls)),
]