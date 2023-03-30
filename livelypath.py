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


def get_best_route(gmaps, origin, destination):
    busy_places_types = ['cafe', 'bar', 'restaurant']
    busy_places_radius = 200  # Adjust the radius as needed

    # Get the route between the origin and destination
    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="walking",
    )

    # Extract the polyline representing the route
    route_polyline = directions[0]["overview_polyline"]["points"]
    route_points = polyline.decode(route_polyline)

    # Select waypoints based on nearby busy places
    waypoints = []
    for i in range(len(route_points) - 1):
        segment_start = route_points[i]
        segment_end = route_points[i + 1]
        segment_length = geopy.distance.distance(segment_start, segment_end).m

        for place_type in busy_places_types:
            busy_places = gmaps.places_nearby(
                location=segment_start,
                radius=min(busy_places_radius, segment_length),
                type=place_type,
            )

            if not busy_places["results"]:
                continue

            # Select the closest place along the segment
            closest_place = min(
                busy_places["results"],
                key=lambda place: geopy.distance.distance(
                    (place["geometry"]["location"]["lat"], place["geometry"]["location"]["lng"]),
                    segment_start,
                ).m,
            )

            lat = closest_place["geometry"]["location"]["lat"]
            lng = closest_place["geometry"]["location"]["lng"]
            waypoint = f"{lat},{lng}"
            waypoints.append(waypoint)

    # Get the best route with the selected waypoints
    best_route = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="walking",
        waypoints=waypoints,
    )[0]

    return best_route


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
