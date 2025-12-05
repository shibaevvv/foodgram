from django.shortcuts import redirect


def recipe_redirect(request, pk):
    """Метод для редиректа короткой ссылки на полный адрес рецепта."""
    return redirect(f'/recipes/{pk}')
