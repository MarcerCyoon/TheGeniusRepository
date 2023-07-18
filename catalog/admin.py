from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateWidget

import datetime

from .models import Match, Designer, ORG, Tag

# Register your models here.

class MatchResource(resources.ModelResource):
    # Custom resource for import so that
    # you don't need to know the pk of
    # designer, ORG and can just use name

    def before_import_row(self, row, **kwargs):
        designer_name = row["designer"]
        Designer.objects.get_or_create(name=designer_name, defaults={"name": designer_name, "desc": "TBD"})

    designer = fields.Field(
        column_name='designer',
        attribute='designer',
        widget=ForeignKeyWidget(Designer, field='name'))
    
    orgs = fields.Field(
        column_name='orgs',
        attribute='ORGs',
        widget=ManyToManyWidget(ORG, field='name', separator='|')
    )

    class Meta:
        model = Match


class ORGResource(resources.ModelResource):
    # Custom resource for import so that
    # you don't need to know the pk of
    # main host and can just use name

    def before_import_row(self, row, **kwargs):
        designer_name = row["main_host"]
        Designer.objects.get_or_create(name=designer_name, defaults={"name": designer_name, "desc": "TBD"})
    
    main_host = fields.Field(
        column_name='main_host',
        attribute='main_host',
        widget=ForeignKeyWidget(Designer, field='name'))
    
    start_date = fields.Field(column_name="start_date", attribute="start_date", widget=DateWidget(format='%m/%d/%y'))
    end_date = fields.Field(column_name="end_date", attribute="end_date", widget=DateWidget(format='%m/%d/%y'))
    
    class Meta:
        model = ORG


@admin.register(Match)
class MatchAdmin(ImportExportModelAdmin):
    resource_classes = [MatchResource]
    list_display = ('match_type', 'name', 'designer', 'display_ORGs', 'display_tags')
    list_display_links = ['name']
    list_filter = ('match_type', 'designer')

admin.site.register(Designer)

@admin.register(ORG)
class ORGAdmin(ImportExportModelAdmin):
    resource_classes = [ORGResource]
    list_displayer = ('name', 'main_host', 'start_date', 'end_date')

admin.site.register(Tag)