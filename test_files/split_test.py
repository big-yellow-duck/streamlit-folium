import json
from typing import Dict, List, Tuple, Union

import folium

# import folium.plugins
import folium.plugins
import folium.plugins.draw
import streamlit as st

# from apollo.utils.folium import InputDraw
from streamlit_folium import st_folium


def polylines_intersect_with_details(line1, line2):
    """
    Check if two polylines intersect and provide details about the intersections.

    :param line1: A list of points [(x1, y1), (x2, y2), ...] representing the first polyline
    :param line2: A list of points [(x3, y3), (x4, y4), ...] representing the second polyline
    :return: A list of tuples, each containing:
             (index of segment in line1, index of segment in line2, intersection point)
             Returns an empty list if no intersections are found.
    """

    def line_segment_intersect(p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if den == 0:  # parallel lines
            return None

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den

        if 0 <= ua <= 1 and 0 <= ub <= 1:
            # Calculate the intersection point
            x = x1 + ua * (x2 - x1)
            y = y1 + ua * (y2 - y1)
            return (x, y)

        return None

    intersections = []

    # Check each segment of line1 against each segment of line2
    for i in range(len(line1) - 1):
        for j in range(len(line2) - 1):
            intersection = line_segment_intersect(
                line1[i], line1[i + 1], line2[j], line2[j + 1]
            )
            if intersection:
                intersections.append((i, j, intersection))

    return intersections


def polylines_intersect_and_split(line1, line2, split_on_intersection: bool = False):
    """
    Check if two polylines intersect, and if line1 can be split into two segments.

    :param line1: A list of points [[x1, y1], [x2, y2], ...] representing the first polyline
    :param line2: A list of points [[x3, y3], [x4, y4], ...] representing the second polyline
    :param split_on_intersection: If True, the split point will be the intersection point.
                                  If False, the split will occur at the nearest vertex of line1.
    :return: A dictionary containing:
             - 'intersections': List of intersection details (index in line1, index in line2, intersection point)
             - 'can_split': Boolean indicating if line1 can be split
             - 'first_segment': List of points for the first segment if split is possible
             - 'second_segment': List of points for the second segment if split is possible
             Returns empty lists for segments if split is not possible.
    """

    def line_segment_intersect(p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        den = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)
        if den == 0:  # parallel lines
            return None

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / den
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / den

        if 0 <= ua <= 1 and 0 <= ub <= 1:
            # Calculate the intersection point
            x = x1 + ua * (x2 - x1)
            y = y1 + ua * (y2 - y1)
            return [x, y]

        return None

    intersections = []

    # Check each segment of line1 against each segment of line2
    for i in range(len(line1) - 1):
        for j in range(len(line2) - 1):
            intersection = line_segment_intersect(
                line1[i], line1[i + 1], line2[j], line2[j + 1]
            )
            if intersection:
                intersections.append((i, j, intersection))

    result = {
        "intersections": intersections,
        "can_split": False,
        "first_segment": [],
        "second_segment": [],
    }

    if intersections:
        # Check if we can split the line (not on first or last segment)
        if 0 < intersections[0][0] < len(line1) - 2:
            result["can_split"] = True
            split_index = intersections[0][0]

            if split_on_intersection:
                split_point = intersections[0][2]
                result["first_segment"] = line1[: split_index + 1] + [split_point]
                result["second_segment"] = [split_point] + line1[split_index + 1 :]
            else:
                result["first_segment"] = line1[: split_index + 1]
                result["second_segment"] = line1[split_index + 1 :]

    return result


def parse_lines_from_json(json_data):
    """
    Parse line coordinates from the given JSON data.

    :param json_data: A string containing JSON data or a dictionary
    :return: A list of lines, where each line is a list of coordinate pairs
    """
    # If json_data is a string, parse it into a dictionary
    if isinstance(json_data, str):
        data = json.loads(json_data)
    else:
        data = json_data

    lines = []

    # Extract lines from 'all_drawings'
    for drawing in data.get("all_drawings", []):
        if drawing["geometry"]["type"] == "LineString":
            coordinates = drawing["geometry"]["coordinates"]
            # Convert coordinates to the format expected by our intersection function
            line = [(coord[0], coord[1]) for coord in coordinates]
            lines.append(line)

    return lines


m = folium.Map(location=[39.949610, -75.150282], zoom_start=16)
# InputDraw(
#     point_coords=[39.949610, -75.150282],
#     polygon_coords=None,
#     polyline_coords=None,
# ).add_to(m)
folium.plugins.Draw().add_to(m)
folium.Marker([39.949610, -75.150282], tooltip="folium point").add_to(m)

st.title("create a a map")

map_columns = st.columns(2)

with map_columns[0]:
    map_out = st_folium(
        m,
        # max_drawn_objects=3,
    )
    pass

with map_columns[1]:
    pass
    st.write(map_out)

    if map_out is not None:
        mylines = parse_lines_from_json(map_out)
        # print(mylines)
        if len(mylines) == 2:
            # intersect_bool = polylines_intersect_with_details(mylines[0], mylines[1])

            intersect_results = polylines_intersect_and_split(
                mylines[0],
                mylines[1],
            )

            # print(mylines)

            print('intersect out: ',intersect_results)

            # if intersect_bool[0][0] == 0 or intersect_bool[0][0] == len(mylines[0])-2:
            #     print(' leave 1 segment for beginning')
            # else:
            #     print('can cut')
            #     # first segment
            #     first_segment  = mylines[0][:intersect_bool[0][0]+1]
            #     second_segment = mylines[0][intersect_bool[0][0]+1: ]
            #     print('first segment: ', first_segment)
            #     print('second segment: ', second_segment)
