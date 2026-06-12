import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version("OsmGpsMap", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gst, OsmGpsMap, Pango
import cairo
import math
import os
import json
import urllib.request
import urllib.parse
from colorthief import ColorThief
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from gi.repository import GdkPixbuf
import random
import threading
from PIL import Image
import subprocess

# ─────────────────────────────────────────────
# 1. ESTILOS CSS
# ─────────────────────────────────────────────
def load_all_css():
    try:
        color_thief = ColorThief("album.jpg")
        r, g, b = color_thief.get_color(quality=1)
    except:
        r, g, b = 105, 17, 173  # Morado #6911AD
    dark_r, dark_g, dark_b = max(r - 70, 0), max(g - 70, 0), max(b - 70, 0)
    css = f"""
    * {{
        font-family: "Pixel Operator";
    }}
    .music-background {{
        background-image: linear-gradient(135deg, rgba({r},{g},{b},0.95),
        rgba({dark_r},{dark_g},{dark_b},0.95));
    }}
    .sidebar-music {{ background: transparent; border-radius: 0px; padding: 20px; }}
    .dashboard-music {{ background: rgba(255,255,255,0.1); border-radius: 0px; padding: 30px; }}
    .clock-label {{ color: white; font-size: 80px; font-weight: 900; }}

    .dock-button {{
        background: transparent;
        border: none;
        box-shadow: none;
        font-size: 35px;
        color: white;
        min-width: 80px;
        min-height: 80px;
    }}
    .circle-button {{
        background: rgba(255,255,255,0.1);
        border-radius: 0px;
        min-width: 80px; min-height: 80px;
        font-size: 30px; color: white; border: none;
    }}
    .date-label {{
        color: rgba(255,255,255,0.75);
        font-size: 50px;
        font-weight: 500;
    }}
    .clock-label {{
        color: white;
        font-family: "Pixel Operator HB 8";
        font-size: 120px;
        font-weight: 900;
    }}
    .hero-song {{
        font-size: 70px;
        font-weight: 900;
        color: white;
    }}
    .hero-artist {{
        font-size: 50px;
        color: rgba(255,255,255,0.75);
    }}
    .home-song {{
        font-size: 40px;
        font-weight: 700;
        color: white;
    }}

    .home-artist {{
        font-size: 30px;
        color: rgba(255,255,255,0.7);
    }}
    .transport-button {{
        background: transparent;
        border: none;
        box-shadow: none;
        font-size: 20px;
        color: white;
        min-height: 80px;
        min-width: 80px;
    }}
    .floating-dock {{
        background: rgba(255,255,255,0.20);
        border-radius: 0px;
        padding: 14px 28px;
    }}
    .dock-button {{
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 12px;
    }}
    .dock-button:hover {{
        background: rgba(255,255,255,0.25);
        border-radius: 0px;
    }}

    /* Temperature widget */
    .temp-card {{
        background: rgba(255,255,255,0.12);
        border-radius: 0px;
        padding: 16px 22px;
    }}
    .temp-value {{
        color: white;
        font-size: 60px;
        font-weight: 900;
    }}
    .temp-label {{
        color: rgba(255,255,255,0.70);
        font-size: 30px;
        font-weight: 500;
    }}
    .temp-city {{
        color: rgba(255,255,255,0.85);
        font-size: 30px;
        font-weight: 600;
    }}
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode())
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), provider, 800
    )

# ─────────────────────────────────────────────
# 2. DIBUJOS CAIRO
# ─────────────────────────────────────────────
def rounded_rect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + r, y + r, r, math.pi, 3 * math.pi / 2)
    cr.arc(x + w - r, y + r, r, 3 * math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.close_path()


class MainGradientBG(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.phase = 0.0
        self.theme = random.randint(0, 4)
        self.connect("draw", self._draw)

    def animate(self):
        self.phase += 0.008
        self.queue_draw()
        return True

    def _draw(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_source_rgb(0.12, 0.11, 0.16)
        cr.paint()
        t = self.phase
        if self.theme == 0:
            c1 = (0.55, 0.18, 1.00); c2 = (0.35, 0.45, 1.00)
            c3 = (0.15, 0.70, 1.00); c4 = (0.85, 0.15, 0.70)
            c5 = (1.00, 1.00, 1.00); c6 = (1.00, 0.85, 0.25)
        elif self.theme == 1:
            c1 = (1.00, 0.30, 0.75); c2 = (1.00, 0.50, 0.85)
            c3 = (0.80, 0.35, 1.00); c4 = (1.00, 0.15, 0.45)
            c5 = (1.00, 1.00, 1.00); c6 = (1.00, 0.75, 0.40)
        elif self.theme == 2:
            c1 = (0.25, 0.45, 1.00); c2 = (0.10, 0.70, 1.00)
            c3 = (0.15, 0.90, 0.90); c4 = (0.35, 0.35, 1.00)
            c5 = (1.00, 1.00, 1.00); c6 = (0.85, 0.90, 1.00)
        elif self.theme == 3:
            c1 = (1.00, 0.40, 0.20); c2 = (1.00, 0.65, 0.15)
            c3 = (1.00, 0.25, 0.55); c4 = (0.80, 0.15, 0.75)
            c5 = (1.00, 1.00, 1.00); c6 = (1.00, 0.90, 0.40)
        else:
            c1 = (0.10, 0.85, 0.75); c2 = (0.10, 0.65, 1.00)
            c3 = (0.15, 1.00, 0.60); c4 = (0.20, 0.80, 0.95)
            c5 = (1.00, 1.00, 1.00); c6 = (0.90, 1.00, 0.60)

        blobs = [
            (w * 0.30 + math.sin(t * 0.7) * 180, h * 0.25 + math.cos(t * 0.4) * 120, w * 0.75, c1, 0.75, 0.25),
            (w * 0.75 + math.cos(t * 0.5) * 140, h * 0.30 + math.sin(t * 0.8) * 110, w * 0.65, c2, 0.60, 0.20),
            (w * 0.55 + math.sin(t * 0.9) * 220, h * 0.80 + math.cos(t * 0.5) * 90,  w * 0.55, c3, 0.45, 0.15),
            (w * 0.90 + math.sin(t * 0.2) * 80,  h * 0.65 + math.cos(t * 0.6) * 140, w * 0.65, c4, 0.35, 0.12),
            (w * 0.15 + math.cos(t * 0.35) * 100, h * 0.75 + math.sin(t * 0.20) * 60, w * 0.55, c5, 0.18, 0.0),
            (w * 0.80 + math.sin(t * 0.45) * 120, h * 0.20 + math.cos(t * 0.25) * 80, w * 0.45, c6, 0.30, 0.10),
        ]
        for (bx, by, br, c, a0, a1) in blobs:
            g = cairo.RadialGradient(bx, by, 0, bx, by, br)
            g.add_color_stop_rgba(0,   c[0], c[1], c[2], a0)
            g.add_color_stop_rgba(0.6, c[0], c[1], c[2], a1)
            g.add_color_stop_rgba(1,   0, 0, 0, 0)
            cr.set_source(g)
            cr.paint()

        glow = cairo.RadialGradient(w * 0.5, h * 0.5, 0, w * 0.5, h * 0.5, w * 0.7)
        glow.add_color_stop_rgba(0, 1, 1, 1, 0.08)
        glow.add_color_stop_rgba(1, 1, 1, 1, 0)
        cr.set_source(glow)
        cr.paint()
        return False


class MusicGradientBG(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.colors = [
            (255, 80, 180),
            (120, 70, 255),
            (60, 180, 255),
            (255, 180, 60),
        ]
        self.phase = 0
        self.connect("draw", self._draw)

    def set_palette(self, palette):

        filtered = []

        for r, g, b in palette:

            # Ignorar grises
            if abs(r - g) < 25 and abs(g - b) < 25:
                continue

            # Ignorar colores demasiado claros
            brightness = (r + g + b) / 3

            if brightness > 220:
                continue

            filtered.append((r, g, b))

        if not filtered:
            filtered = palette

        boosted = []

        for r, g, b in filtered:

            boosted.append((
                min(255, int(r * 1.8)),
                min(255, int(g * 1.8)),
                min(255, int(b * 1.8))
            ))

        self.colors = boosted
        self.queue_draw()

    def _draw(self, widget, cr):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        if not self.colors:
            return False

        r, g, b = self.colors[0]

        levels = [
            1.00,
            0.85,
            0.70,
            0.55,
            0.40
        ]

        band_h = h / len(levels)

        for i, factor in enumerate(levels):

            cr.set_source_rgb(
                (r * factor) / 255,
                (g * factor) / 255,
                (b * factor) / 255
            )

            cr.rectangle(
                0,
                i * band_h,
                w,
                band_h + 2
            )

            cr.fill()

        return False
# ─────────────────────────────────────────────
# 3. TEMPERATURA WIDGET
# ─────────────────────────────────────────────
class TemperatureWidget(Gtk.Box):
    """
    Small weather card that shows current temperature.
    Uses Open-Meteo (free, no API key needed).
    Latitude/Longitude default to Ciudad López Mateos, Mexico.
    """
    LAT = 19.5556
    LON = -99.2472
    CITY = "López Mateos"

    # WMO weather code → emoji
    WMO_ICONS = {
        0: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/sun.png",
        1: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/partly_cloudy.png",
        2: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/cloudy.png",
        3: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/cloud.png",

        45: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/fog.png",
        48: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/fog.png",

        51: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",
        53: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",
        55: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",

        61: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",
        63: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",
        65: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",

        71: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/snow.png",
        73: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/snow.png",
        75: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/snow.png",

        80: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",
        81: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/rain.png",
        82: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/storm.png",

        95: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/storm.png",
        96: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/storm.png",
        99: "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/weather/storm.png",
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.get_style_context().add_class("temp-card")
        self.set_size_request(160, -1)

        # Top row: icon + temperature
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_row.set_halign(Gtk.Align.CENTER)

        self.lbl_icon = Gtk.Image()

        self.lbl_temp = Gtk.Label(label="--°C")
        self.lbl_temp.get_style_context().add_class("temp-value")

        top_row.pack_start(self.lbl_icon, False, False, 0)
        top_row.pack_start(self.lbl_temp, False, False, 0)

        self.lbl_city = Gtk.Label(label=self.CITY)
        self.lbl_city.get_style_context().add_class("temp-city")
        self.lbl_city.set_halign(Gtk.Align.CENTER)

        self.lbl_desc = Gtk.Label(label="Fetching…")
        self.lbl_desc.get_style_context().add_class("temp-label")
        self.lbl_desc.set_halign(Gtk.Align.CENTER)

        self.pack_start(top_row, False, False, 0)
        self.pack_start(self.lbl_city, False, False, 0)
        self.pack_start(self.lbl_desc, False, False, 0)

        # Fetch on start, then every 10 minutes
        self._fetch_async()
        GLib.timeout_add_seconds(600, self._fetch_async)

    def _fetch_async(self):
        t = threading.Thread(target=self._fetch, daemon=True)
        t.start()
        return True  # keep GLib timer alive

    def _fetch(self):
        try:
            url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={self.LAT}&longitude={self.LON}"
                f"&current_weather=true"
                f"&temperature_unit=celsius"
            )
            resp = requests.get(url, timeout=8)
            data = resp.json()
            cw = data["current_weather"]
            temp = round(cw["temperature"])
            code = int(cw["weathercode"])
            icon = self.WMO_ICONS.get(code, "🌡")
            GLib.idle_add(self._update_ui, temp, icon, code)
        except Exception as e:
            print("Weather fetch error:", e)
            GLib.idle_add(self._update_ui, None, "🌡", None)

    def _update_ui(self, temp, icon, code):
        if temp is not None:

            self.lbl_temp.set_text(f"{temp}°C")

            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                icon,
                96,
                96,
                True
            )

            self.lbl_icon.set_from_pixbuf(pixbuf)

            self.lbl_desc.set_text(
                self._code_to_desc(code)
            )

        else:
            self.lbl_temp.set_text("--°C")
            self.lbl_desc.set_text("Sin conexión")

        return False
    @staticmethod
    def _code_to_desc(code):
        mapping = {
            0: "Despejado", 1: "Mayormente despejado",
            2: "Parcialmente nublado", 3: "Nublado",
            45: "Niebla", 48: "Niebla con escarcha",
            51: "Llovizna ligera", 53: "Llovizna moderada", 55: "Llovizna densa",
            61: "Lluvia ligera", 63: "Lluvia moderada", 65: "Lluvia fuerte",
            71: "Nevada ligera", 73: "Nevada moderada", 75: "Nevada intensa",
            80: "Chubascos ligeros", 81: "Chubascos moderados", 82: "Chubascos fuertes",
            95: "Tormenta", 96: "Tormenta con granizo", 99: "Tormenta intensa",
        }
        return mapping.get(code, "")


# ─────────────────────────────────────────────
# 4. NAVIGATION SYSTEM + MAP SCREEN
# ─────────────────────────────────────────────
class NavigationSystem:
    """
    Handles geocoding (Nominatim) and turn-by-turn routing (OSRM).
    All network calls run in daemon threads; results are sent back to
    the GTK main loop via GLib.idle_add so the UI never freezes.
    """

    NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
    OSRM_URL      = "http://router.project-osrm.org/route/v1/driving"
    USER_AGENT    = "STM32-Carplay-Dev"

    def geocode_async(self, query, callback):
        """Resolve a place name to (lat, lon).  callback(lat, lon) on success,
        callback(None, None) on failure — always called on the GTK thread."""
        threading.Thread(
            target=self._geocode_task,
            args=(query, callback),
            daemon=True,
        ).start()

    def _geocode_task(self, query, callback):
        try:
            params = urllib.parse.urlencode({
                "q": query,
                "format": "json",
                "limit": 1,
            })
            url = f"{self.NOMINATIM_URL}?{params}"
            req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            if data:
                lat = float(data[0]["lat"])
                lon = float(data[0]["lon"])
                GLib.idle_add(callback, lat, lon)
            else:
                print(f"Geocode: no results for '{query}'")
                GLib.idle_add(callback, None, None)
        except Exception as e:
            print(f"Geocode error: {e}")
            GLib.idle_add(callback, None, None)

    def request_osrm_route(self, map_widget, start_lat, start_lon, end_lat, end_lon):
        """Spawn a background thread to fetch the route without freezing the UI."""
        threading.Thread(
            target=self._fetch_route_task,
            args=(map_widget, start_lat, start_lon, end_lat, end_lon),
            daemon=True,
        ).start()

    def _fetch_route_task(self, map_widget, start_lat, start_lon, end_lat, end_lon):
        # ⚠️ CRITICAL PITFALL: OSRM expects Longitude FIRST in the URL!
        url = (
            f"{self.OSRM_URL}/"
            f"{start_lon},{start_lat};{end_lon},{end_lat}"
            f"?overview=full&geometries=geojson"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
            if data["code"] == "Ok":
                coordinates = data["routes"][0]["geometry"]["coordinates"]
                GLib.idle_add(self._draw_route_on_map, map_widget, coordinates)
            else:
                print("OSRM routing failed:", data.get("code"))
        except Exception as e:
            print(f"Error connecting to OSRM: {e}")

    def _draw_route_on_map(self, map_widget, coordinates):
        """Executes on the main GTK thread to render the polyline."""
        track = OsmGpsMap.Track()
        for pt in coordinates:
            pt_lon, pt_lat = pt[0], pt[1]
            # ⚠️ CRITICAL PITFALL: OsmGpsMap expects Latitude FIRST!
            map_point = OsmGpsMap.Point.new_degrees(pt_lat, pt_lon)
            track.add_point(map_point)
        map_widget.track_add(track)
        return False  # stop GLib from re-calling


class MapScreen(Gtk.Overlay):

    HOME_LAT = 19.5556
    HOME_LON = -99.2472
    HOME_ZOOM = 14

    def __init__(self, nav_callback):

        super().__init__()

        self._nav_system = NavigationSystem()
        self._active_tracks = []

        self._origin_lat = self.HOME_LAT
        self._origin_lon = self.HOME_LON

        # =========================
        # MAPA
        # =========================

        self.map_widget = OsmGpsMap.Map()

        osd = OsmGpsMap.MapOsd(
            show_scale=True,
            show_coordinates=False
        )

        self.map_widget.layer_add(osd)

        self.map_widget.set_center_and_zoom(
            self.HOME_LAT,
            self.HOME_LON,
            self.HOME_ZOOM
        )

        base = Gtk.Fixed()

        base.put(
            self.map_widget,
            0,
            0
        )

        self.add(base)

        # =========================
        # UI ENCIMA DEL MAPA
        # =========================

        ui_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=0
        )

        ui_box.set_halign(Gtk.Align.FILL)
        ui_box.set_valign(Gtk.Align.START)

        top_bar = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10
        )

        top_bar.set_margin_top(16)
        top_bar.set_margin_start(16)
        top_bar.set_margin_end(16)

        # =========================
        # HOME
        # =========================

        btn_home = Gtk.Button()

        try:

            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/home.png",
                42,
                42,
                True
            )

            btn_home.set_image(
                Gtk.Image.new_from_pixbuf(
                    pixbuf
                )
            )

        except:

            btn_home.set_label("⌂")

        btn_home.connect(
            "clicked",
            lambda _: nav_callback("home")
        )

        # =========================
        # BUSCADOR
        # =========================

        self._entry = Gtk.Entry()

        self._entry.set_placeholder_text(
            "Buscar destino..."
        )

        self._entry.set_hexpand(True)

        self._entry.connect(
            "activate",
            self._on_go_clicked
        )

        # =========================
        # BOTON IR
        # =========================

        btn_go = Gtk.Button(
            label="Ir"
        )

        btn_go.connect(
            "clicked",
            self._on_go_clicked
        )

        # =========================
        # LIMPIAR
        # =========================

        btn_clear = Gtk.Button(
            label="✕"
        )

        btn_clear.connect(
            "clicked",
            self._on_clear_clicked
        )

        # =========================
        # STATUS
        # =========================

        self._lbl_status = Gtk.Label(
            label=""
        )

        self._lbl_status.set_halign(
            Gtk.Align.CENTER
        )

        # =========================
        # LAYOUT
        # =========================

        top_bar.pack_start(
            btn_home,
            False,
            False,
            0
        )

        top_bar.pack_start(
            self._entry,
            True,
            True,
            0
        )

        top_bar.pack_start(
            btn_go,
            False,
            False,
            0
        )

        top_bar.pack_start(
            btn_clear,
            False,
            False,
            0
        )

        ui_box.pack_start(
            top_bar,
            False,
            False,
            0
        )

        ui_box.pack_start(
            self._lbl_status,
            False,
            False,
            0
        )

        base.put(
            ui_box,
            20,
            20
        )

    # ====================================
    # HELPERS
    # ====================================

    def _set_status(self, text, visible=True):

        self._lbl_status.set_text(text)

        if visible:

            self._lbl_status.show()

        else:

            self._lbl_status.hide()

    def _on_go_clicked(self, widget):

        query = self._entry.get_text().strip()

        if not query:
            return

        self._set_status(
            "🔍 Buscando..."
        )

        self._nav_system.geocode_async(
            query,
            self._on_geocode_result
        )

    def _on_geocode_result(self, lat, lon):

        if lat is None:

            self._set_status(
                "Destino no encontrado"
            )

            return

        self._set_status(
            "Calculando ruta..."
        )

        self.map_widget.gps_clear()

        self.map_widget.gps_add(
            lat,
            lon,
            0.0
        )

        self._nav_system.request_osrm_route(
            self.map_widget,
            self._origin_lat,
            self._origin_lon,
            lat,
            lon
        )

        self.map_widget.set_center_and_zoom(
            lat,
            lon,
            13
        )

        self._set_status(
            "",
            False
        )

    def _on_clear_clicked(self, widget):

        try:

            self.map_widget.track_remove_all()

        except:

            pass

        self.map_widget.gps_clear()

        self._entry.set_text("")

        self._set_status(
            "",
            False
        )

        self.map_widget.set_center_and_zoom(
            self.HOME_LAT,
            self.HOME_LON,
            self.HOME_ZOOM
        )

# ─────────────────────────────────────────────
# 5. MÚSICA — HomeSpotifyCard
# ─────────────────────────────────────────────
class HomeSpotifyCard(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=25)
        self.set_size_request(100, 720)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.get_style_context().add_class("dashboard-music")

        self.cover = Gtk.Image()
        self.cover.set_size_request(50, 50)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        self.lbl_song = Gtk.Label(label="No music playing")
        self.lbl_song.get_style_context().add_class("home-song")
        self.lbl_song.set_xalign(0)

        self.lbl_artist = Gtk.Label(label="")
        self.lbl_artist.get_style_context().add_class("home-artist")
        self.lbl_artist.set_xalign(0)

        self.progress = Gtk.ProgressBar()

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        volume_controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10
        )

        
        btn_vol_down = Gtk.Button()
        vol_down_img = Gtk.Image.new_from_file("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/lessvolume.png")
        btn_vol_up = Gtk.Button()
        vol_up_img = Gtk.Image.new_from_file("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/morevolume.png")

        btn_vol_down.set_image(vol_down_img)
        btn_vol_up.set_image(vol_up_img)

        btn_vol_down.get_style_context().add_class("circle-button")
        btn_vol_up.get_style_context().add_class("circle-button")

        btn_vol_down.connect(
            "clicked",
            self.volume_down
        )

        btn_vol_up.connect(
            "clicked",
            self.volume_up
        )

        volume_controls.pack_start(
            btn_vol_down,
            False,
            False,
            0
        )

        volume_controls.pack_start(
            btn_vol_up,
            False,
            False,
            0
        )

        btn_prev = Gtk.Button()
        pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/rewind.png",
            32,
            32,
            True
        )

        btn_prev.set_image(
            Gtk.Image.new_from_pixbuf(pix)
        )

        btn_play = Gtk.Button()
        play_pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/play.png",
            32,
            32,
            True
        )   
        btn_play.set_image(
            Gtk.Image.new_from_pixbuf(play_pix)
        )
        btn_next = Gtk.Button()
        next_pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/next.png",
            32,
            32,
            True
        )
        btn_next.set_image(
            Gtk.Image.new_from_pixbuf(next_pix)
        )


        btn_prev.get_style_context().add_class("transport-button")
        btn_play.get_style_context().add_class("transport-button")
        btn_next.get_style_context().add_class("transport-button")

        controls.pack_start(btn_prev, False, False, 0)
        controls.pack_start(btn_play, False, False, 0)
        controls.pack_start(btn_next, False, False, 0)

        left.pack_start(self.cover, False, False, 0)
        left.pack_start(self.lbl_song,   False, False, 0)
        left.pack_start(self.lbl_artist, False, False, 0)
        left.pack_start(self.progress,   False, False, 0)
        left.pack_start(controls,        False, False, 0)
        left.pack_start(
            volume_controls,
            False,
            False,
            0
        )
        self.pack_start(left, True, True, 0)
        volume_controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=10
        )

        btn_vol_down.connect(
            "clicked",
            self.volume_down
        )

        btn_vol_up.connect(
            "clicked",
            self.volume_up
        )

        volume_controls.pack_start(
            btn_vol_down,
            False,
            False,
            0
        )

        volume_controls.pack_start(
            btn_vol_up,
            False,
            False,
            0
        )

        left.pack_start(
            volume_controls,
            False,
            False,
            0
        )

    def update_progress(self, fraction):
        self.progress.set_fraction(fraction)

    def update_card(self, song, artist):
        self.lbl_song.set_text(song)
        self.lbl_artist.set_text(artist)

    def update_cover(self, pixbuf):
        print(pixbuf)
        self.cover.set_from_pixbuf(pixbuf)

    def volume_up(self, widget):
        subprocess.run([
            "wpctl",
            "set-volume",
            "@DEFAULT_AUDIO_SINK@",
            "5%+"
        ])

    def volume_down(self, widget):
        subprocess.run([
            "wpctl",
            "set-volume",
            "@DEFAULT_AUDIO_SINK@",
            "5%-"
        ])


# ─────────────────────────────────────────────
# 6. MÚSICA — MusicScreen
# ─────────────────────────────────────────────
class MusicScreen(Gtk.Overlay):
    def __init__(self, nav_callback, home_card):
        self.home_card = home_card
        super().__init__()

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id="6186b61db32f4eb59ae55a299ef475ad",
                client_secret="7dea9bd274b0436fafea5b676838c71c",
                redirect_uri="http://127.0.0.1:8888/callback",
                scope="user-read-playback-state user-modify-playback-state",
                cache_path="/home/root/spotify.cache",
                open_browser=False,
            )
        )
        self.current_cover = None

        self.music_bg = MusicGradientBG()
        self.add(self.music_bg)

        fixed = Gtk.Fixed()
        self.add_overlay(fixed)

        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.get_style_context().add_class("sidebar-music")

        btn_back = Gtk.Button()
        img = Gtk.Image.new_from_file("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/home.png")
        btn_back.set_image(img)
        btn_back.get_style_context().add_class("circle-button")
        btn_back.connect("clicked", lambda x: nav_callback("home"))
        sidebar.pack_start(btn_back, False, False, 0)

        # Center content
        center = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=25)
        center.set_halign(Gtk.Align.CENTER)
        center.set_valign(Gtk.Align.CENTER)

        self.album_image = Gtk.Image()
        self.album_image.set_halign(Gtk.Align.CENTER)
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("album.jpg", 320, 320, True)
            self.album_image.set_from_pixbuf(pixbuf)
            
        except Exception:
            pass

        self.lbl_song = Gtk.Label(label="Loading...")
        self.lbl_song.get_style_context().add_class("hero-song")

        self.lbl_art = Gtk.Label(label="")
        self.lbl_art.get_style_context().add_class("hero-artist")

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=40)
        self.btn_prev = Gtk.Button()
        self.btn_play = Gtk.Button()
        self.btn_next = Gtk.Button()

        for (btn, path) in [
            (self.btn_prev, "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/rewind.png"),
            (self.btn_play, "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/play.png"),
            (self.btn_next, "/home/root/copilobarepo/SoC-Carplay/carplay_project/media/next.png"),
        ]:
            pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(path,80, 80, True)
            btn.set_image(Gtk.Image.new_from_pixbuf(pix))
            btn.get_style_context().add_class("transport-button")

        controls.pack_start(self.btn_prev, False, False, 0)
        controls.pack_start(self.btn_play, False, False, 0)
        controls.pack_start(self.btn_next, False, False, 0)

        self.btn_prev.connect("clicked", self.previous_track)
        self.btn_play.connect("clicked", self.toggle_play)
        self.btn_next.connect("clicked", self.next_track)

        fixed.put(sidebar, 0, 0)

        fixed.put(self.album_image, 150, 160)
        fixed.put(self.lbl_song, 600, 200)
        fixed.put(self.lbl_art, 600, 330)
        fixed.put(controls, 700, 450)

        self.update_spotify()
        GLib.timeout_add(2000, self.update_spotify)

    def pixelate_album(self, input_path, output_path):
        img = Image.open(input_path)

        small = img.resize(
            (32, 32),
            Image.NEAREST
        )

        pixel = small.resize(
            img.size,
            Image.NEAREST
        )

        pixel.save(output_path)

    def update_album_art(self, url):
        try:
            response = requests.get(url, timeout=10)
            with open("current_album.jpg", "wb") as f:
                f.write(response.content)

            self.pixelate_album(
                "current_album.jpg",
                "current_album_pixel.jpg"
            )
            try:
                color_thief = ColorThief("current_album.jpg")
                palette = color_thief.get_palette(color_count=6)
                self.music_bg.set_palette([palette[0], palette[1], palette[2], palette[3]])
            except Exception as e:
                print("ColorThief error:", e)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file("current_album_pixel.jpg")
            pixbuf = pixbuf.scale_simple(410, 410, GdkPixbuf.InterpType.NEAREST)
            self.album_image.set_from_pixbuf(pixbuf)

            home_pixbuf = pixbuf.scale_simple(
                300,
                300,
                GdkPixbuf.InterpType.NEAREST
            )
            self.home_card.update_cover(home_pixbuf)

        except Exception as e:
            print("Album art error:", e)

    def update_spotify(self):
        try:
            playback = self.sp.current_playback()
            if not playback:
                return True
            track = playback["item"]
            if not track:
                return True
            fraction = playback["progress_ms"] / track["duration_ms"]
            song   = track["name"]
            artist = track["artists"][0]["name"]
            cover  = track["album"]["images"][0]["url"]
            self.lbl_song.set_text(song)
            self.lbl_art.set_text(artist)
            self.home_card.update_card(song, artist)
            self.home_card.update_progress(fraction)
            if cover != self.current_cover:
                self.current_cover = cover
                self.update_album_art(cover)
        except Exception as e:
            print("Spotify error:", e)
        return True

    def next_track(self, widget):
        try:
            self.sp.next_track()
        except Exception as e:
            print(e)

    def previous_track(self, widget):
        try:
            self.sp.previous_track()
        except Exception as e:
            print(e)

    def toggle_play(self, widget):
        try:
            playback = self.sp.current_playback()
            if playback["is_playing"]:
                self.sp.pause_playback()
                self.btn_play.set_label("▶")
            else:
                self.sp.start_playback()
                self.btn_play.set_label("⏸")
        except Exception as e:
            print(e)


# ─────────────────────────────────────────────
# 7. CAMERA SCREEN
# ─────────────────────────────────────────────
class CameraScreen(Gtk.Overlay):
    def __init__(self, nav_callback):
        super().__init__()
        self.pipeline = Gst.parse_launch(
            "v4l2src device=/dev/video7 ! "
            "image/jpeg,width=640,height=360 ! "
            "jpegdec ! videoconvert ! gtksink name=sink"
        )
        sink = self.pipeline.get_by_name("sink")
        video_widget = sink.get_property("widget")
        self.add(video_widget)

        btn_home = Gtk.Button()
        img = Gtk.Image.new_from_file("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/home.png")
        btn_home.set_image(img)
        btn_home.set_halign(Gtk.Align.START)
        btn_home.set_valign(Gtk.Align.START)
        btn_home.set_margin_start(20)
        btn_home.set_margin_top(20)
        btn_home.set_size_request(64, 64)
        btn_home.connect("clicked", lambda x: nav_callback("home"))

        guide_layer = Gtk.DrawingArea()
        guide_layer.set_can_focus(False)
        guide_layer.set_sensitive(False)
        guide_layer.connect("draw", self.draw_guides)

        self.add_overlay(guide_layer)
        self.add_overlay(btn_home)

    def draw_guides(self, widget, cr):
        w = widget.get_allocated_width()
        h = widget.get_allocated_height()
        cr.set_line_width(8)
        # Verde (lejos)
        cr.set_source_rgba(0, 1, 0, 0.85)
        cr.move_to(w * 0.20, h * 0.55); cr.line_to(w * 0.80, h * 0.55); cr.stroke()
        # Amarillo (medio)
        cr.set_source_rgba(1, 1, 0, 0.85)
        cr.move_to(w * 0.15, h * 0.72); cr.line_to(w * 0.85, h * 0.72); cr.stroke()
        # Rojo (peligro)
        cr.set_source_rgba(1, 0, 0, 0.85)
        cr.move_to(w * 0.10, h * 0.88); cr.line_to(w * 0.90, h * 0.88); cr.stroke()
        return False

    def start_camera(self):
        print("START CAMERA")
        self.pipeline.set_state(Gst.State.PLAYING)

    def stop_camera(self):
        self.pipeline.set_state(Gst.State.NULL)


# ─────────────────────────────────────────────
# 8. RELOJ
# ─────────────────────────────────────────────
class ClockWidget(Gtk.Box):
    def __init__(self):
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=30)
        self.lbl_date  = Gtk.Label()
        self.lbl_clock = Gtk.Label()
        self.lbl_date.set_xalign(0.5)
        self.lbl_clock.set_xalign(0.5)
        self.lbl_date.get_style_context().add_class("date-label")
        self.lbl_clock.get_style_context().add_class("clock-label")
        self.pack_start(self.lbl_date,  False, False, 0)
        self.pack_start(self.lbl_clock, False, False, 0)
        self.update_clock()
        GLib.timeout_add(1000, self.update_clock)

    def update_clock(self):
        now = datetime.now()
        self.lbl_clock.set_text(now.strftime("%H:%M"))
        self.lbl_date.set_text(now.strftime("%a %d %b"))
        return True


# ─────────────────────────────────────────────
# 9. VENTANA PRINCIPAL
# ─────────────────────────────────────────────
class CarPlayWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="CarPlay OS")
        try:
            subprocess.run([
                "pactl",
                "set-default-sink",
                "bluez_output.54_71_DD_B5_AB_B2.1"
            ])
        except Exception as e:
            print("Bluetooth sink error:", e)

        try:
            self.librespot = subprocess.Popen([
                "/home/root/librespot",
                "--name",
                "Copiloba"
            ])
        except Exception as e:
            print("Librespot error:", e)

        self.fullscreen()
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.add(self.stack)

        # Home screen (must be built first so home_card exists)
        self.stack.add_named(self._build_home(), "home")

        # Music screen
        self.music_screen = MusicScreen(self.navigate, self.home_card)
        self.stack.add_named(self.music_screen, "music")

        # Camera screen
        self.camera_screen = CameraScreen(self.navigate)
        self.stack.add_named(self.camera_screen, "camera")

        # Map screen
        self.map_screen = MapScreen(self.navigate)
        self.stack.add_named(self.map_screen, "map")

    def _build_home(self):
        overlay = Gtk.Overlay()
        overlay.add(MainGradientBG())

        fixed = Gtk.Fixed()
        fixed.set_hexpand(True)
        fixed.set_vexpand(True)

        # Clock — top-right area
        clock = ClockWidget()
        fixed.put(clock, 550, 230)

        # Spotify card
        self.home_card = HomeSpotifyCard()
        fixed.put(self.home_card, 0, 0)

        # Temperature widget — top-left
        self.temp_widget = TemperatureWidget()
        fixed.put(self.temp_widget, 30, 500)

        # Dock — bottom-center
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        dock.get_style_context().add_class("floating-dock")

        def create_icon_button(path):
            btn = Gtk.Button()
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 42, 42, True)
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            btn.set_image(img)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("dock-button")
            return btn

        btn_home   = create_icon_button("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/home.png")
        btn_music  = create_icon_button("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/music.png")
        btn_cam    = create_icon_button("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/camera.png")
        # Map button — uses your map.png icon
        btn_map    = create_icon_button("/home/root/copilobarepo/SoC-Carplay/carplay_project/media/map.png")

        for b in [btn_home, btn_music, btn_cam, btn_map]:
            dock.pack_start(b, False, False, 0)

        btn_home.connect( "clicked", lambda x: self.navigate("home"))
        btn_music.connect("clicked", lambda x: self.navigate("music"))
        btn_cam.connect(  "clicked", lambda x: self.navigate("camera"))
        btn_map.connect(  "clicked", lambda x: self.navigate("map"))

        fixed.put(dock, 600, 530)

        overlay.add_overlay(fixed)
        return overlay

    def navigate(self, name):
        if name == "camera":
            self.camera_screen.start_camera()
        else:
            self.camera_screen.stop_camera()
        self.stack.set_visible_child_name(name)

    def on_destroy(self, widget):

        if hasattr(self, "librespot"):
            self.librespot.terminate()

        Gtk.main_quit()


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    Gst.init(None)
    load_all_css()
    win = CarPlayWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
