## Answers

1. Django version and Python version Django==4.2.6, Python==3.12
2. Database engine and version (PostgreSQL) using psycopg2-binary==2.9.9
3. Hosting (Azure) and using docker deployment method
4. Web server and WSGI/ASGI setup
```
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_wsgi_application()
```
5. Is there a staging environment, or is production the only live
instance? Yes
6. Is any part of the frontend already using a JS framework, or is it
entirely Django templates plus Bootstrap? Yes