import os

from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from imagekit.models import ImageSpecField
from imagekit.processors import Adjust, ResizeToFill, ResizeToFit
from pytils.translit import slugify

from backend.utils import RemoveAfterCloseFileProxy, get_path_upload_product_photo
from retail_order_api import settings


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
        choices=settings.USER_TYPE_CHOICES,
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
        validators=[username_validator],
        error_messages={
            "unique": _("A user with that username already exists."),
        },
    )
    is_active = models.BooleanField(
        _("active"),
        default=True,
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
    url = models.URLField(verbose_name="Ссылка", null=True, blank=True)
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
        return f"{self.name}"


class Product(models.Model):
    """
    Модель для представления продукта.
    """

    name = models.CharField(verbose_name="Название", max_length=90, unique=True)
    slug = models.SlugField(
        verbose_name="Слаг", max_length=200, blank=True, unique=True
    )
    category = models.ForeignKey(
        Category,
        verbose_name="Категория",
        related_name="products",
        blank=True,
        on_delete=models.CASCADE,
    )

    image = models.ImageField(
        verbose_name="Фото",
        upload_to=get_path_upload_product_photo,
        null=True,
        blank=True,
        default=settings.DEFAULT_PATH_PRODUCT_IMAGE,
    )

    image_small = ImageSpecField(
        source="image",
        processors=[ResizeToFill(50, 50), Adjust(contrast=1.2, sharpness=1.1)],
        format="JPEG",
        options={"quality": 80},
    )

    image_medium = ImageSpecField(
        source="image",
        processors=[ResizeToFit(300, 200), Adjust(contrast=1.2, sharpness=1.1)],
        format="JPEG",
        options={"quality": 80},
    )

    image_big = ImageSpecField(
        source="image",
        processors=[
            ResizeToFit(640, 480),
            Adjust(contrast=1.2, sharpness=1.1),
        ],
        format="JPEG",
        options={"quality": 80},
    )

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Список продуктов"
        ordering = ("-name",)

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super(Product, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.delete_cached_files()

        # Удаляем директории исходного и производных файлов
        original_image_dir = os.path.dirname(os.path.dirname(self.image_small.path))
        derivative_image_dir = os.path.dirname(self.image.path)
        os.rmdir(original_image_dir)
        os.rmdir(derivative_image_dir)

        super().delete(*args, **kwargs)

    def delete_cached_files(self):
        """
        Удаляет кэшированные файлы для данного продукта.
        """
        if self.image.name != settings.DEFAULT_PATH_PRODUCT_IMAGE:
            derivative_image_dir = os.path.dirname(self.image_small.path)
            RemoveAfterCloseFileProxy(
                self.image.file
            )  # Закрываем и удаляем исходный файл

            for field_name in ["image_small", "image_medium", "image_big"]:
                field = getattr(self, field_name)
                try:
                    file = field.file
                except FileNotFoundError:
                    continue
                cache_backend = field.cachefile_backend
                cache_backend.cache.delete(cache_backend.get_key(file))
                RemoveAfterCloseFileProxy(file)  # Закрываем и удаляем файл

            # Удаляем пустую директорию производных файлов
            try:
                os.rmdir(derivative_image_dir)
            except OSError:
                pass

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
        verbose_name_plural = "Список с информацией о продуктах"
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

    name = models.CharField(max_length=50, unique=True, verbose_name="Название")

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
        Contact,
        verbose_name="Контакт",
        related_name="orders",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(verbose_name="Дата и время заказа", auto_now_add=True)
    state = models.CharField(
        verbose_name="Статус", choices=settings.STATE_CHOICES, max_length=20
    )

    class Meta:
        verbose_name = "Заказ"
        verbose_name_plural = "Список заказов"
        ordering = ("-date",)

    def __str__(self):
        return f"{self.date}"


class OrderItem(models.Model):
    """Модель для представления товара в заказе."""

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
        related_name="ordered_items_info",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(
        verbose_name="Количество",
        validators=[
            MinValueValidator(settings.MIN_QUANTITY_ORDER_ITEM),
            MaxValueValidator(settings.MAX_QUANTITY_ORDER_ITEM),
        ],
        default=settings.DEFAULT_QUANTITY_ORDER_ITEM,
    )

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
