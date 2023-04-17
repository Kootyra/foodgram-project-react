# praktikum_new_diplom

http://62.84.112.56

## Краткое описание проекта,
Учебный проект по созданию приложения «Продуктовый помощник»: сайт, на котором пользователи будут публиковать рецепты, добавлять чужие рецепты в избранное и подписываться на публикации других авторов. Сервис «Список покупок» позволит пользователям создавать список продуктов, которые нужно купить для приготовления выбранных блюд. 


## Шаблон наполнения env-файла,
- DB_ENGINE
- DB_NAME
- POSTGRES_USER
- POSTGRES_PASSWORD
- DB_HOST
- DB_PORT

## Описание команд для запуска приложения в контейнерах
### Из папки infra:
- sudo docker-compose up -d --build
- sudo docker-compose exec web python manage.py migrate
- sudo docker-compose exec web python manage.py createsuperuser
- sudo docker-compose exec web python manage.py collectstatic --no-input

## Описание команды для заполнения базы данными.
- python manage.py loaddata load_ingredients

## Как запустить проект:
Клонировать репозиторий и перейти в него в командной строке:
```
https://github.com/Kootyra/foodgram-project-react.git
```
Cоздать и активировать виртуальное окружение:
```
python3 -m venv venv
```
```
source venv/bin/activate
```
Установить зависимости из файла requirements.txt:
```
python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Выполнить миграции:
```
python3 manage.py migrate
```
Запустить проект:
```
python3 manage.py runserver
```