#!/usr/bin/env python3
"""RIPPERDOC, a native Cyberpunk 2077 save editor for the Steam Deck.

dacctal-themed pywebview front end over the proven cp77edit engine. Safe scalar
edits only (level, street cred, attributes, perk points) plus one-click build
presets and a best-in-slot cyberware reference. Every save is auto-backed-up.
"""

import glob
import os
import re
import sys
import traceback
from pathlib import Path

# webview is imported lazily inside main()/browse_folder so that server.py
# (browser/Deck mode) can import the Api class without pywebview installed.

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cp77edit.editor import SaveEditor, SaveError, ATTRIBUTES, ATTR_LABELS  # noqa
from cp77edit.builds import PRESETS, UNIVERSAL, UNIVERSAL_QUICKHACKS  # noqa


def res_root():
    """Directory that holds web/ and assets/ — the PyInstaller bundle dir when
    frozen (AppImage build), else the source tree."""
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))

HOME = Path.home()
APPID = "1091500"
SAVE_SUBPATH = "Saved Games/CD Projekt Red/Cyberpunk 2077"
PROTON_TAIL = f"steamapps/compatdata/{APPID}/pfx/drive_c/users/steamuser/{SAVE_SUBPATH}"

# Every place a Steam client might live (native, Flatpak, older ~/.steam link,
# and both the internal drive and any SD card / external mount).
STEAM_BASES = [
    HOME / ".local/share/Steam",
    HOME / ".steam/steam",
    HOME / ".steam/root",
    HOME / ".var/app/com.valvesoftware.Steam/.local/share/Steam",  # Flatpak Steam
]

# Direct globs that don't depend on parsing Steam's library index.
STATIC_GLOBS = [
    "/run/media/*/" + PROTON_TAIL,          # SD card / USB (SteamOS mounts)
    "/run/media/*/*/" + PROTON_TAIL,
    "/media/*/" + PROTON_TAIL,
    str(HOME / "Documents" / SAVE_SUBPATH),  # native / GOG / manually copied
    str(HOME / "Saved Games" / SAVE_SUBPATH),
    str(HOME / SAVE_SUBPATH),
    # Dev fallback: bundled samples so the app is testable off a Deck
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "_samples"),
]


def _steam_library_paths():
    """Read Steam's libraryfolders.vdf from every known Steam base and return
    the library roots (an SD card library lives outside the default path)."""
    libs = set()
    for base in STEAM_BASES:
        if not base.is_dir():
            continue
        libs.add(str(base))
        for vdf in (base / "steamapps/libraryfolders.vdf",
                    base / "config/libraryfolders.vdf"):
            if not vdf.is_file():
                continue
            try:
                text = vdf.read_text(errors="ignore")
            except OSError:
                continue
            # entries look like:  "path"   "/run/media/mmcblk0p1"
            for m in re.finditer(r'"path"\s*"([^"]+)"', text):
                libs.add(m.group(1))
    return libs


class Api:
    def __init__(self):
        self.editor = None

    # ---- discovery ------------------------------------------------------
    def _save_roots(self, extra=None):
        roots = []
        globs = list(STATIC_GLOBS)
        if extra:
            globs.insert(0, extra)
        # add the Cyberpunk save folder inside every Steam library we can find
        for lib in _steam_library_paths():
            globs.append(os.path.join(lib, PROTON_TAIL))
        for g in globs:
            for path in glob.glob(g):
                if os.path.isdir(path) and path not in roots:
                    roots.append(path)
        return roots

    def list_saves(self, extra_dir=None):
        out = []
        seen = set()
        for root in self._save_roots(extra_dir):
            for entry in sorted(os.listdir(root)):
                folder = os.path.join(root, entry)
                if folder in seen:
                    continue
                sav = os.path.join(folder, "sav.dat")
                if os.path.isfile(sav):
                    seen.add(folder)
                    out.append({
                        "name": entry,
                        "folder": folder,
                        "mtime": os.path.getmtime(sav),
                        "size_mb": round(os.path.getsize(sav) / 1048576, 1),
                    })
        out.sort(key=lambda x: x["mtime"], reverse=True)
        return out

    def browse_folder(self):
        import webview
        win = webview.windows[0]
        res = win.create_file_dialog(webview.FOLDER_DIALOG)
        if not res:
            return None
        folder = res[0]
        if os.path.isfile(os.path.join(folder, "sav.dat")):
            return folder
        # they may have picked the parent containing many saves
        return folder

    # ---- load / read ----------------------------------------------------
    def load_save(self, folder):
        try:
            self.editor = SaveEditor(folder)
            return {"ok": True, "state": self.editor.read_state()}
        except (SaveError, Exception) as e:  # noqa
            traceback.print_exc()
            return {"ok": False, "error": str(e)}

    def get_state(self):
        if not self.editor:
            return {"ok": False, "error": "no save loaded"}
        return {"ok": True, "state": self.editor.read_state()}

    # ---- edits ----------------------------------------------------------
    def set_level(self, value):
        return self._apply(lambda: self.editor.set_level(value))

    def set_street_cred(self, value):
        return self._apply(lambda: self.editor.set_street_cred(value))

    def set_attribute(self, attr, value):
        return self._apply(lambda: self.editor.set_attribute(attr, value))

    def set_perk_points(self, value):
        return self._apply(lambda: self.editor.set_perk_points(value))

    def set_attribute_points(self, value):
        if not self.editor:
            return {"ok": False, "error": "no save loaded"}
        try:
            res = self.editor.set_attribute_points(value)
            if res is None:
                return {"ok": False, "error": "no_attr_slot",
                        "state": self.editor.read_state()}
            return {"ok": True, "state": self.editor.read_state()}
        except Exception as e:  # noqa
            traceback.print_exc()
            return {"ok": False, "error": str(e)}

    def apply_preset(self, key):
        preset = PRESETS.get(key)
        if not preset:
            return {"ok": False, "error": "unknown preset"}
        return self._apply(lambda: self.editor.apply_preset(preset))

    def _apply(self, fn):
        if not self.editor:
            return {"ok": False, "error": "no save loaded"}
        try:
            fn()
            return {"ok": True, "state": self.editor.read_state()}
        except Exception as e:  # noqa
            traceback.print_exc()
            return {"ok": False, "error": str(e)}

    # ---- persist --------------------------------------------------------
    def save_changes(self):
        if not self.editor:
            return {"ok": False, "error": "no save loaded"}
        try:
            self.editor.save()
            return {"ok": True, "state": self.editor.read_state()}
        except Exception as e:  # noqa
            traceback.print_exc()
            return {"ok": False, "error": str(e)}

    # ---- reference data -------------------------------------------------
    def get_builds(self):
        return {
            "presets": PRESETS,
            "universal": UNIVERSAL,
            "universal_quickhacks": UNIVERSAL_QUICKHACKS,
            "attributes": list(ATTRIBUTES),
            "attr_labels": ATTR_LABELS,
        }


def main():
    try:
        import webview
    except Exception:
        return _fallback("pywebview isn't installed")
    api = Api()
    here = res_root()
    index = os.path.join(here, "web", "index.html")
    icon = os.path.join(here, "assets", "icon.png")
    try:
        webview.create_window(
            "RIPPERDOC // Cyberpunk 2077 Save Editor",
            index,
            js_api=api,
            width=1180,
            height=820,
            min_size=(900, 680),
            background_color="#0a0a0c",
        )
        try:
            webview.start(debug=("--debug" in sys.argv), icon=icon)
        except TypeError:
            webview.start(debug=("--debug" in sys.argv))
    except Exception as e:  # no GUI/webview backend available
        return _fallback(str(e))


def _fallback(reason):
    """No native window backend — run the browser mode instead so the app still
    works, rather than crashing."""
    print(f"[ripperdoc] native window unavailable ({reason}); "
          f"falling back to browser mode.")
    import server
    server.main()


if __name__ == "__main__":
    main()
