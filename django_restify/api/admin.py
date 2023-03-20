from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User,
    Property,
    Reservation,
    PropertyComment,
    UserComment,
    Reply,
    Image,
)

# Register your models here.
admin.site.register(User, UserAdmin)
admin.site.register(Property)
admin.site.register(Reservation)
admin.site.register(PropertyComment)
admin.site.register(UserComment)
admin.site.register(Reply)
admin.site.register(Image)
