from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

STATE_CHOICES = (
    ("basket", "Статус корзины"),
    ("new", "Новый"),
    ("confirmed", "Подтвержден"),
    ("assembled", "Собран"),
    ("sent", "Отправлен"),
    ("delivered", "Доставлен"),
    ("canceled", "Отменен"),
)

USER_TYPE_CHOICES = (
    ("shop", "Магазин"),
    ("buyer", "Покупатель"),
)


class CustomUserManager(BaseUserManager):
    """
    Собственный менеджер для управления пользователями.
    """

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """
        Создает и сохраняет пользователя с указанным email и паролем.
        """
        if not email:
            raise ValueError("Необходимо указать email.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True.")

        return self._create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Расширенная модель пользователя Django с дополнительными полями.
    Поля: patronymic, company, position, type.
    """

    REQUIRED_FIELDS = [
        "first_name",
        "patronymic",
        "last_name",
        "company",
        "position",
        "username",
    ]
    USERNAME_FIELD = "email"

    objects = CustomUserManager()
    username_validator = UnicodeUsernameValidator()

    patronymic = models.CharField(
        verbose_name="Отчество", max_length=150, null=True, blank=True
    )
    company = models.CharField(
        verbose_name="Компания", max_length=40, null=True, blank=True
    )
    position = models.CharField(
        verbose_name="Должность", max_length=40, null=True, blank=True
    )
    type = models.CharField(
        verbose_name="Тип пользователя",
        choices=USER_TYPE_CHOICES,
        max_length=5,
        default="buyer",
    )
    email = models.EmailField(_("email address"), unique=True)
    username = models.CharField(
        _("username"),
        max_length=150,
        unique=True,
        null=True,
        blank=True,
        help_text=_(
            "Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only."
        ),
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Список пользователей"
        ordering = ("email",)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Contact(models.Model):
    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        related_name="user_contacts",
        on_delete=models.CASCADE,
    )
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    city = models.CharField(max_length=50, verbose_name="Город")
    street = models.CharField(max_length=100, verbose_name="Улица")
    house = models.CharField(max_length=15, verbose_name="Дом", null=True, blank=True)
    structure = models.CharField(
        max_length=15, verbose_name="Корпус", null=True, blank=True
    )
    building = models.CharField(
        max_length=15, verbose_name="Строение", null=True, blank=True
    )
    apartment = models.CharField(
        max_length=15, verbose_name="Квартира", null=True, blank=True
    )

    class Meta:
        verbose_name = "Контакты пользователя"
        verbose_name_plural = "Список контактов пользователя"

    def __str__(self):
        return f"{self.city} {self.street} {self.house}"


class Shop(models.Model):
    """
    Модель для представления магазина.
    """

    name = models.CharField(verbose_name="Название", max_length=100)
    url = models.URLField(verbose_name="Ссылка")
    state = models.BooleanField(verbose_name="Статус получения заказов", default=True)
    user = models.OneToOneField(
        CustomUser,
        verbose_name="Пользователь",
        related_name="shop",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Магазин"
        verbose_name_plural = "Список магазинов"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    Модель для представления категории.
    """

    name = models.CharField(verbose_name="Название", max_length=50, unique=True)
    shops = models.ManyToManyField(
        Shop, verbose_name="Магазины", related_name="categories", blank=True
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Список категорий"
        ordering = ("-name",)

    def __str__(self):
        return f'{self.id}: {self.name}'


class Product(models.Model):
    """
    Модель для представления продукта.
    """

    name = models.CharField(verbose_name="Название", max_length=90)
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        related_name="products",
        blank=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Список продуктов"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    """
    Модель для представления информации о продукте в магазине.
    """

    model = models.CharField(
        max_length=80, verbose_name="Модель", null=True, blank=True
    )
    external_id = models.PositiveIntegerField(verbose_name="Внешний ИД")
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    price = models.DecimalField(verbose_name="Цена", max_digits=10, decimal_places=2)
    price_rrp = models.DecimalField(
        verbose_name="Рекомендованная розничная цена", max_digits=10, decimal_places=2
    )

    product = models.ForeignKey(
        Product,
        verbose_name="Продукт",
        related_name="product_info",
        blank=True,
        on_delete=models.CASCADE,
    )
    shop = models.ForeignKey(
        Shop,
        verbose_name="Магазин",
        related_name="product_info",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Информация о продукте в магазине"
        verbose_name_plural = "Информационный список о продуктах"
        ordering = ("product", "shop")
        constraints = [
            models.UniqueConstraint(
                fields=["product", "shop", "external_id"], name="unique_product_info"
            ),
        ]

    def __str__(self):
        return f"{self.product.name} в {self.shop.name}"


class Parameter(models.Model):
    """
    Модель для представления параметра.
    """

    name = models.CharField(max_length=50, verbose_name="Название")

    class Meta:
        verbose_name = "Параметр"
        verbose_name_plural = "Список параметров"
        ordering = ("-name",)

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    """
    Модель для представления параметра продукта.
    """

    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="product_parameters",
        blank=True,
        on_delete=models.CASCADE,
    )
    parameter = models.ForeignKey(
        Parameter,
        verbose_name="Параметр",
        related_name="product_parameters",
        blank=True,
        on_delete=models.CASCADE,
    )
    value = models.CharField(verbose_name="Значение параметра", max_length=100)

    class Meta:
        verbose_name = "Параметр продукта"
        verbose_name_plural = "Список параметров продукта"
        constraints = [
            models.UniqueConstraint(
                fields=["product_info", "parameter"], name="unique_product_parameter"
            )
        ]

    def __str__(self):
        return f"{self.product_info.product.name} - {self.parameter.name}: {self.value}"


class Order(models.Model):
    """
    Модель для представления заказа.
    """

    user = models.ForeignKey(
        CustomUser,
        verbose_name="Пользователь",
        related_name="orders",
        on_delete=models.CASCADE,
    )
    contact = models.ForeignKey(
        Contact, verbose_name="Контакт", related_name="orders", on_delete=models.CASCADE
    )
    date = models.DateTimeField(verbose_name="Дата и время заказа", auto_now_add=True)
    state = models.CharField(
        verbose_name="Статус", choices=STATE_CHOICES, max_length=20
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Список заказов"
        ordering = ("-date",)

    def __str__(self):
        return f"{self.date}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        verbose_name="Заказ",
        related_name="ordered_items",
        blank=True,
        on_delete=models.CASCADE,
    )
    product_info = models.ForeignKey(
        ProductInfo,
        verbose_name="Информация о продукте",
        related_name="ordered_items",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")

    class Meta:
        verbose_name = "Заказанный товар"
        verbose_name_plural = "Список заказанных товаров"
        constraints = [
            models.UniqueConstraint(
                fields=["order_id", "product_info"], name="unique_order_item"
            ),
        ]

    def __str__(self):
        return f"{self.product_info.product.name} в заказе {self.order.id}"


# class ConfirmEmailToken(models.Model):
#     """
#     Модель для представления токена подтверждения Email пользователя.
#     """
#
#     user = models.ForeignKey(
#         CustomUser,
#         verbose_name="Пользователь",
#         related_name="confirm_email_tokens",
#         on_delete=models.CASCADE,
#     )
#
#     created_at = models.DateTimeField(
#         verbose_name="Время создания токена",
#         auto_now_add=True,
#     )
#
#     key = models.CharField(
#         verbose_name="Ключ", max_length=64, db_index=True, unique=True
#     )
#
#     class Meta:
#         verbose_name = "Токен подтверждения Email"
#         verbose_name_plural = "Токены подтверждения Email"
#
#     def __str__(self):
#         return f"Токен сброса пароля для {self.user}"
#
#     def save(self, *args, **kwargs):
#         """
#         Переопределение метода save для генерации ключа при сохранении объекта.
#         """
#         if not self.key:
#             self.key = self.generate_key()
#         return super(ConfirmEmailToken, self).save(*args, **kwargs)
#
#     @staticmethod
#     def generate_key():
#         return get_token_generator().generate_token()
