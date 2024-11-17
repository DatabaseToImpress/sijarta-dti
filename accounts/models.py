from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=[('User', 'User'), ('Worker', 'Worker')])
    phone_number = models.CharField(max_length=15, unique=True)
    sex = models.CharField(max_length=1, choices=[('F', 'Female'), ('M', 'Male')])
    birth_date = models.DateField()
    address = models.TextField()
    # Fields specific to Worker role
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    account_number = models.CharField(max_length=20, null=True, blank=True)
    npwp = models.CharField(max_length=15, null=True, blank=True)
    image_url = models.URLField(null=True, blank=True)

# Signals to create/update Profile automatically when User is saved
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()