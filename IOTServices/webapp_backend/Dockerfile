FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

# install libraries
RUN pip install Flask Flask-Cors requests

ENTRYPOINT ["python"]
CMD ["-u", "webapp_backend_api_rest.py"]