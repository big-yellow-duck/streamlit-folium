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
        output = st_folium(
            m, width=700, height=500, max_drawn_objects=max_drawn_objects
        )

    with c2:
        st.write(output)
