from datetime import datetime
from django.db.models import Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
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
    AuthorSerializer ,AvatarSerializer, IngredientSerializer,
    FavoriteSerializer, RecipeReadSerializer, RecipeShortSerializer,
    RecipeWriteSerializer, ShoppingCartSerializer, SubscribeSerializer,
    TagSerializer
)
from recipes.admin import User
from recipes.models import (
    Ingredient, Favorite, Recipe, RecipeIngredient, ShoppingCart, Subscription,
    Tag
)

RECIPE_NOT_EXIST = 'Рецепта с id - {} не существует'

SHOPPING_CART_TITLE = f'Список покупок от {datetime.now().strftime('%d.%m.%Y')}.'
SHOPPING_CART_RECIPES = '   \u2022 {} (Автор - {})'
SHOPPING_CART_PRODUCTS = '  {}. {}: {} ({})'
DECLENSIONS = {
    'капля': ('капля', 'капель', 'капли'),
    'банка': ('банка', 'банок', 'банки'),
    'стакан': ('стакан', 'стаканов', 'стакана'),
    'щепотка': ('щепотка', 'щепоток', 'щепотки'),
    'горсть': ('горсть', 'горстей', 'горсти'),
    'веточка': ('веточка', 'веточек', 'веточки'),
    'кусок': ('кусок', 'кусков', 'куска'),
    'батон': ('батон', 'батонов', 'батона'),
}


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
        data = {'user': request.user.id, 'author': author.id}
        serializer = SubscribeSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
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

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def favorite(self, request, pk=None):
        """Метод для добавления рецепта в избранное."""
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.pk}
        serializer = FavoriteSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeShortSerializer(
                self.get_object(),
                context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Метод для удаления рецепта из избранного."""
        get_object_or_404(Favorite, user=request.user, recipe=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def shopping_cart(self, request, pk=None):
        """Метод для добавления рецепта в корзину покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.pk}
        serializer = ShoppingCartSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            RecipeShortSerializer(
                self.get_object(),
                context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        """Метод для удаления рецепта из корзины покупок."""
        get_object_or_404(ShoppingCart, user=request.user, recipe=pk).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    def inflect_with_num(self, number, forms):
        """Метод склонения слов в зависимости от числа."""
        if not isinstance(forms, tuple):
            return forms
        units = number % 10
        tens = number % 100 - units
        if tens == 10 or units >= 5 or units == 0:
            needed_form = 1
        elif units > 1:
            needed_form = 2
        else:
            needed_form = 0
        return forms[needed_form]

    def get_shopping_cart_text(self, recipes):
        """Метод для формирования текса скачиваемой корзины покупок."""
        return '\n'.join([
            SHOPPING_CART_TITLE,
            '-' * len(SHOPPING_CART_TITLE),
            '',
            'Для приготовления следующих рецептов:',
            '',
            *[SHOPPING_CART_RECIPES.format(
                recipe['recipe__name'],
                recipe['recipe__author__username'],
            ) for recipe in recipes],
            '',
            'Понадобятся следующие продукты:'
            '',
            '',
            *[SHOPPING_CART_PRODUCTS.format(
                count,
                ingredient['ingredient__name'].capitalize(),
                ingredient['sum'],
                self.inflect_with_num(
                    ingredient['sum'],
                    DECLENSIONS.get(
                        ingredient['ingredient__measurement_unit'],
                        ingredient['ingredient__measurement_unit']
                    )
                ),
                ingredient['ingredient__measurement_unit']
            ) for count, ingredient in enumerate(recipes, 1)],
            '',
            '',
            f'Загружено с сайта: {self.request.get_host()}'
        ])

    @action(detail=False, permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        """Метод для скачивания корзины покупок."""
        recipes = (
            RecipeIngredient.objects.filter(
                recipe__shoppingcarts__user=request.user)
            .values(
                'ingredient__name',
                'ingredient__measurement_unit',
                'recipe__name',
                'recipe__author__username'
            )
            .annotate(sum=Sum('amount'))
        )
        return FileResponse(
            self.get_shopping_cart_text(recipes),
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
