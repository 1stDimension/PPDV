FROM python:3.8-alpine

RUN mkdir /webapp 
WORKDIR /webapp
ADD requirements.txt ./requirements.txt
RUN pip install -r ./requirements.txt
COPY . /webapp
EXPOSE 8050
CMD [ "python", "./app.py" ]