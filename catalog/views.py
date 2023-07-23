from django.shortcuts import render
from django.views import generic
from django.db.models import Q

from .models import Match, Designer, ORG

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

            object_list = Match.objects.all()

            for q in query.split(" "):
                object_list = object_list.filter(
                    Q(name__icontains=q) | Q(tags__name__icontains=q) | Q(designers__name__icontains=q)
                ).distinct()
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

class ORGListView(generic.ListView):
    model = ORG

class MatchDetailView(generic.DetailView):
    model = Match

    def get_context_data(self, **kwargs):
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