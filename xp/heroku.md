
<mediawiki>
https://teamperformanceweb.wordpress.com/2014/02/21/setting-up-mediawiki-on-heroku/

curl -sS https://getcomposer.org/installer | php
php composer.phar update

heroku config | grep HEROKU_POSTGRESQL                  15-03-02 22:30
HEROKU_POSTGRESQL_CYAN_URL: postgres://lffwxkugxvgwya:pjdSck6DcPzMbzzA6zLc2WTp34@ec2-107-21-102-69.compute-1.amazonaws.com:5432/d43vlkclqv32qe

</mediawiki>

<local>
foreman start  # start local web server
</local>

<remote>
heroku create
git push heroku master
heroku ps:scale web=1
heroku run python manage.py syncdb
heroku open

</remote>

<django>
https://devcenter.heroku.com/articles/getting-started-with-django

sudo apt-get install postgresql-server-dev-9.4

* django
cd /workspace/project/gyagp && mkdir heroku && cd heroku
virtualenv venv --no-site-packages  # setup virtualenv
source venv/bin/activate  # activate virtualenv
pip install django-toolbelt
django-admin.py startproject webbench .
echo "web: gunicorn webbench.wsgi --log-file -" >Procfile
pip freeze > requirements.txt
echo "venv\n*.pyc\nstaticfiles" >.gitignore
git init
git add .
git commit -m "Init webbench"

* django-cms
pip install django-cms
pip install django-cms-themes
python manage.py migrate
python manage.py createsuperuser

python manage.py runserver 5000


</django>