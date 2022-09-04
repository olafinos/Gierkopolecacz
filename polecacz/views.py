from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views import generic

from polecacz.models import Game, Opinion


class IndexView(generic.ListView):
    template_name = 'polecacz/index.html'
    context_object_name = 'game'

    def get_queryset(self):
        return Game.objects.order_by('rank')[:10]


class GameDetailView(generic.DetailView):
    model = Game
    template_name = 'polecacz/game_detail.html'


class GameListView(generic.ListView):
    model = Game
    template_name = 'polecacz/game_list.html'
    context_object_name = 'games_list'

    def get_queryset(self):
        return Game.objects.order_by('rank')[:10]


class OpinionDetail(generic.DetailView):
    model = Opinion
    template_name = 'polecacz/opinion_detail.html'
