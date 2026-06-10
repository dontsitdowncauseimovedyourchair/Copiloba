import gi
# Force the script to use GTK3 instead of GTK4
gi.require_version('Gtk', '3.0')
# Import the GTK3 map library
gi.require_version('OsmGpsMap', '1.0')
from gi.repository import Gtk, OsmGpsMap

class Gtk3MapDashboard(Gtk.Window):
    def __init__(self):
        # GTK3 uses slightly different window initialization than GTK4
        super().__init__(title="GTK3 Navigation")
        self.set_default_size(800, 480)
        
        # 1. Create the Map Widget
        self.map_widget = OsmGpsMap.Map()
        
        # 2. Add an On-Screen Display (OSD) for the scale/zoom controls
        osd = OsmGpsMap.MapOsd(show_scale=True, show_coordinates=False)
        self.map_widget.layer_add(osd)
        
        # 3. Center on Ciudad López Mateos (Latitude, Longitude, Zoom Level)
        self.map_widget.set_center_and_zoom(19.5556, -99.2472, 14)
        
        # 4. Add the map to the window
        # Note: GTK3 uses .add() instead of GTK4's .set_child()
        self.add(self.map_widget)

if __name__ == '__main__':
    win = Gtk3MapDashboard()
    # GTK3 requires explicitly connecting the close button to the main loop quit
    win.connect("destroy", Gtk.main_quit)
    
    # GTK3 requires you to explicitly tell it to show all child widgets
    win.show_all()
    
    # Start the GTK3 rendering loop
    Gtk.main()
