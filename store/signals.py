from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        print(f"Creating UserProfile for user {instance.username}")
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()
# signals.py
import string
import random
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Referral
import string
import random
from django.db.models.signals import post_save
from django.dispatch import receiver

def generate_referral_code():
    """Generate a unique referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

@receiver(post_save, sender=User)
def create_referral_for_new_user(sender, instance, created, **kwargs):
    """Create a referral for a new user."""
    if created:
        referral = Referral.objects.create(user=instance, code=generate_referral_code())
        print(f"Referral created: {referral.code}")
