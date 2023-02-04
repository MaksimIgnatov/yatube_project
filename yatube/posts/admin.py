from django.contrib import admin

from .models import Group, Post, Comment, Follow


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display: tuple = (
        'pk',
        'text',
        'created',
        'author',
        'group',
    )
    list_editable: tuple = ('group',)
    search_fields: tuple = ('text',)
    list_filter: tuple = ('created',)
    empty_value_display: str = '-пусто-'


admin.site.register(Group)
admin.site.register(Comment)
admin.site.register(Follow)
