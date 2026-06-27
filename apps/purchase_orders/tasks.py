import logging
from celery import shared_task
logger=logging.getLogger(__name__)
@shared_task(bind=True,max_retries=2)
def process_purchase_order_received_event(self,po_id:int,received_by_user_id:int):
    try:
        logger.info(
            f"EVENT [purchase-order-received]: po_id={po_id}, received_by={received_by_user_id}"
        )
    except Exception as exc:
        logger.error(
            f"Task process_purchase_order_received_event failed, retrying... Exception: {exc}")
        raise self.retry(self,countdown=2**self.request.retries)