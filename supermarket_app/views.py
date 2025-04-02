# supermarket_app/views.py
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.http import Http404, JsonResponse
from django.utils import timezone
from .models import Product, Category, Price, Purchase, DiscountCard


class ProductListView(ListView):
    model = Product
    template_name = 'supermarket_app/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.get_active().select_related('category').order_by('name')
        category_filter = self.request.GET.get('category')
        if category_filter:
             try:
                 category_id = int(category_filter)
                 queryset = queryset.filter(category__id=category_id)
             except (ValueError, TypeError):
                 pass
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['page_title'] = "Каталог товаров"
        return context


class CategoryListView(ListView):
    model = Category
    template_name = 'supermarket_app/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        return Category.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Категории товаров"
        return context


class CategoryProductListView(ListView):
    model = Product
    template_name = 'supermarket_app/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        if category_id is None:
             raise Http404("ID категории не указан.")
        try:
            self.category = get_object_or_404(Category, pk=int(category_id))
        except (ValueError, TypeError):
            raise Http404("Неверный формат ID категории.")

        return Product.objects.get_active().filter(category=self.category).select_related('category').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        context['page_title'] = f"Товары в категории: {self.category.name}"
        context['current_category_id'] = self.category.id
        return context



class ProductDetailView(DetailView):
    model = Product
    template_name = 'supermarket_app/product_detail.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        pk = self.kwargs.get('pk')
        if pk is None:
            raise Http404("ID товара не указан.")
        try:
            pk_int = int(pk)
            obj = get_object_or_404(Product.objects.get_active(), pk=pk_int)
            return obj

        except (ValueError, TypeError):
             raise Http404("Неверный формат ID товара.")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        context['current_price'] = product.get_current_price()
        now = timezone.now()
        context['price_history'] = product.prices.filter(start_date__lte=
                                                         now).order_by('-start_date')
        context['page_title'] = product.name
        return context
