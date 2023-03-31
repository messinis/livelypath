import streamlit as st
import googlemaps
import polyline
import folium
from streamlit_folium import folium_static
import geopy.distance
import openai
import os

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY
API_KEY = os.environ.get("API_KEY")
gmaps = googlemaps.Client(key=API_KEY)

st.set_page_config(layout="wide", page_title="Lively Path")
st.title("Lively Path")

def get_answer_from_chatgpt(prompt):
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.7,
    )

    answer = response.choices[0].text.strip()
    return answer

def point_to_line_distance(point, line_start, line_end):
    numerator = abs((line_end[1] - line_start[1]) * point[0] - (line_end[0] - line_start[0]) * point[1] + line_end[0] * line_start[1] - line_end[1] * line_start[0])
    denominator = geopy.distance.distance(line_start, line_end).m
    return numerator / denominator

import math

def angle_between_steps(step1, step2):
    dy1 = step1['end_location']['lat'] - step1['start_location']['lat']
    dx1 = step1['end_location']['lng'] - step1['start_location']['lng']
    dy2 = step2['end_location']['lat'] - step2['start_location']['lat']
    dx2 = step2['end_location']['lng'] - step2['start_location']['lng']

    angle = math.atan2(dy2, dx2) - math.atan2(dy1, dx1)
    angle = math.degrees(angle)

    # Normalize the angle to the range [0, 360)
    angle = (angle + 360) % 360
    return angle


def cumulative_distance(steps, index):
    distance = 0
    for i in range(index):
        start = (steps[i]['start_location']['lat'], steps[i]['start_location']['lng'])
        end = (steps[i]['end_location']['lat'], steps[i]['end_location']['lng'])
        distance += geopy.distance.distance(start, end).m
    return distance

def route_distance(gmaps, origin, destination, waypoints):
    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="walking",
        waypoints=waypoints,
        optimize_waypoints=True,
    )

    total_distance = 0
    for leg in directions[0]['legs']:
        total_distance += leg['distance']['value']

    return total_distance


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

    # Calculate the total distance of the route without waypoints
    direct_distance = route_distance(gmaps, origin, destination, [])

    # Filter waypoints based on the distance they add to the route
    filtered_waypoints = []
    distance_factor = 1.4  # Adjust this factor to control the distance a waypoint can add to the route

    for waypoint in waypoints:
        new_route_distance = route_distance(gmaps, origin, destination, filtered_waypoints + [waypoint])
        if new_route_distance <= distance_factor * direct_distance:
            filtered_waypoints.append(waypoint)

    # Limit the number of waypoints to 23 to avoid the API's limit
    filtered_waypoints = filtered_waypoints[:23]

    # Get the directions with the filtered waypoints
    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="walking",
        waypoints=filtered_waypoints,
        optimize_waypoints=True,
    )

    best_route = []
    for leg in directions[0]['legs']:
        for step in leg['steps']:
            start = (step['start_location']['lat'], step['start_location']['lng'])
            end = (step['end_location']['lat'], step['end_location']['lng'])
            best_route.append(start)
            best_route.append(end)

    return best_route


# Input origin and destination
with st.form("inputs"):
    origin = st.text_input("Origin Address")
    destination = st.text_input("Destination Address")
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

            # Add markers for origin and destination
            folium.Marker([origin_coords["lat"], origin_coords["lng"]], popup="Origin", icon=folium.Icon(color='green')).add_to(m)
            folium.Marker([destination_coords["lat"], destination_coords["lng"]], popup="Destination", icon=folium.Icon(color='red')).add_to(m)

            for i in range(len(best_route_coords)-1):
                start = best_route_coords[i]
                end = best_route_coords[i+1]
                folium.PolyLine([start, end], color="blue", weight=2.5, opacity=1).add_to(m)
                
            folium_static(m)

            # Get and display the sightseeing attraction near the destination address
            destination_address = destination_geocode[0]['formatted_address']
            question = f"What is one attraction of cultural value, near {destination_address}? Answer only with its name and an one sentence description."
            attraction_info = get_answer_from_chatgpt(question)
            st.markdown(f"**Attraction of Cultural Value Near Destination:** {attraction_info}")

        else:
            st.error("Invalid addresses entered. Please try again.")
    else:
        st.error("Please enter both origin and destination addresses.")

