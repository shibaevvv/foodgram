from django_filters import rest_framework as filters

from recipes.models import Ingredient, Recipe, Tag


class IngredientFilter(filters.FilterSet):
    """Фильтр для Продуктов."""

    name = filters.CharFilter(field_name='name', lookup_expr='istartswith')

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
