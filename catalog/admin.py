import json

from django.contrib import admin
from django.forms import inlineformset_factory, ModelForm
from import_export.admin import ImportExportModelAdmin
from import_export import fields, resources
from import_export.widgets import ForeignKeyWidget, ManyToManyWidget, DateWidget

from .models import Ruleset, Match, Designer, ORG, Tag, Award, YearAward

# Register your models here.

# class RulesetResource(resources.ModelResource):
#     def before_import_row(self, row, **kwargs):
#         tags = row["tags"]
#         for tag_name in tags.split(", "):
#             # create tags that don't exist
#             Tag.objects.get_or_create(name=tag_name, defaults={"name": tag_name})

#         designer_names = row["designer"]
#         for designer_name in designer_names.split(", "):
#             # create designers that don't exist
#             Designer.objects.get_or_create(name=designer_name, defaults={"name": designer_name, "desc": "TBD"})

#     tags = fields.Field(
#         column_name='tags',
#         attribute='tags',
#         widget=ManyToManyWidget(Tag, field='name', separator=', ')
#     )

#     org = fields.Field(
#         column_name="ORG",
#         attribute="ORG",
#         widget=ForeignKeyWidget(ORG, field='name')
#     )

#     designers = fields.Field(
#         column_name="designers",
#         attribute="match__designers",
#         widget=ManyToManyWidget(Designer, field='name', separator=', ')
#     )

#     match = fields.Field(
#         column_name="match",
#         attribute="match",
#         widget=ForeignKeyWidget(Match)
#     )

#     name = fields.Field(
#         column_name="match name",
#         attribute="match__name"
#     )

#     class Meta:
#         model = Ruleset
#         name = "Import/export with names"

class RulesetResource(resources.ModelResource):
    ORG = fields.Field(
            column_name='ORG',
            attribute='ORG',
            widget=ForeignKeyWidget(ORG, field='name'))

    tags = fields.Field(
        column_name='tags',
        attribute='tags',
        widget=ManyToManyWidget(Tag, field='name', separator=', ')
    )
    
    class Meta:
        model = Ruleset
        name = "Import/export with names"
        import_order = ('id', 'alias', 'ORG', 'episode', 'rules', 'tags', 'player_count', 'ordering', 'match')
        export_order = ('id', 'alias', 'ORG', 'episode', 'rules', 'tags', 'player_count', 'ordering', 'match')

class RulesetBasicResource(resources.ModelResource):
    class Meta:
        model = Ruleset
        name = "Import/export with PKs"

# class MatchResource(resources.ModelResource):
#     # Custom resource for import so that
#     # you don't need to know the pk of
#     # designer, ORG and can just use name

#     def before_import_row(self, row, **kwargs):
#         designer_names = row["designer"]
#         for designer_name in designer_names.split(", "):
#             Designer.objects.get_or_create(name=designer_name, defaults={"name": designer_name, "desc": "TBD"})

#         tags = row["tags"]
#         for tag_name in tags.split(", "):
#             # create tags that don't exist
#             Tag.objects.get_or_create(name=tag_name, defaults={"name": tag_name})

#         rulesets = row["rulesets"]
#         for ruleset in rulesets.split("$%^"):
#             Ruleset.objects.get_or_create(rules=ruleset, ORG=None, episode="5") # TODO: fix this

#     designers = fields.Field(
#         column_name='designer',
#         attribute='designers',
#         widget=ManyToManyWidget(Designer, field='name', separator=', '))
    
#     rulesets = fields.Field(
#         column_name="rulesets",
#         attribute='rulesets',
#         widget=ManyToManyWidget(Ruleset, field='rules', separator="$%^")
#     )

#     orgs = fields.Field(
#         column_name='orgs',
#     )

#     def dehydrate_orgs(self, match):
#         data = { int(ruleset.id): ruleset.ORG.name for ruleset in match.rulesets.all() }
#         return json.dumps(data)

#     tags = fields.Field(
#         column_name='tags',
#     )

#     def dehydrate_tags(self, match):
#         data = { int(ruleset.id): list(ruleset.tags.values_list("name", flat=True)) for ruleset in match.rulesets.prefetch_related('tags').all() }
#         return json.dumps(data)

#     class Meta:
#         model = Match
#         name = "Import/export with names"

class MatchResource(resources.ModelResource):
    designers = fields.Field(
        column_name='designers',
        attribute='designers',
        widget=ManyToManyWidget(model=Designer, field='name', separator=', '))

    class Meta:
        model = Match
        name = "Import/export with names"
        import_order = ('id', 'name', 'designers', 'summary', 'match_type', 'see_also', 'awards')
        export_order = ('id', 'name', 'designers', 'summary', 'match_type', 'see_also', 'awards')

class MatchBasicResource(resources.ModelResource):
    class Meta:
        model = Match
        name = "Import/export with PKs"

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

class RulesetInline(admin.StackedInline):
    model = Ruleset
    extra = 0
    filter_horizontal = ('tags',)
    
@admin.register(Match)
class MatchAdmin(ImportExportModelAdmin):
    resource_classes = [MatchResource, MatchBasicResource]
    list_display = ('match_type', 'name', 'display_designers', 'display_ORGs')
    list_display_links = ['name']
    list_filter = ('match_type', 'designers')
    
    inlines = [RulesetInline]
    filter_horizontal = ('designers', 'awards',)

@admin.register(Ruleset)
class RulesetAdmin(ImportExportModelAdmin):
    resource_classes = [RulesetResource, RulesetBasicResource]

    @admin.display(description="Match Type", ordering="match__match_type")
    def get_match_type(self, ruleset):
        return ruleset.match.match_type

    @admin.display(description="Name")
    def get_name(self, ruleset):
        return ruleset.alias if ruleset.alias is not None else ruleset.match.name
    
    list_display = ('get_match_type', 'get_name', 'ORG', 'display_tags')
    list_display_links = ['get_name']
    
    filter_horizontal = ('tags',)

admin.site.register(Designer)

@admin.register(ORG)
class ORGAdmin(ImportExportModelAdmin):
    resource_classes = [ORGResource]
    list_display = ('name', 'main_host', 'start_date', 'end_date')

admin.site.register(Tag)

admin.site.register(Award)

admin.site.register(YearAward)
