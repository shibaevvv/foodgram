from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from api.views import RECIPE_NOT_EXIST
from recipes.models import Recipe


def recipe_redirect(request, pk):
    try:
        Recipe.objects.filter(pk=pk).exists()
        return redirect(f'/recipes/{pk}/')
    except Exception:
        raise ValidationError(RECIPE_NOT_EXIST.format(pk))
