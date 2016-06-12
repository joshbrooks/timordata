from django.db.models.signals import post_save
from django.dispatch import receiver

from nhdb.models import OrganizationPlace

@receiver(post_save, sender=OrganizationPlace)
def organizationplace_update_suco(sender, instance, **kwargs):
    instance.update_place()