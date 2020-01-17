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

CACHE = redis.Redis(host=HOST, port=PORT)


def add(personId: int, data: dict) -> None:
    """
    Synchronously add one entry to personId list
    """
    serialized: str = bytes(json.dumps(data, separators=(",", ":")), "utf8")
    keyBase: str = f"{personId}_"
    keyData: str = f"{keyBase}data"
    keyTimestamp: str = f"{keyBase}timestamp"
    CACHE.lpush(keyData, serialized)
    CACHE.lpush(keyTimestamp, int(datetime.datetime.now().timestamp()) )


async def clean_old(personId: int) -> None:
  """
  Asynchronously and periodically remove data older than MAX_SEC
  """
  print("Cleaning old")

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
      print("to Check{:^12}".format(toCheck))
      clean: bool = toCheck <= datetime.datetime.now().timestamp() - MAX_SEC
      if clean:
        print("Cleaning")
        CACHE.lpop(keyData)
        CACHE.lpop(keyTimestamp)
      else:
        needs_cleaning = False
        
    await asyncio.sleep(CLEAR_DELAY)


async def pull_data(personId: int) -> None:
    """
  Asynchronously and continuously pull data from server with REQUEST_DELAY delay
  """
    while True:
      loop = asyncio.get_event_loop()
      futureResponse = loop.run_in_executor(None, requests.get, f"{BASE_URL}{personId}")
      response = await futureResponse
      data: dict    = response.json()
      trace: dict   = data["trace"]
      sensors: dict = trace["sensors"]

      add(personId, sensors)
      await asyncio.sleep(REQUEST_DELAY)


async def main():
    print(f"execution of loop starts {IDS}")

    pullers = asyncio.gather( *(pull_data(i) for i in IDS) )
    cleaner = asyncio.gather( *(clean_old(i) for i in IDS) )

    all_workers = asyncio.gather(pullers, cleaner)
    await all_workers

    while True:
      await asyncio.sleep(10)

logging.basicConfig(level=logging.DEBUG)
asyncio.run(main(), debug=True)
