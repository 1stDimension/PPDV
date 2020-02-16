"""
ID_ID
"""
import os
import redis
import asyncio
import requests
import json
import logging
from conf import *
import time
import datetime
import random
from functools import reduce

CACHE = None
try:
    CACHE = redis.Redis(host=HOST, port=PORT)
except redis.ConnectionError as e:
    print(f"Connection error occurred:\n{e}")


async def simulate_anomalies(sensors: list) -> dict:
    """
    Simulate anomalies 
    """
    bet: float = random.random()
    if bet < ANOMALIES_TRASHOLD:
        position = random.randrange(SENSOR_NUMBER)
        sensors[position]["anomaly"] = True
    return sensors

async def add(personId: int, data: dict) -> None:
    """
    Synchronously add one entry to personId list
    """
    serialized: str = bytes(json.dumps(data, separators=(",", ":")), "utf8")
    keyBase: str = f"{personId}_"
    keyData: str = f"{keyBase}data"
    keyTimestamp: str = f"{keyBase}timestamp"
    CACHE.rpush(keyData, serialized)
    CACHE.rpush(keyTimestamp, int(datetime.datetime.now().timestamp()))

async def add_anomaly(personId: int, data: dict) -> None:
    """
    Adds anomalies to persons anomalies list
    """
    serialized: str = bytes(json.dumps(data, separators=(",", ":")), "utf8")
    keyBase: str = f"{personId}_"
    keyData: str = f"{keyBase}anomaly"
    keyTimestamp: str = f"{keyBase}anomaly_timestamp"
    CACHE.rpush(keyData, serialized)
    CACHE.rpush(keyTimestamp, int(datetime.datetime.now().timestamp()))


async def clean_old(personId: int) -> None:
    """
  Asynchronously and periodically remove data older than MAX_SEC
  """
    # print("Cleaning old")

    keyBase: str = f"{personId}_"
    keyData: str = f"{keyBase}data"
    keyTimestamp: str = f"{keyBase}timestamp"
    while True:
        needs_cleaning = True
        while needs_cleaning:
            sample: list = CACHE.lrange(keyTimestamp, 0, 0)
            if len(sample) > 0:
                toCheck: int = int(float(sample[0]))
            else:
                break
            # print("to Check{:^12}".format(toCheck))
            clean: bool = toCheck <= int(datetime.datetime.now().timestamp()) - MAX_SEC
            if clean:
                print("Cleaning")
                CACHE.lpop(keyData)
                CACHE.lpop(keyTimestamp)
            else:
                needs_cleaning = False
            await asyncio.sleep(0)
        await asyncio.sleep(CLEAR_DELAY)


async def pull_data(personId: int) -> None:
    """
  Asynchronously and continuously pull data from server with REQUEST_DELAY delay
  """
    while True:
        loop = asyncio.get_event_loop()
        futureResponse = loop.run_in_executor(
            None, requests.get, f"{BASE_URL}{personId}"
        )
        response = await futureResponse
        data: dict = response.json()
        trace: dict = data["trace"]
        sensors: dict = trace["sensors"]

        sensors = await simulate_anomalies(sensors)

        anomalies = map(lambda x: x["anomaly"], sensors)
        anomalies_present = reduce(lambda x, y: x or y, anomalies)
        if anomalies_present:
            await add_anomaly(personId, sensors)

        await add(personId, sensors)
        await asyncio.sleep(REQUEST_DELAY)


async def main():
    print(f"execution of loop starts {IDS}")
    try:
        pullers = asyncio.gather(*(pull_data(i) for i in IDS))
        cleaner = asyncio.gather(*(clean_old(i) for i in IDS))

        all_workers = asyncio.gather(pullers, cleaner)
        await all_workers

        while True:
            await asyncio.sleep(10)
    except requests.exceptions.Timeout as e:
        print(f"Connection to api has timed out:\n{e}")
    except requests.exceptions.ConnectionError as e:
        print(f"There was an error connecting to api:\n{e}")
    except redis.ConnectionError as e:
        print(f"Connection error occurred:\n{e}")


# logging.basicConfig(level=logging.DEBUG)
asyncio.run(main())
