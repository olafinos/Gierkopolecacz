from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

app_name = 'polecacz'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('game/', views.GameListView.as_view(), name='game_list'),
    path('game/<uuid:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('opinion/<uuid:pk>', views.OpinionFormView.as_view(), name='create_opinion'),
    path('opinion/create/<uuid:pk>', views.add_opinion, name='add_opinion'),
    path('game_search/', views.game_search),
    path('add_game_to_selected/<uuid:game_id>', views.add_to_selected_games, name='add_game'),
    path('remove_game_from_selected/<uuid:game_id>', views.remove_from_selected_games, name='remove_game'),
    path('selected_games/', never_cache(views.SelectedGamesListView.as_view()), name='selected_games'),
    path('recommendation/', views.RecommendationListView.as_view(), name='recommendation_list'),
    path('recommendation/<uuid:pk>', views.RecommendationDetailView.as_view(), name='recommendation_detail'),
    path('create_recommendation/', views.create_recommendation, name='create_recommendation')
]