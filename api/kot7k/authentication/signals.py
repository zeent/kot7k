from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from kot7k.applications.models import ApplicationAssignment
from kot7k.authentication.models import AccountActivity
from kot7k.authentication.services.account_activity import record_account_activity


@receiver(post_save, sender=ApplicationAssignment)
def assignment_created(sender, instance, created, **kwargs):
    if created:
        record_account_activity(
            instance.user,
            AccountActivity.Action.ROLE_ASSIGNED,
            f"Role {instance.role.name} assigned for {instance.application.name}.",
            {"application": instance.application.key, "role": instance.role.key},
        )


@receiver(post_delete, sender=ApplicationAssignment)
def assignment_removed(sender, instance, **kwargs):
    record_account_activity(
        instance.user,
        AccountActivity.Action.ROLE_REMOVED,
        f"Role {instance.role.name} removed from {instance.application.name}.",
        {"application": instance.application.key, "role": instance.role.key},
    )
