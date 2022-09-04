from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.views import generic

from polecacz.models import Game, Opinion


class IndexView(generic.ListView):
    template_name = 'polecacz/index.html'
    context_object_name = 'top_games'

    def get_queryset(self):
        return Game.objects.order_by('rank')[:10]


class GameDetailView(generic.DetailView):
    model = Game
    template_name = 'polecacz/game_detail.html'


class GameListView(generic.ListView):
    model = Game
    template_name = 'polecacz/game_list.html'
    context_object_name = 'games_list'
    paginate_by = 20
    ordering = ['rank']
    order_mapping = {
        "rank": "Ranking rosnąco",
        "-rank": "Ranking malejąco",
        "name": "Alfabetycznie A-Z",
        "-name": "Alfabetycznie Z-A",
        "rating": "Średnia rosnąco",
        "-rating": "Średnia malejąco",
    }

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', 'rank')
        return ordering

    def get_context_data(self, **kwargs):
        context = super(GameListView, self).get_context_data(**kwargs)
        ordering = self.request.GET.get('ordering', 'rank')
        order_name = self.order_mapping[ordering]
        context['ordering'] = ordering
        context['order_name'] = order_name
        return context


class OpinionDetail(generic.DetailView):
    model = Opinion
    template_name = 'polecacz/opinion_detail.html'
