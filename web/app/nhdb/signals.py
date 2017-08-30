from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver

from geo.models import Suco
from nhdb.models import OrganizationPlace

import logging
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=OrganizationPlace)
def save_default_category_name(sender, instance, **kwargs):
    if not hasattr(instance, 'suco'):
        try:
            instance.suco = Suco.objects.get(geom__contains=instance.point)
        except Exception as e:
            logger.exception(e.message)
            pass
