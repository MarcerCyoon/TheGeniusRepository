import shlex

from django.shortcuts import render
from django.views import generic
from django.db.models import F, Q, Value, Count, CharField
from django.db.models.functions import Concat

from .models import Match, Designer, ORG, YearAward

def parse_query(query: str):
    """
    Helper function that parses a text query into
    a dictionary object 
    """

    query = query.replace("“", "\"").replace("‘", "'") # replace mobile version of quotes with standard ones
    criteria = shlex.split(query) # shlex.split() preserves quotes
    # TODO: fix bug where single quotes cause server error when used as apostrophes 
    # criteria = query.split(" ")
    dct = {}

    # TODO: implement NOT/OR/AND

    for criterion in criteria:
        if "=" in criterion:
            field, search = criterion.split("=")
            if field in dct:
                dct[field].append(search.replace('"', '').replace("'", "")) # get rid of quotes
            else:
                dct[field] = [search.replace('"', '').replace("'", "")] # get rid of quotes

        elif ":" in criterion:
            field, search = criterion.split(":")
            if field in dct:
                dct[field].append(search.replace('"', '').replace("'", "")) # get rid of quotes
            else:
                dct[field] = [search.replace('"', '').replace("'", "")] # get rid of quotess

        else:
            if "name" in dct:
                dct['name'].append(criterion)
            else:
                dct['name'] = [criterion]

    return dct

# Create your views here.
def index(request):
    num_matches = Match.objects.all().count()
    
    context = {
        'num_matches': num_matches
    }

    return render(request, 'index.html', context=context)

class SearchView(generic.ListView):
    model = Match
    template_name = "search.html"

    def get_queryset(self): 
        query = self.request.GET.get("q")

        if query is not None:
            dct = parse_query(query)
            object_list = Match.objects.all()

            if 'name' in dct:
                for name in dct["name"]:
                    object_list = object_list.filter(Q(name__icontains=name))
            
            if 'tag' in dct:
                for tag in dct["tag"]:
                    object_list = object_list.filter(Q(tags__name__icontains=tag))

            if 'designer' in dct:
                for designer in dct["designer"]:
                    object_list = object_list.filter(Q(designers__name__icontains=designer))

            if 'award' in dct:
                for award in dct["award"]:
                    # going to be real with you I don't know how the fuck this works but it does.
                    # https://stackoverflow.com/questions/3300944/can-i-use-django-f-objects-with-string-concatenation
                    # took stuff from here I guess and tinkered with it until it did what I wanted it to
                    # (namely concatenate the award name and the year so that the contains search could operate on both at once)
                    object_list = object_list.alias(award_name=Concat(F('awards__award__name'), Value(' '), F('awards__year'), output_field=CharField())).filter(Q(award_name__icontains=award))

            if 'org' in dct:
                for org in dct["org"]:
                    object_list = object_list.filter(Q(ORGs__name__icontains=org))

            if 'type' in dct:
                for type in dct["type"]:
                    if type.upper() == "MM":
                        object_list = object_list.filter(Q(match_type__iexact="MM"))
                    if type.upper() == "DM":
                        object_list = object_list.filter(Q(match_type__iexact="DM"))

            object_list = object_list.distinct()
            return object_list
        else:
            return Match.objects.none()
        
    def get_context_data(self, **kwargs):
        # necessary to add query to context to display on results
        context = super(SearchView, self).get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q')
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

        # TODO: support underline and spoiler-text (https://stackoverflow.com/questions/28615544/how-can-i-create-spoiler-text)
        # TODO: also support nicer codeblocks? pink is ugly, and give it a nice background shade
        # TODO: add emoji support too :sob:
        # TODO: delete the newline that exists at the end of non-final variants like wtf
        # maybe just delete all trailing elements that are just empty

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
        
        context['rulesets_line_breaks'] = rulesets_line_breaks
        context['titles'] = titles

        return context
    
class DesignerDetailView(generic.DetailView):
    model = Designer

class ORGDetailView(generic.DetailView):
    model = ORG

    def get_context_data(self, **kwargs):
        context = super(ORGDetailView, self).get_context_data(**kwargs)

        # split by \n
        twists = context['org'].twists.split("\n")
        context['twists'] = twists

        return context