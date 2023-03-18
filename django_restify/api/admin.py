from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Property, Reservation, Image

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Property)
admin.site.register(Reservation)
admin.site.register(Image)
