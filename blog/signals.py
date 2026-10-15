import os
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Post


@receiver(post_delete, sender=Post)
def delete_post_images(sender, instance, **kwargs):
    for field in (instance.cover_image, instance.image):
        if field and os.path.isfile(field.path):
            os.remove(field.path)