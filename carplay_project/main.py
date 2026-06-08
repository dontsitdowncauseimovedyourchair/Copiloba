import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo
import math
import os
from colorthief import ColorThief
from datetime import datetime


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
    .sidebar-music {{ background: rgba(30,30,30,0.6); border-radius: 30px; padding: 20px; }}
    .dashboard-music {{ background: rgba(255,255,255,0.1); border-radius: 40px; padding: 30px; }}
    .clock-label {{ color: white; font-size: 80px; font-weight: 900; }}
    
    /* Botones de la barra inferior */
    .dock-button {{
        background: transparent;
        border: none;
        box-shadow: none;
        font-size: 35px;
        color: white;
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

        self.connect(
            "draw",
            self._draw
        )

        GLib.timeout_add(
            16,
            self.animate
        )

    def animate(self):

        self.phase += 0.008

        self.queue_draw()

        return True

    def _draw(self, widget, cr):

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        # ==========================
        # FONDO OSCURO
        # ==========================

        cr.set_source_rgb(
            0.02,
            0.01,
            0.04
        )

        cr.paint()

        t = self.phase

        # ==========================
        # BLOB 1
        # ==========================

        x1 = w * 0.30 + math.sin(t * 0.7) * 180
        y1 = h * 0.25 + math.cos(t * 0.4) * 120

        r1 = w * 0.65

        g1 = cairo.RadialGradient(
            x1,
            y1,
            0,
            x1,
            y1,
            r1
        )

        g1.add_color_stop_rgba(
            0,
            0.45,
            0.10,
            0.85,
            0.45
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
        # BLOB 2
        # ==========================

        x2 = w * 0.75 + math.cos(t * 0.5) * 140
        y2 = h * 0.30 + math.sin(t * 0.8) * 110

        r2 = w * 0.50

        hue_shift = (
            math.sin(t * 0.3) + 1
        ) / 2

        g2 = cairo.RadialGradient(
            x2,
            y2,
            0,
            x2,
            y2,
            r2
        )

        g2.add_color_stop_rgba(
            0,
            0.25 + hue_shift * 0.25,
            0.35,
            0.95,
            0.35
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
        # BLOB 3
        # ==========================

        x3 = w * 0.55 + math.sin(t * 0.9) * 220
        y3 = h * 0.80 + math.cos(t * 0.5) * 90

        r3 = w * 0.45

        green = (
            math.sin(t * 0.4) + 1
        ) / 2

        g3 = cairo.RadialGradient(
            x3,
            y3,
            0,
            x3,
            y3,
            r3
        )

        g3.add_color_stop_rgba(
            0,
            0.10,
            0.15 + green * 0.35,
            0.90,
            0.25
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
        # BLOB 4
        # ==========================

        x4 = w * 0.90 + math.sin(t * 0.2) * 80
        y4 = h * 0.65 + math.cos(t * 0.6) * 140

        r4 = w * 0.55

        red = (
            math.sin(t * 0.25) + 1
        ) / 2

        g4 = cairo.RadialGradient(
            x4,
            y4,
            0,
            x4,
            y4,
            r4
        )

        g4.add_color_stop_rgba(
            0,
            0.60 + red * 0.25,
            0.15,
            0.55,
            0.20
        )

        g4.add_color_stop_rgba(
            1,
            0,
            0,
            0,
            0
        )
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
            w * 0.45
        )

        g5.add_color_stop_rgba(
            0,
            0.95,
            0.95,
            1.0,
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

        cr.set_source(g4)
        cr.paint()
        # ==========================
        # BLOB 6 - GOLD
        # ==========================

        x6 = w * 0.80 + math.sin(t * 0.45) * 120
        y6 = h * 0.20 + math.cos(t * 0.25) * 80

        gold = (
            math.sin(t * 0.15) + 1
        ) / 2

        g6 = cairo.RadialGradient(
            x6,
            y6,
            0,
            x6,
            y6,
            w * 0.35
        )

        g6.add_color_stop_rgba(
            0,
            1.0,
            0.75 + gold * 0.15,
            0.20,
            0.14
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
            w * 0.55,
            h * 0.45,
            0,
            w * 0.55,
            h * 0.45,
            w * 0.40
        )

        glow.add_color_stop_rgba(
            0,
            1,
            1,
            1,
            0.10
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

class MemojiPanel(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(272, 243)
        self.connect("draw", self._draw)
    def _draw(self, widget, cr):
        w, h = 272, 243
        grad = cairo.LinearGradient(0, 0, 0, h)
        grad.add_color_stop_rgb(0, 0.78, 0.6, 0.92) # Lila
        grad.add_color_stop_rgb(1, 0.44, 0.34, 0.52) # Morado
        cr.set_source(grad)
        rounded_rect(cr, 0, 0, w, h, 15); cr.fill()
        # Emoji placeholder (Lobo)
        cr.set_source_rgb(1, 1, 1)
        cr.set_font_size(80); cr.move_to(w/2-40, h/2+30); cr.show_text("🐺")
        return False
"""
class NavigationPanel(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_size_request(272, 272)
        self.connect("draw", self._draw)
    def _draw(self, widget, cr):
        w, h = 272, 272
        cr.set_source_rgb(0.1, 0.12, 0.15)
        rounded_rect(cr, 0, 0, w, h, 15); cr.fill()
        # Simular mapa
        cr.set_source_rgb(0.2, 0.25, 0.3)
        cr.set_line_width(4)
        for i in range(0, w, 40):
            cr.move_to(i, 0); cr.line_to(i, h); cr.stroke()
            cr.move_to(0, i); cr.line_to(w, i); cr.stroke()
        return False
"""
# ──────────────────────────────────────────────
# 3. INTERFAZ Y NAVEGACIÓN
# ──────────────────────────────────────────────
class BottomBar(Gtk.Overlay):
    """
    Bottom dock:
    - Cairo dibuja el fondo
    - GTK maneja botones reales
    """

    def __init__(self, nav_callback):

        Gtk.Overlay.__init__(self)

        self.set_size_request(1011, 85)

        # ======================
        # CAPA CAIRO
        # ======================

        self.bg = Gtk.DrawingArea()
        self.bg.connect("draw", self._draw)

        self.add(self.bg)

        # ======================
        # CAPA BOTONES
        # ======================

        button_box = Gtk.Box(
            orientation=Gtk.Orientation.HORIZONTAL,
            spacing=100
        )

        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_valign(Gtk.Align.CENTER)

        btn_map = Gtk.Button(label="🗺️")
        btn_music = Gtk.Button(label="🎵")
        btn_loba = Gtk.Button(label="🐺")

        for b in [btn_map, btn_music, btn_loba]:

            b.get_style_context().add_class(
                "dock-button"
            )

            b.set_relief(
                Gtk.ReliefStyle.NONE
            )

            button_box.pack_start(
                b,
                False,
                False,
                0
            )

        btn_map.connect(
            "clicked",
            lambda x: nav_callback("home")
        )

        btn_music.connect(
            "clicked",
            lambda x: nav_callback("music")
        )

        btn_loba.connect(
            "clicked",
            lambda x: print("Copiloba")
        )

        self.add_overlay(button_box)

    def _draw(self, widget, cr):

        w = widget.get_allocated_width()
        h = widget.get_allocated_height()

        # ======================
        # FONDO
        # ======================

        grad = cairo.LinearGradient(
            0, 0, 0, h
        )

        grad.add_color_stop_rgba(
            0.0,
            0,
            0,
            0,
            0.70
        )

        grad.add_color_stop_rgba(
            0.62,
            1,
            1,
            1,
            0.70
        )

        cr.set_source(grad)

        cr.rectangle(
            0,
            0,
            w,
            h
        )

        cr.fill()

        # ======================
        # FRANJA INFERIOR
        # ======================

        grad2 = cairo.LinearGradient(
            0,
            h * 0.39,
            0,
            h
        )

        grad2.add_color_stop_rgba(
            0,
            0,
            0,
            0,
            0.03
        )

        grad2.add_color_stop_rgba(
            1,
            0.83,
            0.83,
            0.83,
            0.27
        )

        cr.set_source(grad2)

        cr.rectangle(
            0,
            h * 0.39,
            w,
            h
        )

        cr.fill()

        # ======================
        # INDICADORES PAGINA
        # ======================

        self._draw_page_indicator(
            cr,
            w * 0.085,
            h * 0.64,
            "25"
        )

        self._draw_page_indicator(
            cr,
            w * 0.915,
            h * 0.64,
            "25"
        )

        # ======================
        # SEPARADORES
        # ======================

        cr.set_source_rgba(
            1,
            1,
            1,
            0.50
        )

        cr.set_line_width(1)

        for sx in (
            w * 0.373,
            w * 0.627
        ):

            cr.move_to(
                sx,
                h * 0.43
            )

            cr.line_to(
                sx,
                h * 0.91
            )

            cr.stroke()

        return False

    def _draw_page_indicator(
        self,
        cr,
        cx,
        cy,
        number
    ):

        cr.set_source_rgb(
            0.20,
            0.55,
            1.0
        )

        cr.select_font_face(
            "sans",
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_BOLD
        )

        cr.set_font_size(18)

        cr.move_to(
            cx - 42,
            cy + 7
        )

        cr.show_text("‹")

        cr.move_to(
            cx + 28,
            cy + 7
        )

        cr.show_text("›")

        # fondo cápsula

        cr.set_source_rgba(
            1,
            1,
            1,
            0.20
        )

        rounded_rect(
            cr,
            cx - 22,
            cy - 14,
            44,
            28,
            14
        )

        cr.fill()

        # número

        cr.set_source_rgb(
            1,
            1,
            1
        )

        cr.select_font_face(
            "Sans",
            cairo.FONT_SLANT_NORMAL,
            cairo.FONT_WEIGHT_NORMAL
        )

        cr.set_font_size(20)

        ext = cr.text_extents(number)

        cr.move_to(
            cx - ext.width / 2,
            cy + 8
        )

        cr.show_text(number)

class MusicScreen(Gtk.Overlay):
    def __init__(self, nav_callback):
        super().__init__()
        
        # 1. Fondo (Base del Overlay)
        bg = Gtk.Box()
        bg.get_style_context().add_class("music-background")
        self.add(bg)

        # 2. Contenedor Principal (Horizontal)
        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        content.set_margin_top(40)
        content.set_margin_bottom(40)
        content.set_margin_start(40)
        content.set_margin_end(40)
        self.add_overlay(content)

        # 3. Sidebar (Izquierda)
        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.get_style_context().add_class("sidebar-music")
        btn_back = Gtk.Button(label="🏠")
        btn_back.get_style_context().add_class("circle-button")
        btn_back.connect("clicked", lambda x: nav_callback("home"))
        sidebar.pack_start(btn_back, False, False, 0)

        # 4. Dashboard (Contenedor de la derecha)
        dash = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        dash.get_style_context().add_class("dashboard-music")

        # 5. Dash Main (El layout interno: Izquierda [Reloj/Imagen] + Derecha [Cards])
        dash_main = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=20)
        dash_main.get_style_context().add_class("dashboard")

        # --- Panel Izquierdo del Dash ---
        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        lbl_date = Gtk.Label(label="Mon 18 May")
        lbl_date.get_style_context().add_class("date-label")
        lbl_clock = Gtk.Label(label="11:34")
        lbl_clock.get_style_context().add_class("clock-label")
        
        img = Gtk.Image()
        try:
            # Asegúrate de importar GdkPixbuf al inicio: from gi.repository import GdkPixbuf
            from gi.repository import GdkPixbuf
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale("album.jpg", 240, 240, True)
            img.set_from_pixbuf(pixbuf)
        except: 
            pass
        img.get_style_context().add_class("album-cover")

        left.pack_start(lbl_date, False, False, 0)
        left.pack_start(lbl_clock, False, False, 0)
        left.pack_start(img, False, False, 0)
        dash_main.pack_start(left, False, False, 0)

        # --- Panel Derecho del Dash ---
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        
        map_card = Gtk.Box()
        map_card.get_style_context().add_class("map-card")
        map_card.set_size_request(450, 250)
        lbl_map = Gtk.Label(label="MAP")
        lbl_map.get_style_context().add_class("map-text")
        map_card.add(lbl_map)

        music_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        music_card.get_style_context().add_class("music-card")
        lbl_art = Gtk.Label(label="Labrinth")
        lbl_art.get_style_context().add_class("artist-label")
        lbl_song = Gtk.Label(label="ALL FOR US")
        lbl_song.get_style_context().add_class("song-label")
        lbl_ctrl = Gtk.Label(label="⏮  ⏸  ⏭")
        lbl_ctrl.get_style_context().add_class("controls-label")
        
        music_card.pack_start(lbl_art, False, False, 0)
        music_card.pack_start(lbl_song, False, False, 0)
        music_card.pack_start(lbl_ctrl, False, False, 0)

        right.pack_start(map_card, True, True, 0)
        right.pack_start(music_card, True, True, 0)
        dash_main.pack_start(right, True, True, 0)

        # 6. Empaquetado final en orden jerárquico
        dash.pack_start(dash_main, True, True, 0) # Metemos todo el diseño en el dash
        content.pack_start(sidebar, False, False, 0) # Sidebar al contenido principal
        content.pack_start(dash, True, True, 0)    # Dash al contenido principal

class ClockWidget(Gtk.Box):

    def __init__(self):

        Gtk.Box.__init__(
            self,
            orientation=Gtk.Orientation.VERTICAL,
            spacing=5
        )

        self.lbl_date = Gtk.Label()
        self.lbl_clock = Gtk.Label()

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
        self.set_default_size(1024, 600)
        self.set_resizable(False)

        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.add(self.stack)

        # Cargar Vistas
        self.stack.add_named(self._build_home(), "home")
        self.stack.add_named(MusicScreen(self.navigate), "music")

    def _build_home(self):
        overlay = Gtk.Overlay()
        overlay.add(MainGradientBG())

        fixed = Gtk.Fixed()

        clock = ClockWidget()

        fixed.put(
            clock,
            35,
            25
        )

        fixed.put(
            MusicCard(),
            35,
            150
        )

        fixed.put(
            MemojiPanel(),
            720,
            10
        )
 #       fixed.put(NavigationPanel(), 720, 265)
        
        # Barra de botones (Dock)
        bar = BottomBar(self.navigate)
        fixed.put(bar, 6, 515) # Centrado abajo
        
        overlay.add_overlay(fixed)
        return overlay

    def navigate(self, name):
        self.stack.set_visible_child_name(name)

if __name__ == "__main__":
    load_all_css()
    win = CarPlayWindow()
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()
