import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GLib
import cairo
import math
import os
from colorthief import ColorThief

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
        self.connect("draw", self._draw)
    def _draw(self, widget, cr):
        w, h = widget.get_allocated_width(), widget.get_allocated_height()
        # Fondo base ultra oscuro
        cr.set_source_rgb(0.02, 0.01, 0.04); cr.paint()
        # Brillo púrpura central
        grad = cairo.RadialGradient(w*0.4, h*0.4, 0, w*0.4, h*0.4, w*0.6)
        grad.add_color_stop_rgba(0, 0.4, 0.1, 0.6, 0.4)
        grad.add_color_stop_rgba(1, 0.02, 0.01, 0.04, 0)
        cr.set_source(grad); cr.paint()
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

# ──────────────────────────────────────────────
# 3. INTERFAZ Y NAVEGACIÓN
# ──────────────────────────────────────────────

class BottomBar(Gtk.Box):
    def __init__(self, nav_callback):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=100)
        self.set_halign(Gtk.Align.CENTER)
        
        btn_map = Gtk.Button(label="🗺️")
        btn_music = Gtk.Button(label="🎵")
        btn_loba = Gtk.Button(label="🐺")

        for b in [btn_map, btn_music, btn_loba]:
            b.get_style_context().add_class("dock-button")
            b.set_relief(Gtk.ReliefStyle.NONE) # Quita el cuadro blanco
            self.pack_start(b, False, False, 0)
        
        btn_music.connect("clicked", lambda x: nav_callback("music"))
        btn_map.connect("clicked", lambda x: nav_callback("home"))

class MusicScreen(Gtk.Overlay):
    def __init__(self, nav_callback):
        super().__init__()
        bg = Gtk.Box()
        bg.get_style_context().add_class("music-background")
        self.add(bg)

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=30)
        content.set_margin_top(40); content.set_margin_bottom(40)
        content.set_margin_start(40); content.set_margin_end(40)
        self.add_overlay(content)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        sidebar.get_style_context().add_class("sidebar-music")
        btn_back = Gtk.Button(label="🏠")
        btn_back.get_style_context().add_class("circle-button")
        btn_back.connect("clicked", lambda x: nav_callback("home"))
        sidebar.pack_start(btn_back, False, False, 0)

        dash = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        dash.get_style_context().add_class("dashboard-music")
        lbl = Gtk.Label(label="11:34")
        lbl.get_style_context().add_class("clock-label")
        dash.pack_start(lbl, True, True, 0)

        content.pack_start(sidebar, False, False, 0)
        content.pack_start(dash, True, True, 0)

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
        fixed.put(MusicCard(), 30, 30)
        fixed.put(MemojiPanel(), 720, 10)
        fixed.put(NavigationPanel(), 720, 265)
        
        # Barra de botones (Dock)
        bar = BottomBar(self.navigate)
        fixed.put(bar, 350, 510) # Centrado abajo
        
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