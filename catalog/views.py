import random
import shlex
from typing import Any

from django.db.models.query import QuerySet
from django.shortcuts import redirect, render
from django.views import generic
from django.db.models import F, Q, Value, Count, CharField, Prefetch
from django.db.models.functions import Concat

from .models import Ruleset, Match, Designer, ORG, Tag, YearAward

def double_quote_split(value):
    # https://stackoverflow.com/questions/6868382/python-shlex-split-ignore-single-quotes
    lex = shlex.shlex(value, posix=True)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    try:
        return list(lex)
    except ValueError:
        return ['"']

SEARCH_FIELDS = ["name", "tag", "designer", "award", "org", "type", "players"]

class Expression:
    def __init__(self, field: str, operator: str, search: str):
        """
        field (operator) search
        ex. number > =13
        """
        # supported search fields
        if not (field.lower() in SEARCH_FIELDS):
            raise ValueError
        
        # if searching using greater than or lesser than on strings, return error
        if field != "players" and not (operator in ["!=", "="]):
            raise ValueError
        
        if field.lower() == 'org':
            # capitalize ORG for pretty print purposes
            self.field = "ORG"
        else:
            self.field = field

        self.operator = operator

        if search.count('"') == 2:
            self.search = search.replace('"', '')
        else:
            self.search = search

class Query:
    def __init__(self):
        self.expressions = []

    def add_expression(self, exp: Expression):
        self.expressions.append(exp)

    def __str__(self):
        lst = []

        for exp in self.expressions:
            if exp.field in ['tag', 'award']:
                if exp.operator == "=":
                    lst.append(f"has {exp.search} {exp.field}")
                else:
                    lst.append(f"doesn't have {exp.search} {exp.field}")

            elif exp.field == 'players':
                lst.append(f"{exp.field} {exp.operator} {exp.search}")
            else:
                operator_to_verb = {
                    "=": "is",
                    "!=": "isn't",
                }

                lst.append(f"{exp.field} {operator_to_verb[exp.operator]} {exp.search}")
        
        return ", ".join(lst)

def parse_query(query: str):
    """
    Helper function that parses a text query into
    a dictionary object 
    """
    # replace mobile version of quotes with standard ones
    query = query.replace("“", "\"").replace("‘", "\"") 

    # double_quote_split preserves double-quotes
    criteria = double_quote_split(query)
    query_obj = Query()

    # TODO: implement NOT/OR/AND

    invalid_query = False

    for criterion in criteria:
        try:
            if "!=" in criterion:
                field, search = criterion.split("!=")
                exp = Expression(field, "!=", search)
            elif ">=" in criterion:
                field, search = criterion.split(">=")
                exp = Expression(field, ">=", search)
            elif "<=" in criterion:
                field, search = criterion.split("<=")
                exp = Expression(field, "<=", search)
            elif ">" in criterion:
                field, search = criterion.split(">")
                exp = Expression(field, ">", search)
            elif "<" in criterion:
                field, search = criterion.split("<")
                exp = Expression(field, "<", search)
            elif "=" in criterion:
                field, search = criterion.split("=")
                exp = Expression(field, "=", search)
            elif ":" in criterion:
                field, search = criterion.split(":")
                exp = Expression(field, "=", search)
            else:
                exp = Expression("name", "=", criterion)
        except ValueError:
            invalid_query = True
        else:
            query_obj.add_expression(exp)

    return query_obj, invalid_query

def annotate_match(match):
    """
    Given a list of Rulesets for a Match,
    return ORGs, Player Counts, Tags, and Aliases
    to annotate the Match itself with. 
    """
    rulesets = match.rulesets.all()
    match.ORGs = sorted(set(ruleset.ORG for ruleset in rulesets), key=lambda org: org.start_date)
    match.player_counts = "/".join([str(count) for count in sorted(set(ruleset.player_count for ruleset in rulesets))])

    tags = set()
    match.aliases = set()
    for ruleset in rulesets:
        for tag in ruleset.tags.all():
            tags.add(tag)

        if ruleset.alias:
            match.aliases.add(ruleset.alias)

    match.tags = sorted(tags, key=lambda tag: tag.name)

    return match

# Create your views here.
def index(request):
    matches = Match.objects.all().only('pk')
    num_matches = matches.count()
    
    context = {
        'num_matches': num_matches
    }

    return render(request, 'index.html', context=context)

def random_redirect(request):
    matches = Match.objects.values_list('pk', flat=True)
    rand = random.choice(matches)

    return redirect('match-detail', pk=rand, permanent=True)
    
def about_us(request):
    return render(request, 'about_us.html')

def tag_generator(request):
    num = request.GET.get('num')

    if request.GET.get('num'):
        try:
            num = int(num)
        except ValueError:
            return render(request, 'tag_generator.html')

        tags = list(Tag.objects.all())
        random.shuffle(tags)
        tags = tags[:num]

        rulesets = Ruleset.objects.all()

        for tag in tags:
            rulesets = rulesets.filter(Q(tags__name__contains=tag))

        rulesets = (
                    rulesets
                    .distinct()
                    .select_related('ORG')
                    .select_related('match')
                    .prefetch_related('match__designers')
                    .prefetch_related(
                        Prefetch(
                            'match__rulesets',
                            queryset=Ruleset.objects.order_by('ordering', 'id').select_related('ORG')
                        )
                    )
                    .prefetch_related('tags')
                )

        context = {
            'generated_tags': tags,
            'generated_count': rulesets.count(),
            'tags_rulesets': rulesets,
            'num': num
        }
    else:
        context = {}

    return render(request, 'tag_generator.html', context=context)

class SearchView(generic.ListView):
    model = Ruleset
    template_name = "search.html"

    def get_queryset(self): 
        query = self.request.GET.get('q')

        if query is not None:
            query_obj, _ = parse_query(query)
            object_list = Ruleset.objects.exclude(rules="-")
            
            for exp in query_obj.expressions:
                if exp.field == 'name':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(alias__icontains=exp.search) | (Q(alias=None) & Q(match__name__icontains=exp.search)))
                    else:
                        object_list = object_list.filter(~Q(alias__icontains=exp.search) | (Q(alias=None) & Q(match__name__icontains=exp.search)))
                
                elif exp.field == 'tag':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(tags__name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(tags__name__icontains=exp.search))

                elif exp.field == 'designer':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(match__designers__name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(match__designers__name__icontains=exp.search))

                elif exp.field == 'award':
                    if exp.operator == "=":
                        object_list = object_list.alias(award_name=Concat(F('match_awards__award__name'), Value(' '), F('match__awards__year'), output_field=CharField())).filter(Q(award_name__icontains=exp.search))
                    else:
                        object_list = object_list.alias(award_name=Concat(F('match_awards__award__name'), Value(' '), F('match__awards__year'), output_field=CharField())).filter(~Q(award_name__icontains=exp.search))

                elif exp.field == 'ORG':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(ORG__name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(ORG__name__icontains=exp.search))

                elif exp.field == 'type':
                    if exp.operator == "=":
                        if exp.search.upper() == "MM":
                            object_list = object_list.filter(Q(match__match_type__exact="MM"))
                        if exp.search.upper() == "DM":
                            object_list = object_list.filter(Q(match__match_type__exact="DM"))
                    else:
                        if exp.search.upper() == "MM":
                            object_list = object_list.filter(Q(match__match_type__exact="DM"))
                        if exp.search.upper() == "DM":
                            object_list = object_list.filter(Q(match__match_type__exact="MM"))

                elif exp.field == 'players':
                    if exp.operator == ">":
                        object_list = object_list.filter(Q(player_count__gt=exp.search))
                    elif exp.operator == "<":
                        object_list = object_list.filter(Q(player_count__lt=exp.search))
                    elif exp.operator == ">=":
                        object_list = object_list.filter(Q(player_count__gte=exp.search))
                    elif exp.operator == "<=":
                        object_list = object_list.filter(Q(player_count__lte=exp.search))
                    elif exp.operator == "!=":
                        object_list = object_list.filter(~Q(player_count__exact=exp.search))
                    else:
                        object_list = object_list.filter(Q(player_count__exact=exp.search))

            object_list = (object_list
                            .distinct()
                            .select_related('ORG')
                            .select_related('match')
                            .prefetch_related('match__designers')
                            .prefetch_related(
                                Prefetch(
                                    'match__rulesets',
                                    queryset=Ruleset.objects.order_by('ordering', 'id').select_related('ORG')
                                )
                            )
                            .prefetch_related('tags')
                            .order_by('ordering', 'id')
                        )
            
            return object_list
        else:
            return Ruleset.objects.none()
        
    def get_context_data(self, **kwargs):
        # necessary to add query to context to display on results
        context = super(SearchView, self).get_context_data(**kwargs)
        query = self.request.GET.get('q')

        if query:
            context['query'], context['invalid_query'] = parse_query(query)

            if str(context['query']) == "":
                context['query'] = "empty query"

        if query is not None:
            context["opengraph_title"] = "Search Results"
            context["opengraph_description"] = f"Search results for {', '.join(double_quote_split(query))}."
        else:
            context["opengraph_title"] = "Search"
            context["opengraph_description"] = "Search for matches on The Genius Repository."

        context["filtered_ruleset_list"] = []
        filtered_pks = []

        for object in context["object_list"]:
            if object.match.pk not in filtered_pks:
                context["filtered_ruleset_list"].append(object)
                filtered_pks.append(object.match.pk)

        return context

class GenericMatchListView(generic.ListView):
    """
    Generic class that is shared between
    the Match list view that is paginated
    and unpaginated.
    """
    model = Match

    def get_queryset(self):
        queryset = super().get_queryset().prefetch_related(Prefetch('rulesets', queryset=Ruleset.objects.select_related('ORG').prefetch_related('tags'))).prefetch_related('designers')
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(GenericMatchListView, self).get_context_data(**kwargs)
        
        for match in context['match_list']:
            match = annotate_match(match)
            
        return context

class PagedMatchListView(GenericMatchListView):
    template_name = "catalog/match/paged_match_list.html"
    paginate_by = 20

    def get_queryset(self):
        # sort matches purely by alphabetical order for pagination,
        # so that the first few pages aren't entirely dominated by MMs
        queryset = super().get_queryset().order_by("name")
        return queryset

class MatchListView(GenericMatchListView):
    template_name = "catalog/match/match_list.html"

class DesignerListView(generic.ListView):
    model = Designer
    template_name = "catalog/designer/designer_list.html"

    def get_context_data(self, **kwargs):
        context = super(DesignerListView, self).get_context_data(**kwargs)
        
        context['sorted_designer_list'] = context['designer_list'].annotate(num_matches=Count('match')).order_by("-num_matches")

        # abusing the crap out of Prefetch to collect every single piece of data necessary for the loops later
        context['sorted_designer_list'] = context['sorted_designer_list'].prefetch_related(
            Prefetch(
                    'match_set',
                     queryset=Match.objects.prefetch_related(
                         Prefetch(
                                'rulesets',
                                queryset=Ruleset.objects.select_related('ORG'))
                         )
                     )
            )
        
        context['designer_orgs'] = {}
        
        for designer in context['sorted_designer_list']:
            org_list = []
            for game in designer.match_set.all():
                game_list = game.rulesets.all()
                for ruleset in game_list:
                    # This is a really crappy way of making sure I can have the ORGs in the right order (by start date).
                    # I just simply save the start date into the list alongside the name, then sort it manually
                    # using the second element later. Then, in the actual HTML, only access the first element for
                    # actual display. Also, the third element stores the URL because now we can't access that easily!
                    # I love Django! There is almost certainly an easier way to do this, but my hackish method works...
                    # I think.
                    org_info = [ruleset.ORG.name, ruleset.ORG.start_date, ruleset.ORG.get_absolute_url()]
                    if org_info not in org_list: 
                        org_list.append(org_info)

            org_list.sort(key=lambda x: x[1])

            if len(org_list) > 0:
                context['designer_orgs'][designer.name] = org_list

        return context

class ORGListView(generic.ListView):
    model = ORG
    template_name = "catalog/org/org_list.html"

    def get_queryset(self):
        queryset = ORG.objects.all().prefetch_related('ruleset_set').select_related('main_host')
        return queryset

class TagListView(generic.ListView):
    model = Tag

    def get_queryset(self):
        queryset = Tag.objects.all().annotate(count=Count('ruleset'))
        return queryset

# TODO: Awards Detail View

class YearAwardListView(generic.ListView):
    model = YearAward

    def get_queryset(self):
        queryset = YearAward.objects.all().prefetch_related('match_set').select_related('award')
        return queryset

    def get_context_data(self, **kwargs):
        context = super(YearAwardListView, self).get_context_data(**kwargs)
        context['sorted_award_dct'] = {}

        lst = context['yearaward_list'].all()

        for award in lst:
            if award.year in context['sorted_award_dct']:
                context['sorted_award_dct'][award.year].append(award)
            else:
                context['sorted_award_dct'][award.year] = [award]

        return context

class MatchDetailView(generic.DetailView):
    model = Match
    template_name = "catalog/match/match_detail.html"

    def get_queryset(self):
        return Match.objects.prefetch_related(
            Prefetch('rulesets', queryset=Ruleset.objects.select_related('ORG').prefetch_related('tags').order_by('ordering', 'id')),
            Prefetch('designers', queryset=Designer.objects.only('name')),
            Prefetch('awards', queryset=YearAward.objects.all())
        )

    def get_context_data(self, **kwargs):
        import re, copy
        context = super(MatchDetailView, self).get_context_data(**kwargs)

        query_ruleset = self.request.GET.get('rs')

        # default parameters: the first tab and the match name
        context['active_ruleset'] = -1
        context['ruleset_name'] = context['match'].name

        context['match'] = annotate_match(context['match'])

        # exclude rulesets with only "-", as it is a placeholder character
        # to denote a ruleset that isn't on the repository yet
        rulesets = context['match'].rulesets.exclude(rules="-")

        for ruleset in rulesets:
            # set ruleset_name to correct alias on first page load.
            if query_ruleset is not None and query_ruleset.isdigit() and ruleset.pk == int(query_ruleset):
                context['active_ruleset'] = int(query_ruleset)

                if ruleset.alias is not None and ruleset.alias != "":
                    context['ruleset_name'] = ruleset.alias

            # split rules by \r\n so that each can be displayed in
            # their own div and each can be markdownified properly.
            # also, this makes image processing possible as well.
            rulesets_line_breaks = ruleset.rules.replace("\r\n", "\n").split("\n")

            # let's re-join together some things that need it for proper rendering.
            for rules in rulesets_line_breaks:
                begin = -1
                end = -1
                copy_rules = copy.copy(rules) # make a copy of the ruleset so we don't have to deal with index shenanigans

                # re-join together ordered lists
                for rule in copy_rules:
                    if re.match("[0-9]+.", rule) is not None:
                        if begin == -1:
                            begin = rule
                            end = rule
                        else:
                            end = rule
                    else:
                        if begin != -1:
                            b = rules.index(begin)
                            e = rules.index(end)
                            rules[b:e+1] = ['\n'.join(rules[b:e+1])]
                            begin = -1
                            end = -1
                else:
                    if begin != -1:
                        b = rules.index(begin)
                        e = rules.index(end)
                        rules[b:e+1] = ['\n'.join(rules[b:e+1])]
                        begin = -1
                        end = -1

                # then, re-join together unordered lists
                begin = -1
                end = -1
                for rule in copy_rules:
                    if rule.startswith("- "):
                        if begin == -1:
                            begin = rule
                            end = rule
                        else:
                            end = rule
                    else:
                        if begin != -1:
                            b = rules.index(begin)
                            e = rules.index(end)
                            rules[b:e+1] = ['\n'.join(rules[b:e+1])]
                            begin = -1
                            end = -1
                else:
                    if begin != -1:
                        b = rules.index(begin)
                        e = rules.index(end)
                        rules[b:e+1] = ['\n'.join(rules[b:e+1])]
                        begin = -1
                        end = -1

                # i apologize for bad coding

            rulesets_line_breaks_no_trailing_newlines = []

            for rules in rulesets_line_breaks:
                # let's delete all trailing elements that are empty, 
                # as they are unnecessary to render.
                delete_blanks = None
                for i, line in reversed(list(enumerate(rules))):
                    if line != "":
                        delete_blanks = i + 1
                        break
                
                if delete_blanks is not None:
                    rules = rules[:delete_blanks]
            
                rulesets_line_breaks_no_trailing_newlines.append(rules)

            ruleset.rules_formatted = rulesets_line_breaks_no_trailing_newlines

        context['rulesets'] = rulesets

        return context

class DesignerDetailView(generic.DetailView):
    model = Designer
    template_name = "catalog/designer/designer_detail.html"

    def get_context_data(self, **kwargs):
        context = super(DesignerDetailView, self).get_context_data(**kwargs)
        context['match_list'] = context['designer'].match_set.all().prefetch_related('designers')
        context['match_list'] = context['match_list'].prefetch_related(
            Prefetch(
                'rulesets',
                queryset=Ruleset.objects.select_related('ORG').prefetch_related('tags')
            )
        )
        
        for match in context['match_list']:
            match = annotate_match(match)

        context['match_exists'] = len(context['match_list']) > 0

        return context

class ORGDetailView(generic.DetailView):
    model = ORG
    template_name = "catalog/org/org_detail.html"

    def get_context_data(self, **kwargs):
        context = super(ORGDetailView, self).get_context_data(**kwargs)
        context['ruleset_list'] = (context['org'].ruleset_set.all()
                                    .select_related('ORG')
                                    .select_related('match')
                                    .prefetch_related('match__designers')
                                    .prefetch_related(
                                        Prefetch(
                                            'match__rulesets',
                                            queryset=Ruleset.objects.order_by('ordering', 'id').select_related('ORG'))
                                        )
                                    .prefetch_related('tags')
                                )

        context['ruleset_exists'] = len(context['ruleset_list']) > 0

        twists = context['org'].twists.split("\n")
        context['twists'] = twists
        
        return context
