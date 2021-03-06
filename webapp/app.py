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

PATIENTS_DATA = []  # Repository for user data
OPTIONS = []  # container for dropdown options
CACHE = None  # Redis object for storing data

try:
    CACHE = redis.Redis(host=HOST, port=PORT)
except redis.ConnectionError as e:
    print(f"Redis connection error:\n{e}")
    exit(-1)

try:
    for i in IDS:
        # print(BASE_URL + f"{i}")
        response = requests.get(url=BASE_URL + f"{i}")
        # print(response.json())
        json_data = response.json()
        data = {
            "birthdate": json_data["birthdate"],
            "disabled": json_data["disabled"],
            "firstname": json_data["firstname"],
            "id": i - 1,
            "lastname": json_data["lastname"],
        }
        PATIENTS_DATA.append(data)
except requests.RequestException as e:
    print(f"Error fetching data:\n{e}")
    exit(-1)

for i in PATIENTS_DATA:
    OPTIONS.append({"label": i["lastname"] + " " + i["firstname"], "value": i["id"]})

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def generate_patient_info_bar(patient: dict) -> dbc.Col:
    """
  Generates Dash Bootstrap Component's Column with patient's data
  """
    return dbc.Col(
        [
            html.Div(
                children=[
                    html.H2("Patient's basic information"),
                    html.Div(
                        [
                            html.Dl(
                                [
                                    html.Dt("Name:"),
                                    html.Dd(
                                        patient["lastname"] + " " + patient["firstname"]
                                    ),
                                    html.Dt("Born:"),
                                    html.Dd(patient["birthdate"]),
                                    html.Dt("Disabled:"),
                                    html.Dd("Yes" if patient["disabled"] else "No"),
                                ]
                            )
                        ],
                    ),
                ],
                className="d-flex flex-column",
            )
        ],
        className="d-flex align-items-center border shadow",
    )


navbar = dbc.NavbarSimple(
    children=[
        # dbc.NavItem(children=["Happy Feet 😀"]),
        html.Div(
            [
                dcc.Dropdown(
                    id="patient_picker",
                    options=OPTIONS,
                    placeholder="Patient",
                    value=0,
                    style={"min-width": "200px"},
                ),
            ],
            className="d-flex justify-content-between",
        )
    ],
    # className="navbar "
    brand="Happy Feet 😀",
    brand_href="#",
    sticky="top",
)

content = dbc.Container(
    [
        dcc.Store(id="patient_id", storage_type="session", data={"id": 0}),
        html.Div(
            [
                html.Div(
                    id="patient_info_container", className="d-flex align-items-stretch",
                ),
                dbc.Col([dcc.Graph(id="walking")], className="border shadow"),
            ],
            className="d-flex flex-row bd-highlight pt-4",
        ),
        dcc.Interval(id="walking_interval", interval=100, n_intervals=0),
        dcc.Interval(id="interval", interval=5 * 1000, n_intervals=0),
        dcc.Interval(id="anomaly_interval", interval=60 * 1000, n_intervals=0),
        dbc.Col(
            [   
                html.H3("Live data", className="text-center"),
                html.H6("Show only every n-th elements", className="text-center p-3"),
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
                html.Hr(),
                html.H3("Anomalies", className="text-center"),
                html.H6("Show only every n-th elements", className="text-center p-3"),
                dcc.Slider(
                    id="anomaly_skip_slider",
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
                dcc.Graph(id="left_foot_anomaly"),
                dcc.Graph(id="right_foot_anomaly"),
                dcc.Graph(id="anomaly_histogram"),
            ],
            className="border shadow pt-5",
        ),
    ]
)
app.layout = html.Div(children=[navbar, content])


@app.callback(
    [Output("patient_info_container", "children"), Output("patient_id", "data")],
    [Input("patient_picker", "value")],
)
def change_patient(value):
    newPatientData: dict = PATIENTS_DATA[value]
    html_element = generate_patient_info_bar(newPatientData)
    return (html_element, {"id": value})


@app.callback(
    Output("walking", "figure"),
    [Input("interval", "n_intervals"), Input("patient_id", "data")],
)
def update_waliking(n, patient_data):
    # start = datetime.datetime.now().timestamp()
    id = patient_data["id"] + 1
    key: str = f"{id}_data"
    sampleList: list = CACHE.lrange(key, -1, -1)
    response = [None, None]
    colours = ["orange",] * 6
    colours[3:] = ["rgb(55, 83, 109)",] * 3
    # print(colours)
    if len(sampleList) > 0:
        sample = sampleList[0]
        deserialized = json.loads(sample)

        values = list(map(lambda x: x["value"], deserialized))

        response = values
    return {
        "data": [
            {
                "type": "bar",
                "x": list(f"Sensor {i}" for i in range(6)),
                "y": response,
                # "text": response,
                "textposition": "auto",
                "marker": {"color": colours},
            },
        ],
        "layout": {"showlegend": False, "title": "Current pressure "}
    }


@app.callback(
    [Output("left_foot_sensors", "figure"), Output("right_foot_sensors", "figure")],
    [
        Input("interval", "n_intervals"),
        Input("sensor_skip_slider", "value"),
        Input("patient_id", "data"),
    ],
)
def update_sensors(n, step, patient_data):
    id: int = patient_data["id"] + 1
    key: str = f"{id}_data"
    data: list = CACHE.lrange(key, 0, -1)

    sensors = []
    for i in SENSORS_ID:
        sensors.append(list(map(lambda x: json.loads(x)[i].get("value"), data)))
    return (
        {
            "data": generate_sensors_data_list(
                sensors[:3], [f"Sensor {i}" for i in range(3)], step=step
            ),
            "layout": {"title": "Left foot sensors"},
            "frames": [],
        },
        {
            "data": generate_sensors_data_list(
                sensors[3:], [f"Sensor {i}" for i in range(3, 6)], step=step
            ),
            "layout": {"title": "Right foot sensors"},
            "frames": [],
        },
    )


@app.callback(
    [Output("left_foot_anomaly", "figure"), Output("right_foot_anomaly", "figure")],
    [
        Input("interval", "n_intervals"),
        Input("anomaly_skip_slider", "value"),
        Input("patient_id", "data"),
    ],
)
def update_anomaly(n, step, patient_data):
    id: int = patient_data["id"] + 1
    key: str = f"{id}_anomaly"
    key_datetime: str = f"{id}_anomaly_timestamp"
    data: list = CACHE.lrange(key, 0, -1)
    timestamps: list = CACHE.lrange(key_datetime, 0, -1)
    datetimes = list(map(lambda x: datetime.datetime.utcfromtimestamp(int(x)), timestamps))
    sensors = []
    for i in SENSORS_ID:
        sensors.append(list(map(lambda x: json.loads(x)[i].get("value"), data)))
    return (
        {
            "data": generate_sensors_data_list(
                sensors[:3], [f"Sensor {i}" for i in range(3)], step=step, datetimes=datetimes
            ),
            "layout": {"title": "Left foot sensors"},
            "frames": [],
        },
        {
            "data": generate_sensors_data_list(
                sensors[3:], [f"Sensor {i}" for i in range(3, 6)], step=step, datetimes=datetimes
            ),
            "layout": {"title": "Right foot sensors"},
            "frames": [],
        },
    )

@app.callback(
    Output("anomaly_histogram", "figure"),
    [
        Input("anomaly_interval", "n_intervals"),
        Input("patient_id", "data"),
    ],) 
def update_histogram(n, patient_data):
    id: int = patient_data["id"] + 1
    key: str = f"{id}_anomaly"
    data: list = CACHE.lrange(key, 0, -1)

    def extract_left(x, pivot=3):
        entry = json.loads(x);
        return [ value["value"] for value in entry[:pivot] ]

    def extract_right(x, pivot=3):
        entry = json.loads(x);
        return [ value["value"] for value in entry[pivot:] ]

    extracted_left = map(extract_left, data)
    extracted_right = map(extract_right, data)

    left = (reduce(lambda x,y: x+y, extracted_left, [0]))
    right = (reduce(lambda x,y: x+y, extracted_right, [0]))
    # left_histogram = np.histogram(left,bins = [0,128,256,384,512,640, 768, 896, 1024]) 
    # right_histogram = np.histogram(right,bins = [0,128,256,384,512,640, 768, 896, 1024]) 
    # print(left_histogram[0])
    return {
        "data": [{
            "x": left,
            # "y": left_histogram[0],
            "name": "Left foot anomalies",
            "type": "histogram"
        },{
            "x": right,
            "name": "Right foot anomalies",
            "type": "histogram"
        }],
        "layout": {
            "Title": "Histogram of gathered anomalies"
        }
    }

def generate_sensors_data_list(
    sensors: List[list],
    sensor_names: List[str],
    step: int = 1,
    colours: list = [(255, 0, 0), (0, 255, 0), (0, 0, 255),],
    datetimes: list=None
) -> list:
    data = []
    for idx, value in enumerate(sensors):
        if datetimes != None:
            trace = {
            "x": datetimes[::step],
            "y": value[::step],
            "name": sensor_names[idx],
            "type": "scatter",
            "mode": "lines+markers",
            "marker": {"size": 3, "color": "rgb({},{},{})".format(*(colours[idx]))},
            }
        else:
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

