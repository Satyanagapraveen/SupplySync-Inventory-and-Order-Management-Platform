import logging
from celery import shared_task

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