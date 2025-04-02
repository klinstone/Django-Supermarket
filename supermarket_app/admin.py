from django.contrib import admin
from .models import (
    Category, TransportCompany, Product, Price, PaymentMethod,
    Cashier, CashRegister, DiscountCard, Purchase, PurchaseItem
)



class TimestampedAdmin(admin.ModelAdmin):
    readonly_fields = ('created_at', 'updated_at')

class IsActiveAdmin(admin.ModelAdmin):
    list_display = ('is_active',)
    list_filter = ('is_active',)

@admin.register(Category)
class CategoryAdmin(TimestampedAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

@admin.register(TransportCompany)
class TransportCompanyAdmin(TimestampedAdmin):
    list_display = ('name', 'created_at', 'updated_at')
    search_fields = ('name',)

class PriceInline(admin.TabularInline):
    model = Price
    extra = 1
    ordering = ('-start_date',)
    readonly_fields = ('created_at', 'updated_at')
    fields = ('value', 'start_date', 'created_at', 'updated_at') # Указываем поля

@admin.register(Product)
class ProductAdmin(TimestampedAdmin, IsActiveAdmin):
    list_display = ('name', 'category', 'get_current_price_display', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'transport_companies')
    search_fields = ('name', 'description')
    filter_horizontal = ('transport_companies',)
    inlines = [PriceInline]
    list_select_related = ('category',)

    def get_current_price_display(self, obj):
        current_price = obj.get_current_price()
        return f"{current_price} руб." if current_price is not None else "Нет цены"
    get_current_price_display.short_description = 'Текущая цена'
    get_current_price_display.admin_order_field = None

@admin.register(Price)
class PriceAdmin(TimestampedAdmin):
    list_display = ('product', 'value', 'start_date', 'created_at')
    list_filter = ('product__category', 'start_date')
    search_fields = ('product__name',)
    date_hierarchy = 'start_date'
    list_select_related = ('product',)

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name',)

@admin.register(Cashier)
class CashierAdmin(TimestampedAdmin, IsActiveAdmin):
    list_display = ('name', 'is_active', 'created_at')
    search_fields = ('name',)

@admin.register(CashRegister)
class CashRegisterAdmin(TimestampedAdmin, IsActiveAdmin):
    list_display = ('number', 'get_supported_methods_display', 'is_active', 'created_at')
    search_fields = ('number',)
    filter_horizontal = ('supported_payment_methods',)

    def get_supported_methods_display(self, obj):
        return ", ".join([p.name for p in obj.supported_payment_methods.all()])
    get_supported_methods_display.short_description = 'Поддерживаемые методы оплаты'

@admin.register(DiscountCard)
class DiscountCardAdmin(TimestampedAdmin, IsActiveAdmin):
    list_display = ('card_number', 'discount_percent', 'is_active', 'created_at')
    search_fields = ('card_number',)

class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1
    readonly_fields = ('line_total',)
    can_delete = True
    fields = ('product', 'quantity', 'price_at_purchase', 'line_total')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('product')

@admin.register(Purchase)
class PurchaseAdmin(TimestampedAdmin):
    list_display = ('id', 'purchase_time', 'cash_register', 'cashier', 'discount_card_display', 'final_amount', 'payment_summary')
    list_filter = ('purchase_time', 'cash_register', 'cashier', 'discount_card')
    search_fields = ('id', 'cashier__name', 'discount_card__card_number')
    date_hierarchy = 'purchase_time'
    inlines = [PurchaseItemInline]
    readonly_fields = (
        'created_at', 'updated_at', 'purchase_time',
        'total_amount_before_discount', 'discount_amount', 'final_amount',
        'amount_paid_cash', 'amount_paid_card', 'payment_methods_used_display'
    )
    list_select_related = ('cash_register', 'cashier', 'discount_card')

    fields = (
        ('cash_register', 'cashier'),
        'discount_card',
        'purchase_time',
        ('total_amount_before_discount', 'discount_amount', 'final_amount'),
        ('amount_paid_cash', 'amount_paid_card'),
        'payment_methods_used_display',
        ('created_at', 'updated_at'),
    )

    def discount_card_display(self, obj):
        return str(obj.discount_card) if obj.discount_card else "Нет"
    discount_card_display.short_description = 'Дисконтная карта'

    def payment_summary(self, obj):
        methods = []
        if obj.amount_paid_cash > 0:
            methods.append(f"Нал: {obj.amount_paid_cash}")
        if obj.amount_paid_card > 0:
            methods.append(f"Карта: {obj.amount_paid_card}")
        return " / ".join(methods) if methods else "Не оплачен"
    payment_summary.short_description = 'Оплата'
    payment_summary.short_description = 'Оплата'

    def payment_methods_used_display(self, obj):
        return ", ".join([p.name for p in obj.payment_methods_used.all()]) or "Нет данных"
    payment_methods_used_display.short_description = 'Использованные методы оплаты'


    def has_add_permission(self, request):
        return True

    def has_change_permission(self, request, obj=None):
         return True