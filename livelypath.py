import requests
import streamlit as st
import googlemaps
import polyline
import folium
from streamlit_folium import folium_static

import os
API_KEY = os.environ.get("API_KEY")

gmaps = googlemaps.Client(key=API_KEY)

st.set_page_config(layout="wide", page_title="Busy Path Finder")
st.title("Busy Path Finder")

def get_best_route(origin, destination, api_key):
    places_types = ['cafe', 'bar', 'restaurant']
    places_ranking = "prominence"
    waypoints = []

    for place_type in places_types:
        result = requests.get(f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={origin["lat"]},{origin["lng"]}&radius=1000&type={place_type}&rankby={places_ranking}&key={api_key}').json()

        if result.get('results'):
            waypoints.append(result['results'][0]['geometry']['location'])

    waypoints_str = [f'{wp["lat"]},{wp["lng"]}' for wp in waypoints]
    directions_result = gmaps.directions(origin=f'{origin["lat"]},{origin["lng"]}',
                                         destination=f'{destination["lat"]},{destination["lng"]}',
                                         mode="walking",
                                         waypoints=waypoints_str,
                                         optimize_waypoints=True)

    return directions_result[0]

# Input origin and destination
with st.form("inputs"):
    origin = st.text_input("Origin Address (Point A)")
    destination = st.text_input("Destination Address (Point B)")
    submitted = st.form_submit_button("Find Best Route")

if submitted:
    if origin and destination:
        # Geocode the origin and destination addresses
        origin_geocode = gmaps.geocode(origin)
        destination_geocode = gmaps.geocode(destination)

        if origin_geocode and destination_geocode:
            origin_coords = origin_geocode[0]['geometry']['location']
            destination_coords = destination_geocode[0]['geometry']['location']

            best_route = get_best_route(origin_coords, destination_coords, API_KEY)

            # Display the map with the best route
            map_data = polyline.decode(best_route["overview_polyline"]["points"])
            m = folium.Map(location=[origin_coords["lat"], origin_coords["lng"]], zoom_start=14)

            folium.PolyLine(map_data, color="blue", weight=2.5, opacity=1).add_to(m)
            folium_static(m)
        else:
            st.error("Invalid addresses entered. Please try again.")
    else:
        st.error("Please enter both origin and destination addresses.")
