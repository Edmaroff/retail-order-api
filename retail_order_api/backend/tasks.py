from celery import shared_task
from django.apps import apps
from django.db import IntegrityError, transaction
from requests import get
from yaml import SafeLoader
from yaml import load as load_yaml
from yaml.error import YAMLError

from backend.models import (
    Category,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)


@shared_task()
def do_import_celery(url, user_id):
    try:
        stream = get(url).content
        data = load_yaml(stream, Loader=SafeLoader)
    except YAMLError:
        return {
            "Status": False,
            "Errors": "Ошибка при загрузке данных из файла YAML.",
        }
    with transaction.atomic():
        try:
            # # ОТЛАДКА - чтение файла с ПК
            # import os
            # url = "http://www.exmple100.ru"
            # stream = os.path.join(os.getcwd(), "data/shop_1.yaml")
            # with open(stream, encoding="utf-8") as file:
            #     data = load_yaml(file, Loader=SafeLoader)
            # # ОТЛАДКА - чтение файла с ПК

            # Создание или обновление магазина
            shop, _ = Shop.objects.update_or_create(
                user_id=user_id,
                defaults={"name": data.get("shop_name"), "url": url},
            )

            # Обработка категорий
            shop.categories.clear()  # Удаление существующих категорий
            category_name_to_id = {}  # Для создания товаров
            categories_data = data.get("categories", [])
            for category_name in categories_data:
                category_object, _ = Category.objects.get_or_create(name=category_name)
                category_object.shops.add(shop.id)
                category_name_to_id[category_name] = category_object.id

            # Обработка товаров
            ProductInfo.objects.filter(
                shop_id=shop.id
            ).delete()  # Удаление существующих товаров магазина
            products_data = data.get("goods", [])
            for product_data in products_data:
                # Попытка получить товар, если его нет — создание
                try:
                    product = Product.objects.get(name=product_data.get("name"))
                    # Проверка связи категории товара с магазином
                    if product.category.name not in category_name_to_id:
                        product.category.shops.add(shop.id)
                except Product.DoesNotExist:
                    category_id = category_name_to_id.get(product_data.get("category"))
                    product = Product.objects.create(
                        name=product_data.get("name"), category_id=category_id
                    )

                # Обработка информации о товаре
                product_info = ProductInfo.objects.create(
                    product_id=product.id,
                    shop_id=shop.id,
                    external_id=product_data.get("id"),
                    model=product_data.get("model"),
                    price=product_data.get("price"),
                    price_rrp=product_data.get("price_rrp"),
                    quantity=product_data.get("quantity"),
                )

                # Обработка параметров товара
                parameters_data = product_data.get("parameters", {})
                for param_name, param_value in parameters_data.items():
                    parameter, _ = Parameter.objects.get_or_create(name=param_name)
                    ProductParameter.objects.create(
                        product_info_id=product_info.id,
                        parameter=parameter,
                        value=param_value,
                    )

            return {"Status": True, "Message": "Магазин успешно обновлен."}
        except (IntegrityError, TypeError, AttributeError):
            return {"Status": False, "Errors": "Не указаны все необходимые аргументы."}


@shared_task
def delete_cached_files_celery(instance_id, app_label, model_name):
    model = apps.get_model(app_label, model_name)
    instance = model.objects.get(id=instance_id)
    instance.delete_cached_files()


"""Отладка файл с ПК"""
# @shared_task()
# def do_import(url, user_id):
#     print(11111111111111111111111111111111111111111111111)
#     try:
#         stream = get(url).content
#         data = load_yaml(stream, Loader=SafeLoader)
#     except YAMLError:
#         return {"Status": False, "Errors": "Ошибка при загрузке данных "
#                                            "из файла YAML."}
#     with transaction.atomic():
#         try:
#             # ОТЛАДКА - чтение файла с ПК
#             import os
#             url = "http://www.exmple100.ru"
#             stream = os.path.join(os.getcwd(), "data/shop_test.yaml")
#             with open(stream, encoding="utf-8") as file:
#                 data = load_yaml(file, Loader=SafeLoader)
#             # ОТЛАДКА - чтение файла с ПК
#
#                 # Создание или обновление магазина
#                 shop, _ = Shop.objects.update_or_create(
#                     user_id=user_id,
#                     defaults={"name": data.get("shop_name"), "url": url},
#                 )
#
#                 # Обработка категорий
#                 shop.categories.clear()  # Удаление существующих категорий
#                 category_name_to_id = {}  # Для создания товаров
#                 categories_data = data.get("categories", [])
#                 print(categories_data)
#                 for category_name in categories_data:
#                     category_object, _ = Category.objects. \
#                                             get_or_create(name=category_name)
#                     category_object.shops.add(shop.id)
#                     category_name_to_id[category_name] = category_object.id
#
#                 # Обработка товаров
#                 ProductInfo.objects.filter(
#                     shop_id=shop.id
#                 ).delete()  # Удаление существующих товаров магазина
#                 products_data = data.get("goods", [])
#                 for product_data in products_data:
#                     # Попытка получить товар, если его нет — создание
#                     try:
#                         product = Product.objects.get(name=product_data.get("name"))
#                         # Проверка связи категории товара с магазином
#                         if product.category.name not in category_name_to_id:
#                             product.category.shops.add(shop.id)
#                     except Product.DoesNotExist:
#                         category_id = category_name_to_id. \
#                                         get(product_data.get("category"))
#                         product = Product.objects.create(
#                             name=product_data.get("name"), category_id=category_id
#                         )
#
#                     # Обработка информации о товаре
#                     product_info = ProductInfo.objects.create(
#                         product_id=product.id,
#                         shop_id=shop.id,
#                         external_id=product_data.get("id"),
#                         model=product_data.get("model"),
#                         price=product_data.get("price"),
#                         price_rrp=product_data.get("price_rrp"),
#                         quantity=product_data.get("quantity"),
#                     )
#
#                     # Обработка параметров товара
#                     parameters_data = product_data.get("parameters", {})
#                     for param_name, param_value in parameters_data.items():
#                         parameter, _ = Parameter.objects. \
#                                         get_or_create(name=param_name)
#                         ProductParameter.objects.create(
#                             product_info_id=product_info.id,
#                             parameter=parameter,
#                             value=param_value,
#                         )
#
#                 return {"Status": True, "Message": "Магазин успешно обновлен."}
#         except (IntegrityError, TypeError):
#             return {"Status": False, "Errors": "Не указаны все "
#                                                "необходимые аргументы."}
