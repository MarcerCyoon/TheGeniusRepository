import shlex

from django.shortcuts import render
from django.views import generic
from django.db.models import F, Q, Value, Count, CharField
from django.db.models.functions import Concat

from .models import Match, Designer, ORG, Tag, YearAward

def double_quote_split(value):
    # https://stackoverflow.com/questions/6868382/python-shlex-split-ignore-single-quotes
    lex = shlex.shlex(value, posix=True)
    lex.quotes = '"'
    lex.whitespace_split = True
    lex.commenters = ''
    return list(lex)

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
        self.search = search.replace('"', '')

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

# Create your views here.
def index(request):
    num_matches = Match.objects.all().count()
    
    context = {
        'num_matches': num_matches
    }

    return render(request, 'index.html', context=context)

def about_us(request):
    return render(request, 'about_us.html')

def tag_generator(request):
    num = request.GET.get('num')

    if request.GET.get('num'):
        try:
            num = int(num)
        except ValueError:
            return render(request, 'tag_generator.html')

        import random

        tags = list(Tag.objects.all())
        random.shuffle(tags)
        tags = tags[:num]

        matches = Match.objects.all()

        for tag in tags:
            matches = matches.filter(Q(tags__name__contains=tag))

        matches = matches.distinct().prefetch_related('ORGs').prefetch_related('designers').prefetch_related('tags')

        context = {
            'generated_tags': tags,
            'generated_count': matches.count(),
            'tags_matches': matches,
            'num': num
        }
    else:
        context = {}

    return render(request, 'tag_generator.html', context=context)

class SearchView(generic.ListView):
    model = Match
    template_name = "search.html"

    def get_queryset(self): 
        query = self.request.GET.get("q")

        if query is not None:
            query_obj, _ = parse_query(query)
            object_list = Match.objects.all()
            
            for exp in query_obj.expressions:
                if exp.field == 'name':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(name__icontains=exp.search))
                
                elif exp.field == 'tag':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(tags__name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(tags__name__icontains=exp.search))

                elif exp.field == 'designer':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(designers__name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(designers__name__icontains=exp.search))

                elif exp.field == 'award':
                    if exp.operator == "=":
                        object_list = object_list.alias(award_name=Concat(F('awards__award__name'), Value(' '), F('awards__year'), output_field=CharField())).filter(Q(award_name__icontains=exp.search))
                    else:
                        object_list = object_list.alias(award_name=Concat(F('awards__award__name'), Value(' '), F('awards__year'), output_field=CharField())).filter(~Q(award_name__icontains=exp.search))

                elif exp.field == 'ORG':
                    if exp.operator == "=":
                        object_list = object_list.filter(Q(ORGs__name__icontains=exp.search))
                    else:
                        object_list = object_list.filter(~Q(ORGs__name__icontains=exp.search))

                elif exp.field == 'type':
                    if exp.operator == "=":
                        if exp.search.upper() == "MM":
                            object_list = object_list.filter(Q(match_type__exact="MM"))
                        if exp.search.upper() == "DM":
                            object_list = object_list.filter(Q(match_type__exact="DM"))
                    else:
                        if exp.search.upper() == "MM":
                            object_list = object_list.filter(Q(match_type__exact="DM"))
                        if exp.search.upper() == "DM":
                            object_list = object_list.filter(Q(match_type__exact="MM"))

                elif exp.field == 'players':
                    if exp.operator == ">":
                        object_list = object_list.filter(Q(min_players__gt=exp.search))
                    elif exp.operator == "<":
                        object_list = object_list.filter(Q(min_players__lt=exp.search))
                    elif exp.operator == ">=":
                        object_list = object_list.filter(Q(min_players__gte=exp.search))
                    elif exp.operator == "<=":
                        object_list = object_list.filter(Q(min_players__lte=exp.search))
                    elif exp.operator == "!=":
                        object_list = object_list.filter(~Q(min_players__exact=exp.search))
                    else:
                        object_list = object_list.filter(Q(min_players__exact=exp.search))

            object_list = object_list.distinct().prefetch_related('ORGs').prefetch_related('designers').prefetch_related('tags')
            return object_list
        else:
            return Match.objects.none()
        
    def get_context_data(self, **kwargs):
        # necessary to add query to context to display on results
        context = super(SearchView, self).get_context_data(**kwargs)
        query = self.request.GET.get("q")

        if query:
            context['query'], context['invalid_query'] = parse_query(self.request.GET.get('q'))

            if str(context['query']) == "":
                context['query'] = "empty query"

        return context

class MatchListView(generic.ListView):
    model = Match

    def get_queryset(self):
        queryset = Match.objects.all().defer('max_players', 'summary', 'rules').prefetch_related('ORGs').prefetch_related('designers').prefetch_related('tags')
        return queryset

class DesignerListView(generic.ListView):
    model = Designer

    def get_context_data(self, **kwargs):
        context = super(DesignerListView, self).get_context_data(**kwargs)
        context['sorted_designer_list'] = context['designer_list'].annotate(num_matches=Count('match')).order_by("-num_matches").prefetch_related('match_set')
        context['designer_orgs'] = {}
        
        for designer in context['sorted_designer_list']:
            match_list = designer.match_set.all().prefetch_related('ORGs').only('ORGs')
            if match_list.count() > 0:
                org_list = []
                for game in match_list:
                    for ORG in game.ORGs.all().only('name', 'start_date'):
                        # This is a really crappy way of making sure I can have the ORGs in the right order (by start date).
                        # I just simply save the start date into the list alongside the name, then sort it manually
                        # using the second element later. Then, in the actual HTML, only access the first element for
                        # actual display. Also, the third element stores the URL because now we can't access that easily!
                        # I love Django! There is almost certainly an easier way to do this, but my hackish method works...
                        # I think.
                        org_info = [ORG.name, ORG.start_date, ORG.get_absolute_url()]
                        if org_info not in org_list: 
                            org_list.append(org_info)

                org_list.sort(key=lambda x: x[1])

                context['designer_orgs'][designer.name] = org_list

        return context

class ORGListView(generic.ListView):
    model = ORG

    def get_queryset(self):
        queryset = ORG.objects.all().prefetch_related('match_set')
        # queryset = Match.objects.all().defer('max_players', 'summary', 'rules').prefetch_related('ORGs').prefetch_related('designers').prefetch_related('tags')
        return queryset

class TagListView(generic.ListView):
    model = Tag

    def get_queryset(self):
        queryset = Tag.objects.all().prefetch_related('match_set')
        return queryset

# TODO: Awards Detail View

class YearAwardListView(generic.ListView):
    model = YearAward

    def get_context_data(self, **kwargs):
        context = super(YearAwardListView, self).get_context_data(**kwargs)
        context['sorted_award_dct'] = {}

        for award in context['yearaward_list'].all():

            if award.year in context['sorted_award_dct']:
                context['sorted_award_dct'][award.year].append(award)
            else:
                context['sorted_award_dct'][award.year] = [award]

        return context

class MatchDetailView(generic.DetailView):
    model = Match

    def get_context_data(self, **kwargs):
        import re, copy
        context = super(MatchDetailView, self).get_context_data(**kwargs)

        # split by pre-chosen divider $%^ to get different rulesets
        rulesets = context['match'].rules.split("$%^")[1:]
        titles = rulesets[::2] # all even indices are titles
        rulesets = rulesets[1::2] # all odd indices are rulesets

        rulesets_line_breaks = []

        for ruleset in rulesets:
            # split rules by \r\n so that each can be displayed in
            # their own div and each can be markdownified properly.
            # also, this makes image processing possible as well.
            ruleset_line_breaks = ruleset.replace("\r\n", "\n").split("\n")
            rulesets_line_breaks.append(ruleset_line_breaks)

        # let's re-join together some things that need it for proper rendering.
        for ruleset in rulesets_line_breaks:
            begin = -1
            end = -1
            copy_ruleset = copy.copy(ruleset) # make a copy of the ruleset so we don't have to deal with index shenanigans

            # re-join together ordered lists
            for rule in copy_ruleset:
                if re.match("[0-9]+.", rule) is not None:
                    if begin == -1:
                        begin = rule
                        end = rule
                    else:
                        end = rule
                else:
                    if begin != -1:
                        b = ruleset.index(begin)
                        e = ruleset.index(end)
                        ruleset[b:e+1] = ['\n'.join(ruleset[b:e+1])]
                        begin = -1
                        end = -1
            else:
                if begin != -1:
                    b = ruleset.index(begin)
                    e = ruleset.index(end)
                    ruleset[b:e+1] = ['\n'.join(ruleset[b:e+1])]
                    begin = -1
                    end = -1

            # then, re-join together unordered lists
            begin = -1
            end = -1
            for rule in copy_ruleset:
                if rule.startswith("- "):
                    if begin == -1:
                        begin = rule
                        end = rule
                    else:
                        end = rule
                else:
                    if begin != -1:
                        b = ruleset.index(begin)
                        e = ruleset.index(end)
                        ruleset[b:e+1] = ['\n'.join(ruleset[b:e+1])]
                        begin = -1
                        end = -1
            else:
                if begin != -1:
                    b = ruleset.index(begin)
                    e = ruleset.index(end)
                    ruleset[b:e+1] = ['\n'.join(ruleset[b:e+1])]
                    begin = -1
                    end = -1

            # i apologize for bad coding

        rulesets_line_breaks_no_trailing_newlines = []

        for ruleset in rulesets_line_breaks:
            # let's delete all trailing elements that are empty, 
            # as they are unnecessary to render.
            delete_blanks = None
            for i, line in reversed(list(enumerate(ruleset))):
                if line != "":
                    delete_blanks = i + 1
                    break
            
            if delete_blanks is not None:
                ruleset = ruleset[:delete_blanks]

            rulesets_line_breaks_no_trailing_newlines.append(ruleset)

        context['rulesets_line_breaks'] = rulesets_line_breaks_no_trailing_newlines
        context['titles'] = titles

        return context

class DesignerDetailView(generic.DetailView):
    model = Designer

    def get_context_data(self, **kwargs):
        context = super(DesignerDetailView, self).get_context_data(**kwargs)
        context['match_list'] = context['designer'].match_set.all().prefetch_related('ORGs').prefetch_related('designers').prefetch_related('tags')
        context['match_exists'] = len(context['match_list']) > 0

        return context

class ORGDetailView(generic.DetailView):
    model = ORG

    def get_context_data(self, **kwargs):
        context = super(ORGDetailView, self).get_context_data(**kwargs)
        context['match_list'] = context['org'].match_set.all().prefetch_related('ORGs').prefetch_related('designers').prefetch_related('tags')
        context['match_exists'] = len(context['match_list']) > 0
        # split by \n
        twists = context['org'].twists.split("\n")
        context['twists'] = twists

        return context