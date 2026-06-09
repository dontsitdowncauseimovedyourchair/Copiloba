"""
osm_map_gtk3.py — OpenStreetMap viewer for STM32MP257F-DK
Dependencies: python3-gobject (GTK3), Pillow, urllib (stdlib)

Usage:
    python3 osm_map_gtk3.py
    python3 osm_map_gtk3.py --lat 19.4326 --lon -99.1332 --zoom 13
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

import math
import os
import io
import threading
import argparse
import urllib.request
from PIL import Image, ImageDraw, ImageFont

# ─── Configuration ────────────────────────────────────────────────────────────

TILE_SERVER  = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
CACHE_DIR    = os.path.expanduser("~/.cache/osm_tiles")
TILE_SIZE    = 256          # OSM standard tile size in pixels
USER_AGENT   = "STM32MP257-MapViewer/1.0 (embedded; contact: user@example.com)"
FETCH_TIMEOUT = 10          # seconds per tile HTTP request
MIN_ZOOM     = 2
MAX_ZOOM     = 18

# ─── Tile Math ────────────────────────────────────────────────────────────────

def lat_lon_to_tile_float(lat: float, lon: float, zoom: int):
    """Convert lat/lon to fractional tile coordinates at the given zoom."""
    n = 2.0 ** zoom
    x = (lon + 180.0) / 360.0 * n
    lat_r = math.radians(lat)
    y = (1.0 - math.asinh(math.tan(lat_r)) / math.pi) / 2.0 * n
    return x, y


def lat_lon_to_tile(lat: float, lon: float, zoom: int):
    x, y = lat_lon_to_tile_float(lat, lon, zoom)
    return int(x), int(y)


def tile_to_lat_lon(tx: int, ty: int, zoom: int):
    """Top-left corner of a tile → lat/lon."""
    n = 2.0 ** zoom
    lon = tx / n * 360.0 - 180.0
    lat_r = math.atan(math.sinh(math.pi * (1 - 2 * ty / n)))
    return math.degrees(lat_r), lon

# ─── Tile Fetching & Cache ────────────────────────────────────────────────────

def _cache_path(z: int, x: int, y: int) -> str:
    return os.path.join(CACHE_DIR, str(z), str(x), f"{y}.png")


def fetch_tile(z: int, x: int, y: int) -> Image.Image:
    """
    Return a 256×256 RGBA PIL image for tile (z, x, y).
    Checks disk cache first; fetches from OSM if missing.
    Returns a grey placeholder on network error.
    """
    path = _cache_path(z, x, y)

    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA")
        except Exception:
            os.remove(path)          # corrupt cache entry — refetch

    # Clamp tile coords to valid range
    max_tile = 2 ** z
    if not (0 <= x < max_tile and 0 <= y < max_tile):
        return _placeholder_tile("out of range")

    url = TILE_SERVER.format(z=z, x=x, y=y)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            data = resp.read()

        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)

        return Image.open(io.BytesIO(data)).convert("RGBA")

    except Exception as e:
        print(f"[tile] fetch error {z}/{x}/{y}: {e}")
        return _placeholder_tile("no data")


def _placeholder_tile(label: str) -> Image.Image:
    """Grey tile with a label — used when a tile cannot be loaded."""
    img = Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (200, 200, 200, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, TILE_SIZE - 1, TILE_SIZE - 1], outline=(180, 180, 180))
    draw.text((TILE_SIZE // 2 - 20, TILE_SIZE // 2 - 6), label, fill=(120, 120, 120))
    return img

# ─── Map Rendering (Pillow) ───────────────────────────────────────────────────

def render_map(center_lat: float, center_lon: float, zoom: int,
               width: int, height: int) -> Image.Image:
    """
    Render a (width × height) map image centred on (center_lat, center_lon).
    Fetches and stitches OSM tiles using Pillow.
    """
    # Fractional tile position of the centre pixel
    cx_f, cy_f = lat_lon_to_tile_float(center_lat, center_lon, zoom)

    # How many tiles we need on each side
    half_w = math.ceil(width  / (2 * TILE_SIZE)) + 1
    half_h = math.ceil(height / (2 * TILE_SIZE)) + 1

    tile_x0 = int(cx_f) - half_w
    tile_y0 = int(cy_f) - half_h
    tile_x1 = int(cx_f) + half_w + 1
    tile_y1 = int(cy_f) + half_h + 1

    cols = tile_x1 - tile_x0
    rows = tile_y1 - tile_y0

    # Stitch all tiles onto a canvas
    canvas_w = cols * TILE_SIZE
    canvas_h = rows * TILE_SIZE
    canvas = Image.new("RGBA", (canvas_w, canvas_h))

    for col, tx in enumerate(range(tile_x0, tile_x1)):
        for row, ty in enumerate(range(tile_y0, tile_y1)):
            tile_img = fetch_tile(zoom, tx, ty)
            canvas.paste(tile_img, (col * TILE_SIZE, row * TILE_SIZE))

    # Pixel position of centre on the canvas
    centre_px = int((cx_f - tile_x0) * TILE_SIZE)
    centre_py = int((cy_f - tile_y0) * TILE_SIZE)

    # Crop to exactly (width × height) centred on the map centre
    left   = centre_px - width  // 2
    top    = centre_py - height // 2
    right  = left + width
    bottom = top  + height

    # Pad if the crop extends beyond the canvas (e.g. at low zoom levels)
    if left < 0 or top < 0 or right > canvas_w or bottom > canvas_h:
        padded = Image.new("RGBA", (right - left, bottom - top), (200, 200, 200, 255))
        src_x = max(0, -left)
        src_y = max(0, -top)
        padded.paste(canvas, (src_x, src_y))
        return padded
    else:
        return canvas.crop((left, top, right, bottom))

# ─── PIL → GdkPixbuf conversion ──────────────────────────────────────────────

def pil_to_pixbuf(img: Image.Image) -> GdkPixbuf.Pixbuf:
    """Convert a PIL RGBA image to a GdkPixbuf (zero-copy via raw bytes)."""
    img_rgb = img.convert("RGB")
    w, h = img_rgb.size
    data = img_rgb.tobytes()          # raw RGB bytes
    return GdkPixbuf.Pixbuf.new_from_bytes(
        GLib.Bytes.new(data),
        GdkPixbuf.Colorspace.RGB,
        False,                        # no alpha
        8,                            # bits per channel
        w, h,
        w * 3                         # row stride
    )

# ─── GTK3 Map Widget ─────────────────────────────────────────────────────────

class OsmMapWidget(Gtk.DrawingArea):
    """
    A GTK3 DrawingArea that displays an OSM tile map.
    Supports:
      • Drag-to-pan
      • Scroll-wheel zoom
      • Keyboard arrows to pan, +/- to zoom
    """

    def __init__(self, lat: float = 48.8566, lon: float = 2.3522, zoom: int = 13,
                 width: int = 800, height: int = 480):
        super().__init__()

        self.center_lat = lat
        self.center_lon = lon
        self.zoom       = zoom
        self.map_w      = width
        self.map_h      = height

        self._pixbuf      = None       # current rendered pixbuf
        self._loading     = False
        self._drag_origin = None       # (mouse_x, mouse_y) at drag start
        self._drag_lat    = lat        # center_lat at drag start
        self._drag_lon    = lon

        self.set_size_request(width, height)
        self.set_can_focus(True)

        mask = (
            Gdk.EventMask.BUTTON_PRESS_MASK   |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.SCROLL_MASK         |
            Gdk.EventMask.KEY_PRESS_MASK
        )
        self.add_events(mask)

        self.connect("draw",                  self._on_draw)
        self.connect("button-press-event",    self._on_button_press)
        self.connect("button-release-event",  self._on_button_release)
        self.connect("motion-notify-event",   self._on_motion)
        self.connect("scroll-event",          self._on_scroll)
        self.connect("key-press-event",       self._on_key_press)
        self.connect("size-allocate",         self._on_size_allocate)

        self._schedule_load()

    # ── Loading ──────────────────────────────────────────────────────────────

    def _schedule_load(self):
        if self._loading:
            return
        self._loading = True
        # Snapshot parameters for the background thread
        lat, lon, zoom = self.center_lat, self.center_lon, self.zoom
        w,   h         = self.map_w,      self.map_h
        threading.Thread(
            target=self._load_thread,
            args=(lat, lon, zoom, w, h),
            daemon=True
        ).start()

    def _load_thread(self, lat, lon, zoom, w, h):
        try:
            img    = render_map(lat, lon, zoom, w, h)
            pixbuf = pil_to_pixbuf(img)
        except Exception as e:
            print(f"[map] render error: {e}")
            pixbuf = None
        finally:
            GLib.idle_add(self._on_map_loaded, lat, lon, zoom, pixbuf)

    def _on_map_loaded(self, lat, lon, zoom, pixbuf):
        # Only accept the result if the map hasn't panned/zoomed since
        if lat == self.center_lat and lon == self.center_lon and zoom == self.zoom:
            self._pixbuf  = pixbuf
            self._loading = False
            self.queue_draw()
        else:
            # Parameters changed while loading — trigger a fresh load
            self._loading = False
            self._schedule_load()
        return False   # remove idle callback

    # ── Drawing ──────────────────────────────────────────────────────────────

    def _on_draw(self, widget, cr):
        w = self.get_allocated_width()
        h = self.get_allocated_height()

        if self._pixbuf:
            Gdk.cairo_set_source_pixbuf(cr, self._pixbuf, 0, 0)
            cr.paint()
        else:
            # Loading placeholder
            cr.set_source_rgb(0.85, 0.85, 0.85)
            cr.paint()
            cr.set_source_rgb(0.4, 0.4, 0.4)
            cr.select_font_face("Sans", 0, 0)
            cr.set_font_size(16)
            text = "Loading map tiles…"
            ext  = cr.text_extents(text)
            cr.move_to(w / 2 - ext.width / 2, h / 2)
            cr.show_text(text)

        # Crosshair at centre
        cx, cy = w / 2, h / 2
        cr.set_source_rgba(0.9, 0.1, 0.1, 0.8)
        cr.set_line_width(1.5)
        cr.move_to(cx - 10, cy); cr.line_to(cx + 10, cy)
        cr.move_to(cx, cy - 10); cr.line_to(cx, cy + 10)
        cr.stroke()

        # Attribution (OSM requires this)
        cr.set_source_rgba(1, 1, 1, 0.75)
        cr.rectangle(0, h - 18, w, 18)
        cr.fill()
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.set_font_size(11)
        cr.move_to(4, h - 4)
        cr.show_text("© OpenStreetMap contributors")

        # Zoom level indicator
        cr.set_source_rgba(1, 1, 1, 0.75)
        cr.rectangle(w - 50, 4, 46, 20)
        cr.fill()
        cr.set_source_rgb(0.2, 0.2, 0.2)
        cr.set_font_size(12)
        cr.move_to(w - 46, 18)
        cr.show_text(f"z={self.zoom}")

    # ── Interaction ──────────────────────────────────────────────────────────

    def _on_button_press(self, widget, event):
        if event.button == 1:
            self._drag_origin = (event.x, event.y)
            self._drag_lat    = self.center_lat
            self._drag_lon    = self.center_lon
        self.grab_focus()

    def _on_button_release(self, widget, event):
        if event.button == 1 and self._drag_origin:
            dx = event.x - self._drag_origin[0]
            dy = event.y - self._drag_origin[1]
            if abs(dx) > 2 or abs(dy) > 2:
                self._apply_pixel_pan(dx, dy, from_lat=self._drag_lat,
                                              from_lon=self._drag_lon)
            self._drag_origin = None

    def _on_motion(self, widget, event):
        if self._drag_origin and (event.state & Gdk.ModifierType.BUTTON1_MASK):
            dx = event.x - self._drag_origin[0]
            dy = event.y - self._drag_origin[1]
            # Live pan preview using fractional pixel offset (no reload yet)
            # For simplicity on embedded hw, just reload on release
            # For smoother panning, store offset and composite on draw
            pass   # heavy live redraw is expensive on A35 — pan on release

    def _on_scroll(self, widget, event):
        if event.direction == Gdk.ScrollDirection.UP:
            self._set_zoom(self.zoom + 1)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self._set_zoom(self.zoom - 1)

    def _on_key_press(self, widget, event):
        pan_step = TILE_SIZE // 2   # pixels per keypress
        key = event.keyval
        if   key == Gdk.KEY_plus  or key == Gdk.KEY_equal: self._set_zoom(self.zoom + 1)
        elif key == Gdk.KEY_minus:                          self._set_zoom(self.zoom - 1)
        elif key == Gdk.KEY_Left:   self._apply_pixel_pan( pan_step, 0)
        elif key == Gdk.KEY_Right:  self._apply_pixel_pan(-pan_step, 0)
        elif key == Gdk.KEY_Up:     self._apply_pixel_pan(0,  pan_step)
        elif key == Gdk.KEY_Down:   self._apply_pixel_pan(0, -pan_step)

    def _on_size_allocate(self, widget, alloc):
        if alloc.width != self.map_w or alloc.height != self.map_h:
            self.map_w = alloc.width
            self.map_h = alloc.height
            self._schedule_load()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _set_zoom(self, new_zoom: int):
        new_zoom = max(MIN_ZOOM, min(MAX_ZOOM, new_zoom))
        if new_zoom != self.zoom:
            self.zoom = new_zoom
            self._schedule_load()

    def _apply_pixel_pan(self, dx_px: float, dy_px: float,
                         from_lat: float = None, from_lon: float = None):
        """
        Pan the map by (dx_px, dy_px) screen pixels.
        Converts pixel delta to lat/lon delta using the tile scale at current zoom.
        """
        base_lat = from_lat if from_lat is not None else self.center_lat
        base_lon = from_lon if from_lon is not None else self.center_lon

        # Tile coordinate of the current centre
        cx, cy = lat_lon_to_tile_float(base_lat, base_lon, self.zoom)

        # Shift by pixel delta (note: right/down = positive tile coords)
        new_cx = cx - dx_px / TILE_SIZE
        new_cy = cy - dy_px / TILE_SIZE

        # Back to lat/lon
        n = 2.0 ** self.zoom
        new_lon = new_cx / n * 360.0 - 180.0
        new_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * new_cy / n))))

        # Clamp latitude to Mercator limits
        new_lat = max(-85.0511, min(85.0511, new_lat))

        self.center_lat = new_lat
        self.center_lon = new_lon
        self._schedule_load()

    def go_to(self, lat: float, lon: float, zoom: int = None):
        """Jump the map to a new position (public API)."""
        self.center_lat = lat
        self.center_lon = lon
        if zoom is not None:
            self.zoom = max(MIN_ZOOM, min(MAX_ZOOM, zoom))
        self._schedule_load()

# ─── Main Window ─────────────────────────────────────────────────────────────

class MapWindow(Gtk.Window):
    def __init__(self, lat: float, lon: float, zoom: int):
        super().__init__(title="OSM Map Viewer — STM32MP257F-DK")
        self.set_default_size(800, 480)    # native DSI panel resolution
        self.connect("destroy", Gtk.main_quit)

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(vbox)

        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        toolbar.set_margin_start(4)
        toolbar.set_margin_end(4)
        toolbar.set_margin_top(4)
        toolbar.set_margin_bottom(4)
        vbox.pack_start(toolbar, False, False, 0)

        btn_zoom_in  = Gtk.Button(label=" + ")
        btn_zoom_out = Gtk.Button(label=" − ")
        lat_entry    = Gtk.Entry(); lat_entry.set_width_chars(10)
        lon_entry    = Gtk.Entry(); lon_entry.set_width_chars(10)
        btn_go       = Gtk.Button(label="Go")

        lat_entry.set_placeholder_text("Latitude")
        lon_entry.set_placeholder_text("Longitude")
        lat_entry.set_text(str(round(lat, 5)))
        lon_entry.set_text(str(round(lon, 5)))

        toolbar.pack_start(btn_zoom_in,  False, False, 0)
        toolbar.pack_start(btn_zoom_out, False, False, 0)
        toolbar.pack_start(Gtk.Label(label="  Lat:"), False, False, 0)
        toolbar.pack_start(lat_entry,    False, False, 0)
        toolbar.pack_start(Gtk.Label(label="  Lon:"), False, False, 0)
        toolbar.pack_start(lon_entry,    False, False, 0)
        toolbar.pack_start(btn_go,       False, False, 0)

        # ── Map widget ───────────────────────────────────────────────────────
        self.map_widget = OsmMapWidget(lat=lat, lon=lon, zoom=zoom)
        vbox.pack_start(self.map_widget, True, True, 0)

        # ── Wire toolbar ─────────────────────────────────────────────────────
        btn_zoom_in.connect("clicked",  lambda _: self.map_widget._set_zoom(self.map_widget.zoom + 1))
        btn_zoom_out.connect("clicked", lambda _: self.map_widget._set_zoom(self.map_widget.zoom - 1))

        def on_go(_btn):
            try:
                new_lat = float(lat_entry.get_text())
                new_lon = float(lon_entry.get_text())
                self.map_widget.go_to(new_lat, new_lon)
            except ValueError:
                pass

        btn_go.connect("clicked", on_go)
        lat_entry.connect("activate", on_go)
        lon_entry.connect("activate", on_go)

        self.show_all()

# ─── Entry Point ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="OSM Map Viewer for STM32MP257F-DK")
    parser.add_argument("--lat",  type=float, default=48.8566,  help="Initial latitude")
    parser.add_argument("--lon",  type=float, default=2.3522,   help="Initial longitude")
    parser.add_argument("--zoom", type=int,   default=13,       help="Initial zoom level (2–18)")
    args = parser.parse_args()

    os.makedirs(CACHE_DIR, exist_ok=True)

    win = MapWindow(lat=args.lat, lon=args.lon, zoom=args.zoom)
    Gtk.main()


if __name__ == "__main__":
    main()