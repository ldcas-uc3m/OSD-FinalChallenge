FROM python:3.7.3

COPY /app /etc/usr/src/app

WORKDIR /etc/usr/src/app

# install packages
RUN pip install paho-mqtt

ENTRYPOINT ["python"]
CMD ["-u", "digital_twin.py"]