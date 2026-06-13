from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_add='django.db.models.BigAutoField'
    name='apps.inventory'
    label='inventory'
    