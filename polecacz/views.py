from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic

from polecacz.models import Game, Opinion, SelectedGames
from polecacz.service import PolecaczService

ORDER_MAPPING = {
        "rank": "Ranking rosnąco",
        "-rank": "Ranking malejąco",
        "name": "Alfabetycznie A-Z",
        "-name": "Alfabetycznie Z-A",
        "rating": "Średnia rosnąco",
        "-rating": "Średnia malejąco",
    }

class IndexView(generic.ListView):
    template_name = 'polecacz/index.html'
    context_object_name = 'top_games'

    def get_queryset(self):
        return Game.objects.order_by('rank')[:12]


class GameDetailView(LoginRequiredMixin, generic.DetailView):
    model = Game
    template_name = 'polecacz/game_detail.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super(GameDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        game = Game.objects.get(id=self.kwargs['pk'])
        try:
            user_selected = SelectedGames.objects.get(user=user)
            context['selected_game'] = game in user_selected.selected_games.all()
        except SelectedGames.DoesNotExist:
            context['selected_game'] = False
        return context


class GameListView(LoginRequiredMixin, generic.ListView):
    model = Game
    template_name = 'polecacz/game_list.html'
    login_url = '/login/'
    context_object_name = 'games_list'
    paginate_by = 20
    ordering = ['rank']
    order_mapping = ORDER_MAPPING

    def get_ordering(self):
        ordering = self.request.GET.get('ordering', 'rank')
        return ordering

    def get_context_data(self, **kwargs):
        context = super(GameListView, self).get_context_data(**kwargs)
        ordering = self.request.GET.get('ordering', 'rank')
        order_name = self.order_mapping[ordering]
        user = self.request.user
        try:
            user_selected = SelectedGames.objects.get(user=user)
            context['selected_games'] = user_selected.selected_games.all()
        except SelectedGames.DoesNotExist:
            context['selected_games'] = []
        context['ordering'] = ordering
        context['order_name'] = order_name
        return context

    def get_queryset(self):
        game = self.request.GET.get('game', None)
        if game:
            object_list = Game.objects.filter(name__icontains=game)
            return object_list
        else:
            return super(GameListView, self).get_queryset()


class SelectedGamesListView(LoginRequiredMixin, generic.ListView):
    model = SelectedGames
    template_name = 'polecacz/selected_games.html'
    login_url = '/login/'
    context_object_name = 'games_list'
    paginate_by = 20

    def get_queryset(self):
        selected_games_object, _ = SelectedGames.objects.get_or_create(user=self.request.user)
        return selected_games_object.selected_games.all()


class RecommendationsView(generic.ListView):
    template_name = 'polecacz/recommendations.html'
    context_object_name = 'recommended_games'

    def get_queryset(self):
        selected_games_obj = SelectedGames.objects.get(user=self.request.user)
        games = selected_games_obj.selected_games.all()
        games_ids = list(games.values_list('id', flat=True))
        tag_list = []
        for game in games:
            for tag in game.tags.values_list('name', flat=True):
                tag_list.append(tag)
        recommended_games = PolecaczService.find_most_similar_games(list(set(tag_list)))
        recommended_games = recommended_games.exclude(id__in=games_ids)
        return recommended_games[:20]


class OpinionDetail(LoginRequiredMixin, generic.DetailView):
    model = Opinion
    template_name = 'polecacz/opinion_detail.html'


@login_required
def game_search(request):
    game = request.GET.get('game')
    payload = []
    if game:
        games_objs = Game.objects.filter(name__icontains=game)

        for game_obj in games_objs:
            payload.append(game_obj.name)

    return JsonResponse({'status': 200, 'data': payload})


def _build_url_with_pagination_and_order(url: str, request) -> str:
    url = url + '?'
    ordering = request.GET.get('ordering')
    page = request.GET.get('page')
    if ordering:
        url += f'ordering={ordering}&'
    if page:
        url += f'page={page}'
    return url


@login_required
def add_to_selected_games(request, game_id):
    game = get_object_or_404(Game, id = game_id)
    selected_games_object, _ = SelectedGames.objects.get_or_create(user=request.user)
    selected_games_object.selected_games.add(game)
    selected_games_object.save()
    return redirect(_build_url_with_pagination_and_order(reverse_lazy("polecacz:game_list"), request))

@login_required
def remove_from_selected_games(request, game_id):
    game = get_object_or_404(Game, id = game_id)
    selected_games_object, _ = SelectedGames.objects.get_or_create(user=request.user)
    selected_games_object.selected_games.remove(game)
    selected_games_object.save()
    if request.GET.get('redirect') == 'selected_games':
        return redirect("/polecacz/selected_games")
    return redirect(_build_url_with_pagination_and_order(reverse_lazy("polecacz:game_list"), request))

