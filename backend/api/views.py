from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from djoser.views import UserViewSet as BaseUserViewSet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import (
    SAFE_METHODS, IsAuthenticated, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.pagination import LimitPageNumberPagination
from api.permisions import IsOwnerOrReadOnly
from api.serializers import (
    AuthorSerializer, AvatarSerializer, IngredientSerializer,
    RecipeReadSerializer, RecipeShortSerializer, RecipeWriteSerializer,
    TagSerializer
)
from api.shopping_cart import get_shopping_cart_text
from recipes.admin import User
from recipes.models import (
    Ingredient, Favorite, Recipe, RecipeIngredient, ShoppingCart, Subscription,
    Tag
)

RECIPE_NOT_EXIST = 'Рецепта с id - {} не существует!'
SELF_SUBSCRIBE_ERROR = 'Подписка на самого себя запрещена!'
ALREADY_SUBSCRIBED_ERROR = 'Подписка на автора ({}) оформлена ранее!'
RECIPE_EXISTS_IN_MODEL = 'Рецепт ({}) уже добавлен в {}!'


class UserViewSet(BaseUserViewSet):
    """Класс для работы с пользователями."""

    pagination_class = LimitPageNumberPagination

    def get_permissions(self):
        """Получение класса разрешений к странице /me/."""
        if self.action == 'me':
            return (IsAuthenticated(),)
        return super().get_permissions()

    @action(['put'], detail=False, url_path='me/avatar',)
    def avatar(self, request, *args, **kwargs):
        """Добавление аватара профиля пользователя."""
        serializer = AvatarSerializer(
            instance=request.user,
            data=request.data,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @avatar.mapping.delete
    def delete_avatar(self, request, *args, **kwargs):
        """Удаление аватара профиля пользователя."""
        request.user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        permission_classes=(IsAuthenticated,),
        url_path='subscriptions',
    )
    def subscriptions(self, request):
        """Показывает на каких авторов подписан пользователь."""
        return self.get_paginated_response(
            AuthorSerializer(
                self.paginate_queryset(
                    self.get_queryset().filter(
                        author_subscriptions__user=request.user
                    )
                ),
                context={'request': request},
                many=True
            ).data
        )

    @action(
        methods=['post'], detail=True, url_path='subscribe')
    def subscribe(self, request, id=None):
        """Метод для оформления подписки на автора."""
        author = get_object_or_404(User, id=id)
        if request.user == author:
            raise ValidationError(SELF_SUBSCRIBE_ERROR)
        _, created = Subscription.objects.get_or_create(
            user=request.user,
            author=author
        )
        if not created:
            raise ValidationError(
                ALREADY_SUBSCRIBED_ERROR.format(author.username)
            )
        return Response(
            AuthorSerializer(
                author,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @subscribe.mapping.delete
    def unsubscribe(self, request, id=None):
        """Метод для удаления подписки на автора."""
        get_object_or_404(Subscription, user=request.user, author=id).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TagViewSet(ReadOnlyModelViewSet):
    """Вьюсет (только чтение) для работы с тэгами."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer


class IngredientViewSet(ReadOnlyModelViewSet):
    """Вьюсет (только чтение) для работы с продуктами."""

    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter


class RecipeViewSet(ModelViewSet):
    """Вьюсет для работы с рецептами."""

    queryset = Recipe.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly,)
    pagination_class = LimitPageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ('get', 'post', 'patch', 'delete',)

    def get_serializer_class(self):
        """Метод для определения сериалтзатора вьюсета рецептов."""
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @staticmethod
    def add_favorite_shopping(request, model, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        _, created = model.objects.get_or_create(
            user=request.user,
            recipe=recipe
        )
        if not created:
            raise ValidationError(
                RECIPE_EXISTS_IN_MODEL.format(
                    recipe.name,
                    model._meta.verbose_name)
            )
        return Response(
            RecipeShortSerializer(
                recipe,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED
        )

    @staticmethod
    def delete_favorite_shopping(request, model, pk):
        get_object_or_404(model, user=request.user, recipe=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Метод для добавления рецепта в избранное."""
        return self.add_favorite_shopping(request, Favorite, pk)

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Метод для удаления рецепта из избранного."""
        return self.delete_favorite_shopping(request, Favorite, pk)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления рецепта в корзину покупок."""
        return self.add_favorite_shopping(request, ShoppingCart, pk)

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        """Метод для удаления рецепта из корзины покупок."""
        return self.delete_favorite_shopping(request, ShoppingCart, pk)

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Метод для скачивания корзины покупок."""
        return FileResponse(
            get_shopping_cart_text(
                RecipeIngredient.objects.filter(
                    recipe__shoppingcarts__user=request.user
                ).values(
                    'ingredient__name',
                    'ingredient__measurement_unit',
                    'recipe__name',
                    'recipe__author__username'
                ).annotate(
                    sum=Sum('amount')
                ),
                self.request.get_host()
            ),
            'shopping_cart.txt'
        )

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk):
        """Метод для формирования короткой ссылки на страницу рецепта."""
        if self.get_queryset().filter(pk=pk).exists():
            return Response({
                'short-link': request.build_absolute_uri(
                    reverse('short-link', args=(pk,)))
            })
        raise ValidationError(RECIPE_NOT_EXIST.format(pk))


def recipe_redirect(request, pk):
    try:
        Recipe.objects.filter(pk=pk).exists()
        return redirect(f'/recipes/{pk}/')
    except Exception:
        raise ValidationError(RECIPE_NOT_EXIST.format(pk))
