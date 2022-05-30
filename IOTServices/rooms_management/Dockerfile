FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

# install libraries
RUN pip install paho-mqtt requests

ENTRYPOINT ["python"]
CMD ["-u", "rooms_management.py"]
