"""
ID_ID
"""
import os
import redis 
import requests 
import json
from conf import *
import datetime

ts = datetime.datetime.now().timestamp()

IDS = range(1, 1)

CACHE = redis.Redis(host=HOST, port=PORT)

def add(personId: int, data: dict)-> None:
  serialized: str = bytes(json.dumps(data, separators=(',',':')), "utf8")
  keyBase: str = f"{personId}_"
  keyData: str = f"{keyBase}data"
  keyTimestamp: str =  f"{keyBase}timestamp"
  CACHE.lpush(keyData, serialized)
  CACHE.lpush(keyTimestamp, datetime.datetime.now().timestamp())


def clean_old(personId: int) -> None:
  """
  Remove data older than MAX_SEC
  """
  keyBase: str = f"{personId}_"
  keyData: str = f"{keyBase}data"
  keyTimestamp: str =  f"{keyBase}timestamp"

  needs_cleaning = True
  while needs_cleaning:
    toCheck: int = int.from_bytes(CACHE.lrange(keyTimestamp, 0 ,0)[0])
    clean: bool = toCheck <= datetime.datetime.now().timestamp() - MAX_SEC
    if clean:
      CACHE.lpop(keyData)
      CACHE.lpop(keyTimestamp)
    else:
      needs_cleaning = False


for i in IDS:
  i = 1
  response = requests.get(f"{BASE_URL}{i}")
  data = response.json()
  trace = data["trace"]
  sensors = trace["sensors"]
  add(i, sensors)


print(json.dumps(sensors, indent=2))



