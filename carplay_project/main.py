import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")
gi.require_version("OsmGpsMap", "1.0")
from gi.repository import Gtk, Gdk, GLib, Gst, OsmGpsMap
import cairo
import math
import os
from colorthief import ColorThief
from datetime import datetime
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import requests
from gi.repository import GdkPixbuf
import random
import threading

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
    .music-background {{
        background-image: linear-gradient(135deg, rgba({r},{g},{b},0.95),
        rgba({dark_r},{dark_g},{dark_b},0.95));
    }}
    .sidebar-music {{ background: transparent; border-radius: 30px; padding: 20px; }}
    .dashboard-music {{ background: rgba(255,255,255,0.1); border-radius: 40px; padding: 30px; }}
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
        border-radius: 999px;
        min-width: 80px; min-height: 80px;
        font-size: 30px; color: white; border: none;
    }}
    .date-label {{
        color: rgba(255,255,255,0.75);
        font-size: 20px;
        font-weight: 500;
    }}
    .clock-label {{
        color: white;
        font-size: 72px;
        font-weight: 900;
    }}
    .hero-song {{
        font-size: 42px;
        font-weight: 900;
        color: white;
    }}
    .hero-artist {{
        font-size: 22px;
        color: rgba(255,255,255,0.75);
    }}
    .transport-button {{
        background: transparent;
        border: none;
        box-shadow: none;
        font-size: 54px;
        color: white;
        min-height: 80px;
        min-width: 80px;
    }}
    .floating-dock {{
        background: rgba(255,255,255,0.12);
        border-radius: 35px;
        padding: 14px 28px;
    }}
    .dock-button {{
        background: transparent;
        border: none;
        box-shadow: none;
        padding: 12px;
    }}
    .dock-button:hover {{
        background: rgba(255,255,255,0.12);
        border-radius: 18px;
    }}

    /* Temperature widget */
    .temp-card {{
        background: rgba(255,255,255,0.12);
        border-radius: 24px;
        padding: 16px 22px;
    }}
    .temp-value {{
        color: white;
        font-size: 36px;
        font-weight: 900;
    }}
    .temp-label {{
        color: rgba(255,255,255,0.70);
        font-size: 14px;
        font-weight: 500;
    }}
    .temp-city {{
        color: rgba(255,255,255,0.85);
        font-size: 16px;
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
        boosted = []
        for r, g, b in palette:
            boosted.append((
                min(255, int(r * 1.6)),
                min(255, int(g * 1.6)),
                min(255, int(b * 1.6)),
            ))
        self.colors = boosted
        self.queue_draw()

    def _draw(self, widget, cr):
        w = self.get_allocated_width()
        h = self.get_allocated_height()
        cr.set_source_rgb(0.10, 0.08, 0.15)
        cr.paint()
        t = 0
        for i, color in enumerate(self.colors):
            r, g, b = color
            x = w * 0.2 + i * 200 + math.sin(t + i) * 120
            y = h * 0.5 + math.cos(t * 0.7 + i) * 80
            grad = cairo.RadialGradient(x, y, 0, x, y, 700)
            grad.add_color_stop_rgba(0, r / 255, g / 255, b / 255, 0.85)
            grad.add_color_stop_rgba(1, r / 255, g / 255, b / 255, 0)
            cr.set_source(grad)
            cr.paint()
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
        0: "☀️", 1: "🌤", 2: "⛅", 3: "☁️",
        45: "🌫", 48: "🌫",
        51: "🌦", 53: "🌦", 55: "🌧",
        61: "🌧", 63: "🌧", 65: "🌧",
        71: "🌨", 73: "🌨", 75: "❄️",
        80: "🌦", 81: "🌧", 82: "⛈",
        95: "⛈", 96: "⛈", 99: "⛈",
    }

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.get_style_context().add_class("temp-card")
        self.set_size_request(160, -1)

        # Top row: icon + temperature
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        top_row.set_halign(Gtk.Align.CENTER)

        self.lbl_icon = Gtk.Label(label="🌡")
        self.lbl_icon.set_markup('<span font="28">🌡</span>')

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
            self.lbl_icon.set_markup(f'<span font="28">{icon}</span>')
            desc = self._code_to_desc(code)
            self.lbl_desc.set_text(desc)
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
# 4. MAPA SCREEN
# ─────────────────────────────────────────────
class MapScreen(Gtk.Overlay):
    """Full-screen OsmGpsMap view with a home button overlay."""

    LAT = 19.5556
    LON = -99.2472
    ZOOM = 14

    def __init__(self, nav_callback):
        super().__init__()

        # Map widget
        self.map_widget = OsmGpsMap.Map()
        osd = OsmGpsMap.MapOsd(show_scale=True, show_coordinates=False)
        self.map_widget.layer_add(osd)
        self.map_widget.set_center_and_zoom(self.LAT, self.LON, self.ZOOM)
        self.add(self.map_widget)

        # Overlay: home button (top-left)
        btn_home = Gtk.Button()
        try:
            img = Gtk.Image.new_from_file("/home/root/media/home.png")
        except Exception:
            img = Gtk.Label(label="⌂")
        btn_home.set_image(img)
        btn_home.get_style_context().add_class("circle-button")
        btn_home.set_halign(Gtk.Align.START)
        btn_home.set_valign(Gtk.Align.START)
        btn_home.set_margin_start(20)
        btn_home.set_margin_top(20)
        btn_home.connect("clicked", lambda x: nav_callback("home"))
        self.add_overlay(btn_home)


# ─────────────────────────────────────────────
# 5. MÚSICA — HomeSpotifyCard
# ─────────────────────────────────────────────
class HomeSpotifyCard(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=25)
        self.set_size_request(650, 320)
        self.get_style_context().add_class("dashboard-music")

        self.cover = Gtk.Image()
        self.pack_start(self.cover, False, False, 20)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)

        self.lbl_song = Gtk.Label(label="No music playing")
        self.lbl_song.get_style_context().add_class("hero-song")
        self.lbl_song.set_xalign(0)

        self.lbl_artist = Gtk.Label(label="")
        self.lbl_artist.get_style_context().add_class("hero-artist")
        self.lbl_artist.set_xalign(0)

        self.progress = Gtk.ProgressBar()

        controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)

        btn_prev = Gtk.Button()
        prev_img = Gtk.Image.new_from_file("/home/root/media/rewind.png")
        btn_prev.set_image(prev_img)

        btn_play = Gtk.Button()
        play_img = Gtk.Image.new_from_file("/home/root/media/play.png")
        btn_play.set_image(play_img)

        btn_next = Gtk.Button()
        next_img = Gtk.Image.new_from_file("/home/root/media/next.png")
        btn_next.set_image(next_img)

        controls.pack_start(btn_prev, False, False, 0)
        controls.pack_start(btn_play, False, False, 0)
        controls.pack_start(btn_next, False, False, 0)

        right.pack_start(self.lbl_song,   False, False, 0)
        right.pack_start(self.lbl_artist, False, False, 0)
        right.pack_start(self.progress,   False, False, 0)
        right.pack_start(controls,        False, False, 0)
        self.pack_start(right, True, True, 0)

    def update_progress(self, fraction):
        self.progress.set_fraction(fraction)

    def update_card(self, song, artist):
        self.lbl_song.set_text(song)
        self.lbl_artist.set_text(artist)

    def update_cover(self, pixbuf):
        self.cover.set_from_pixbuf(pixbuf)


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

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(40)
        content.set_margin_end(40)
        self.add_overlay(content)

        # Sidebar
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.get_style_context().add_class("sidebar-music")

        btn_back = Gtk.Button()
        img = Gtk.Image.new_from_file("/home/root/media/home.png")
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
            (self.btn_prev, "/home/root/media/rewind.png"),
            (self.btn_play, "/home/root/media/play.png"),
            (self.btn_next, "/home/root/media/next.png"),
        ]:
            pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 48, 48, True)
            btn.set_image(Gtk.Image.new_from_pixbuf(pix))
            btn.get_style_context().add_class("transport-button")

        controls.pack_start(self.btn_prev, False, False, 0)
        controls.pack_start(self.btn_play, False, False, 0)
        controls.pack_start(self.btn_next, False, False, 0)

        self.btn_prev.connect("clicked", self.previous_track)
        self.btn_play.connect("clicked", self.toggle_play)
        self.btn_next.connect("clicked", self.next_track)

        center.pack_start(self.album_image, False, False, 0)
        center.pack_start(self.lbl_song,    False, False, 0)
        center.pack_start(self.lbl_art,     False, False, 0)
        center.pack_start(controls,         False, False, 0)

        content.pack_start(sidebar, False, False, 0)
        content.pack_start(center,  True,  True,  0)

        self.update_spotify()
        GLib.timeout_add(2000, self.update_spotify)

    def update_album_art(self, url):
        try:
            response = requests.get(url, timeout=10)
            with open("current_album.jpg", "wb") as f:
                f.write(response.content)
            try:
                color_thief = ColorThief("current_album.jpg")
                palette = color_thief.get_palette(color_count=6)
                self.music_bg.set_palette([palette[0], palette[1], palette[2], palette[3]])
            except Exception as e:
                print("ColorThief error:", e)
            pixbuf = GdkPixbuf.Pixbuf.new_from_file("current_album.jpg")
            pixbuf = pixbuf.scale_simple(280, 280, GdkPixbuf.InterpType.BILINEAR)
            self.album_image.set_from_pixbuf(pixbuf)
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
        img = Gtk.Image.new_from_file("/home/root/media/home.png")
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
        Gtk.Box.__init__(self, orientation=Gtk.Orientation.VERTICAL, spacing=5)
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
        fixed.put(clock, 430, 40)

        # Spotify card
        self.home_card = HomeSpotifyCard()
        fixed.put(self.home_card, 30, 130)

        # Temperature widget — top-left
        self.temp_widget = TemperatureWidget()
        fixed.put(self.temp_widget, 30, 40)

        # Dock — bottom-center
        dock = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=60)
        dock.get_style_context().add_class("floating-dock")

        def create_icon_button(path):
            btn = Gtk.Button()
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(path, 42, 42, True)
            img = Gtk.Image.new_from_pixbuf(pixbuf)
            btn.set_image(img)
            btn.set_relief(Gtk.ReliefStyle.NONE)
            btn.get_style_context().add_class("dock-button")
            return btn

        btn_home   = create_icon_button("/home/root/media/home.png")
        btn_music  = create_icon_button("/home/root/media/music.png")
        btn_cam    = create_icon_button("/home/root/media/camera.png")
        # Map button — uses your map.png icon
        btn_map    = create_icon_button("/home/root/media/map.png")

        for b in [btn_home, btn_music, btn_cam, btn_map]:
            dock.pack_start(b, False, False, 0)

        btn_home.connect( "clicked", lambda x: self.navigate("home"))
        btn_music.connect("clicked", lambda x: self.navigate("music"))
        btn_cam.connect(  "clicked", lambda x: self.navigate("camera"))
        btn_map.connect(  "clicked", lambda x: self.navigate("map"))

        fixed.put(dock, 250, 530)

        overlay.add_overlay(fixed)
        return overlay

    def navigate(self, name):
        if name == "camera":
            self.camera_screen.start_camera()
        else:
            self.camera_screen.stop_camera()
        self.stack.set_visible_child_name(name)


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
