from django.contrib import admin

from .models import Match, Designer, ORG, Tag

# Register your models here.

@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ('match_type', 'name', 'designer', 'display_ORGs', 'display_tags')
    list_display_links = ['name']
    list_filter = ('match_type', 'designer')

admin.site.register(Designer)

@admin.register(ORG)
class ORGAdmin(admin.ModelAdmin):
    list_displayer = ('name', 'main_host', 'start_date', 'end_date')

admin.site.register(Tag)