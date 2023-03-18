from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator


class User(AbstractUser):
    email = models.EmailField(null=False)
    first_name = models.CharField(max_length=150, null=False)
    last_name = models.CharField(max_length=150, null=False)
    phone_number = models.IntegerField(null=True)
    avatar = models.TextField(null=True)


class Image(models.Model):
    h = models.CharField(primary_key=True, max_length=32)
    extension = models.CharField(max_length=10)
    data = models.BinaryField()


class Property(models.Model):
    host = models.ForeignKey(
        User, related_name="properties", null=False, on_delete=models.CASCADE
    )
    address = models.CharField(max_length=255, null=False)
    description = models.TextField(null=True)
    guest_capacity = models.PositiveIntegerField(null=False, default=0)
    availability = models.JSONField(null=False, default=list)  # list of objects
    amenities = models.JSONField(null=False, default=list)  # list of strings
    images = models.ManyToManyField(Image, related_name="properties")


class Reservation(models.Model):
    PENDING = "PE"
    DENIED = "DE"
    EXPIRED = "EX"
    APPROVED = "AP"
    CANCELED = "CA"
    TERMINATED = "TE"
    COMPLETED = "CO"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (DENIED, "Denied"),
        (EXPIRED, "Expired"),
        (APPROVED, "Approved"),
        (COMPLETED, "Completed"),
        (CANCELED, "Cancelled"),
        (TERMINATED, "Terminated"),
    ]
    guest = models.ForeignKey(
        User, related_name="reservations_outgoing", null=False, on_delete=models.CASCADE
    )
    property = models.ForeignKey(
        Property, related_name="reservations", null=False, on_delete=models.CASCADE
    )
    status = models.CharField(
        max_length=20, null=False, default=PENDING, choices=STATUS_CHOICES
    )
    guest_count = models.PositiveIntegerField(null=False, default=1)
    from_date = models.DateField(null=True)
    to_date = models.DateField(null=True)


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    is_cancel_req = models.BooleanField(default=False)
    is_cleared = models.BooleanField(default=False)
    content = models.TextField(default=None)
