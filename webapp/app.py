import dash
import json
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc

PATIENT_IDS = [range(1, 7)]

MOCK_DATA: dict = json.loads(
    '{ "birthdate": "1982", "disabled": false, "firstname": "Janek", "id": 12, "lastname": "Grzegorczyk", "trace": { "id": 2494801012010, "name": "bach", "sensors": [ { "anomaly": false, "id": 0, "value": 1023 }, { "anomaly": false, "id": 1, "value": 692 }, { "anomaly": false, "id": 2, "value": 31 }, { "anomaly": false, "id": 3, "value": 542 }, { "anomaly": false, "id": 4, "value": 134 }, { "anomaly": false, "id": 5, "value": 1023 } ] } }'
)

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

print(json.dumps(MOCK_DATA, indent=2))

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
        className="col-5 border shadow m-2 p-3",
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
        dcc.Interval(
          id="interval",
          interval= 1*1000,
          n_intervals = 0
        ),
        dbc.Col(
            [
                dbc.Row(dcc.Graph(id="left_foot_sensors")),
                dbc.Row(dcc.Graph(id="right_foot_sensors")),
            ]
        ),
        dbc.Col(),
    ]
)
app.layout = html.Div(children=[navbar, content])

def update_left_sensors(n, step):
    key: str = f"{MOCK_ID}_data"
    data: list = CACHE.lrange(key, 0, -1)
    deserialized = map(lambda x: json.loads(x), data)
    sensors = []
    for i in range(6):
        sensors.append(map(lambda x: x[i]["value"], deserialized))


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")

