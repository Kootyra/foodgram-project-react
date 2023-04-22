from django.contrib import admin
from .models import User, Subscriptions


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'username', 'email', 'password', 'first_name', 'last_name',
    )
    list_editable = ('password', )
    list_filter = ('username', 'email')
    search_fields = ('username', 'email')
    empty_value_display = '-пусто-'


@admin.register(Subscriptions)
class SubscribeAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'user', 'author')
    list_editable = ('user', 'author')
    empty_value_display = '-пусто-'
