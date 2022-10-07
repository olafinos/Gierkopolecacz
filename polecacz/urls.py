from django.urls import path
from django.views.decorators.cache import never_cache

from . import views

app_name = "polecacz"
urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("game/", views.GameListView.as_view(), name="game_list"),
    path("game/<uuid:pk>/", views.GameDetailView.as_view(), name="game_detail"),
    path("game_search/", views.GameSearchView.as_view()),
    path(
        "add_game_to_selected/<uuid:game_id>/",
        views.AddGameToSelectedGamesView.as_view(),
        name="add_game",
    ),
    path(
        "remove_game_from_selected/<uuid:game_id>/",
        views.RemoveFromSelectedGamesView.as_view(),
        name="remove_game",
    ),
    path(
        "selected_games/",
        never_cache(views.SelectedGamesListView.as_view()),
        name="selected_games",
    ),
    path(
        "recommendation/",
        views.RecommendationListView.as_view(),
        name="recommendation_list",
    ),
    path(
        "recommendation/<uuid:pk>/",
        views.RecommendationDetailView.as_view(),
        name="recommendation_detail",
    ),
    path(
        "create_recommendation/",
        views.CreateRecommendationView.as_view(),
        name="create_recommendation",
    ),
    path("opinion/<uuid:pk>/", views.OpinionFormView.as_view(), name="create_opinion"),
    path("opinion/create/<uuid:pk>/", views.AddOpinionView.as_view(), name="add_opinion"),
]
