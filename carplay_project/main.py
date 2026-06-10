import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
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
import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gst", "1.0")

from gi.repository import Gtk, Gdk, GLib, Gst

# ──────────────────────────────────────────────
# 1. ESTILOS CSS (Limpios y sin errores)
# ──────────────────────────────────────────────

def load_all_css():
    try:
        color_thief = ColorThief("album.jpg")
        r, g, b = color_thief.get_color(quality=1)
    except:
        r, g, b = 105, 17, 173 # Morado #6911AD

    dark_r, dark_g, dark_b = max(r-70,0), max(g-70,0), max(b-70,0)

    css = f"""
    .music-background {{
        background-image: linear-gradient(135deg, rgba({r},{g},{b},0.95), rgba({dark_r},{dark_g},{dark_b},0.95));
    }}
    .sidebar-music {{ background: transparent; border-radius: 30px; padding: 20px; }}
    .dashboard-music {{ background: rgba(255,255,255,0.1); border-radius: 40px; padding: 30px; }}
    .clock-label {{ color: white; font-size: 80px; font-weight: 900; }}
    
    /* Botones de la barra inferior */
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
    """
    provider = Gtk.CssProvider()
    provider.load_from_data(css.encode())
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), provider, 800)

# ──────────────────────────────────────────────
# 2. DIBUJOS CAIRO (El "Alma" del Dashboard)
# ──────────────────────────────────────────────

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

        self.connect(
            "draw",
            self._draw
        )

# GLib.timeout_add(
#     16,
#     self.animate
# )

    def animate(self):

        self.phase += 0.008

        self.queue_draw()

        return True

    def _draw(self, widget, cr):

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        # ==========================
        # FONDO BASE
        # ==========================

        cr.set_source_rgb(
            0.12,
            0.11,
            0.16
        )

        cr.paint()

        t = self.phase

        if self.theme == 0:      # Morado

            c1 = (0.55, 0.18, 1.00)
            c2 = (0.35, 0.45, 1.00)
            c3 = (0.15, 0.70, 1.00)
            c4 = (0.85, 0.15, 0.70)
            c5 = (1.00, 1.00, 1.00)
            c6 = (1.00, 0.85, 0.25)

        elif self.theme == 1:    # Rosa

            c1 = (1.00, 0.30, 0.75)
            c2 = (1.00, 0.50, 0.85)
            c3 = (0.80, 0.35, 1.00)
            c4 = (1.00, 0.15, 0.45)
            c5 = (1.00, 1.00, 1.00)
            c6 = (1.00, 0.75, 0.40)

        elif self.theme == 2:    # Azul

            c1 = (0.25, 0.45, 1.00)
            c2 = (0.10, 0.70, 1.00)
            c3 = (0.15, 0.90, 0.90)
            c4 = (0.35, 0.35, 1.00)
            c5 = (1.00, 1.00, 1.00)
            c6 = (0.85, 0.90, 1.00)

        elif self.theme == 3:    # Atardecer

            c1 = (1.00, 0.40, 0.20)
            c2 = (1.00, 0.65, 0.15)
            c3 = (1.00, 0.25, 0.55)
            c4 = (0.80, 0.15, 0.75)
            c5 = (1.00, 1.00, 1.00)
            c6 = (1.00, 0.90, 0.40)

        else:                    # Aqua

            c1 = (0.10, 0.85, 0.75)
            c2 = (0.10, 0.65, 1.00)
            c3 = (0.15, 1.00, 0.60)
            c4 = (0.20, 0.80, 0.95)
            c5 = (1.00, 1.00, 1.00)
            c6 = (0.90, 1.00, 0.60)

        # ==========================
        # BLOB 1 - PURPLE
        # ==========================

        x1 = w * 0.30 + math.sin(t * 0.7) * 180
        y1 = h * 0.25 + math.cos(t * 0.4) * 120

        g1 = cairo.RadialGradient(
            x1,
            y1,
            0,
            x1,
            y1,
            w * 0.75
        )

        g1.add_color_stop_rgba(
            0,
            c1[0],
            c1[1],
            c1[2],
            0.75
        )

        g1.add_color_stop_rgba(
            0.6,
            c1[0],
            c1[1],
            c1[2],
            0.25
        )

        g1.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )

        cr.set_source(g1)
        cr.paint()

        # ==========================
        # BLOB 2 - BLUE
        # ==========================

        x2 = w * 0.75 + math.cos(t * 0.5) * 140
        y2 = h * 0.30 + math.sin(t * 0.8) * 110

        g2 = cairo.RadialGradient(
            x2,
            y2,
            0,
            x2,
            y2,
            w * 0.65
        )

        g2.add_color_stop_rgba(
            0,
            c2[0],
            c2[1],
            c2[2],
            0.60
        )

        g2.add_color_stop_rgba(
            0.6,
            c2[0],
            c2[1],
            c2[2],
            0.20
        )

        g2.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )

        cr.set_source(g2)
        cr.paint()

        # ==========================
        # BLOB 3 - CYAN
        # ==========================

        x3 = w * 0.55 + math.sin(t * 0.9) * 220
        y3 = h * 0.80 + math.cos(t * 0.5) * 90

        g3 = cairo.RadialGradient(
            x3,
            y3,
            0,
            x3,
            y3,
            w * 0.55
        )

        g3.add_color_stop_rgba(
            0,
            c3[0],
            c3[1],
            c3[2],
            0.45
        )

        g3.add_color_stop_rgba(
            0.6,
            c3[0],
            c3[1],
            c3[2],
            0.15
        )

        g3.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )

        cr.set_source(g3)
        cr.paint()

        # ==========================
        # BLOB 4 - MAGENTA
        # ==========================

        x4 = w * 0.90 + math.sin(t * 0.2) * 80
        y4 = h * 0.65 + math.cos(t * 0.6) * 140

        g4 = cairo.RadialGradient(
            x4,
            y4,
            0,
            x4,
            y4,
            w * 0.65
        )

        g4.add_color_stop_rgba(
            0,
            c4[0],
            c4[1],
            c4[2],
            0.35
        )

        g4.add_color_stop_rgba(
            0.6,
            c4[0],
            c4[1],
            c4[2],
            0.12
        )

        g4.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )

        cr.set_source(g4)
        cr.paint()

        # ==========================
        # BLOB 5 - SILVER
        # ==========================

        x5 = w * 0.15 + math.cos(t * 0.35) * 100
        y5 = h * 0.75 + math.sin(t * 0.20) * 60

        g5 = cairo.RadialGradient(
            x5,
            y5,
            0,
            x5,
            y5,
            w * 0.55
        )

        g5.add_color_stop_rgba(
            0,
            c5[0],
            c5[1],
            c5[2],
            0.18
        )

        g5.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )

        cr.set_source(g5)
        cr.paint()

        # ==========================
        # BLOB 6 - GOLD
        # ==========================

        x6 = w * 0.80 + math.sin(t * 0.45) * 120
        y6 = h * 0.20 + math.cos(t * 0.25) * 80


        g6 = cairo.RadialGradient(
            x6,
            y6,
            0,
            x6,
            y6,
            w * 0.45
        )

        g6.add_color_stop_rgba(
            0,
            c6[0],
            c6[1],
            c6[2],
            0.30
        )

        g6.add_color_stop_rgba(
            0.6,
            c6[0],
            c6[1],
            c6[2],
            0.10
        )

        g6.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )

        cr.set_source(g6)
        cr.paint()

        # ==========================
        # CENTER GLOW
        # ==========================

        glow = cairo.RadialGradient(
            w * 0.5,
            h * 0.5,
            0,
            w * 0.5,
            h * 0.5,
            w * 0.7
        )

        glow.add_color_stop_rgba(
            0,
            1,
            1,
            1,
            0.08
        )

        glow.add_color_stop_rgba(
            1,
            1,
            1,
            1,
            0
        )

        cr.set_source(glow)
        cr.paint()

        return False
    
class MusicCard(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(257, 270)
        self.connect("draw", self._draw)
    def _draw(self, widget, cr):
        rounded_rect(cr, 0, 0, 257, 270, 18)
        cr.set_source_rgb(1, 1, 1); cr.fill()
        # Artist placeholder
        cr.set_source_rgb(0.6, 0.4, 0.8)
        rounded_rect(cr, 15, 15, 90, 90, 10); cr.fill()
        # Text
        cr.set_source_rgb(0, 0, 0)
        cr.select_font_face("Sans", 0, 1)
        cr.set_font_size(14); cr.move_to(120, 50); cr.show_text("RECENTLY PLAYED")
        cr.set_font_size(20); cr.move_to(120, 75); cr.show_text("COOL")
        cr.set_source_rgb(0.8, 0, 0.4)
        cr.set_font_size(16); cr.move_to(120, 95); cr.show_text("Dua Lipa")
        return False


# ──────────────────────────────────────────────
# 3. INTERFAZ Y NAVEGACIÓN
# ──────────────────────────────────────────────

class MusicGradientBG(Gtk.DrawingArea):

    def __init__(self):

        super().__init__()

        self.colors = [

            (255, 80, 180),   # rosa
            (120, 70, 255),   # morado
            (60, 180, 255),   # azul
            (255, 180, 60)

        ]

        self.phase = 0

        self.connect(
            "draw",
            self._draw
        )

    def set_palette(self, palette):

        boosted = []

        for r, g, b in palette:

            boosted.append(

                (
                    min(255, int(r * 1.6)),
                    min(255, int(g * 1.6)),
                    min(255, int(b * 1.6))
                )

            )

        self.colors = boosted

        self.queue_draw()

    def _draw(self, widget, cr):

        w = self.get_allocated_width()
        h = self.get_allocated_height()

        cr.set_source_rgb(
            0.10,
            0.08,
            0.15
        )

        cr.paint()

        t = 0

        for i, color in enumerate(self.colors):

            r, g, b = color

            x = (
                w * 0.2
                + i * 200
                + math.sin(t + i) * 120
            )

            y = (
                h * 0.5
                + math.cos(t * 0.7 + i) * 80
            )

            grad = cairo.RadialGradient(
                x,
                y,
                0,
                x,
                y,
                700
            )

            grad.add_color_stop_rgba(
                0,
                r / 255,
                g / 255,
                b / 255,
                0.85
            )

            grad.add_color_stop_rgba(
                1,
                r / 255,
                g / 255,
                b / 255,
                0
            )

            cr.set_source(
                grad
            )

            cr.paint()

        return False

class HomeSpotifyCard(Gtk.Box):

    def __init__(self):

        super().__init__(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=25
        )

        self.set_size_request(
            650,
            320
        )

        self.get_style_context().add_class(
            "dashboard-music"
        )

        # portada

        self.cover = Gtk.Image()

        self.pack_start(
            self.cover,
            False,
            False,
            20
        )

        # lado derecho

        right = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=15
        )

        self.lbl_song = Gtk.Label(
            label="No music playing"
        )

        self.lbl_song.get_style_context().add_class(
            "hero-song"
        )

        self.lbl_song.set_xalign(0)

        self.lbl_artist = Gtk.Label(
            label=""
        )

        self.lbl_artist.get_style_context().add_class(
            "hero-artist"
        )

        self.lbl_artist.set_xalign(0)

        right.pack_start(
            self.lbl_song,
            False,
            False,
            0
        )

        right.pack_start(
            self.lbl_artist,
            False,
            False,
            0
        )

        self.pack_start(
            right,
            True,
            True,
            0
        )

class MusicScreen(Gtk.Overlay):

    def __init__(self, nav_callback):

        super().__init__()

        # =========================
        # SPOTIFY
        # =========================

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id="6186b61db32f4eb59ae55a299ef475ad",
                client_secret="7dea9bd274b0436fafea5b676838c71c",
                redirect_uri="http://127.0.0.1:8888/callback",
                scope="user-read-playback-state user-modify-playback-state",
                cache_path="/home/root/spotify.cache",
                open_browser=False
            )
        )

        self.current_cover = None

        # =========================
        # FONDO
        # =========================

        self.music_bg = MusicGradientBG()

        self.add(
            self.music_bg
        )

        # =========================
        # CONTENIDO PRINCIPAL
        # =========================

        content = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=30
        )

        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(40)
        content.set_margin_end(40)

        self.add_overlay(content)

        # =========================
        # SIDEBAR
        # =========================

        sidebar = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL
        )

        sidebar.get_style_context().add_class(
            "sidebar-music"
        )

        btn_back = Gtk.Button(
            label="🏠"
        )

        btn_back.get_style_context().add_class(
            "circle-button"
        )

        btn_back.connect(
            "clicked",
            lambda x: nav_callback("home")
        )

        sidebar.pack_start(
            btn_back,
            False,
            False,
            0
        )

        # =========================
        # DASHBOARD
        # =========================

        dash = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL
        )

        dash.get_style_context().add_class(
            "dashboard-music"
        )

        dash_main = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=20
        )

        # =========================
        # CONTENIDO CENTRAL
        # =========================

        center = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=25
        )

        center.set_halign(Gtk.Align.CENTER)
        center.set_valign(Gtk.Align.CENTER)

        # portada

        self.album_image = Gtk.Image()

        self.album_image.set_halign(
            Gtk.Align.CENTER
        )
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                "album.jpg",
                320,
                320,
                True
            )

            self.album_image.set_from_pixbuf(
                pixbuf
            )

        except:
            pass

        # titulo grande

        self.lbl_song = Gtk.Label(
            label="Loading..."
        )

        self.lbl_song.get_style_context().add_class(
            "hero-song"
        )

        # artista

        self.lbl_art = Gtk.Label(
            label=""
        )

        self.lbl_art.get_style_context().add_class(
            "hero-artist"
        )

        # controles

        controls = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=40
        )

        self.btn_prev = Gtk.Button()

        self.btn_play = Gtk.Button()

        self.btn_next = Gtk.Button()

        prev_pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "/home/root/media/rewind.png",
            48,
            48,
            True
        )

        prev_img = Gtk.Image.new_from_pixbuf(
            prev_pix
        )

        play_pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "/home/root/media/play.png",
            48,
            48,
            True
        )

        play_img = Gtk.Image.new_from_pixbuf(
            play_pix
        )

        next_pix = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            "/home/root/media/next.png",
            48,
            48,
            True
        )

        next_img = Gtk.Image.new_from_pixbuf(
            next_pix
        )

        self.btn_prev.set_image(
            prev_img
        )

        self.btn_play.set_image(
            play_img
        )

        self.btn_next.set_image(
            next_img
        )

        for btn in [
            self.btn_prev,
            self.btn_play,
            self.btn_next
        ]:
            btn.get_style_context().add_class(
                "transport-button"
            )

        controls.pack_start(
            self.btn_prev,
            False,
            False,
            0
        )

        controls.pack_start(
            self.btn_play,
            False,
            False,
            0
        )

        controls.pack_start(
            self.btn_next,
            False,
            False,
            0
        )

        self.btn_prev.connect(
            "clicked",
            self.previous_track
        )

        self.btn_play.connect(
            "clicked",
            self.toggle_play
        )

        self.btn_next.connect(
            "clicked",
            self.next_track
        )

        center.pack_start(
            self.album_image,
            False,
            False,
            0
        )

        center.pack_start(
            self.lbl_song,
            False,
            False,
            0
        )

        center.pack_start(
            self.lbl_art,
            False,
            False,
            0
        )

        center.pack_start(
            controls,
            False,
            False,
            0
        )

        content.pack_start(
            sidebar,
            False,
            False,
            0
        )

        content.pack_start(
            center,
            True,
            True,
            0
        )
        # =========================
        # ACTUALIZAR SPOTIFY
        # =========================

        self.update_spotify()

        GLib.timeout_add(
            2000,
            self.update_spotify
        )

    def update_album_art(self, url):
        try:

            response = requests.get(
                url,
                timeout=10
            )

            with open(
                "current_album.jpg",
                "wb"
            ) as f:

                f.write(
                    response.content
                )

            # =========================
            # EXTRAER COLORES
            # =========================

            try:

                color_thief = ColorThief(
                    "current_album.jpg"
                )

                palette = color_thief.get_palette(
                    color_count=6
                )

                self.music_bg.set_palette(
                    [
                        palette[0],
                        palette[1],
                        palette[2],
                        palette[3]
                    ]
                )

            except Exception as e:

                print(
                    "ColorThief error:",
                    e
                )

            # =========================
            # CARGAR PORTADA
            # =========================

            pixbuf = GdkPixbuf.Pixbuf.new_from_file(
                "current_album.jpg"
            )

            pixbuf = pixbuf.scale_simple(
                280,
                280,
                GdkPixbuf.InterpType.BILINEAR
            )

            self.album_image.set_from_pixbuf(
                pixbuf
            )

        except Exception as e:

            print(
                "Album art error:",
                e
            )

    def update_spotify(self):

        try:

            playback = self.sp.current_playback()

            if not playback:
                return True

            track = playback["item"]

            if not track:
                return True

            song = track["name"]

            artist = track["artists"][0]["name"]

            cover = (
                track["album"]
                ["images"][0]
                ["url"]
            )

            self.lbl_song.set_text(
                song
            )

            self.lbl_art.set_text(
                artist
            )

            if cover != self.current_cover:

                self.current_cover = cover

                self.update_album_art(
                    cover
                )

        except Exception as e:

            print(
                "Spotify error:",
                e
            )

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

                self.btn_play.set_label(
                    "▶"
                )

            else:

                self.sp.start_playback()

                self.btn_play.set_label(
                    "⏸"
                )

        except Exception as e:

            print(e)

class CameraScreen(Gtk.Overlay):

    def __init__(self, nav_callback):

        super().__init__()

        self.pipeline = Gst.parse_launch(
            "v4l2src device=/dev/video7 ! "
            "image/jpeg,width=640,height=360 ! "
            "jpegdec ! "
            "videoconvert ! "
            "gtksink name=sink"
        )

        sink = self.pipeline.get_by_name(
            "sink"
        )

        video_widget = sink.get_property(
            "widget"
        )

        self.add(
            video_widget
        )

        btn_home = Gtk.Button()

        img = Gtk.Image.new_from_file(
            "/home/root/media/home.png"
        )

        btn_home.set_image(img)

        btn_home.set_halign(
            Gtk.Align.START
        )

        btn_home.set_valign(
            Gtk.Align.START
        )

        btn_home.set_margin_start(20)
        btn_home.set_margin_top(20)

        btn_home.set_size_request(
            64,
            64
        )

        btn_home.connect(
            "clicked",
            lambda x: nav_callback("home")
        )

        guide_layer = Gtk.DrawingArea()

        guide_layer.set_can_focus(False)
        guide_layer.set_sensitive(False)

        guide_layer.connect(
            "draw",
            self.draw_guides
        )

        self.add_overlay(
            guide_layer
        )

        self.add_overlay(
            btn_home
        )

    def draw_guides(self, widget, cr):

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        cr.set_line_width(8)

        # VERDE (lejos)

        cr.set_source_rgba(
            0,
            1,
            0,
            0.85
        )

        cr.move_to(
            w * 0.20,
            h * 0.55
        )

        cr.line_to(
            w * 0.80,
            h * 0.55
        )

        cr.stroke()

        # AMARILLO (medio)

        cr.set_source_rgba(
            1,
            1,
            0,
            0.85
        )

        cr.move_to(
            w * 0.15,
            h * 0.72
        )

        cr.line_to(
            w * 0.85,
            h * 0.72
        )

        cr.stroke()

        # ROJO (peligro)

        cr.set_source_rgba(
            1,
            0,
            0,
            0.85
        )

        cr.move_to(
            w * 0.10,
            h * 0.88
        )

        cr.line_to(
            w * 0.90,
            h * 0.88
        )

        cr.stroke()

        return False
    
    def start_camera(self):

        print("START CAMERA")

        self.pipeline.set_state(
            Gst.State.PLAYING
        )

    def stop_camera(self):

        self.pipeline.set_state(
            Gst.State.NULL
        )
class ClockWidget(Gtk.Box):

    def __init__(self):

        Gtk.Box.__init__(
            self,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5
        )

        self.lbl_date = Gtk.Label()
        self.lbl_clock = Gtk.Label()

        self.lbl_date.set_xalign(0.5)
        self.lbl_clock.set_xalign(0.5)

        self.lbl_date.get_style_context().add_class(
            "date-label"
        )

        self.lbl_clock.get_style_context().add_class(
            "clock-label"
        )

        self.pack_start(
            self.lbl_date,
            False,
            False,
            0
        )

        self.pack_start(
            self.lbl_clock,
            False,
            False,
            0
        )

        self.update_clock()

        GLib.timeout_add(
            1000,
            self.update_clock
        )

    def update_clock(self):

        now = datetime.now()

        self.lbl_clock.set_text(
            now.strftime("%H:%M")
        )

        self.lbl_date.set_text(
            now.strftime("%a %d %b")
        )

        return True

class CarPlayWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="CarPlay OS")
        self.fullscreen()

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.add(self.stack)

        # Cargar Vistas
        self.stack.add_named(self._build_home(), "home")
        self.stack.add_named(MusicScreen(self.navigate), "music")
        self.camera_screen = CameraScreen(
            self.navigate
        )

        self.stack.add_named(
            self.camera_screen,
            "camera"
        )

    def _build_home(self):

        overlay = Gtk.Overlay()
        overlay.add(MainGradientBG())

        fixed = Gtk.Fixed()

        fixed.set_hexpand(True)
        fixed.set_vexpand(True)

        clock = ClockWidget()

        fixed.put(
            clock,
            430,
            40
        )

        card = HomeSpotifyCard()

        fixed.put(
            card,
            30,
            130
        )
        dock = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=60
        )

        dock.get_style_context().add_class(
            "floating-dock"
        )

        def create_icon_button(path):

            btn = Gtk.Button()

            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                path,
                42,
                42,
                True
            )

            img = Gtk.Image.new_from_pixbuf(
                pixbuf
            )

            btn.set_image(img)

            btn.set_relief(
                Gtk.ReliefStyle.NONE
            )

            btn.get_style_context().add_class(
                "dock-button"
            )

            return btn


        btn_home = create_icon_button(
            "/home/root/media/home.png"
        )

        btn_music = create_icon_button(
            "/home/root/media/music.png"
        )

        btn_cam = create_icon_button(
            "/home/root/media/camera.png"
        )

        for b in [btn_home, btn_music, btn_cam]:

            dock.pack_start(
                b,
                False,
                False,
                0
            )

        btn_home.connect(
            "clicked",
            lambda x: self.navigate("home")
        )

        btn_music.connect(
            "clicked",
            lambda x: self.navigate("music")
        )

        btn_cam.connect(
            "clicked",
            lambda x: self.navigate("camera")
        )

        fixed.put(
            dock,
            310,
            530
        )

        overlay.add_overlay(fixed)

        return overlay
        
    def navigate(self, name):

        if name == "camera":

            self.camera_screen.start_camera()

        else:

            self.camera_screen.stop_camera()

        self.stack.set_visible_child_name(name)

if __name__ == "__main__":
    Gst.init(None)
    load_all_css()
    win = CarPlayWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
