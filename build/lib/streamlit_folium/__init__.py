from __future__ import annotations

import hashlib
import os
import re
import warnings
from textwrap import dedent
from typing import Iterable

import branca
import folium
import folium.elements
import folium.plugins
import streamlit as st
import streamlit.components.v1 as components
from jinja2 import UndefinedError

# Create a _RELEASE constant. We'll set this to False while we're developing
# the component, and True when we're ready to package and distribute it.
_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "st_folium", url="http://localhost:3001"
    )

else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("st_folium", path=build_dir)


def generate_js_hash(
    js_string: str, key: str | None = None, return_on_hover: bool = False
) -> str:
    """
    Generate a standard key from a javascript string representing a series
    of folium-generated leaflet objects by replacing the hash's at the end
    of variable names (e.g. "marker_5f9d46..." -> "marker"), and returning
    the hash.

    Also strip maps/<random_hash>, which is generated by google earth engine
    """
    pattern = r"(_[a-z0-9]+)"
    standardized_js = re.sub(pattern, "", js_string) + str(key)
    url_pattern = r"(maps\/[-a-z0-9]+\/)"
    standardized_js = (
        re.sub(url_pattern, "", standardized_js) + str(key) + str(return_on_hover)
    )
    s = hashlib.sha256(standardized_js.encode()).hexdigest()
    return s


def folium_static(
    fig: folium.Figure | folium.Map,
    width: int | None = 700,
    height: int = 500,
):
    """
    Renders `folium.Figure` or `folium.Map` in a Streamlit app. This method is
    a static Streamlit Component, meaning, no information is passed back from
    Leaflet on browser interaction.
    Parameters
    ----------
    fig  : folium.Map or folium.Figure
        Geospatial visualization to render
    width : int
        Width of result
    Height : int
        Height of result
    Note
    ----
    If `height` is set on a `folium.Map` or `folium.Figure` object,
    that value supersedes the values set with the keyword arguments of this function.

    Example
    -------
    >>> m = folium.Map(location=[45.5236, -122.6750])
    >>> folium_static(m)
    """
    warnings.warn(
        dedent(
            """
        folium_static is deprecated and will be removed in a future release, or
        simply replaced with with st_folium which always passes
        returned_objects=[] to the component.
        Please try using st_folium instead, and
        post an issue at https://github.com/randyzwitch/streamlit-folium/issues
        if you experience issues with st_folium.
        """
        ),
        DeprecationWarning,
    )
    # if Map, wrap in Figure
    if isinstance(fig, folium.Map):
        fig = folium.Figure().add_child(fig)
        return components.html(
            fig.render(), height=(fig.height or height) + 10, width=width
        )

    # if DualMap, get HTML representation
    elif isinstance(fig, folium.plugins.DualMap) or isinstance(
        fig, branca.element.Figure
    ):
        return components.html(fig._repr_html_(), height=height + 10, width=width)
    return st_folium(fig, width=width, height=height, returned_objects=[])


def _get_siblings(fig: folium.MacroElement) -> str:
    """Get the html for any siblings of the map"""
    children = list(fig.get_root()._children.values())

    html = ""
    if len(children) > 1:
        for child in children[1:]:
            try:
                html += child._template.module.html() + "\n"
            except Exception:
                pass

    return html


def get_full_id(m: folium.MacroElement) -> str:
    if isinstance(m, folium.plugins.DualMap):
        m = m.m1

    return f"{m._name.lower()}_{m._id}"


def _get_map_string(fig: folium.Map) -> str:
    leaflet = generate_leaflet_string(fig)

    # Get rid of the annoying popup
    leaflet = leaflet.replace("alert(coords);", "")

    # Rename drawnItems
    leaflet = leaflet.replace("drawnItems_draw_control_div_1", "drawnItems")

    leaflet = dedent(leaflet)

    if "drawnItems" not in leaflet:
        leaflet += "\nvar drawnItems = [];"

    # Replace the folium generated map_{random characters} variables
    # with map_div and map_div2 (these end up being both the assumed)
    # div id where the maps are inserted into the DOM, and the names of
    # the variables themselves.
    if isinstance(fig, folium.plugins.DualMap):
        m2_id = get_full_id(fig.m2)
        leaflet = leaflet.replace(m2_id, "map_div2")

    return leaflet


def _get_feature_group_string(
    feature_group_to_add: folium.FeatureGroup,
    map: folium.Map,
    idx: int = 0,
) -> str:
    feature_group_to_add._id = f"feature_group_{idx}"
    feature_group_to_add.add_to(map)
    feature_group_to_add.render()
    feature_group_string = generate_leaflet_string(
        feature_group_to_add, base_id=f"feature_group_{idx}"
    )
    m_id = get_full_id(map)
    feature_group_string = feature_group_string.replace(m_id, "map_div")
    feature_group_string = dedent(feature_group_string)

    feature_group_string += dedent(
        f"""
        map_div.addLayer(feature_group_feature_group_{idx});
        window.feature_group = window.feature_group || [];
        window.feature_group.push(feature_group_feature_group_{idx});
        """
    )

    return feature_group_string


def _get_layer_control_string(
    control: folium.LayerControl,
    map: folium.Map,
) -> str:
    control._id = "layer_control"
    control.add_to(map)
    control.render()
    control_string = generate_leaflet_string(control, base_id="layer_control")
    m_id = get_full_id(map)
    control_string = control_string.replace(m_id, "map_div")
    control_string = dedent(control_string)
    control_string += dedent(
        """
        window.layer_control = layer_control_layer_control;
        """
    )

    return control_string


def st_folium(
    fig: folium.MacroElement,
    key: str | None = None,
    height: int = 700,
    width: int | None = 500,
    returned_objects: Iterable[str] | None = None,
    zoom: int | None = None,
    center: tuple[float, float] | None = None,
    feature_group_to_add: list[folium.FeatureGroup] | folium.FeatureGroup | None = None,
    return_on_hover: bool = False,
    use_container_width: bool = False,
    layer_control: folium.LayerControl | None = None,
    pixelated: bool = False,
    debug: bool = False,
    render: bool = True,
    max_drawn_objects: int = 0,
    max_drawn_objects_remove_old: bool = True,
):
    """Display a Folium object in Streamlit, returning data as user interacts
    with app.
    Parameters
    ----------
    fig  : folium.Map or folium.Figure
        Geospatial visualization to render
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.
    returned_objects: Iterable
        A list of folium objects (as keys of the returned dictionart) that will be
        returned to the user when they interact with the map. If None, all folium
        objects will be returned. This is mainly useful for when you only want your
        streamlit app to rerun under certain conditions, and not every time the user
        interacts with the map. If an object not in returned_objects changes on the map,
        the app will not rerun.
    zoom: int or None
        The zoom level of the map. If None, the zoom level will be set to the
        default zoom level of the map. NOTE that if this zoom level is changed, it
        will *not* reload the map, but simply dynamically change the zoom level.
    center: tuple(float, float) or None
        The center of the map. If None, the center will be set to the default
        center of the map. NOTE that if this center is changed, it will *not* reload
        the map, but simply dynamically change the center.
    feature_group_to_add: List[folium.FeatureGroup] or folium.FeatureGroup or None
        If you want to dynamically add features to a feature group, you can pass
        the feature group here. NOTE that if you add a feature to the map, it
        will *not* reload the map, but simply dynamically add the feature.
    return_on_hover: bool
        If True, the app will rerun when the user hovers over the map, not
        just when they click on it. This is useful if you want to dynamically
        update your app based on where the user is hovering. NOTE: This may cause
        performance issues if the app is rerunning too often.
    use_container_width: bool
        If True, set the width of the map to the width of the current container.
        This overrides the `width` parameter.
    layer_control: folium.LayerControl or None
        If you want to have layer control for dynamically added layers, you can
        pass the layer control here.
    pixelated: bool
        If True, add CSS rules to render image crisp pixels which gives a pixelated
        result instead of a blurred image.
    debug: bool
        If True, print out the html and javascript code used to render the map with
        st.code
    render: bool
        If True, the map will be rendered as html, this must be done at least once.
        Disabling this may improve performance as you can cache the rendering step.
        *Note* if this is disabled and the map is not rendered elsewhere the map
        will be missing attributes
    max_drawn_objects: int
        If not 0, this will limit the number of objects drawn on the map using the draw
        tool, by default the oldest object will be removed when we hit the limit,
        Set oldest or newest object or oldest object to delete using max_drawn_objects_remove_old
    max_drawn_objects_remove_old:
        If True, remove the oldest object drawn using the draw tool. If False, the newest
        object drawn will be removed, preventing the user from adding more draw objects
        to the map. Only works then max_drawn_objects is not 0
    Returns
    -------
    dict
        Selected data from Folium/leaflet.js interactions in browser
    """
    # Call through to our private component function. Arguments we pass here
    # will be sent to the frontend, where they'll be available in an "args"
    # dictionary.
    #
    # "default" is a special argument that specifies the initial return
    # value of the component before the user has interacted with it.

    if use_container_width:
        width = None

    folium_map: folium.Map = fig  # type: ignore
    if render:
        folium_map.render()

    # handle the case where you pass in a figure rather than a map
    # this assumes that a map is the first child
    if not (isinstance(fig, folium.Map) or isinstance(fig, folium.plugins.DualMap)):
        folium_map = list(fig._children.values())[0]

    folium_map.render()

    leaflet = _get_map_string(folium_map)  # type: ignore

    html = _get_siblings(folium_map)

    m_id = get_full_id(folium_map)

    def bounds_to_dict(bounds_list: list[list[float]]) -> dict[str, dict[str, float]]:
        southwest, northeast = bounds_list
        return {
            "_southWest": {
                "lat": southwest[0],
                "lng": southwest[1],
            },
            "_northEast": {
                "lat": northeast[0],
                "lng": northeast[1],
            },
        }

    try:
        bounds = folium_map.get_bounds()
    except AttributeError:
        bounds = [[None, None], [None, None]]

    _defaults = {
        "last_clicked": None,
        "last_object_clicked": None,
        "last_object_clicked_tooltip": None,
        "last_object_clicked_popup": None,
        "all_drawings": None,
        "last_active_drawing": None,
        "bounds": bounds_to_dict(bounds),
        "zoom": folium_map.options.get("zoom")
        if hasattr(folium_map, "options")
        else {},
        "last_circle_radius": None,
        "last_circle_polygon": None,
    }

    # If the user passes a custom list of returned objects, we'll only return those

    defaults = {
        k: v
        for k, v in _defaults.items()
        if returned_objects is None or k in returned_objects
    }

    # Convert the feature group to a javascript string which can be used to create it
    # on the frontend.
    feature_group_string = None
    if feature_group_to_add is not None:
        if isinstance(feature_group_to_add, folium.FeatureGroup):
            feature_group_to_add = [feature_group_to_add]
        feature_group_string = ""
        for idx, feature_group in enumerate(feature_group_to_add):
            feature_group_string += _get_feature_group_string(
                feature_group,
                map=folium_map,
                idx=idx,
            )

    layer_control_string = None
    if layer_control is not None:
        layer_control_string = _get_layer_control_string(layer_control, folium_map)

    if debug:
        with st.expander("Show generated code"):
            if html:
                st.info("HTML:")
                st.code(html)

            st.info("Main Map Leaflet js:")
            st.code(leaflet)

            if feature_group_string is not None:
                st.info("Feature group js:")
                st.code(feature_group_string)

            if layer_control_string is not None:
                st.info("Layer control js:")
                st.code(layer_control_string)

    def walk(fig):
        if isinstance(fig, branca.colormap.ColorMap):
            yield fig
        if isinstance(fig, folium.plugins.DualMap):
            yield from walk(fig.m1)
            yield from walk(fig.m2)
        if isinstance(fig, folium.elements.JSCSSMixin):
            yield fig
        if hasattr(fig, "_children"):
            for child in fig._children.values():
                yield from walk(child)

    css_links: list[str] = []
    js_links: list[str] = []

    for elem in walk(folium_map):
        if isinstance(elem, branca.colormap.ColorMap):
            # manually add d3.js
            js_links.insert(
                0, "https://cdnjs.cloudflare.com/ajax/libs/d3/3.5.5/d3.min.js"
            )
            js_links.insert(0, "https://d3js.org/d3.v4.min.js")
        css_links.extend([href for _, href in getattr(elem, "default_css", [])])
        js_links.extend([src for _, src in getattr(elem, "default_js", [])])

    component_value = _component_func(
        script=leaflet,
        html=html,
        id=m_id,
        key=generate_js_hash(leaflet, f"{key}_{max_drawn_objects}", return_on_hover),
        height=height,
        width=width,
        returned_objects=returned_objects,
        default=defaults,
        zoom=zoom,
        center=center,
        feature_group=feature_group_string,
        return_on_hover=return_on_hover,
        layer_control=layer_control_string,
        pixelated=pixelated,
        css_links=css_links,
        js_links=js_links,
        max_drawn_objects=max_drawn_objects,
        max_drawn_objects_remove_old=max_drawn_objects_remove_old,
    )

    return component_value


def _generate_leaflet_string(
    m: folium.MacroElement,
    nested: bool = True,
    base_id: str = "0",
    mappings: dict[str, str] | None = None,
) -> tuple[str, dict[str, str]]:
    if mappings is None:
        mappings = {}

    mappings[m._id] = base_id
    try:
        element_id = m.element_name.replace("map_", "").replace("tile_layer_", "")
        parent_id = m.element_parent_name.replace("map_", "").replace("tile_layer_", "")
        if element_id not in mappings:
            mappings[element_id] = m._parent._id
        if parent_id not in mappings:
            mappings[parent_id] = m._parent._parent._id
    except AttributeError:
        pass

    m._id = base_id

    if isinstance(m, folium.plugins.DualMap):
        m.render()
        m.m1.render()
        m.m2.render()
        if not nested:
            return _generate_leaflet_string(
                m.m1, nested=False, mappings=mappings, base_id=base_id
            )
        # Generate the script for map1
        leaflet, _ = _generate_leaflet_string(
            m.m1, nested=nested, mappings=mappings, base_id=base_id
        )
        # Add the script for map2
        leaflet += (
            "\n"
            + _generate_leaflet_string(
                m.m2, nested=nested, mappings=mappings, base_id="div2"
            )[0]
        )
        # Add the script that syncs them together
        leaflet += m._template.module.script(m)
        return leaflet, mappings

    try:
        leaflet = m._template.module.script(m)
    except UndefinedError:
        # Correctly render Popup elements, and perhaps others. Not sure why
        # this is necessary. Some deep magic related to jinja2 templating, perhaps.
        leaflet = m._template.render(this=m, kwargs={})

    if not nested:
        return leaflet, mappings

    for idx, child in enumerate(m._children.values()):
        try:
            leaflet += (
                "\n"
                + _generate_leaflet_string(
                    child, base_id=f"{base_id}_{idx}", mappings=mappings
                )[0]
            )
        except (UndefinedError, AttributeError):
            pass

    return leaflet, mappings


_FOLIUM_VAR_SUFFIX_PATTERN = re.compile("_[a-z0-9]+(?!_)")


def _replace_folium_vars(leaflet: str, mappings: dict[str, str]) -> str:
    def replace(match: re.Match):
        match_str = match.group()
        leaflet_id = match_str.strip("_")
        replacement = mappings.get(leaflet_id)
        if replacement:
            match_str = match_str.replace(leaflet_id, replacement)
        return match_str

    return _FOLIUM_VAR_SUFFIX_PATTERN.sub(replace, leaflet)


def generate_leaflet_string(
    m: folium.MacroElement, nested: bool = True, base_id: str = "div"
) -> str:
    """
    Call the _generate_leaflet_string function, and then replace the
    folium generated var {thing}_{random characters} variables with
    standardized variables, in case any didn't already get replaced
    (e.g. in the case of a LayerControl, it still has a reference
    to the old variable for the tile_layer_{random_characters}).

    This also allows the output to be more testable, since the
    variable names are consistent.
    """
    leaflet, mappings = _generate_leaflet_string(m, nested=nested, base_id=base_id)

    leaflet = _replace_folium_vars(leaflet, mappings)

    return leaflet