from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser, Article, Journal, Author, Country


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    list_display = ['username', ]


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Journal)
admin.site.register(Author)
admin.site.register(Article)
admin.site.register(Country)

