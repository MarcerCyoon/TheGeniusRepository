from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('matches/', views.MatchListView.as_view(), name='matches'),
    path('match/<int:pk>', views.MatchDetailView.as_view(), name='match-detail')
]