import json
import redis
import statistics as stat
from functools import reduce

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

PATIENT_IDS = [range(1, 7)]

MOCK_DATA: dict = json.loads(
    '{ "birthdate": "1982", "disabled": false, "firstname": "Janek", "id": 12, "lastname": "Grzegorczyk", "trace": { "id": 2494801012010, "name": "bach", "sensors": [ { "anomaly": false, "id": 0, "value": 1023 }, { "anomaly": false, "id": 1, "value": 692 }, { "anomaly": false, "id": 2, "value": 31 }, { "anomaly": false, "id": 3, "value": 542 }, { "anomaly": false, "id": 4, "value": 134 }, { "anomaly": false, "id": 5, "value": 1023 } ] } }'
)

MOCK_ID = 1

MOCK_WALK: dict = json.loads(
    """{
    "1": [
        {
            "anomaly": false,
            "value": 1023
        },
        {
            "anomaly": false,
            "value": 1023
        },
        {
            "anomaly": false,
            "value": 33
        },
        {
            "anomaly": false,
            "value": 1023
        },
        {
            "anomaly": false,
            "value": 660
        },
        {
            "anomaly": false,
            "value": 33
        }
    ],
    "2": [
        {
            "anomaly": false,
            "value": 33
        },
        {
            "anomaly": false,
            "value": 103
        },
        {
            "anomaly": false,
            "value": 1023
        },
        {
            "anomaly": false,
            "value": 1023
        },
        {
            "anomaly": false,
            "value": 283
        },
        {
            "anomaly": false,
            "value": 1023
        }
    ],
    "3": [
      {
        "anomaly": false,
        "id": 0,
        "value": 1023
      },
      {
        "anomaly": false,
        "id": 1,
        "value": 981
      },
      {
        "anomaly": false,
        "id": 2,
        "value": 30
      },
      {
        "anomaly": false,
        "id": 3,
        "value": 30
      },
      {
        "anomaly": false,
        "id": 4,
        "value": 36
      },
      {
        "anomaly": false,
        "id": 5,
        "value": 1023
      }
    ]
}"""
)

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
                className="",
            ),
        ],
        className="col-5 border shadow",
    )


def pressure_graph(one: list, two: list, tree: list) -> None:
    """
  Creates line graph of one foot's presure 
  """
    pass


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
        patient_info_bar,
        dcc.Interval(id="walking_interval", interval=50, n_intervals=0),
        dcc.Interval(id="interval", interval=5 * 1000, n_intervals=0),
        dbc.Col(
            [
                dcc.Graph(id="left_foot_sensors"),
                dcc.Slider(
                    id="sensor_skip_slider",
                    min=1,
                    max=10,
                    step=1,
                    value=1,
                    marks={
                        # 0:  {'label': '0', 'style': {'color': '#f50'}},
                        i: "{}".format(i)
                        for i in range(1, 11)
                        # 10: {'label': '10', 'style': {'color': '#f50'}}
                    },
                ),
                dcc.Graph(id="right_foot_sensors"),
            ],
            className="border shadow",
        ),
        dbc.Col([dcc.Graph(id="walking"),]),
    ]
)
app.layout = html.Div(children=[navbar, content])


@app.callback(Output("walking", "figure"), [Input("interval", "n_intervals")])
def update_left_waliking(n):
    # start = datetime.datetime.now().timestamp()
    key: str = f"{MOCK_ID}_data"
    sampleList: list = CACHE.lrange(key, -1, -1)
    response = [None, None]
    if len(sampleList) > 0:
        sample = sampleList[0]
        # print(f"_|{sample}|_")
        deserialized = json.loads(sample)
        # filter(lambda x: )
        left = list(map(lambda x: x["value"], deserialized[:3]))
        right = list(map(lambda x: x["value"], deserialized[3:]))

        left_avg = stat.mean(left)
        right_avg = stat.mean(right)
        # end = datetime.datetime.now().timestamp()
        # print(f":::{end - start}:::")
        response = [left_avg, right_avg]
    return {"data": [{"type": "bar", "x": ["Left", "Right"], "y": response}]}


@app.callback(
    Output("left_foot_sensors", "figure"),
    [Input("interval", "n_intervals"), Input("sensor_skip_slider", "value")],
)
def update_left_sensors(n, step):
    key: str = f"{MOCK_ID}_data"
    data: list = CACHE.lrange(key, 0, -1)
    deserialized = map(lambda x: json.loads(x), data)

    # a = json.loads(data)
    # print(json.dumps(a, indent=2))

    sensors = []
    for i in range(6):
        sensors.append(list(map(lambda x: x[i].get("value"), deserialized)))

    # sensor_zero = map(lambda x: x["value"], left)
    # sensor_zero_anomaly = map(lambda x: x["value"] if x["anomaly"] else None, left)
    # fig = go.Figure()
    return {
        "data": [
            {
                # "x": list(range(0, len(data))),
                "y": sensors[0],
                # "text": ["a", "b", "c", "d"],
                # "customdata": ["c.a", "c.b", "c.c", "c.d"],
                "name": f"Sensor 1",
                "type": "scatter",
                "mode": "lines+markers",
                "marker": {"size": 3, "color": "rgb(255, 0, 0)"},
            },
            {
                # "x": list(range(0, len(data))),
                "y": sensors[1],
                # "text": ["w", "x", "y", "z"],
                # "customdata": ["c.w", "c.x", "c.y", "c.z"],
                "name": "Sensor 2",
                "type": "scatter",
                "mode": "lines",
                "marker": {"size": 3, "color": "rgb(0,255,0)"},
            },
        ],
        "layout": {"title": "Left foot sensors"},
        "frames": [],
    }


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

