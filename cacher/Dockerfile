FROM python:3.8-alpine

RUN mkdir /cacher 
WORKDIR /cacher
COPY . /cacher
RUN pip install -r ./requirements.txt

CMD [ "python", "./main.py" ]