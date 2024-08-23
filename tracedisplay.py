import xml.etree.ElementTree as ET
from math import cos
import requests
from time import sleep
from pathlib import Path
import json

def lat2m(latitude):
    return 111132.92-559.82 * cos(2 * latitude) + 1.175 * cos(4*latitude) - 0.0023 * cos(6 * latitude)

def lon2m(longitude):
    return 111412.84 * cos(longitude) - 93.5 * cos(3 * longitude) + 0.118 * cos(5 * longitude)

def get_mult_ele(locations, dataset):
    print(len(locations))
    data = {"results": []}
    n = 100
    for sublocs in [locations[i:i+n] for i in range(0, len(locations), n)]:
        sleep(1)
        print(len(sublocs))
        result = get_opentopo_ele(sublocs, dataset)
        data["results"].extend(result["results"])
    return data

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

filename = "/gpx/20240819.gpx"

tree = ET.parse(filename)
root = tree.getroot()

trk = root.find('{http://www.topografix.com/GPX/1/0}trk')
seg = trk.find('{http://www.topografix.com/GPX/1/0}trkseg')

data = {"lat":[], "lon":[], "text":[], "ele": [], "src": []}

max_lon = None
min_lon = None
max_lat = None
min_lat = None

for child in seg:
    lat = float(child.get('lat'))
    lon = float(child.get('lon'))

    if not max_lat or lat > max_lat: max_lat = lat
    if not min_lat or lat < min_lat: min_lat = lat
    if not max_lon or lon > max_lon: max_lon = lon
    if not min_lon or lon < min_lon: min_lon = lon

    # data["lat"].append(lat2m(lat))
    # data["lon"].append(lon2m(lon))

    data["lat"].append(lat)
    data["lon"].append(lon)
    data["ele"].append(float(child.find('{http://www.topografix.com/GPX/1/0}ele').text))
    data["text"].append(child.find('{http://www.topografix.com/GPX/1/0}time').text)
    data["src"].append("red")
    # print(child.attrib)


xsize = max(data["lat"]) - min(data["lat"])


ysize = max(data["lon"]) - min(data["lon"])
# print("trace size", xsize, ysize)

# print(min(data["lat"]) , max(data["lat"]) , min(data["lon"]) , max(data["lon"]) )

# print(min(data["lat"]) - xsize / 2, max(data["lat"]) + xsize / 2, min(data["lon"]) - ysize / 2 , max(data["lon"]) + ysize / 2)

lats = []
lons = []
grid, lats, lons = get_lat_lon_grid(min(data["lat"]) - xsize / 2, max(data["lat"]) + xsize / 2, min(data["lon"]) - ysize / 2 , max(data["lon"]) + ysize / 2)

if not Path(filename + ".json").exists():

    result = get_mult_ele(grid, "mapzen")
    with open(filename + ".json", 'w') as convert_file: 
        convert_file.write(json.dumps(result))

else:
    with open(filename + ".json", 'r') as convert_file:
        result = json.load(convert_file)


x,y,z = opentopodata2surfacedata(result)



# elevs = []
# for la in lats:
#     for lo in lons:
#         if len(elevs) == 0 or len(elevs[-1]) == len(lats):
#             elevs.append([])
#         elev = find_elev(la, lo, result)
#         print(elev)
#         elevs[-1].append(elev)

# data = {"lat":[], "lon":[], "text":[], "ele": [], "src": []}


# data["lat"].extend(result["lat"])
# data["lon"].extend(result["lon"])
# data["ele"].extend(result["ele"])
# data["src"].extend(["grey"] * len(result["lat"]))

# elx = [x["longitude"] for x in el["results"]]
# ely = [x["latitude"] for x in el["results"]]
# elz = [x["elevation"] for x in el["results"]]

import plotly.graph_objects as go


#fig = go.Figure(data=go.Scatter3d(x=elx, y=ely, z=elz, mode='markers'))


fig = go.Figure(data=[go.Surface(x = x, y = y, z = z, hidesurface = True, opacity = 0.75, contours = {"z": {"show": True, "start": 100, "end": 1700, "size": 100}}),
go.Scatter3d(x = data["lon"], y = data["lat"], z = data["ele"]
, text=data["text"], mode='markers',  marker=dict(
        size=1,
        color=data["src"],                # set color to an array/list of desired values
        colorscale='Viridis',   # choose a colorscale
        opacity=0.8
    ))])

fig.update_yaxes(scaleanchor='x')

fig.write_html("/gpx/file.html")
