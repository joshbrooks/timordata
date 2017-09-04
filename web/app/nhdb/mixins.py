from datetime import datetime

from django.db import models
from django.utils.translation import ugettext as translate
from django.utils.timezone import now


class TimestampedMixin(models.Model):

    created_at = models.DateTimeField(
        verbose_name=translate('created at'),
        unique=False,
        null=True,
        blank=True,
        db_index=True
    )

    updated_at = models.DateTimeField(
        verbose_name=translate('updated at'),
        unique=False,
        null=True,
        blank=True,
        db_index=True
    )

    deleted_at = models.DateTimeField(
        verbose_name=translate('deleted at'),
        unique=False,
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.pk or not self.created_at:
            self.created_at = self.updated_at = now()
        elif not kwargs.pop('disable_auto_updated_at', False):
            if (now()-self.created_at).seconds > 5 or kwargs.pop('force_updated_at', False):
                # Allow five seconds after creation
                self.updated_at = now()
        super(TimestampedMixin, self).save(*args, **kwargs)

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = now()
        kwargs = {
            'using': using,
        }
        if hasattr(self, 'updated_at'):
            kwargs['disable_auto_updated_at'] = True
        self.save(**kwargs)