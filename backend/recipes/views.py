from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def recipe_redirect(request, pk):
    """Метод для редиректа короткой ссылки на полный адрес рецепта."""
    if Recipe.objects.filter(pk=pk).exists():
        return redirect(f'/recipes/{pk}')

