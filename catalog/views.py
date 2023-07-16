from django.shortcuts import render
from django.views import generic

from .models import Match, Designer

# Create your views here.
def index(request):
    num_matches = Match.objects.all().count()
    
    context = {
        'num_matches': num_matches
    }

    return render(request, 'index.html', context=context)

class MatchListView(generic.ListView):
    model = Match

class MatchDetailView(generic.DetailView):
    model = Match

    def get_context_data(self, **kwargs):
        context = super(MatchDetailView, self).get_context_data(**kwargs)

        rule_line_breaks = context['match'].rules.split("\r\n")
        rule_line_breaks = [rule for rule in rule_line_breaks if rule != ""]
        context['rule_line_breaks'] = rule_line_breaks

        return context
    
class DesignerDetailView(generic.DetailView):
    model = Designer