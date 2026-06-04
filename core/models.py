from django.models import models

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)
    
class BaseUser(models.Manager):
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)
    is_deleted=models.BooleanField(default=False)
    all_objects=models.Manager()
    objects=SoftDeleteManager()

    class Meta:
        abstract=True


        
    