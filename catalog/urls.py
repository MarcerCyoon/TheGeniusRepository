from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
	path('about_us/', views.about_us, name='about-us'),
    path('search/', views.SearchView.as_view(), name='search'),
	path('tag_generator/', views.tag_generator, name='tag-generator'),
	path('matches/', views.PagedMatchListView.as_view(), name='matches'),
    path('matches/all', views.MatchListView.as_view(), name='all-matches'),
    path('designers/', views.DesignerListView.as_view(), name='designers'),
	path('awards/', views.YearAwardListView.as_view(), name='awards'),
    path('orgs/', views.ORGListView.as_view(), name="orgs"),
	path('tags/', views.TagListView.as_view(), name="tags"),
	path('match/random', views.random_redirect, name='random'),
    path('match/<int:pk>', views.MatchDetailView.as_view(), name='match-detail'),
	path('match/<int:pk>/<int:ruleset__pk>', views.MatchDetailView.as_view(), name='match-detail-page'),
    path('designer/<int:pk>', views.DesignerDetailView.as_view(), name='designer-detail'),
    path('org/<int:pk>', views.ORGDetailView.as_view(), name="org-detail"),
]