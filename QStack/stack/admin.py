from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Question, Answer, Tag, VoteAnswer, VoteQuestion
from .forms import CustomUserCreationForm, CustomUserChangeForm
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe


class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = get_user_model()
    list_display = ['email', 'username', 'first_name', 'last_name', 'image', 'image_tag']
    readonly_fields = ('image_tag',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('email', 'image', 'image_tag')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = ((None, {
            'classes': ('wide',),
            'fields': ('username', 'password1', 'password2', 'image'),
        }),)

    def image_tag(self, obj):
        if obj.id:
            return mark_safe('<img src="/photos/%s" width="150" height="150" />' % obj.image)
        return ''

    image_tag.short_description = 'Image'
    image_tag.allow_tags = True


admin.site.register(VoteQuestion)
admin.site.register(VoteAnswer)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Tag)
admin.site.register(get_user_model(), CustomUserAdmin)
