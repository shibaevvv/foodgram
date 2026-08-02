# Foodgram — продуктовый помощник

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.x-092E20?logo=django)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-REST_API-red)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?logo=docker)](https://www.docker.com/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?logo=nginx)](https://nginx.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-CI/CD-2088FF?logo=github-actions)](https://github.com/features/actions)

</div>

Онлайн-сервис для публикации рецептов, подписки на авторов и формирования списка покупок.

Пользователи могут публиковать собственные рецепты, добавлять понравившиеся блюда в избранное, подписываться на любимых авторов, автоматически формировать список необходимых ингредиентов и делиться рецептами по коротким ссылкам.

> **Важно:** в рамках данного проекта мной была реализована backend-часть приложения (API, бизнес-логика, база данных, Docker, настройка инфраструктуры). Frontend был предоставлен заранее и не входит в область моей разработки.

---

## Статус проекта

[![Main Foodgram workflow](https://github.com/shibaevvv/foodgram/actions/workflows/main.yml/badge.svg?event=push)](https://github.com/shibaevvv/foodgram/actions/workflows/main.yml)

---

## Возможности

- регистрация и авторизация пользователей;
- публикация, редактирование и удаление рецептов;
- загрузка изображений блюд;
- теги и ингредиенты;
- подписка на авторов;
- избранные рецепты;
- корзина покупок;
- выгрузка списка покупок в текстовый файл;
- короткие ссылки на рецепты;
- административная панель Django;
- REST API;
- контейнеризация приложения с Docker;
- автоматический CI/CD через GitHub Actions.

---

## Стек технологий

### Backend

- Python 3.12
- Django 5
- Django REST Framework
- Djoser
- JWT Authentication

### База данных

- PostgreSQL 17
- SQLite (для локальной разработки)

### Инфраструктура

- Docker
- Docker Compose
- Gunicorn
- Nginx
- GitHub Actions

---

## Структура проекта

```text
backend/        Backend на Django
frontend/       React-приложение (предоставлено)
infra/          Docker, Gunicorn, Nginx
docs/           Документация API
data/           Начальные данные
```

---

## Быстрый запуск

### 1. Клонировать репозиторий

```bash
git clone https://github.com/shibaevvv/foodgram.git

cd foodgram
```

### 2. Создать файл `.env`

Скопируйте файл:

```bash
cp .env.example .env
```

и заполните необходимые переменные.

### 3. Запустить приложение

```bash
docker compose up -d
```

### 4. Выполнить миграции

```bash
docker compose exec backend python manage.py migrate
```

### 5. Собрать статические файлы

```bash
docker compose exec backend python manage.py collectstatic

docker compose exec backend cp -r /app/collected_static/. /backend_static/static/
```

### 6. Загрузить тестовые данные (необязательно)

```bash
docker compose exec backend python manage.py load_data ingredients.json

docker compose exec backend python manage.py load_data tags.json
```

### 7. Создать администратора

```bash
docker compose exec backend python manage.py createsuperuser
```

---

## Локальный запуск Backend

Перейдите в каталог проекта:

```bash
cd backend
```

Создайте виртуальное окружение:

```bash
python -m venv venv
```

Активируйте его.

Установите зависимости:

```bash
pip install -r requirements.txt
```

Выполните миграции:

```bash
python manage.py migrate
```

При необходимости загрузите тестовые данные:

```bash
python manage.py load_data ingredients.json

python manage.py load_data tags.json
```

Запустите сервер:

```bash
python manage.py runserver
```

---

## Основные адреса

| Адрес | Назначение |
|-------|------------|
| http://localhost/ | Веб-интерфейс |
| http://localhost/api/docs/ | Документация REST API |
| http://localhost/admin/ | Панель администратора |

---

## Переменные окружения

Основные параметры приложения:

```env
POSTGRES_DB=foodgram

POSTGRES_USER=foodgram_user

POSTGRES_PASSWORD=foodgram_password

DB_HOST=db

DB_PORT=5432

SECRET_KEY=your_secret_key

DEBUG=False

ALLOWED_HOSTS=localhost,127.0.0.1

CSRF_TRUSTED_ORIGINS=https://example.com
```

Полный список переменных приведён в файле `.env.example`.

---

## Автор

**Владимир Шибаев**

- GitHub: https://github.com/shibaevvv
- Telegram: https://t.me/shibaevvv
- Email: shibaev.vladimir@gmail.com
