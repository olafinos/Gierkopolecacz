from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.http import JsonResponse, HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import generic

from polecacz.bgg_api import CATEGORIES_MAP, MECHANICS_MAP
from polecacz.forms import OpinionForm
from polecacz.models import Game, Opinion, SelectedGames, Recommendation
from polecacz.service import SelectedGamesService, RecommendationService, GameService

ORDER_MAPPING = {
    "rank": "Ranking rosnąco",
    "-rank": "Ranking malejąco",
    "name": "Alfabetycznie A-Z",
    "-name": "Alfabetycznie Z-A",
    "rating": "Średnia ocen rosnąco",
    "-rating": "Średnia ocen malejąco",
}


class IndexView(generic.ListView):
    """
    Main view, which greets the user.
    """

    template_name = "polecacz/index.html"
    context_object_name = "top_games"

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        return GameService.get_all_games_ordered_by("rank")[:12]


class GameDetailView(LoginRequiredMixin, generic.DetailView):
    """
    View responsible for retrieving Game details. Requires to be logged in
    """

    model = Game
    template_name = "polecacz/game_detail.html"
    login_url = "/login/"

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(GameDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        game = GameService.get_game_by_id(self.kwargs["pk"])
        try:
            context[
                "selected_game"
            ] = game in SelectedGamesService.get_user_selected_games(user=user)
        except SelectedGames.DoesNotExist:
            context["selected_game"] = False
        return context


class GameListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving Game list. Allows to change by user ordering and filtering. Also allows to use
    search bar.
    """

    model = Game
    template_name = "polecacz/game_list.html"
    login_url = "/login/"
    context_object_name = "games_list"
    paginate_by = 10
    ordering = ["rank"]
    order_mapping = ORDER_MAPPING
    categories = list(CATEGORIES_MAP.values())
    mechanics = list(MECHANICS_MAP.values())

    def get_ordering(self):
        """
        Return the field or fields to use for ordering the queryset.
        """
        ordering = self.request.GET.get("ordering", "rank")
        return ordering

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(GameListView, self).get_context_data(**kwargs)
        context = self._prepare_context(context)
        return context

    def _prepare_context(self, context: dict) -> dict:
        """Retrives user information about ordering, selected games, searched game, selected categories and mechanics
        from request and set it to context dictionary
        :param context: Dictionary with response context
        """
        order_name, ordering = self._get_ordering_options()
        context["selected_games"] = SelectedGamesService().get_user_selected_games(
            self.request.user
        )
        context["ordering"] = ordering
        context["order_name"] = order_name
        context["mechanics"] = self.mechanics
        context["categories"] = self.categories
        context["selected_categories"] = self.request.GET.getlist(
            "selected_categories", []
        )
        context["selected_mechanics"] = self.request.GET.getlist(
            "selected_mechanics", []
        )
        context["game_name"] = self.request.GET.get("game_name", "")
        return context

    def _get_ordering_options(self) -> tuple[str, str]:
        """
        Retrieves information about used ordering
        """
        ordering = self.request.GET.get("ordering", "rank")
        order_name = self.order_mapping[ordering]
        return order_name, ordering

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        game = self.request.GET.get("game_name", "")
        tags = self.request.GET.getlist("selected_categories", [])
        tags.extend(self.request.GET.getlist("selected_mechanics", []))
        if game or tags:
            object_list = GameService.filter_games_which_contains_string(game)
            for tag in tags:
                object_list = GameService.filter_games_which_name_contains_tag(
                    tag, object_list
                )
            return object_list.order_by(self.request.GET.get("ordering", "rank"))
        else:
            return super(GameListView, self).get_queryset()


class SelectedGamesListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving SelectedGames list
    """

    model = SelectedGames
    template_name = "polecacz/selected_games.html"
    login_url = "/login/"
    context_object_name = "games_list"

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        selected_games_object, _ = SelectedGames.objects.get_or_create(
            user=self.request.user
        )
        return SelectedGamesService.get_user_selected_games(self.request.user)


class RecommendationDetailView(LoginRequiredMixin, generic.DetailView):
    """
    View responsible for retrieving Recommendation details
    """

    model = Recommendation
    template_name = "polecacz/recommendation_detail.html"
    login_url = "/login/"
    context_object_name = "games"

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(RecommendationDetailView, self).get_context_data(**kwargs)
        id = self.kwargs["pk"]
        context["recommended_games"] = RecommendationService().get_recommended_games(id)
        context["selected_games"] = RecommendationService().get_selected_games(id)[:4]
        context["opinion_created"] = RecommendationService().get_opinion_created(id)
        context["id"] = id
        return context


class RecommendationListView(LoginRequiredMixin, generic.ListView):
    """
    View responsible for retrieving Recommendation list
    """

    model = Recommendation
    template_name = "polecacz/recommendation_list.html"
    login_url = "/login/"
    context_object_name = "recommendations"
    paginate_by = 20

    def get_queryset(self):
        """
        Return the list of items for this view.
        """
        recommendation_objects = RecommendationService.get_all_recommendations(
            self.request.user
        )
        return recommendation_objects.order_by('-creation_date')


class OpinionFormView(LoginRequiredMixin, SuccessMessageMixin, generic.FormView):
    """
    View responsible for Opinion form processing
    """

    model = Opinion
    template_name = "polecacz/create_opinion.html"
    context_object_name = "context"
    form_class = OpinionForm
    success_url = "/polecacz/recommendation_list"
    success_message = "Dziękujemy za zostawienie opinii."

    def get_context_data(self, **kwargs):
        """
        Get the context for this view.
        """
        context = super(OpinionFormView, self).get_context_data(**kwargs)
        recommendation = RecommendationService().get_recommendation_by_id(
            id=self.kwargs["pk"]
        )
        context["id"] = recommendation.id
        return context


class AddOpinionView(LoginRequiredMixin, generic.View):

    name_map = {"Description": "Uwagi do rekomendacji", "Rating": "Ocena"}

    def post(self, request: HttpRequest, pk: str):
        """
        Function responsible for adding opinion. Accepts only POST requests
        :param request: Incoming HttpRequest with all data
        :param pk: Recommendation id
        """
        form = OpinionForm(request.POST)
        if form.is_valid():
            recommendation = RecommendationService.get_recommendation_by_id(id=pk)
            opinion = form.save(commit=False)
            opinion.recommendation = recommendation
            opinion.user = request.user
            opinion.save()
            recommendation.opinion_created = True
            recommendation.save()
            return redirect("/polecacz/recommendation")
        else:
            return render(
                request=request,
                template_name="./polecacz/create_opinion.html",
                context={"form": form, "id": pk, "name_map": self.name_map},
            )

    def get(self, request: HttpRequest, pk: str):
        form = OpinionForm()
        return render(
            request=request,
            template_name="./polecacz/create_opinion.html",
            context={"form": form, "id": pk, "name_map": self.name_map},
        )


class GameSearchView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """
        Method responsible for autocompletion feature in searchbar
        :param request: Incoming HttpRequest with all data
        """
        game = request.GET.get("game_name")
        payload = []
        if game:
            games_objs = GameService.filter_games_which_contains_string(
                searched_string=game
            )[:10]

            for game_obj in games_objs:
                payload.append(game_obj.name)

        return JsonResponse({"status": 200, "data": payload})


def _build_url_with_pagination_and_order(url: str, request: HttpRequest) -> str:
    """
    Builds url with all attributes like pagination, ordering, searched games,
    selected categories and selected mechanics
    :param url: Base URL
    :param request: Incoming HttpRequest with all data
    :return: URL with included all attributes
    """
    url = url + "?"
    (
        game,
        ordering,
        page,
        selected_categories,
        selected_mechanics,
    ) = _retrieve_attributes_from_request(request)

    if ordering:
        url += f"&ordering={ordering}"
    if page:
        url += f"&page={page}"
    if game:
        url += f"&game_name={game}"
    if selected_categories:
        for category in selected_categories:
            url += f"&selected_categories={category}"
    if selected_mechanics:
        for mechanics in selected_mechanics:
            url += f"&selected_categories={mechanics}"
    return url


def _retrieve_attributes_from_request(
    request: HttpRequest,
) -> tuple[str, str, str, list, list]:
    """
    Retrieves information about pagination, ordering, searched games,
    selected categories and selected mechanics
    :param request: Incoming HttpRequest with all data
    """
    ordering = request.GET.get("ordering", "")
    page = request.GET.get("page", "")
    game = request.GET.get("game_name", "")
    selected_categories = request.GET.getlist("selected_categories", [])
    selected_mechanics = request.GET.getlist("selected_mechanics", [])
    return game, ordering, page, selected_categories, selected_mechanics


class AddGameToSelectedGamesView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, game_id: str, *args, **kwargs):
        """
        Adds game to user selected games
        :param request: Incoming HttpRequest with all data
        :param game_id: Game id
        """
        game = GameService.get_game_by_id(id=game_id)
        selected_games_object, _ = SelectedGames.objects.get_or_create(
            user=request.user
        )
        selected_games_object.selected_games.add(game)
        selected_games_object.save()
        return redirect(
            _build_url_with_pagination_and_order(
                reverse_lazy("polecacz:game_list"), request
            )
        )


class RemoveFromSelectedGamesView(LoginRequiredMixin, generic.View):

    def get(self, request: HttpRequest, game_id: str):
        """
        Removes game to user selected games
        :param request: Incoming HttpRequest with all data
        :param game_id: Game id
        """
        game = GameService.get_game_by_id(id=game_id)
        selected_games_object, _ = SelectedGames.objects.get_or_create(
            user=request.user
        )
        selected_games_object.selected_games.remove(game)
        selected_games_object.save()

        if request.GET.get("redirect") == "selected_games":
            return redirect("/polecacz/selected_games")

        return redirect(
            _build_url_with_pagination_and_order(
                reverse_lazy("polecacz:game_list"), request
            )
        )


class CreateRecommendationView(LoginRequiredMixin, generic.View):
    def post(self, request: HttpRequest):
        """
        Creates Recommendation object based on user selected games
        :param request: Incoming HttpRequest with all data
        """
        selected_games_obj = SelectedGamesService.get_selected_games_object_by_user(
            user=request.user
        )
        games = SelectedGamesService.get_user_selected_games(user=request.user)
        if not games:
            return redirect("polecacz:selected_games")

        recommendation_object = RecommendationService.create_recommendation(
            user=request.user
        )
        games_ids = GameService.get_ids_from_game_queryset(games)

        tag_list = []
        for game in games:
            recommendation_object.selected_games.add(game)
            tag_list.extend(GameService.get_tag_names_list_from_game(game))

        recommended_games_query = self._create_recommendation_using_tags(games_ids, tag_list)
        for game in recommended_games_query[:10]:
            recommendation_object.recommended_games.add(game)
        recommendation_object.save()
        selected_games_obj.selected_games.clear()
        selected_games_obj.save()
        return redirect("polecacz:recommendation_detail", recommendation_object.id)

    def _create_recommendation_using_tags(self,
        used_games_ids: list[str], tag_list: list[str]
    ) -> QuerySet:
        """
        Returns games in which were used similar mechanics and game categories
        :param used_games_ids: List with game ids which were used to create recommendations
        :param tag_list: List with tags used in games which were used to create recommendations
        :return: QuerySet with games in which were used similar mechanics and game categories
        """
        recommended_games_query = GameService.find_most_similar_games(list(set(tag_list)))
        recommended_games_query = recommended_games_query.exclude(id__in=used_games_ids)
        return recommended_games_query
