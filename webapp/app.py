import json
import redis
import statistics as stat
from functools import reduce
from typing import List, Tuple
import requests

import datetime
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash.dependencies import Input, Output


from conf import *

CACHE = None
try:
    CACHE = redis.Redis(host=HOST, port=PORT)
except redis.ConnectionError as e:
    print(f"Redis connection error:\n{e}")
    exit(-1)

PATIENT_IDS = [range(1, 7)]
PATIENT_DATA = []
for i in PATIENT_IDS:
    response = requests.get(BASE_URL + f"{i}")
    json_data = response.json()
    data = {
    "birthdate": json_data["birthdate"],
    "disabled": json_data["disabled"],
    "firstname": json_data["firstname"],
    "id": json_data["id"],
    "lastname": json_data["lastname"],
    }
    PATIENT_DATA.append(data)


SENSORS_ID = list(range(6))

MOCK_DATA: dict = json.loads(
    '{ "birthdate": "1982", "disabled": false, "firstname": "Janek", "id": 12, "lastname": "Grzegorczyk", "trace": { "id": 2494801012010, "name": "bach", "sensors": [ { "anomaly": false, "id": 0, "value": 1023 }, { "anomaly": false, "id": 1, "value": 692 }, { "anomaly": false, "id": 2, "value": 31 }, { "anomaly": false, "id": 3, "value": 542 }, { "anomaly": false, "id": 4, "value": 134 }, { "anomaly": false, "id": 5, "value": 1023 } ] } }'
)

MOCK_ID = 1


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def generate_patient_info_bar(patient: dict) -> dbc.Col:
    """
  Generates Dash Bootstrap Component's Column with patient's data
  """
    return dbc.Col(
        [
            html.H2("Patient's basic information"),
            html.Div(
                [
                    html.Dl(
                        [
                            html.Dt("Name:"),
                            html.Dd(patient["lastname"] + " " + patient["firstname"]),
                            html.Dt("Born:"),
                            html.Dd(patient["birthdate"]),
                            html.Dt("Disabled:"),
                            html.Dd("Yes" if patient["disabled"] else "No"),
                        ]
                    )
                ],
            ),
        ],
        className="border shadow",
    )


patient_info_bar = generate_patient_info_bar(MOCK_DATA)

navbar = dbc.NavbarSimple(
    children=[
        # dbc.NavItem(dbc.NavLink("Link", href="#")),
    ],
    brand="Happy Feet 😀",
    # brand_href="#",
    sticky="top",
)

content = dbc.Container(
    [
        dcc.Store(id="patient_id", storage_type='session', data={"id": 1}),
        html.Div(
            [
                patient_info_bar,
                dbc.Col([dcc.Graph(id="walking")], className="border shadow"),
            ],
            className="d-flex flex-row bd-highlight",
        ),
        dcc.Interval(id="walking_interval", interval=50, n_intervals=0),
        dcc.Interval(id="interval", interval=5 * 1000, n_intervals=0),
        dbc.Col(
            [
                dcc.Slider(
                    id="sensor_skip_slider",
                    min=1,
                    max=10,
                    step=1,
                    value=5,
                    marks={
                        # 0:  {'label': '0', 'style': {'color': '#f50'}},
                        i: "{}".format(i)
                        for i in range(1, 11)
                        # 10: {'label': '10', 'style': {'color': '#f50'}}
                    },
                ),
                dcc.Graph(id="left_foot_sensors"),
                dcc.Graph(id="right_foot_sensors"),
            ],
            className="border shadow",
        ),
    ]
)
app.layout = html.Div(children=[navbar, content])


@app.callback(Output("walking", "figure"), [Input("interval", "n_intervals"), Input("patient_id", "data")])
def update_waliking(n, patient_data):
    # start = datetime.datetime.now().timestamp()
    id = patient_data["id"]
    key: str = f"{id}_data"
    sampleList: list = CACHE.lrange(key, -1, -1)
    response = [None, None]
    colours = ["orange",] * 6 
    colours[3:] = ["rgb(55, 83, 109)",] * 3
    # print(colours)
    if len(sampleList) > 0:
        sample = sampleList[0]
        deserialized = json.loads(sample)
        # left = list(map(lambda x: x["value"], deserialized[:3]))
        # right = list(map(lambda x: x["value"], deserialized[3:]))

        values = list(map(lambda x: x["value"], deserialized))

        # left_avg = stat.mean(left)
        # right_avg = stat.mean(right)
        response = values
    return {
        "data": [
            {
                "type": "bar",
                # "x": ["Left", "Right"],
                "y": response,
                "text": response,
                "textposition": "auto",
                "marker": {"color": colours},
            }
        ]
    }


@app.callback(
    [Output("left_foot_sensors", "figure"), Output("right_foot_sensors", "figure")],
    [Input("interval", "n_intervals"), Input("sensor_skip_slider", "value"), Input("patient_id", "data")],
)
def update_sensors(n, step, patient_data):
    id: int = patient_data["id"]
    key: str = f"{id}_data"
    data: list = CACHE.lrange(key, 0, -1)

    sensors = []
    for i in SENSORS_ID:
        sensors.append(list(map(lambda x: json.loads(x)[i].get("value"), data)))
    return (
        {
            "data": generate_sensors_data_list(
                sensors[:3], [f"Sensor {i}" for i in SENSORS_ID], step=step
            ),
            "layout": {"title": "Left foot sensors"},
            "frames": [],
        },
        {
            "data": generate_sensors_data_list(
                sensors[3:], [f"Sensor {i}" for i in SENSORS_ID[3:]], step=step
            ),
            "layout": {"title": "Right foot sensors"},
            "frames": [],
        },
    )


def generate_sensors_data_list(
    sensors: List[list],
    sensor_names: List[str],
    step: int = 1,
    colours: list = [(255, 0, 0), (0, 255, 0), (0, 0, 255),],
) -> list:
    data = []
    for idx, value in enumerate(sensors):
        trace = {
            "y": value[::step],
            "name": sensor_names[idx],
            "type": "scatter",
            "mode": "lines+markers",
            "marker": {"size": 3, "color": "rgb({},{},{})".format(*(colours[idx]))},
        }
        data.append(trace)
    return data


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

