from django.core.mail import EmailMultiAlternatives
from django.dispatch import Signal, receiver

from backend.models import CustomUser
from retail_order_api import settings

new_order = Signal()


@receiver(new_order)
def new_order_signal(user_id, order_id, **kwargs):
    """Сигнал для отправки письма покупателю при изменении статуса заказа."""
    user = CustomUser.objects.get(id=user_id)

    msg = EmailMultiAlternatives(
        # Тема:
        f"Обновление статуса заказа",
        # Сообщение:
        f"Заказ №{order_id} успешно оформлен.",
        # От кого:
        settings.EMAIL_HOST_USER,
        # Кому:
        [user.email],
    )
    msg.send()
