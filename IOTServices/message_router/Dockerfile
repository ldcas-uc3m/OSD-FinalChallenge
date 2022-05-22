FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

# install libraries
RUN pip install paho-mqtt requests Flask Flask-Cors

ENTRYPOINT ["python"]
CMD ["-u", "message_router.py"]
