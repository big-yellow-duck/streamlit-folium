from __future__ import annotations

from typing import Union

from branca.element import Element, Figure, MacroElement
from folium.elements import JSCSSMixin
from jinja2 import Template


class InputDraw(JSCSSMixin, MacroElement):
    """
    Point and vector drawing and editing plugin for Leaflet.

    Examples:

    ```python
    m = folium.Map()
    Draw(
        export=True,
        filename="my_data.geojson",
        position="topleft",
        draw_options={"polyline": {"allowIntersection": False}},
        edit_options={"poly": {"allowIntersection": False}},
    ).add_to(m)
    ```

    For more info please check
    https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html

    """

    _template = Template(
        """
        {% macro script(this, kwargs) %}
            var options = {
              position: {{ this.position|tojson }},
              draw: {{ this.draw_options|tojson }},
              edit: {{ this.edit_options|tojson }},
            }
            // FeatureGroup is to store editable layers.
            var orangeIcon = new L.Icon({
                iconUrl: 'https://autoecm-qc.akirakan.com/icons/teardrop-outline-orange.png',
                shadowUrl: null,
                iconSize: [40, 40],
                iconAnchor: [20, 40],
                popupAnchor: null,
                shadowSize: null,
                zIndexOffset: -100000
            });

            var points = [
                {%- for feature in this.point_coords %}
                    new L.marker({{ feature|tojson }}, {icon: orangeIcon}),
                {% endfor %}
            ]
            var polylines = [
                {%- for feature in this.polyline_coords %}
                    new L.Polyline({{ feature| tojson }}, {color: "#e99b48"}),
                {% endfor %}
            ]
            var polygons = [
                {%- for feature in this.polygon_coords %}
                    new L.Polygon({{ feature|tojson }}, {color: "#e99b48"}),
                {% endfor %}
            ]
            var drawnItems = new L.featureGroup(
                points.concat(polylines).concat(polygons)
            ).addTo(
                {{ this._parent.get_name() }}
            );
            options.edit.featureGroup = drawnItems;
            var {{ this.get_name() }} = new L.Control.Draw(
                options
            ).addTo( {{this._parent.get_name()}} );
            {{ this._parent.get_name() }}.on(L.Draw.Event.CREATED, function(e) {
                var layer = e.layer,
                    type = e.layerType;
                var coords = JSON.stringify(layer.toGeoJSON());
                {%- if this.show_geometry_on_click %}
                layer.on('click', function() {
                    alert(coords);
                    console.log(coords);
                });
                {%- endif %}
                drawnItems.addLayer(layer);
             });
            {{ this._parent.get_name() }}.on('draw:created', function(e) {
                drawnItems.addLayer(e.layer);
            });
            {% if this.export %}
            document.getElementById('export').onclick = function(e) {
                var data = drawnItems.toGeoJSON();
                var convertedData = 'text/json;charset=utf-8,'
                    + encodeURIComponent(JSON.stringify(data));
                document.getElementById('export').setAttribute(
                    'href', 'data:' + convertedData
                );
                document.getElementById('export').setAttribute(
                    'download', {{ this.filename|tojson }}
                );
            }
            {% endif %}
        {% endmacro %}
        """
    )

    default_js = [
        (
            "leaflet_draw_js",
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.2/leaflet.draw.js",
        )
    ]
    default_css = [
        (
            "leaflet_draw_css",
            "https://cdnjs.cloudflare.com/ajax/libs/leaflet.draw/1.0.2/leaflet.draw.css",
        )
    ]

    def __init__(
        self,
        point_coords: Union[list, None] = None,
        polyline_coords: Union[list, None] = None,
        polygon_coords: Union[list, None] = None,
        export: bool = False,
        filename: str = "data.geojson",
        position: str = "topleft",
        show_geometry_on_click: bool = True,
        draw_options: Union[dict, None] = None,
        edit_options: Union[dict, None] = None,
    ):
        """
        Point and vector drawing and editing plugin for Leaflet.

        Parameters
        ----------

        Args:
            point_coords (Union[list, None], optional): List of point coordinates.
                Should be a list of [x, y] coordinates. Defaults to None.
            polyline_coords (Union[list, None], optional): List of polyline coordinates.
                Should be a list of list of [x, y] coordinates. Defaults to None.
            polygon_coords (Union[list, None], optional): List of polygon coordinates.
                Should be a list of list of [x, y] coordinates. Defaults to None.
            export (bool, optional): Add a small button that exports the drawn shapes
                as a GeoJSON file. Defaults to False.
            filename (str, optional): Name of the exported GeoJSON file.
                Defaults to "data.geojson".
            position (str, optional): Position of control: {'topleft', 'topright', 'bottomleft', 'bottomright'}.
                Defaults to "topleft". See https://leafletjs.com/reference.html#control.
            show_geometry_on_click (bool, optional): When True, opens an alert with
                the geometry description on click. Defaults to True.
            draw_options (Union[dict, None], optional): The options used to configure the draw toolbar.
                See http://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#drawoptions.
                Defaults to None.
            edit_options (Union[dict, None], optional): The options used to configure the edit toolbar.
                See https://leaflet.github.io/Leaflet.draw/docs/leaflet-draw-latest.html#editpolyoptions.
                Defaults to None.
        """
        super().__init__()
        self._name = "DrawControl"
        # self.point_coords = [
        #     [22.332214, 114.177604],
        # ]
        # self.polyline_coords = [
        #     [
        #         [22.333414, 114.171581],
        #         [22.329709, 114.17347],
        #         [22.328386, 114.169521],
        #     ]
        # ]
        # self.polygon_coords = [
        #     [
        #         [22.328189, 114.198296],
        #         [22.328142, 114.199648],
        #         [22.327064, 114.199741],
        #         [22.326958, 114.198411],
        #         [22.327719, 114.198661],
        #         [22.328189, 114.198296],
        #     ]
        # ]
        self.point_coords = [] if point_coords is None else point_coords
        self.polyline_coords = [] if polyline_coords is None else polyline_coords
        self.polygon_coords = [] if polygon_coords is None else polygon_coords
        self._name = "DrawControl"
        self.export = export
        self.filename = filename
        self.position = position
        self.show_geometry_on_click = show_geometry_on_click
        self.draw_options = draw_options or {}
        self.edit_options = edit_options or {}

    def render(self, **kwargs):
        super().render(**kwargs)

        figure = self.get_root()
        assert isinstance(
            figure, Figure
        ), "You cannot render this Element if it is not in a Figure."

        export_style = """
            <style>
                #export {
                    position: absolute;
                    top: 5px;
                    right: 10px;
                    z-index: 999;
                    background: white;
                    color: black;
                    padding: 6px;
                    border-radius: 4px;
                    font-family: 'Helvetica Neue';
                    cursor: pointer;
                    font-size: 12px;
                    text-decoration: none;
                    top: 90px;
                }
            </style>
        """
        export_button = """<a href='#' id='export'>Export</a>"""
        if self.export:
            figure.header.add_child(Element(export_style), name="export")
            figure.html.add_child(Element(export_button), name="export_button")
