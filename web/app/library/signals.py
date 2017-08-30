
from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from library.models import Thumbnail, Version
import os


@receiver(post_save, sender=Version)
def version_saved(sender, instance, **kwargs):
    """
    Create a thumbnail for the Version when it is saved
    :param sender:
    :param instance:
    :param kwargs:
    :return:
    """
    instance.thumbnail()


@receiver(post_delete, sender=Version)
def version_dropped(sender, instance, **kwargs):
    """
    Remove all thumbnails for a created version
    """
    Thumbnail.get_from_instance(instance=instance).delete()


@receiver(pre_delete, sender=Thumbnail)
def thumbnail_delete(sender, instance, **kwargs):

    if not instance.thumbnailPath:
        return

    if not os.path.isfile(instance.thumbnailPath):
        return
    os.remove(instance.thumbnailPath)
