"""
voice/command_router.py — Copiloba Command Router

Maps action strings (from Claude's JSON response) to real app operations.
The router receives a reference to CarPlayWindow so it can call navigate()
and the Spotipy methods already wired up in MusicScreen.

All methods are called on the GTK main thread (via GLib.idle_add in
assistant.py), so direct GTK calls here are safe.
"""


class CommandRouter:
    """
    Wires Claude command actions to live application objects.

    Usage:
        router = CommandRouter(window)
        router.route("open_music")
        router.route("pause_music")
    """

    def __init__(self, window):
        """
        window : CarPlayWindow instance
            Provides navigate() and music_screen.sp (Spotipy client).
        """
        self._window = window

    def route(self, action: str) -> bool:
        """
        Dispatch an action string.
        Returns True if the action was recognised, False otherwise.
        """
        handlers = {
            # ── Navigation ──────────────────────────────────────────────────
            "open_home":    self._open_home,
            "open_music":   self._open_music,
            "open_camera":  self._open_camera,
            "open_map":     self._open_map,

            # ── Spotify ─────────────────────────────────────────────────────
            "pause_music":  self._pause_music,
            "resume_music": self._resume_music,
            "next_track":   self._next_track,
            "prev_track":   self._prev_track,
        }

        handler = handlers.get(action)
        if handler:
            try:
                handler()
            except Exception as e:
                print(f"[CommandRouter] Error executing '{action}': {e}")
            return True

        print(f"[CommandRouter] Unknown action: '{action}'")
        return False

    # ── Navigation ───────────────────────────────────────────────────────────

    def _open_home(self):
        self._window.navigate("home")

    def _open_music(self):
        self._window.navigate("music")

    def _open_camera(self):
        self._window.navigate("camera")

    def _open_map(self):
        self._window.navigate("map")

    # ── Spotify controls — delegates to MusicScreen's Spotipy instance ──────
    # MusicScreen already has next_track / previous_track / toggle_play
    # bound to buttons; we call the Spotipy client directly here to avoid
    # needing a widget reference.

    def _sp(self):
        """Return the Spotipy client from MusicScreen (may raise if not init)."""
        return self._window.music_screen.sp

    def _pause_music(self):
        playback = self._sp().current_playback()
        if playback and playback.get("is_playing"):
            self._sp().pause_playback()

    def _resume_music(self):
        playback = self._sp().current_playback()
        if playback and not playback.get("is_playing"):
            self._sp().start_playback()

    def _next_track(self):
        self._sp().next_track()

    def _prev_track(self):
        self._sp().previous_track()
