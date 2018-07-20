from django.db.models import Model
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from suggest.models import Suggest, AffectedInstance


from functools import wraps
from functools import wraps


def skip_signal():
    def _skip_signal(signal_func):
        @wraps(signal_func)
        def _decorator(sender, instance, **kwargs):
            if hasattr(instance, "skip_signal"):
                return None
            return signal_func(sender, instance, **kwargs)

        return _decorator

    return _skip_signal


@receiver(post_save, sender=Suggest)
@skip_signal()
def suggest_saved(sender, instance, **kwargs):
    def make_ai(instance, model):

        if not isinstance(model, Model):
            return
        if model.pk and not isinstance(model.pk, int):
            return
            # TODO: Handle "null" model PK's
            # TODO: Suggestions API can not yet handle non-integer values for a foreign key

        ai, c = AffectedInstance.objects.get_or_create(
            model_name=u"%s_%s" % (model._meta.app_label, model._meta.model_name),
            suggestion_id=instance.pk,
            model_pk=model.pk,
            primary=False,
        )
        if c:
            ai.save()

    for fieldname, model in instance.references():
        if isinstance(model, list):
            for i in model:
                make_ai(instance, model)
        make_ai(instance, model)


@receiver(post_save, sender=AffectedInstance)
@skip_signal()
def post_save_affectedinstance(sender, instance, **kwargs):
    try:
        s = instance.suggestion
    except Suggest.DoesNotExist:
        return
    # Mark the suggestion as "Accepted" if conditions are met

    if instance.primary and not isinstance(instance, Suggest) and s.action == "CM":
        if instance.instance.pk:
            s.state = "A"
            s.skip_signal = True
            # s.state = 'A'
            s.save()

    # If there is a "child" instance, update the suggestion pk with the "new" pk

    return
