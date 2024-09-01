import xml.etree.ElementTree as ET
from math import cos, radians, sqrt
import requests
from time import sleep
from pathlib import Path
import json
from datetime import datetime
import plotly.graph_objects as go

from flask import Flask, render_template, url_for

app = Flask(__name__)
with app.test_request_context():
    url_for('static', filename='styles.css')

app.logger.info("dsfdsfsfsd")



'''
https://en.wikipedia.org/wiki/Geographic_coordinate_system#Latitude_and_longitude
'''
def lat2m(latitude):
    return 111132.92 - 559.82 * cos(2 * radians(latitude)) + 1.175 * cos(4 * radians(latitude)) - 0.0023 * cos(6 * radians(latitude))

'''
https://en.wikipedia.org/wiki/Geographic_coordinate_system#Latitude_and_longitude
'''
def lon2m(longitude):
    return 111412.84 * cos(radians(longitude)) - 93.5 * cos(3 * radians(longitude)) + 0.118 * cos(5 * radians(longitude))

def get_mult_ele(locations, dataset):
    global app
    print(len(locations))
    data = {"results": []}
    n = 100
    nbdownloaded =  0
    for sublocs in [locations[i:i+n] for i in range(0, len(locations), n)]:
        sleep(1)
        result = get_opentopo_ele(sublocs, dataset)
        nbdownloaded += len(sublocs)
        app.logger.debug(f"{nbdownloaded}/{len(locations)}")

        data["results"].extend(result["results"])
    return data


def get_lat_lon_grid_fixednbpt(lat_start, lat_stop, lon_start, lon_stop):
    # print(lat_start, lat_stop)
    maxpoints = 1000
    locations = []
    lats = []
    lons = []

    # res = 0.001
    # latsteps = (lat_stop - lat_start) / res
    # # print(latsteps)
    # lonsteps = (lon_stop - lon_start) / res
    
    # latspets * lonspets = maxpoints
    # latsteps = (lat_stop - lat_start) / res
    # lonsteps = (lon_stop - lon_start) / res
    # (lat_stop - lat_start) / res * (lon_stop - lon_start) / res = maxpoints
    res = sqrt((lat_stop - lat_start) * (lon_stop - lon_start) / maxpoints)

    latsteps = (lat_stop - lat_start) / res
    lonsteps = (lon_stop - lon_start) / res

    # print(lonsteps)
    for idx in range(0, int(latsteps)):
        lat = lat_start + idx * res
        lats.append(lat)
        # print (f"min = {lat_start}, max = {lat_stop}", lat, str(lat >= lat_start), str(lat < lat_stop))
        for jdx in range(0, int(lonsteps)):
            lon = lon_start + jdx * res
            lons.append(lon)
            # print (f"min = {lon_start}, max = {lon_stop}", lon, lon >= lon_start, lon < lon_stop)
            locations.append({"lat": lat, "lon": lon})
    return locations, lats, lons

def get_lat_lon_grid(lat_start, lat_stop, lon_start, lon_stop):
    # print(lat_start, lat_stop)
    locations = []
    lats = []
    lons = []
    res = 0.001
    latsteps = (lat_stop - lat_start) / res
    # print(latsteps)
    lonsteps = (lon_stop - lon_start) / res
    # print(lonsteps)
    for idx in range(0, int(latsteps)):
        lat = lat_start + idx * res
        lats.append(lat)
        # print (f"min = {lat_start}, max = {lat_stop}", lat, str(lat >= lat_start), str(lat < lat_stop))
        for jdx in range(0, int(lonsteps)):
            lon = lon_start + jdx * res
            lons.append(lon)
            # print (f"min = {lon_start}, max = {lon_stop}", lon, lon >= lon_start, lon < lon_stop)
            locations.append({"lat": lat, "lon": lon})
    return locations, lats, lons


def get_opentopo_ele(locations, dataset):
    loc_str = "|".join([str(x["lat"])+","+str(x['lon']) for x in locations])

    url = f"https://api.opentopodata.org/v1/{dataset}"
    data = {
        "locations": loc_str,
        "interpolation": "cubic",
    }
    r = requests.post(url, json=data)

    d = {"lat": [], "lon": [], "ele": []}
    # print(r.json())
    return r.json()

def opentododata2scatterdata(result):
    for x in result["results"]:
        d["lat"].append(x["location"]["lat"])
        d["lon"].append(x["location"]["lng"])
        d["ele"].append(x["elevation"])
    return d

def opentopodata2surfacedata(result):
    sorted_result = sorted(result["results"], key = lambda x: (x["location"]["lat"], x["location"]["lng"]))

    x = sorted(set([x["location"]["lng"] for x in sorted_result]))
    y = sorted(set([x["location"]["lat"] for x in sorted_result]))
    z_list = [x["elevation"] for x in sorted_result]

    z_matrix = []
    for z in z_list:
        if len(z_matrix) == 0 or len(z_matrix[-1]) == len(x):
            z_matrix.append([])
        z_matrix[-1].append(z)

    return x,y,z_matrix

def get_open_elevations(locations):
    payload = {"locations": []}
    for LOC in locations:
        payload["locations"].append({"latitude": loc["lat"], "longitude": loc["lon"]})

    r = requests.post('https://api.open-elevation.com/api/v1/lookup', json=payload)

    data = {"lat": [], "lon": [], "ele": []}
    for x in r["results"]:
        data["lon"].append(x["longitude"])
        data["lat"].append(x["latitude"])
        data["ele"].append(x["elevation"])
    return data

def getdatafromgpx(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    trk = root.find('{http://www.topografix.com/GPX/1/0}trk')
    seg = trk.find('{http://www.topografix.com/GPX/1/0}trkseg')

    data = {"lat":[], "lon":[], "text":[], "ele": [], "src": []}

    # max_lon = None
    # min_lon = None
    # max_lat = None
    # min_lat = None

    for child in seg:
        lat = float(child.get('lat'))
        lon = float(child.get('lon'))

        # if not max_lat or lat > max_lat: max_lat = lat
        # if not min_lat or lat < min_lat: min_lat = lat
        # if not max_lon or lon > max_lon: max_lon = lon
        # if not min_lon or lon < min_lon: min_lon = lon

        data["lat"].append(lat)
        data["lon"].append(lon)
        data["ele"].append(float(child.find('{http://www.topografix.com/GPX/1/0}ele').text))
        data["text"].append(child.find('{http://www.topografix.com/GPX/1/0}time').text)
        # data["src"].append("red")
        # print(child.attrib)

    start_time = datetime.fromisoformat(seg[0].find('{http://www.topografix.com/GPX/1/0}time').text[:-1])
    end_time = datetime.fromisoformat(seg[-1].find('{http://www.topografix.com/GPX/1/0}time').text[:-1])

    return data, start_time, end_time


def get_metadata(min_lat, max_lat, min_lon, max_lon, lat_range, lon_range):

    lon_center = lon_range / 2
    lat_center = lat_range / 2

    # lats = []
    # lons = []
    grid, lats, lons = get_lat_lon_grid_fixednbpt(min_lat - lon_range / 2, max_lat + lon_range / 2, min_lon - lat_range / 2 , max_lon + lat_range / 2)

    result = get_mult_ele(grid, "mapzen")

    return result

def plot(gpxdata, metadata, lat_center, lon_center):
    # app.logger.info(metadata)
    lat, lon, z = opentopodata2surfacedata(metadata)

    # Convertion from lat, lon in degrees to x,y in meters.
    x = [-1 * (i - lon_center) * lon2m(lon_center) for i in lat]
    y = [-1 * (i - lat_center) * lat2m(lat_center) for i in lon]

    gpxdata["x"] = [-1 * (i - lon_center) * lon2m(lon_center) for i in gpxdata["lon"]]
    gpxdata["y"] = [-1 * (i - lat_center) * lat2m(lat_center) for i in gpxdata["lat"]]


    fig = go.Figure(data=[go.Surface(x = x, y = y, z = z,
                                    hidesurface = True,
                                    showscale = False,
                                    opacity = 0.75,
                                    contours = {"z": {"show": True, "start": 100, "end": 1700, "size": 100}}),
    go.Scatter3d(x = gpxdata["x"], y = gpxdata["y"], z = gpxdata["ele"],
                text=gpxdata["text"], mode='markers',  marker=dict(
                size=1,
                color="red",
                colorscale='Viridis',
                opacity=0.8
        ))
    ])


    fig.update_scenes(xaxis_visible=False, yaxis_visible=False,zaxis_visible=False )
    fig.update_scenes(aspectmode="data")
    fig.update_scenes(bgcolor='rgba(184, 134, 11,1)')
    fig.update_layout(margin = {"b": 0, 't':0, 'r':0, 'l':0})
    fig.update_layout(width = 400)
    fig.update_layout(height = 400)
    # fig.update_scenes(aspectratio=dict(x = 1, y = 1, z = 1))

    # fig.update_xaxes(visible=False)
    # fig.update_yaxes(visible=False)
    # fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    # fig.update_layout(plot_bgcolor='rgba(0,0,0,0)')
    # fig.update_layout(showlegend=False)



    return fig.to_html(full_html= False)





@app.route("/")
def hello_world():

    plots = []
    global app

    for path in sorted(Path('/gpx').glob('*.gpx')):
        app.logger.info(path)
        filename = str(path)
        gpxdata, start_time, end_time = getdatafromgpx(filename)

        lon_range = max(gpxdata["lon"]) - min(gpxdata["lon"])
        lat_range = max(gpxdata["lat"]) - min(gpxdata["lat"])

        if not Path(filename + ".json").exists():
            metadata = get_metadata(min(gpxdata["lat"]), max(gpxdata["lat"]), min(gpxdata["lon"]), max(gpxdata["lon"]), lat_range, lon_range)
            with open(filename + ".json", 'w') as convert_file:
                app.logger.info(f'writting metadata to {filename + ".json"}')
                convert_file.write(json.dumps(metadata))
        else:
            with open(filename + ".json", 'r') as convert_file:
                metadata = json.load(convert_file)

        p = plot(gpxdata, metadata, lat_range / 2 , lon_range / 2)
        p1 = plot(gpxdata, metadata, lat_range / 2 , lon_range / 2)

        plots.append({"plot": p, "start_time": start_time, "end_time": end_time, "name": path.name})

    return render_template("index.html", plots = plots)