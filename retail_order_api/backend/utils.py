import os
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.utils import FileProxyMixin
from imagekit.utils import suggest_extension
from social_core.pipeline.user import USER_FIELDS
from social_core.utils import module_member, slugify


def custom_get_username(strategy, details, backend, user=None):
    """
    Метод является модифицированной версией social_core.pipeline.user.get_username.

    Изменения:
    - Добавлена проверка существования пользователя с таким же именем в таблице CustomUser.

    Используется для генерации уникального имени пользователя при регистрации через социальные сети.
    """
    if "username" not in backend.setting("USER_FIELDS", USER_FIELDS):
        return
    storage = strategy.storage

    if not user:
        email_as_username = strategy.setting("USERNAME_IS_FULL_EMAIL", False)
        uuid_length = strategy.setting("UUID_LENGTH", 16)
        max_length = storage.user.username_max_length()
        do_slugify = strategy.setting("SLUGIFY_USERNAMES", False)
        do_clean = strategy.setting("CLEAN_USERNAMES", True)

        def identity_func(val):
            return val

        if do_clean:
            override_clean = strategy.setting("CLEAN_USERNAME_FUNCTION")
            if override_clean:
                clean_func = module_member(override_clean)
            else:
                clean_func = storage.user.clean_username
        else:
            clean_func = identity_func

        if do_slugify:
            override_slug = strategy.setting("SLUGIFY_FUNCTION")
            slug_func = module_member(override_slug) if override_slug else slugify
        else:
            slug_func = identity_func

        if email_as_username and details.get("email"):
            username = details["email"]
        elif details.get("username"):
            username = details["username"]
        else:
            username = uuid4().hex

        short_username = (
            username[: max_length - uuid_length] if max_length is not None else username
        )
        final_username = slug_func(clean_func(username[:max_length]))

        user_model = get_user_model()

        while (
            not final_username
            or user_model.objects.filter(username=final_username).exists()
            or storage.user.user_exists(username=final_username)
        ):
            username = short_username + uuid4().hex[:uuid_length]
            final_username = slug_func(clean_func(username[:max_length]))
    else:
        final_username = storage.user.get_username(user)
    return {"username": final_username}


def custom_source_name_as_path(generator):
    """
    Метод является модифицированной версией imagekit.cachefiles.namers.source_name_as_path.

    Генерация пути к измененному файлу

    Пример исходного файла: images/products/nazvanie-produkta/Screenshot_1.jpg
    Пример измененного файла: images/products/nazvanie-produkta/Screenshot_1/{width}x{height}.jpg,
    где {width} и {height} - ширина и высота изображения.
    """
    source_filename = getattr(generator.source, "name", None)
    height, width = 0, 0
    for processor in generator.processors:
        if hasattr(processor, "height") and hasattr(processor, "width"):
            height = processor.height
            width = processor.width
            break

    if source_filename is None or os.path.isabs(source_filename):
        dir_cache = settings.IMAGEKIT_CACHEFILE_DIR
    else:
        dir_cache = os.path.join(
            settings.IMAGEKIT_CACHEFILE_DIR, os.path.splitext(source_filename)[0]
        )

    ext = suggest_extension(source_filename or "", generator.format)

    return os.path.normpath(os.path.join(dir_cache, f"{width}x{height}{ext}"))


def get_path_upload_product_photo(instance, file):
    """
    Построение пути к файлу, format: (media)/images/products/slug(product_name)/photo.jpg
    """
    return f"images/products/{instance.slug}/{file}"


class RemoveAfterCloseFileProxy(FileProxyMixin):
    """
    Прокси-объект для работы с файлом, который будет удален после его закрытия.
    """

    def __init__(self, file):
        self.file = file
        self.name = file.name

    def close(self):
        if not self.closed:
            self.file.close()
            try:
                os.remove(self.name)
            except FileNotFoundError:
                pass

    def __del__(self):
        self.close()
