FROM python:3.8-alpine

RUN mkdir /cacher 
WORKDIR /cacher
ADD requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
COPY . /cacher

CMD [ "python", "./main.py" ]