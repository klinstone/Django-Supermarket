from django.urls import path
from . import views

app_name = 'supermarket_app'

urlpatterns = [
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/<int:category_id>/products/', views.CategoryProductListView.as_view(), name='category_product_list'),
]