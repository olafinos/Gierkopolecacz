from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import generic

from polecacz.bgg_api import CATEGORIES_MAP, MECHANICS_MAP
from polecacz.forms import OpinionForm
from polecacz.models import Game, Opinion, SelectedGames, Recommendation
from polecacz.service import PolecaczService

ORDER_MAPPING = {
        "rank": "Ranking rosnąco",
        "-rank": "Ranking malejąco",
        "name": "Alfabetycznie A-Z",
        "-name": "Alfabetycznie Z-A",
        "rating": "Średnia ocen rosnąco",
        "-rating": "Średnia ocen malejąco",
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
    paginate_by = 10
    ordering = ['rank']
    order_mapping = ORDER_MAPPING
    categories = list(CATEGORIES_MAP.values())
    mechanics = list(MECHANICS_MAP.values())

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
        context['mechanics'] = self.mechanics
        context['categories'] = self.categories
        context['selected_categories'] = self.request.GET.getlist('selected_categories', [])
        context['selected_mechanics'] = self.request.GET.getlist('selected_mechanics', [])
        context['game'] = self.request.GET.get('game', '')
        return context

    def get_queryset(self):
        game = self.request.GET.get('game', '')
        tags = self.request.GET.getlist('selected_categories', [])
        tags.extend(self.request.GET.getlist('selected_mechanics', []))
        if game or tags:
            object_list = Game.objects.filter(name__icontains=game)
            for tag in tags:
                object_list = object_list.filter(tags__name__contains=tag)
            return object_list.order_by(self.request.GET.get('ordering', 'rank'))
        else:
            return super(GameListView, self).get_queryset()


        # objects_list = Game.objects.all()
        # if game:
        #     objects_list = objects_list.filter(name__icontains=game)
        # elif tags:
        #     for tag in tags:
        #         objects_list = objects_list.filter(tags__name__contains=tag)
        # elif game or tags:
        #     return objects_list
        # else:
        #     return super(GameListView, self).get_queryset()

class SelectedGamesListView(LoginRequiredMixin, generic.ListView):
    model = SelectedGames
    template_name = 'polecacz/selected_games.html'
    login_url = '/login/'
    context_object_name = 'games_list'
    paginate_by = 10

    def get_queryset(self):
        selected_games_object, _ = SelectedGames.objects.get_or_create(user=self.request.user)
        return selected_games_object.selected_games.all()


class RecommendationDetailView(LoginRequiredMixin, generic.DetailView):
    model = Recommendation
    template_name = 'polecacz/recommendation_detail.html'
    login_url = '/login/'
    context_object_name = 'games'

    def get_context_data(self, **kwargs):
        context = super(RecommendationDetailView, self).get_context_data(**kwargs)
        recommendation = Recommendation.objects.get(id = self.kwargs['pk'])
        context['recommended_games'] = recommendation.recommended_games.all()
        context['selected_games'] = recommendation.selected_games.all()[:4]
        context['opinion_created'] = recommendation.opinion_created
        context['id'] = self.kwargs['pk']
        return context


class RecommendationListView(LoginRequiredMixin, generic.ListView):
    model = Recommendation
    template_name = 'polecacz/recommendation_list.html'
    login_url = '/login/'
    context_object_name = 'recommendations'
    paginate_by = 20

    def get_queryset(self):
        recommendation_objects = Recommendation.objects.all().order_by('-creation_date')
        return recommendation_objects


class OpinionFormView(LoginRequiredMixin, SuccessMessageMixin, generic.FormView):
    model = Opinion
    template_name = 'polecacz/create_opinion.html'
    context_object_name = 'context'
    form_class = OpinionForm
    success_url = '/polecacz/recommendation_list'
    success_message = 'Dziękujemy za zostawienie opinii.'

    def get_context_data(self, **kwargs):
        context = super(OpinionFormView, self).get_context_data(**kwargs)
        recommendation = Recommendation.objects.get(id=self.kwargs['pk'])
        context['id'] = recommendation.id
        return context


@login_required
def add_opinion(request, pk):
    if request.method == 'POST':
        form = OpinionForm(request.POST)
        if form.is_valid():
            recommendation = get_object_or_404(Recommendation, id=pk)
            opinion = form.save(commit=False)
            opinion.recommendation = recommendation
            opinion.user = request.user
            opinion.save()
            recommendation.opinion_created = True
            recommendation.save()
            return redirect('/polecacz/recommendation')
        else:
            return render(
                request=request,
                template_name="./polecacz/create_opinion.html",
                context={"form": form}
            )
    else:
        form = OpinionForm()
    return render(
        request=request,
        template_name="./polecacz/create_opinion.html",
        context={"form": form}
    )

@login_required
def game_search(request):
    if request.method == 'GET':
        game = request.GET.get('game')
        payload = []
        if game:
            games_objs = Game.objects.filter(name__icontains=game)

            for game_obj in games_objs:
                payload.append(game_obj.name)

        return JsonResponse({'status': 200, 'data': payload})
    else:
        return JsonResponse({'status': 404})


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
    if request.method == 'GET':
        game = get_object_or_404(Game, id = game_id)
        selected_games_object, _ = SelectedGames.objects.get_or_create(user=request.user)
        selected_games_object.selected_games.add(game)
        selected_games_object.save()
        return redirect(_build_url_with_pagination_and_order(reverse_lazy("polecacz:game_list"), request))
    else:
        return redirect('/polecacz/game_list')

@login_required
def remove_from_selected_games(request, game_id):
    if request.method == 'GET':
        game = get_object_or_404(Game, id = game_id)
        selected_games_object, _ = SelectedGames.objects.get_or_create(user=request.user)
        selected_games_object.selected_games.remove(game)
        selected_games_object.save()
        if request.GET.get('redirect') == 'selected_games':
            return redirect("/polecacz/selected_games")
        return redirect(_build_url_with_pagination_and_order(reverse_lazy("polecacz:game_list"), request))
    else:
        return redirect("/polecacz/game_list")

@login_required
def create_recommendation(request):
    if request.method == 'POST':
        selected_games_obj = SelectedGames.objects.get(user=request.user)
        if not selected_games_obj.selected_games.all():
            return redirect("polecacz:selected_games")
        recommendation_object = Recommendation.objects.create(user=request.user)
        games = selected_games_obj.selected_games.all()
        games_ids = list(games.values_list('id', flat=True))
        tag_list = []
        for game in games:
            recommendation_object.selected_games.add(game)
            for tag in game.tags.values_list('name', flat=True):
                tag_list.append(tag)
        recommended_games_query = PolecaczService.find_most_similar_games(list(set(tag_list)))
        recommended_games_query = recommended_games_query.exclude(id__in=games_ids)
        for game in recommended_games_query[:10]:
            recommendation_object.recommended_games.add(game)
        recommendation_object.save()
        selected_games_obj.selected_games.clear()
        selected_games_obj.save()
        return redirect("polecacz:recommendation_detail", recommendation_object.id)
    else:
        return redirect("/polecacz/game_list")
