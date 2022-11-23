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
        "add_game_to_owned/<uuid:game_id>/",
        views.AddGameToOwnedGamesView.as_view(),
        name="add_to_owned_game",
    ),
    path("add_image/<uuid:game_id>/",
         views.AddImageView.as_view(),
         name="add_image"
    ),
    path("remove_image/<uuid:game_id>/",
         views.RemoveImageView.as_view(),
         name="remove_image"
         ),
    path(
        "remove_game_from_owned/<uuid:game_id>/",
        views.RemoveFromOwnedGamesView.as_view(),
        name="remove_from_owned_game",
    ),
    path(
        "selected_games/",
        never_cache(views.SelectedGamesListView.as_view()),
        name="selected_games",
    ),
    path(
        "owned_games/",
        never_cache(views.OwnedGamesListView.as_view()),
        name="owned_games",
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
