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

import geopy.distance

def get_best_route(gmaps, origin, destination):
    busy_places_types = ['cafe', 'bar', 'restaurant']
    busy_places_radius = 200  # Adjust the radius as needed
    min_segment_length = 100  # Adjust the minimum segment length as needed

    waypoints = []
    segment_start = origin
    route_segments = []

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
    )

    # Split the route into segments based on the distance between waypoints
    for i, leg in enumerate(directions[0]['legs']):
        for j, step in enumerate(leg['steps']):
            start = (step['start_location']['lat'], step['start_location']['lng'])
            end = (step['end_location']['lat'], step['end_location']['lng'])
            distance = geopy.distance.distance(segment_start, end).m

            if distance > min_segment_length:
                route_segments.append((segment_start, start))
                segment_start = start

    route_segments.append((segment_start, destination_coords))

    # Calculate the route through the segments
    route_waypoints = []

    for segment_start, segment_end in route_segments:
        segment_directions = gmaps.directions(
            origin=f"{segment_start[0]},{segment_start[1]}",
            destination=f"{segment_end[0]},{segment_end[1]}",
            mode="walking",
            waypoints=waypoints,
        )

        for i, leg in enumerate(segment_directions[0]['legs']):
            for j, step in enumerate(leg['steps']):
                for point in polyline.decode(step['polyline']['points']):
                    route_waypoints.append((point[0], point[1]))

    # Return the route as a list of (latitude, longitude) tuples
    return route_waypoints


# def get_best_route(gmaps, origin, destination):
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
    )

 # Return the first route in the list of directions
    return directions[0]


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

            best_route = get_best_route(gmaps, origin_coords, destination_coords)
            print(best_route)
            map_data = polyline.decode(best_route["overview_polyline"]["points"])
            print(map_data)

            # Display the map with the best route
            map_data = polyline.decode(best_route["overview_polyline"]["points"])
            m = folium.Map(location=[origin_coords["lat"], origin_coords["lng"]], zoom_start=14)

            folium.PolyLine(map_data, color="blue", weight=2.5, opacity=1).add_to(m)
            folium_static(m)
        else:
            st.error("Invalid addresses entered. Please try again.")
    else:
        st.error("Please enter both origin and destination addresses.")
