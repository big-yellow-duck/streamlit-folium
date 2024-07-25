import streamlit as st

st.set_page_config(
    page_title="streamlit-folium documentation: Draw Support",
    page_icon=":pencil:",
    layout="wide",
)

"""
# streamlit-folium: Draw Support

Folium supports some of the [most popular leaflet
plugins](https://python-visualization.github.io/folium/plugins.html). In this example,
we can add the
[`Draw`](https://python-visualization.github.io/folium/plugins.html#folium.plugins.Draw)
plugin to our map, which allows for drawing geometric shapes on the map.

When a shape is drawn on the map, the coordinates that represent that shape are passed
back as a geojson feature via the `all_drawings` and `last_active_drawing` data fields.

Draw something below to see the return value back to Streamlit!

You can specify the max drawn objects to limit the maximum number of features drawn on
the map.
The oldest drawn item will be removed when you reach the limit.

You can now set the keep items on map function to maintain a minimum number of drawn
items
on the map even after deleting them.

by default will keep the oldest item drawn on the map when using "Clear all"

Set the limit to 0 for no limit.
"""

with st.echo(code_location="below"):
    import folium
    import streamlit as st
    from folium.plugins import Draw

    from streamlit_folium import st_folium

    m = folium.Map(location=[39.949610, -75.150282], zoom_start=5)
    Draw(export=True).add_to(m)

    c1, c2 = st.columns(2)

    with c1:
        max_drawn_objects = st.number_input("max drawn objects", 0, 3, 0)
        keep_items_on_map = st.number_input("keep items on map", 0, 3, 0)
        output = st_folium(
            m,
            width=700,
            height=500,
            max_drawn_objects=max_drawn_objects,
            keep_items_on_map=keep_items_on_map,
        )

    with c2:
        st.write(output)
