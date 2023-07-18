from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('matches/', views.MatchListView.as_view(), name='matches'),
    path('designers/', views.DesignerListView.as_view(), name='designers'),
    path('orgs/', views.ORGListView.as_view(), name="orgs"),
    path('match/<int:pk>', views.MatchDetailView.as_view(), name='match-detail'),
    path('designer/<int:pk>', views.DesignerDetailView.as_view(), name='designer-detail'),
    path('org/<int:pk>', views.ORGDetailView.as_view(), name="org-detail"),
]