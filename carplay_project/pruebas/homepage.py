#!/usr/bin/env python3
"""
CarPlay-style Dashboard — GTK 3.0
Translated from the HTML/CSS design.
"""

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import cairo
import math
import os


# ──────────────────────────────────────────────
# CSS PROVIDER
# ──────────────────────────────────────────────

def load_css():
    css_provider = Gtk.CssProvider()
    css_file = os.path.join(os.path.dirname(__file__), "carplay_style.css")
    if os.path.exists(css_file):
        css_provider.load_from_path(css_file)
    else:
        css_provider.load_from_data(b"")  # fallback: empty
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )


# ──────────────────────────────────────────────
# GRADIENT BACKGROUND  (drawn with Cairo)
# ──────────────────────────────────────────────

class GradientBackground(Gtk.DrawingArea):
    """Deep purple radial-gradient background behind the main panel."""

    def __init__(self):
        super().__init__()
        self.connect("draw", self._draw)

    def _draw(self, widget, cr):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        # Dark base
        cr.set_source_rgb(0.02, 0.01, 0.04)
        cr.paint()

        # Central glow — matches the purple ellipses from the original
        gradient = cairo.RadialGradient(w * 0.46, h * 0.48, 0, w * 0.46, h * 0.48, w * 0.55)
        gradient.add_color_stop_rgba(0.0, 0.48, 0.22, 0.65, 0.55)   # #7A38A6
        gradient.add_color_stop_rgba(0.45, 0.28, 0.08, 0.40, 0.40)
        gradient.add_color_stop_rgba(1.0,  0.02, 0.01, 0.04, 0.0)
        cr.set_source(gradient)
        cr.paint()

        # Second, offset glow (screen blend simulation)
        gradient2 = cairo.RadialGradient(w * 0.25, h * 0.35, 0, w * 0.25, h * 0.35, w * 0.32)
        gradient2.add_color_stop_rgba(0.0, 0.55, 0.18, 0.72, 0.30)
        gradient2.add_color_stop_rgba(1.0, 0.02, 0.01, 0.04, 0.0)
        cr.set_source(gradient2)
        cr.set_operator(cairo.OPERATOR_SCREEN)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)

        return False


# ──────────────────────────────────────────────
# ROUNDED-RECTANGLE helper
# ──────────────────────────────────────────────

def rounded_rect(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + r,     y + r,     r, math.pi,       3 * math.pi / 2)
    cr.arc(x + w - r, y + r,     r, 3 * math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0,             math.pi / 2)
    cr.arc(x + r,     y + h - r, r, math.pi / 2,   math.pi)
    cr.close_path()


# ──────────────────────────────────────────────
# MUSIC CARD
# ──────────────────────────────────────────────

class MusicCard(Gtk.DrawingArea):
    """
    White card — "Recently Played / COOL / Dua Lipa" + album grid.
    Mirrors .large-music-2 (256×269 px, border-radius 16.9 px).
    """

    ALBUMS = [
        # (label, colour)  — placeholder colours matching screenshot tones
        ("#3B7A57", "Translation"),
        ("#1A1A2E", "Dark"),
        ("#D3CBCB", "Light"),
        ("#C62A88", "CHVRCHES"),
        ("#6AAB9C", "Robyn"),
        ("#C46B2D", "Orange"),
        ("#7B3F00", "Brown"),
        ("#E8B4B8", "Pink"),
    ]

    def __init__(self):
        super().__init__()
        self.set_size_request(257, 270)
        self.connect("draw", self._draw)

    def _draw(self, widget, cr):
        w, h = 257, 270

        # Card background
        cr.set_source_rgb(1, 1, 1)
        rounded_rect(cr, 0, 0, w, h, 17)
        cr.fill()

        # ── Artist thumbnail (top-left square, ~99×99 px)
        cr.set_source_rgb(0.55, 0.35, 0.75)   # placeholder purple
        rounded_rect(cr, 12, 10, 99, 99, 8)
        cr.fill()
        # small person silhouette hint
        cr.set_source_rgba(1, 1, 1, 0.35)
        cr.arc(62, 42, 18, 0, 2 * math.pi)
        cr.fill()
        cr.set_source_rgba(1, 1, 1, 0.25)
        cr.arc(62, 78, 28, math.pi, 2 * math.pi)
        cr.fill()

        # ── Text labels
        # "RECENTLY PLAYED"
        cr.set_source_rgb(0.62, 0.62, 0.62)
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(7.8)
        cr.move_to(126, 83)
        cr.show_text("RECENTLY PLAYED")

        # "COOL"
        cr.set_source_rgb(0, 0, 0)
        cr.set_font_size(12)
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.move_to(126, 97)
        cr.show_text("COOL")

        # "Dua Lipa"
        cr.set_source_rgb(0.854, 0, 0.514)   # #DA0083
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11.7)
        cr.move_to(126, 112)
        cr.show_text("Dua Lipa")

        # ── Music note icon (top-right)
        cr.set_source_rgb(0.988, 0.176, 0.522)  # Apple Music pink
        cr.set_font_size(16)
        cr.move_to(229, 28)
        cr.show_text("♪")

        # ── Album grid separator line
        cr.set_source_rgb(0.88, 0.88, 0.88)
        cr.set_line_width(0.5)
        cr.move_to(0, 127)
        cr.line_to(257, 127)
        cr.stroke()

        # ── Album grid  (4 cols × 2 rows beneath separator)
        colours = [
            (0.23, 0.48, 0.34), (0.10, 0.10, 0.18),
            (0.83, 0.80, 0.80), (0.78, 0.16, 0.53),
            (0.42, 0.67, 0.61), (0.77, 0.42, 0.18),
            (0.48, 0.25, 0.00), (0.91, 0.71, 0.72),
        ]
        labels = ["Translation", "Dark", "Light", "CHVRCHES",
                  "Robyn", "Cara", "Frank", "Pink"]
        cell_w, cell_h = 64, 71
        for i, (col, lbl) in enumerate(zip(colours, labels)):
            col_i = i % 4
            row_i = i // 4
            cx = col_i * cell_w
            cy = 127 + row_i * cell_h
            cr.set_source_rgb(*col)
            cr.rectangle(cx, cy, cell_w, cell_h)
            cr.fill()
            # tiny label
            cr.set_source_rgba(1, 1, 1, 0.7)
            cr.set_font_size(7)
            cr.move_to(cx + 4, cy + cell_h - 6)
            cr.show_text(lbl)

        return False


# ──────────────────────────────────────────────
# MEMOJI PANEL
# ──────────────────────────────────────────────

class MemojiPanel(Gtk.DrawingArea):
    """
    Purple gradient panel with a wolf Memoji placeholder.
    Mirrors .chatgpt-image-may-wrapper (272×243 px).
    """

    def __init__(self):
        super().__init__()
        self.set_size_request(272, 243)
        self.connect("draw", self._draw)

    def _draw(self, widget, cr):
        w, h = 272, 243

        # Gradient background: rgba(199,154,235) → rgba(113,87,133)
        grad = cairo.LinearGradient(0, 0, 0, h)
        grad.add_color_stop_rgb(0.0, 199 / 255, 154 / 255, 235 / 255)
        grad.add_color_stop_rgb(1.0, 113 / 255,  87 / 255, 133 / 255)
        cr.set_source(grad)
        rounded_rect(cr, 0, 0, w, h, 8)
        cr.fill()

        # Wolf emoji placeholder (drawn)
        self._draw_wolf(cr, w // 2, h // 2 + 10, 90)

        return False

    def _draw_wolf(self, cr, cx, cy, r):
        """Simple stylised wolf face as a placeholder for the Memoji image."""
        # Head
        cr.set_source_rgb(0.58, 0.53, 0.50)
        cr.arc(cx, cy, r, 0, 2 * math.pi)
        cr.fill()

        # Ears
        for ex in (cx - r * 0.60, cx + r * 0.60):
            cr.set_source_rgb(0.58, 0.53, 0.50)
            cr.move_to(ex, cy - r * 0.70)
            cr.rel_line_to(-20 if ex < cx else 20, -35)
            cr.rel_line_to(28 if ex < cx else -28, 35)
            cr.close_path()
            cr.fill()
            # inner ear
            cr.set_source_rgb(0.85, 0.65, 0.65)
            cr.move_to(ex, cy - r * 0.72)
            cr.rel_line_to(-10 if ex < cx else 10, -20)
            cr.rel_line_to(16 if ex < cx else -16, 20)
            cr.close_path()
            cr.fill()

        # Eyes (big cartoon)
        for ex in (cx - r * 0.32, cx + r * 0.32):
            cr.set_source_rgb(1, 1, 1)
            cr.arc(ex, cy - r * 0.10, 18, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(0.55, 0.35, 0.10)
            cr.arc(ex, cy - r * 0.10, 11, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(0.0, 0.0, 0.0)
            cr.arc(ex, cy - r * 0.10, 7, 0, 2 * math.pi)
            cr.fill()
            cr.set_source_rgb(1, 1, 1)
            cr.arc(ex + 4, cy - r * 0.10 - 4, 3, 0, 2 * math.pi)
            cr.fill()

        # Snout
        cr.set_source_rgb(0.72, 0.65, 0.62)
        cr.arc(cx, cy + r * 0.22, 26, 0, 2 * math.pi)
        cr.fill()
        # Nose
        cr.set_source_rgb(0.25, 0.18, 0.15)
        cr.arc(cx, cy + r * 0.10, 9, 0, 2 * math.pi)
        cr.fill()

        # Paws covering mouth (surprised look)
        for px, py in ((cx - 52, cy + 30), (cx + 52, cy + 30)):
            cr.set_source_rgb(0.58, 0.53, 0.50)
            rounded_rect(cr, px - 22, py - 22, 44, 44, 10)
            cr.fill()
            # fingers hint
            cr.set_source_rgb(0.50, 0.45, 0.42)
            for fi in range(4):
                cr.arc(px - 15 + fi * 10, py - 22, 5, math.pi, 2 * math.pi)
                cr.fill()


# ──────────────────────────────────────────────
# NAVIGATION PANEL
# ──────────────────────────────────────────────

class NavigationPanel(Gtk.DrawingArea):
    """
    Map-style navigation tile.
    Mirrors .div-2 (271×271 px, border-radius 8.8 px).
    """

    def __init__(self):
        super().__init__()
        self.set_size_request(272, 272)
        self.connect("draw", self._draw)

    def _draw(self, widget, cr):
        w, h = 272, 272

        # Dark map background
        cr.set_source_rgb(0.12, 0.13, 0.17)
        rounded_rect(cr, 0, 0, w, h, 9)
        cr.fill_preserve()
        cr.clip()

        # Grid of city blocks (simulated map)
        self._draw_map(cr, w, h)

        # Route highlight line
        self._draw_route(cr, w, h)

        # Location pin label "The Embarcadero"
        self._draw_location_pin(cr, w, h)

        # Navigation header box
        self._draw_nav_header(cr, w)

        return False

    def _draw_map(self, cr, w, h):
        cr.set_source_rgb(0.14, 0.16, 0.21)
        cr.paint()
        # Roads
        cr.set_source_rgb(0.22, 0.24, 0.30)
        cr.set_line_width(8)
        for x in range(0, w, 38):
            cr.move_to(x, 0); cr.line_to(x, h); cr.stroke()
        for y in range(0, h, 45):
            cr.move_to(0, y); cr.line_to(w, y); cr.stroke()
        # Diagonal main boulevard
        cr.set_source_rgb(0.28, 0.30, 0.38)
        cr.set_line_width(14)
        cr.move_to(50, 0); cr.line_to(180, h); cr.stroke()
        cr.move_to(80, 0); cr.line_to(210, h); cr.stroke()

    def _draw_route(self, cr, w, h):
        cr.set_source_rgb(0.20, 0.55, 1.0)
        cr.set_line_width(6)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(w * 0.42, 0)
        cr.line_to(w * 0.42, h * 0.55)
        cr.line_to(w * 0.62, h * 0.55)
        cr.line_to(w * 0.62, h)
        cr.stroke()
        # Current position dot
        cx, cy = w * 0.42, h * 0.55
        cr.set_source_rgb(1, 1, 1)
        cr.arc(cx, cy, 9, 0, 2 * math.pi); cr.fill()
        cr.set_source_rgb(0.20, 0.55, 1.0)
        cr.arc(cx, cy, 6, 0, 2 * math.pi); cr.fill()

    def _draw_location_pin(self, cr, w, h):
        lx, ly = w * 0.50, h * 0.56
        # Pin badge
        cr.set_source_rgb(0.87, 0.89, 0.96)
        badge_w, badge_h = 108, 22
        rounded_rect(cr, lx - badge_w / 2, ly, badge_w, badge_h, 3)
        cr.fill()
        cr.set_source_rgb(0.36, 0.59, 0.99)
        cr.set_line_width(1)
        rounded_rect(cr, lx - badge_w / 2, ly, badge_w, badge_h, 3)
        cr.stroke()
        # Label text
        cr.set_source_rgb(0.19, 0.31, 0.53)
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(11)
        extents = cr.text_extents("The Embarcadero")
        cr.move_to(lx - extents.width / 2, ly + 15)
        cr.show_text("The Embarcadero")

    def _draw_nav_header(self, cr, w):
        # Semi-transparent header box
        cr.set_source_rgba(0, 0, 0, 0.5)
        rounded_rect(cr, 22, 16, 227, 66, 15)
        cr.fill()

        # Up arrow
        cr.set_source_rgb(1, 1, 1)
        cr.set_line_width(3)
        cr.set_line_cap(cairo.LINE_CAP_ROUND)
        cr.move_to(44, 70); cr.line_to(44, 30)
        cr.stroke()
        cr.move_to(38, 40); cr.line_to(44, 30); cr.line_to(50, 40)
        cr.stroke()

        # "22 mi"
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(19)
        cr.set_source_rgb(1, 1, 1)
        cr.move_to(70, 52)
        cr.show_text("22 mi")

        # "Continue Straight"
        cr.select_font_face("Inter", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(12)
        cr.set_source_rgb(0.678, 0.675, 0.761)   # #ADACC2
        cr.move_to(70, 68)
        cr.show_text("Continue Straight")


# ──────────────────────────────────────────────
# BOTTOM BAR
# ──────────────────────────────────────────────

class BottomBar(Gtk.DrawingArea):
    """
    Dock bar at the bottom of the screen.
    Gradient background + page indicators + app icons.
    """

    ICONS = [
        ("🗺", "Maps"),
        ("📻", "Radio"),
        ("📞", "Phone"),
        ("💨", "Fan"),
        ("⚙", "Settings"),
    ]

    def __init__(self):
        super().__init__()
        self.set_size_request(-1, 85)
        self.connect("draw", self._draw)

    def _draw(self, widget, cr):
        w = self.get_allocated_width()
        h = 85

        # Background gradient
        grad = cairo.LinearGradient(0, 0, 0, h)
        grad.add_color_stop_rgba(0.0, 0, 0, 0, 0.70)
        grad.add_color_stop_rgba(0.62, 1, 1, 1, 0.70)
        cr.set_source(grad)
        cr.rectangle(0, 0, w, h)
        cr.fill()

        # Lower stripe
        grad2 = cairo.LinearGradient(0, h * 0.39, 0, h)
        grad2.add_color_stop_rgba(0, 0, 0, 0, 0.03)
        grad2.add_color_stop_rgba(1, 0.83, 0.83, 0.83, 0.27)
        cr.set_source(grad2)
        cr.rectangle(0, h * 0.39, w, h)
        cr.fill()

        mid = w / 2

        # ── Left page indicator: "< 25 >"
        self._draw_page_indicator(cr, w * 0.085, h * 0.64, "25")

        # ── Right page indicator: "< 25 >"
        self._draw_page_indicator(cr, w * 0.905, h * 0.64, "25")

        # ── Vertical separators
        cr.set_source_rgba(1, 1, 1, 0.50)
        cr.set_line_width(1)
        for sx in (w * 0.373, w * 0.627):
            cr.move_to(sx, h * 0.43)
            cr.line_to(sx, h * 0.91)
            cr.stroke()

        # ── App grid icon (9-dots) area
        cr.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(26)
        cr.set_source_rgb(1, 1, 1)
        icons_x = [mid - 145, mid - 75, mid, mid + 75, mid + 145]
        emojis   = ["🗺", "📻", "📞", "💨", "⚙"]
        for ix, em in zip(icons_x, emojis):
            cr.move_to(ix - 13, h * 0.78)
            cr.show_text(em)

        return False

    def _draw_page_indicator(self, cr, cx, cy, number):
        """Draw  <  [25]  >  page-turn control."""
        cr.set_source_rgb(0.20, 0.55, 1.0)   # blue arrows
        cr.select_font_face("sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(18)
        cr.move_to(cx - 42, cy + 7); cr.show_text("‹")
        cr.move_to(cx + 28, cy + 7); cr.show_text("›")

        # Pill background
        cr.set_source_rgba(1, 1, 1, 0.20)
        rounded_rect(cr, cx - 22, cy - 14, 44, 28, 14)
        cr.fill()

        # Number
        cr.set_source_rgb(1, 1, 1)
        cr.select_font_face("SF Pro Rounded", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(20)
        ext = cr.text_extents(number)
        cr.move_to(cx - ext.width / 2, cy + 8)
        cr.show_text(number)


# ──────────────────────────────────────────────
# MAIN WINDOW
# ──────────────────────────────────────────────

class CarPlayWindow(Gtk.Window):

    WIDTH  = 1024
    HEIGHT = 600

    def __init__(self):
        super().__init__(title="CarPlay Dashboard")
        self.set_default_size(self.WIDTH, self.HEIGHT)
        self.set_resizable(False)
        self.set_name("carplay-window")
        self.connect("destroy", Gtk.main_quit)
        self.connect("key-press-event", self._on_key)

        self._build_ui()

    # ── Layout ────────────────────────────────

    def _build_ui(self):
        # Root overlay: gradient sits under everything
        overlay = Gtk.Overlay()
        self.add(overlay)

        # Background
        bg = GradientBackground()
        bg.set_hexpand(True)
        bg.set_vexpand(True)
        overlay.add(bg)

        # Foreground fixed layout
        fixed = Gtk.Fixed()
        fixed.set_size_request(self.WIDTH, self.HEIGHT)
        overlay.add_overlay(fixed)

        # ── Music card  (top-left)
        music = MusicCard()
        fixed.put(music, 29, 28)

        # ── Memoji panel  (top-right)
        memoji = MemojiPanel()
        fixed.put(memoji, 748, 9)

        # ── Navigation panel (bottom-right)
        nav = NavigationPanel()
        fixed.put(nav, 748, 258)

        # ── Bottom bar (full width, pinned to bottom)
        bottom = BottomBar()
        bottom.set_size_request(self.WIDTH, 85)
        fixed.put(bottom, 5, 507)

    # ── Keyboard shortcut ─────────────────────

    def _on_key(self, widget, event):
        if event.keyval in (Gdk.KEY_Escape, Gdk.KEY_q):
            Gtk.main_quit()


# ──────────────────────────────────────────────
# ENTRY POINT
# ──────────────────────────────────────────────

def main():
    load_css()
    win = CarPlayWindow()
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
