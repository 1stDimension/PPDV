# Task
The goal of this project is to create an application visualizing realtime data from an API providing information about foot pressure. Example of API response:
```json
{
  "birthdate": "1982",
  "disabled": false,
  "firstname": "Janek",
  "id": 12,
  "lastname": "Grzegorczyk",
  "trace": {
    "id": 2350401012010,
    "name": "bach",
    "sensors": [
      {
        "anomaly": false,
        "id": 0,
        "value": 1023
      },
      {
        "anomaly": false,
        "id": 1,
        "value": 637
      },
      {
        "anomaly": false,
        "id": 2,
        "value": 1023
      },
      {
        "anomaly": false,
        "id": 3,
        "value": 1023
      },
      {
        "anomaly": false,
        "id": 4,
        "value": 162
      },
      {
        "anomaly": false,
        "id": 5,
        "value": 1023
      }
    ]
  }
}
```

# Details

## General
I decided to separate python application into 2 main components and a data store. Webapp, and cacher. This allows both processes to run in paralel, which is crustal in order to achieve near real time visualisation of walking person as python's Global Interpreter Lock is a major drawback when it comes to the performance.

## Webapp
The webapp actually presenting the data was written using Dash framework with additional package called Dash Bootstrap Components. The power of Dash is the ability to create layouts in Python which combined with Plotly library for ploting graphs allows for very sophisticated user interface without boilerplate code.

## Storage
Realtime nature of the data requires frequent write operations. Considering this I chose Redis. Redis as in-memory data store is designed for such operations. The down side is that in case of failure all the data will be gone. However it is possible to configure for redis to periodically save data to filesystem. Sensor data of every patient is stored as 4 lists
accessed by keys "{personId}_anomaly", "{personId}_anomaly_timestamp", "{personId}_data", "{personId}_timestamp". Timestamp lists are straightforward. Other entries are stringified JSONs of sensor data as received from API

## Caching
Caching is handled by dedicated application called "Cacher". The main feature of it is an ability to fetch data asynchronously. This allows for setting delays between requests for the same patient, which to certain degree is un affected by the amount of people to request data about. Besides caching the data Cacher also ensures that records older than **MAX_SEC** are removed. Simply every **CLEAR_DELAY** the clean up is performed. For demonstration purposes there is also one functionality, simulating anomalies in data. Every time the data is fetched dices are rolled (between 0 and 1) if threshold **ANOMALIES_TRASHOLD** is exceeded. Data of random sensor is changed to indicate anomaly. Anomalies deserve special attention therefore are stored is separate list and are *never* removed.

# Running application

Before attempting to start this program make sure you've created configuration files for each module (file called conf.py in module's root directory)

App makes use of docker-compose. Docker-compose is an extension of Docker, program allowing for executing processes in an isolated environment. This makes starting my application trivial. Only one command is needed. Namely :
```shell
docker-compose up -d
```
Ran in projects root directory. Then we should allow docker to do it's magic. If all goes well head to localhost:8050 to see this project in action.

# Configuration
Configuration of each module has to be in file called "conf.py". Most of settings is self explanatory

