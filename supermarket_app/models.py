from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q, Max



class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время обновления")

    class Meta:
        abstract = True


class IsActiveManager(models.Manager):
    def get_active(self):
        return self.get_queryset().filter(is_active=True)


class IsActiveModel(models.Model):
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    objects = IsActiveManager()

    class Meta:
        abstract = True



class Category(TimestampedModel):
    name = models.CharField(max_length=100, unique=True, verbose_name="Название категории")
    description = models.TextField(blank=True, verbose_name="Описание")

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ['name']

    def __str__(self):
        return self.name


class TransportCompany(TimestampedModel):
    name = models.CharField(max_length=200, unique=True, verbose_name="Название компании")
    contact_info = models.TextField(blank=True, verbose_name="Контактная информация")

    class Meta:
        verbose_name = "Транспортная компания"
        verbose_name_plural = "Транспортные компании"
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(TimestampedModel, IsActiveModel):
    name = models.CharField(max_length=200, verbose_name="Название товара")
    description = models.TextField(blank=True, verbose_name="Описание")
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='products',
        verbose_name="Категория"
    )
    transport_companies = models.ManyToManyField(
        TransportCompany,
        related_name='products',
        verbose_name="Транспортные компании",
        blank=True
    )

    class Meta:
        verbose_name = "Товар"
        verbose_name_plural = "Товары"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_current_price(self):
        now = timezone.now()
        try:
            current_price_obj = self.prices.filter(start_date__lte=now).latest('start_date')
            return current_price_obj.value
        except Price.DoesNotExist:
            return None


class Price(TimestampedModel):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='prices',
        verbose_name="Товар"
    )
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Цена"
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата начала действия цены"
    )

    class Meta:
        verbose_name = "Цена"
        verbose_name_plural = "Цены (История)"
        ordering = ['-start_date']
        get_latest_by = 'start_date'

    def __str__(self):
        return f"{self.product.name} - {self.value} руб. (с {self.start_date.strftime('%Y-%m-%d %H:%M')})"


class PaymentMethod(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Название метода")

    CASH = 'cash'
    CARD = 'card'
    METHOD_CHOICES = [
        (CASH, 'Наличные'),
        (CARD, 'Безналичный расчет'),
    ]
    code = models.CharField(max_length=10, unique=True, choices=METHOD_CHOICES, default=CARD)

    class Meta:
        verbose_name = "Метод оплаты"
        verbose_name_plural = "Методы оплаты"

    def __str__(self):
        return self.name


class Cashier(TimestampedModel, IsActiveModel):
    name = models.CharField(max_length=150, verbose_name="Имя кассира")

    class Meta:
        verbose_name = "Кассир"
        verbose_name_plural = "Кассиры"
        ordering = ['name']

    def __str__(self):
        return self.name


class CashRegister(TimestampedModel, IsActiveModel):
    number = models.PositiveIntegerField(unique=True, verbose_name="Номер кассы")
    supported_payment_methods = models.ManyToManyField(
        PaymentMethod,
        related_name='cash_registers',
        verbose_name="Поддерживаемые методы оплаты"
    )

    class Meta:
        verbose_name = "Касса"
        verbose_name_plural = "Кассы"
        ordering = ['number']

    def __str__(self):
        return f"Касса №{self.number}"

    def supports_cash(self):
        return self.supported_payment_methods.filter(code=PaymentMethod.CASH).exists()

    def supports_card(self):
        return self.supported_payment_methods.filter(code=PaymentMethod.CARD).exists()


class DiscountCard(TimestampedModel, IsActiveModel):
    card_number = models.CharField(max_length=20, unique=True, verbose_name="Номер карты")
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.0), MaxValueValidator(100.0)],
        verbose_name="Процент скидки (%)"
    )

    class Meta:
        verbose_name = "Дисконтная карта"
        verbose_name_plural = "Дисконтные карты"
        ordering = ['card_number']

    def __str__(self):
        return f"Карта {self.card_number} ({self.discount_percent}%)"


class Purchase(TimestampedModel):
    purchase_time = models.DateTimeField(default=timezone.now, verbose_name="Время покупки")
    cash_register = models.ForeignKey(
        CashRegister,
        on_delete=models.PROTECT,
        related_name='purchases',
        verbose_name="Касса"
    )
    cashier = models.ForeignKey(
        Cashier,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases',
        verbose_name="Кассир"
    )
    discount_card = models.ForeignKey(
        DiscountCard,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchases',
        verbose_name="Дисконтная карта"
    )
    total_amount_before_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Сумма до скидки")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Сумма скидки")
    final_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Итоговая сумма")

    amount_paid_cash = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Оплачено наличными")
    amount_paid_card = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name="Оплачено картой")

    payment_methods_used = models.ManyToManyField(
        PaymentMethod,
        related_name='purchases_where_used',
        verbose_name="Использованные методы оплаты",
        blank=True
    )


    class Meta:
        verbose_name = "Покупка (Чек)"
        verbose_name_plural = "Покупки (Чеки)"
        ordering = ['-purchase_time']

    def __str__(self):
        return f"Чек №{self.id} от {self.purchase_time.strftime('%Y-%m-%d %H:%M')}"

    def recalculate_totals(self):
        items = self.items.all()
        self.total_amount_before_discount = sum(item.line_total for item in items)

        if self.discount_card and self.discount_card.is_active:
            discount_decimal = self.discount_card.discount_percent / 100
            self.discount_amount = self.total_amount_before_discount * discount_decimal
        else:
            self.discount_amount = 0

        self.final_amount = self.total_amount_before_discount - self.discount_amount
        self.save(update_fields=['total_amount_before_discount', 'discount_amount', 'final_amount'])


class PurchaseItem(models.Model):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Покупка (Чек)"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='purchase_items',
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Количество")
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена на момент покупки")
    line_total = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Сумма по позиции")

    class Meta:
        verbose_name = "Позиция в чеке"
        verbose_name_plural = "Позиции в чеках"
        unique_together = ('purchase', 'product')

    def __str__(self):
        return f"{self.quantity} x {self.product.name} @ {self.price_at_purchase}"

    def save(self, *args, **kwargs):
        self.line_total = self.price_at_purchase * self.quantity
        is_new = self._state.adding
        super().save(*args, **kwargs)
        self.purchase.recalculate_totals()

    def delete(self, *args, **kwargs):
        purchase = self.purchase
        super().delete(*args, **kwargs)
        purchase.recalculate_totals()