from uuid import uuid4

from django.contrib.auth import get_user_model
from social_core.pipeline.user import USER_FIELDS
from social_core.utils import module_member, slugify


def custom_get_username(strategy, details, backend, user=None, *args, **kwargs):
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
