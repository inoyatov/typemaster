release: cd ./src/ && python manage.py collectstatic --no-input && python manage.py migrate --no-input
web: cd ./src/ && gunicorn config.wsgi
