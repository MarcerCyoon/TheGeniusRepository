import shlex

from django.shortcuts import render
from django.views import generic
from django.db.models import Q, Count

from .models import Match, Designer, ORG, Award

def parse_query(query: str):
    """
    Helper function that parses a text query into
    a dictionary object 
    """

    query = query.replace("“", "\"").replace("‘", "'") # replace mobile version of quotes with standard ones
    criteria = shlex.split(query) # shlex.split() preserves quotes
    # criteria = query.split(" ")
    dct = {}

    # TODO: implement OR/AND

    for criterion in criteria:
        if "=" in criterion:
            field, search = criterion.split("=")
            if field in dct:
                dct[field].append(search.replace('"', '').replace("'", "")) # get rid of quotes
            else:
                dct[field] = [search.replace('"', '').replace("'", "")] # get rid of quotes

        else:
            if "name" in dct:
                dct['name'].append(criterion)
            else:
                dct['name'] = [criterion]

    print(dct)
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

class DesignerListView(generic.ListView):
    model = Designer

    def get_context_data(self, **kwargs):
        context = super(DesignerListView, self).get_context_data(**kwargs)
        context['sorted_designer_list'] = context['designer_list'].annotate(num_matches=Count('match')).order_by("-num_matches")
        return context

class ORGListView(generic.ListView):
    model = ORG

# TODO: Awards List and Detail View

class AwardListView(generic.ListView):
    model = Award

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