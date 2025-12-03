from django.http import Http404
from django.shortcuts import redirect

from recipes.models import Recipe

RECIPE_NOT_FOUND = 'Рецепта с id = {} не существует!'


def recipe_redirect(request, pk):
    """Метод для редиректа короткой ссылки на полный адрес рецепта."""
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(f'/recipes/{pk}')
    return Http404(RECIPE_NOT_FOUND.format(pk))
