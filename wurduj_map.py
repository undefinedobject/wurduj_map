import requests
import pandas as pd
import matplotlib
import folium
from folium.plugins import MarkerCluster
import json
import geojson
import geopandas as gpd

wd = "" #Set Working Directory

#Get Wurduj District Boundaries from OSM using Overpass API
#Retrieve Wurduj Boundaries
overpass_url = "http://overpass-api.de/api/interpreter"

query = """
[out:json];
relation(6564595);
out geom;
"""

response = requests.get(overpass_url, params={'data': query})
wurduj_rel = requests.get(overpass_url, params={'data': query}).json()

#Find boundaries
minlat = wurduj_rel['elements'][0]['bounds']['minlat']
minlon = wurduj_rel['elements'][0]['bounds']['minlon']
maxlat = wurduj_rel['elements'][0]['bounds']['maxlat']
maxlon = wurduj_rel['elements'][0]['bounds']['maxlon']

#Read Wurduj JSON
osmWurdujPath = wd + "wurduj.json"
f = open(osmWurdujPath, "r")
wurduj_geojson = json.load(f)
f.close()

#Read data collected from streetview
streetviewFp = wd + "streetview_wardooj.csv"
wurduj_villages = pd.read_csv(streetviewFp)

#Create geopandas GeoDataFrame 
wurdujGeo = gpd.GeoDataFrame()
for col in wurduj_villages.columns:
    wurdujGeo[col] = wurduj_villages[col]

villagePoints = [geojson.Point([wurdujGeo['lon'][i],wurdujGeo['lat'][i]]) for i in range(len(wurdujGeo))]
wurdujGeo.set_geometry(villagePoints, inplace=True)

#Set CRS
wurdujGeo.crs = "epsg:4326"
wurdujGeo = wurdujGeo.to_crs(epsg='4326')

#Initialize Map
#Define coordinates of where we want to center our map
centre = [(minlat+maxlat)/2, (minlon+maxlon)/2]
#Create the map
my_map = folium.Map(location = centre, zoom_start = 10)

#Add Wurduj Border to Map
wurdujBorderLayer = folium.GeoJson(wurduj_geojson,
                    style_function=lambda feature:{
                            'fillColor': 'yellow',
                            'color': 'black',
                            'weight': 2,
                            'fillOpacity': 0.3,
                            },
                    name="Warduj District Border").add_to(my_map)

# Define a function to create custom markers for point features
def point_to_layer(feature, latlng, tooltip_text, color):
    icon = folium.Icon(color=color) 
    return folium.Marker(location=latlng, icon=icon, tooltip=tooltip_text)

#Add NotInSample Layer
# Create a feature group to hold the markers
notInSampleGroup = folium.FeatureGroup(name="Not In Sample")

# Add customized markers
for _, row in wurdujGeo[wurdujGeo.in_sample == 0].iterrows():
    marker = point_to_layer(None, [row['geometry'].y, row['geometry'].x],
                           row['village'], 'red')
    marker.add_to(notInSampleGroup)

addedNotInSampleGroup = notInSampleGroup.add_to(my_map)

#Add InSample Layer
# Create a feature group to hold the markers
inSampleGroup = folium.FeatureGroup(name="In Sample")

# Add customized markers
for _, row in wurdujGeo[wurdujGeo.in_sample == 1].iterrows():
    marker = point_to_layer(None, [row['geometry'].y, row['geometry'].x],
                           row['village']+" | "+"Beneficiaries: "+str(int(row['atr_num_benef'])),
                           'green')
    marker.add_to(inSampleGroup)

addedInSampleGroup = inSampleGroup.add_to(my_map)

#Add Layer Control
addLayerControl = folium.LayerControl().add_to(my_map)

#Save map as HTML file
saveFp = "wardooj_beneficiaries_map.html"
my_map.save(saveFp)