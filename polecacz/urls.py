from django.urls import path

from . import views

app_name = 'polecacz'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('game/', views.GameListView.as_view(), name='game_list'),
    path('game/<uuid:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('opinion/<uuid:pk>/', views.OpinionDetail.as_view(), name='opinion_detail'),
    path('game_search/', views.game_search),
    path('add_game_to_selected/<uuid:game_id>', views.add_to_selected_games, name='add_game'),
    path('remove_game_from_selected/<uuid:game_id>', views.remove_from_selected_games, name='remove_game'),
    path('selected_games/', views.SelectedGamesListView.as_view(), name='selected_games'),
    path('create_recommendation', views.RecommendationsView.as_view(), name='create_recommendations')
]