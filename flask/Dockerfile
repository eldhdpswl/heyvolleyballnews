FROM python:3.9

RUN apt-get -y update
RUN apt-get -y upgrade

RUN mkdir /app
ADD . /app

WORKDIR /app

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["uwsgi","uwsgi.ini"]