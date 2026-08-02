from django_filters import rest_framework as filters
from django.db.models import Case, IntegerField, Value, When, Q

from recipes.models import Ingredient, Recipe, Tag


class IstartsIcontainsFilter(filters.Filter):
    def filter(self, qs, value):
        if value:
            return (
                qs.filter(name__icontains=value)
                .annotate(
                    is_start=Case(
                        When(name__istartswith=value, then=Value(0)),
                        default=Value(1),
                        output_field=IntegerField(),
                    )
                )
                .order_by("is_start", "name")
            )
        return qs


class IngredientFilter(filters.FilterSet):
    """Фильтр для продуктов."""

    name = IstartsIcontainsFilter(field_name='name')

    class Meta:
        model = Ingredient
        fields = ('name',)


class RecipeFilter(filters.FilterSet):
    """Фильтр для рецептов."""

    tags = filters.ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = filters.BooleanFilter(
        method='get_is_favorited'
    )
    is_in_shopping_cart = filters.BooleanFilter(
        method='get_is_in_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited', 'is_in_shopping_cart')

    def get_is_favorited(self, recipes, name, value):
        """Метод фильтрации по избранному."""
        if value and self.request.user.is_authenticated:
            return recipes.filter(favorites__user=self.request.user)
        return recipes

    def get_is_in_shopping_cart(self, recipes, name, value):
        """Метод фильтрации по корзине покупок."""
        if value and self.request.user.is_authenticated:
            return recipes.filter(shoppingcarts__user=self.request.user)
        return recipes
