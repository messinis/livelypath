import streamlit as st
import googlemaps
import polyline
import folium
from streamlit_folium import folium_static
import geopy.distance

import os

API_KEY = os.environ.get("API_KEY")
gmaps = googlemaps.Client(key=API_KEY)

st.set_page_config(layout="wide", page_title="Busy Path Finder")
st.title("Lively Path")

def get_best_route(gmaps, origin, destination):
    busy_places_types = ['cafe', 'bar', 'restaurant']
    busy_places_radius = 200  # Adjust the radius as needed

    waypoints = []

    for place_type in busy_places_types:
        busy_places = gmaps.places_nearby(
            location=origin,
            radius=busy_places_radius,
            type=place_type,
        )

        for place in busy_places['results']:
            lat = place['geometry']['location']['lat']
            lng = place['geometry']['location']['lng']
            waypoint = f"{lat},{lng}"
            waypoints.append(waypoint)

    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="walking",
        waypoints=waypoints,
        optimize_waypoints=True,
    )

    best_route = []
    for leg in directions[0]['legs']:
        for step in leg['steps']:
            start = (step['start_location']['lat'], step['start_location']['lng'])
            end = (step['end_location']['lat'], step['end_location']['lng'])
            segment_length = geopy.distance.distance(start, end).m
            if segment_length > 100:  # Only include segments longer than 100m
                best_route.append(start)
            best_route.append(end)
    
    # Return the list of coordinates making up the best route
    return best_route

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

            best_route_coords = get_best_route(gmaps, origin_coords, destination_coords)

            # Display the map with the best route
            m = folium.Map(location=[origin_coords["lat"], origin_coords["lng"]], zoom_start=14)

            for i in range(len(best_route_coords)-1):
                start = best_route_coords[i]
                end = best_route_coords[i+1]
                folium.PolyLine([start, end], color="blue", weight=2.5, opacity=1).add_to(m)
                
            folium_static(m)
        else:
            st.error("Invalid addresses entered. Please try again.")
    else:
        st.error("Please enter both origin and destination addresses.")
