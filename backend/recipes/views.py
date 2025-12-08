from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def recipe_redirect(request, pk):
    get_object_or_404(Recipe, id=pk)
    return redirect(f'/recipes/{pk}/')
