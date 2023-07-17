from django.shortcuts import render
from django.views import generic
from django.db.models import Q

from .models import Match, Designer

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
            object_list = Match.objects.filter(
                Q(name__icontains=query) | Q(tags__name__icontains=query) | Q(designer__name__icontains=query)
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

class MatchDetailView(generic.DetailView):
    model = Match

    def get_context_data(self, **kwargs):
        context = super(MatchDetailView, self).get_context_data(**kwargs)

        # split rules by \r\n so that each can be displayed in
        # their own div and each can be markdownified properly.
        # also, this makes image processing possible as well.
        rule_line_breaks = context['match'].rules.split("\r\n")
        context['rule_line_breaks'] = rule_line_breaks

        return context
    
class DesignerDetailView(generic.DetailView):
    model = Designer