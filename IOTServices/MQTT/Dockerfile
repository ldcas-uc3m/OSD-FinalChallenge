FROM debian:buster

RUN apt update && apt upgrade -y

RUN apt install mosquitto mosquitto-clients -y

# provisional credentials
RUN touch /etc/mosquitto/passwd
RUN mosquitto_passwd -b /etc/mosquitto/passwd dso_server dso_password

CMD ["/usr/sbin/mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"]
