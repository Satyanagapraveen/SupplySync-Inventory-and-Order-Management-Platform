import logging
from celery import shared_task
from django.utils import timezone
from apps.purchase_orders.models import PurchaseOrder
from apps.sales_orders.models import SalesOrder

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_sales_order_created_event(self, order_id: int, created_by_user_id: int):
    try:
        logger.info(f"EVENT [sales-order-created]: order_id={order_id}, created_by={created_by_user_id}")
    except Exception as exc:
        logger.error(f"Task process_sales_order_created_event failed, retrying... Exception: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)

@shared_task(bind=True, max_retries=3)
def process_sales_order_cancelled_event(self, order_id: int):
    try:
        logger.info(f"EVENT [sales-order-cancelled]: order_id={order_id}")
    except Exception as exc:
        logger.error(f"Task process_sales_order_cancelled_event failed, retrying... Exception: {exc}")
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
    
@shared_task
def generate_daily_operations_summary():
    today = timezone.now().date()
    
    new_pos = PurchaseOrder.objects.filter(created_at__date=today).count()
    received_pos = PurchaseOrder.objects.filter(updated_at__date=today, status='RECEIVED').count()
    
    new_sos = SalesOrder.objects.filter(created_at__date=today).count()
    dispatched_sos = SalesOrder.objects.filter(updated_at__date=today, status='DISPATCHED').count()
    delivered_sos = SalesOrder.objects.filter(updated_at__date=today, status='DELIVERED').count()
    
    logger.info(
        f"DAILY SUMMARY: Date={today}, New POs={new_pos}, POs Received={received_pos}, "
        f"New Sales Orders={new_sos}, Orders Dispatched={dispatched_sos}, Orders Delivered={delivered_sos}"
    )