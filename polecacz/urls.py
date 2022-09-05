from django.urls import path

from . import views

app_name = 'polecacz'
urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('game/', views.GameListView.as_view(), name='game_list'),
    path('game/<uuid:pk>/', views.GameDetailView.as_view(), name='game_detail'),
    path('opinion/<uuid:pk>/', views.OpinionDetail.as_view(), name='opinion_detail'),
]