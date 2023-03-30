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



def get_best_route(gmaps, origin, destination):
    busy_places_types = ['cafe', 'bar', 'restaurant']
    busy_places_radius = 500  # Increase the radius to cover a larger area

    waypoints = []

    # Calculate the straight-line distance between origin and destination
    straight_distance = geopy.distance.distance((origin['lat'], origin['lng']), (destination['lat'], destination['lng'])).m

    # Determine the number of waypoints based on the desired interval (e.g., one waypoint every 100 meters)
    waypoint_interval = 100
    num_waypoints = min(int(straight_distance / waypoint_interval), 23)

    for place_type in busy_places_types:
        busy_places = gmaps.places_nearby(
            location=origin,
            radius=busy_places_radius,
            type=place_type,
        )

        waypoints_per_type = []
        for place in busy_places['results']:
            lat = place['geometry']['location']['lat']
            lng = place['geometry']['location']['lng']
            waypoint = (lat, lng)

            distance_from_route = point_to_line_distance(waypoint, (origin['lat'], origin['lng']), (destination['lat'], destination['lng']))
            rating = place.get("rating", 0)

            # Calculate a score based on distance from the direct route and rating
            distance_weight = 3  # Adjust this value to find the best balance between distance and rating
            score = (1 / (1 + distance_from_route)) ** distance_weight * rating
            waypoints_per_type.append((waypoint, score))

        # Sort waypoints by score (in descending order) and keep the top waypoints for each place type
        waypoints_per_type.sort(key=lambda x: x[1], reverse=True)
        waypoints.extend(waypoints_per_type[:num_waypoints])

    # Sort waypoints by score (in descending order) and keep the top num_waypoints
    waypoints.sort(key=lambda x: x[1], reverse=True)
    waypoints = [f"{wp[0][0]},{wp[0][1]}" for wp in waypoints[:num_waypoints]]

    directions = gmaps.directions(
        origin=origin,
        destination=destination,
        mode="walking",
        waypoints=waypoints,
        optimize_waypoints=True,
    )

    best_route = []
    legs_steps = [step for leg in directions[0]['legs'] for step in leg['steps']]
    total_distance = sum([geopy.distance.distance((step['start_location']['lat'], step['start_location']['lng']),
                                                (step['end_location']['lat'], step['end_location']['lng'])).m
                        for step in legs_steps])

    for i in range(len(legs_steps)):
        step = legs_steps[i]
        start = (step['start_location']['lat'], step['start_location']['lng'])
        end = (step['end_location']['lat'], step['end_location']['lng'])

        # Calculate the cumulative distance of the step along the route
        cum_distance = cumulative_distance(legs_steps, i)

        # Calculate the straight-line distance between the origin and the end location of the step
        straight_distance_to_end = geopy.distance.distance((origin['lat'], origin['lng']), end).m

        # Skip the step if the cumulative distance is much greater than the straight-line distance to the end location
        if cum_distance > 1.5 * straight_distance_to_end and cum_distance < 0.9 * total_distance:
            continue

        best_route.append(start)
        best_route.append(end)


    # Return the list of coordinates making up the best route
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
            question = f"What is one historical sightseeing attraction, near {destination_address}? Answer only with the name of the attraction and a one-sentence description."
            attraction_info = get_answer_from_chatgpt(question)
            st.markdown(f"**Sightseeing Attraction Near Point B:** {attraction_info}")

        else:
            st.error("Invalid addresses entered. Please try again.")
    else:
        st.error("Please enter both origin and destination addresses.")

