from datetime import datetime

SHOPPING_CART_TITLE = (
    f'Список покупок от {datetime.now().strftime("%d.%m.%Y")}.'
)
SHOPPING_CART_RECIPES = '   \u2022 {} (Автор - {})'
SHOPPING_CART_PRODUCTS = '  {}. {} - {} ({})'


def get_shopping_cart_text(recipes, domain):
    """Метод для формирования текса скачиваемой корзины покупок."""
    return '\n'.join([
        SHOPPING_CART_TITLE,
        '-' * len(SHOPPING_CART_TITLE),
        '',
        'Для приготовления следующих рецептов:',
        '',
        *{SHOPPING_CART_RECIPES.format(
            recipe['recipe__name'],
            recipe['recipe__author__username'],
        ) for recipe in recipes},
        '',
        'Понадобятся следующие продукты:'
        '',
        '',
        *[SHOPPING_CART_PRODUCTS.format(
            count,
            ingredient['ingredient__name'].capitalize(),
            ingredient['sum'],
            ingredient['ingredient__measurement_unit']
        ) for count, ingredient in enumerate(recipes, 1)],
        '',
        '',
        f'Загружено с сайта: {domain}'
    ])
