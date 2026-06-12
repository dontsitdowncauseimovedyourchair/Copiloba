import gi
import json
import urllib.request
import threading

# Force the script to use GTK3
gi.require_version('Gtk', '3.0')
gi.require_version('GLib', '2.0')  # Required for thread-safe UI updates
gi.require_version('OsmGpsMap', '1.0')
from gi.repository import Gtk, GLib, OsmGpsMap


class Gtk3MapDashboard(Gtk.Window):
    def __init__(self):
        super().__init__(title="GTK3 Navigation with OSRM")
        self.set_default_size(800, 480)

        # --- 1. Layout Setup (VBox allows multiple widgets) ---
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(self.vbox)

        # --- 2. Top Header / Controls ---
        self.header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        # Add a little padding to the top bar
        self.vbox.pack_start(self.header, False, False, 5)

        self.route_btn = Gtk.Button(label="Trace Path to Naucalpan")
        self.route_btn.connect("clicked", self.on_route_btn_clicked)
        self.header.pack_start(self.route_btn, False, False, 5)

        # --- 3. Map Setup ---
        self.map_widget = OsmGpsMap.Map()
        osd = OsmGpsMap.MapOsd(show_scale=True, show_coordinates=False)
        self.map_widget.layer_add(osd)

        # Center on Ciudad López Mateos (Start Point)
        self.map_widget.set_center_and_zoom(19.5556, -99.2472, 13)

        # Expand the map to fill the remaining window space
        self.vbox.pack_start(self.map_widget, True, True, 0)

    # --- Interaction Logic ---
    def on_route_btn_clicked(self, widget):
        # Disable the button so the user can't spam the server
        self.route_btn.set_sensitive(False)
        self.route_btn.set_label("Calculating Route...")

        # Start: Ciudad López Mateos | End: Naucalpan Center (Roughly)
        start_lat, start_lon = 19.5556, -99.2472
        end_lat, end_lon = 19.4785, -99.2329

        self.request_osrm_route(self.map_widget, start_lat, start_lon, end_lat, end_lon)

    # --- Background Routing Logic ---
    def request_osrm_route(self, map_widget, start_lat, start_lon, end_lat, end_lon):
        """Spawns the background thread."""
        threading.Thread(
            target=self._fetch_route_task,
            args=(map_widget, start_lat, start_lon, end_lat, end_lon),
            daemon=True
        ).start()

    def _fetch_route_task(self, map_widget, start_lat, start_lon, end_lat, end_lon):
        """Runs invisibly in the background, making the HTTP request."""
        # OSRM URL format requires Longitude FIRST
        url = f"http://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}?overview=full&geometries=geojson"

        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'STM32-Carplay-Dev'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            if data['code'] == 'Ok':
                coordinates = data['routes'][0]['geometry']['coordinates']
                # Pass data back to GTK safely using GLib.idle_add
                GLib.idle_add(self._draw_route_on_map, map_widget, coordinates)
            else:
                print("OSRM Routing failed!")
                GLib.idle_add(self._reset_button)

        except Exception as e:
            print(f"Error connecting to OSRM: {e}")
            GLib.idle_add(self._reset_button)

    def _draw_route_on_map(self, map_widget, coordinates):
        """Executes on the Main UI Thread to draw the geometry."""
        # ⚠️ Auto-handling introspection naming quirks based on your board's Yocto build
        try:
            track = OsmGpsMap.Track()
        except AttributeError:
            track = OsmGpsMap.MapTrack()

        for pt in coordinates:
            pt_lon, pt_lat = pt[0], pt[1]
            try:
                map_point = OsmGpsMap.Point.new_degrees(pt_lat, pt_lon)
            except AttributeError:
                map_point = OsmGpsMap.MapPoint.new_degrees(pt_lat, pt_lon)

            track.add_point(map_point)

        map_widget.track_add(track)

        # Reset the button
        self._reset_button()
        return False  # Tells GLib to stop looping this idle function

    def _reset_button(self):
        """Helper to reset the UI button state safely."""
        self.route_btn.set_sensitive(True)
        self.route_btn.set_label("Trace Path to Naucalpan")
        return False


if __name__ == '__main__':
    win = Gtk3MapDashboard()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()