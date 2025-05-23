from celery import shared_task
from django.utils import timezone
from .models import Order, OrderStatus
from datetime import timedelta

@shared_task
def cancel_expired_orders():
    orders = Order.objects.filter(status=OrderStatus.BOOKED.value)
    now = timezone.now()
    for order in orders:
        if order.booked_at + timedelta(days=1) < now:
            order.status = OrderStatus.CANCELLED.value
            print(f"Order {order.id} cancelled due to timeout.")
            order.save()