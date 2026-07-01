"""High level Cyberpunk 2077 save editor.

Wraps the vendored container parser (see _container/, proven to round trip a
patch 2.31 sav.dat byte for byte) and exposes safe, scalar edits to the player
development data: level, street cred, the five attributes and unspent perk
points. Every edit is a same length Int32 patch, so array offsets never move
and the save structure stays intact.
"""

import json
import os
import struct
import sys
from pathlib import Path

_C = os.path.join(os.path.dirname(__file__), "_container")
if _C not in sys.path:
    sys.path.insert(0, _C)

import cp2077chunk as _chunk

# Patch 2.31 grew the chunk table capacity to 512 entries; the upstream parser
# only whitelisted 256 and 1024. Belt and braces in case the vendored copy is
# ever refreshed from upstream.
if 0x200 not in _chunk.DataChunkTableChunk.VALID_CAPACITY:
    _chunk.DataChunkTableChunk.VALID_CAPACITY = (0x100, 0x200, 0x400)

from cp2077save import SaveFile  # noqa: E402

ATTRIBUTES = ("Strength", "Reflexes", "TechnicalAbility", "Intelligence", "Cool")
# Body is labelled "Strength" inside the save.
ATTR_LABELS = {
    "Strength": "Body",
    "Reflexes": "Reflexes",
    "TechnicalAbility": "Technical Ability",
    "Intelligence": "Intelligence",
    "Cool": "Cool",
}
ATTR_MIN, ATTR_MAX = 3, 20
LEVEL_MIN, LEVEL_MAX = 1, 50
CRED_MIN, CRED_MAX = 1, 50


class SaveError(Exception):
    pass


def _strs(struct_data):
    return [s for s in struct_data._strings if isinstance(s, str)]


class SaveEditor:
    def __init__(self, folder):
        self.folder = Path(folder)
        if self.folder.is_file():
            self.folder = self.folder.parent
        sav = self.folder / "sav.dat"
        if not sav.is_file():
            raise SaveError(f"No sav.dat in {self.folder}")
        self.sf = SaveFile(self.folder)
        self._meta_path = self.folder / "metadata.9.json"
        self._meta = None
        if self._meta_path.is_file():
            self._meta = json.loads(self._meta_path.read_text())
        self._container = None
        self._config = None
        self._dev = None
        self._open()

    # ---- low level ------------------------------------------------------
    def _open(self):
        self._container = self.sf.nodes.ScriptableSystemsContainer
        self._config = self._container.__enter__()
        self._dev = self._find_player_dev(self._config)
        if self._dev is None:
            raise SaveError("Could not locate the player's development data")

    @staticmethod
    def _find_player_dev(config):
        for item in config:
            if item._name != "PlayerDevelopmentData":
                continue
            names = set(_strs(item))
            if "Level" in names and "StreetCred" in names:
                return item
        return None

    def _field_raw(self, struct_data, field):
        _, _, slc = struct_data._field_info(field)
        return slc, bytes(bytearray.__getitem__(struct_data, slc))

    def _set_field_raw(self, struct_data, slc, new_bytes):
        old = bytes(bytearray.__getitem__(struct_data, slc))
        if len(new_bytes) != len(old):
            raise SaveError("internal: refusing variable length field write")
        bytearray.__setitem__(struct_data, slc, new_bytes)

    # Byte size of a serialised scalar field by its type name. Enum/gamedata*
    # "Type" values are stored as a 2-byte index into the node string table.
    _TYPE_SIZE = {
        "Int8": 1, "Uint8": 1, "Bool": 1,
        "Int16": 2, "Uint16": 2, "CName": 2,
        "Int32": 4, "Uint32": 4, "Float": 4, "CRUID": 4,
        "Int64": 8, "Uint64": 8, "TweakDBID": 8, "NodeRef": 8,
    }

    def _type_size(self, type_name):
        t = str(type_name)
        if t in self._TYPE_SIZE:
            return self._TYPE_SIZE[t]
        if "Type" in t:  # gamedataProficiencyType / gamedataStatType / ... -> index
            return 2
        return 4

    def _walk(self, pb):
        """Walk a CDPR array-of-struct field. Yields (abs_offset, fields).

        fields maps name -> (type_name, value_abs_offset, raw_bytes).
        Element boundaries are derived from the last field's type size, so
        variable field counts per element are handled correctly.
        """
        count = struct.unpack("<I", pb[:4])[0]
        strings = self._dev._strings
        n_strings = len(strings)
        p = 4
        for _ in range(count):
            if p + 2 > len(pb):
                break
            fc = struct.unpack("<H", pb[p : p + 2])[0]
            descs = []
            ok = True
            for k in range(fc):
                o = p + 2 + 8 * k
                nm, ty, off = struct.unpack("<HHI", pb[o : o + 8])
                if nm >= n_strings or ty >= n_strings:
                    ok = False
                    break
                descs.append((nm, ty, off))
            if not ok:
                break
            fields = {}
            for k, (nm, ty, off) in enumerate(descs):
                end = (p + descs[k + 1][2]) if k < fc - 1 else None
                fields[strings[nm]] = (
                    strings[ty],
                    p + off,
                    pb[p + off : end] if end else pb[p + off :],
                )
            yield p, fields
            if descs:
                last_off = descs[-1][2]
                p += last_off + self._type_size(strings[descs[-1][1]])
            else:
                p += 2

    # ---- reads ----------------------------------------------------------
    def read_state(self):
        profs = self._proficiencies()
        attrs = self._attributes()
        return {
            "folder": str(self.folder),
            "save_name": self.folder.name,
            "game_version": self.sf.header.game_ver / 1000.0,
            "save_version": self.sf.header.save_ver,
            "name": (self._meta or {}).get("name", self.folder.name),
            "lifepath": self._meta_field("lifePath"),
            "body_gender": self._meta_field("bodyGender"),
            "play_time_h": round((self._meta_field("playTime") or 0) / 3600.0, 1),
            "patch": self._meta_field("buildPatch"),
            "level": profs.get("Level"),
            "street_cred": profs.get("StreetCred"),
            "attributes": {a: attrs.get(a) for a in ATTRIBUTES},
            "attr_labels": ATTR_LABELS,
            "perk_points": self._perk_points(),
        }

    def _proficiencies(self):
        _, pb = self._field_raw(self._dev, "proficiencies")
        out = {}
        for _, fields in self._walk(pb):
            t = fields.get("type")
            cl = fields.get("currentLevel")
            if not t or not cl:
                continue
            tname = self._dev._strings[struct.unpack("<H", t[2][:2])[0]]
            out[tname] = struct.unpack("<i", cl[2][:4])[0]
        return out

    def _attributes(self):
        _, ab = self._field_raw(self._dev, "attributes")
        out = {}
        for _, fields in self._walk(ab):
            an = fields.get("attributeName")
            v = fields.get("value")
            if not an or not v:
                continue
            aname = self._dev._strings[struct.unpack("<H", an[2][:2])[0]]
            out[aname] = struct.unpack("<i", v[2][:4])[0]
        return out

    def _perk_points(self):
        _, db = self._field_raw(self._dev, "devPoints")
        for _, fields in self._walk(db):
            t = fields.get("type")
            if not t:
                continue
            tname = self._dev._strings[struct.unpack("<H", t[2][:2])[0]]
            if tname == "Primary":
                un = fields.get("unspent")
                return struct.unpack("<i", un[2][:4])[0] if un else 0
        return None

    def _meta_field(self, key):
        if not self._meta:
            return None
        return self._meta.get("Data", {}).get("metadata", {}).get(key)

    # ---- writes ---------------------------------------------------------
    def _set_proficiency(self, target_type, value):
        slc, pb = self._field_raw(self._dev, "proficiencies")
        pb = bytearray(pb)
        for _, fields in self._walk(bytes(pb)):
            t = fields.get("type")
            cl = fields.get("currentLevel")
            if not t or not cl:
                continue
            tname = self._dev._strings[struct.unpack("<H", t[2][:2])[0]]
            if tname == target_type:
                off = cl[1]
                pb[off : off + 4] = struct.pack("<i", value)
                self._set_field_raw(self._dev, slc, bytes(pb))
                return True
        return False

    def set_level(self, value):
        value = max(LEVEL_MIN, min(LEVEL_MAX, int(value)))
        self._set_proficiency("Level", value)
        self._meta_set("level", float(value))
        return value

    def set_street_cred(self, value):
        value = max(CRED_MIN, min(CRED_MAX, int(value)))
        self._set_proficiency("StreetCred", value)
        self._meta_set("streetCred", float(value))
        return value

    def set_attribute(self, attr, value):
        if attr not in ATTRIBUTES:
            raise SaveError(f"unknown attribute {attr}")
        value = max(ATTR_MIN, min(ATTR_MAX, int(value)))
        slc, ab = self._field_raw(self._dev, "attributes")
        ab = bytearray(ab)
        done = False
        for _, fields in self._walk(bytes(ab)):
            an = fields.get("attributeName")
            v = fields.get("value")
            if not an or not v:
                continue
            aname = self._dev._strings[struct.unpack("<H", an[2][:2])[0]]
            if aname == attr:
                off = v[1]
                ab[off : off + 4] = struct.pack("<i", value)
                done = True
                break
        if done:
            self._set_field_raw(self._dev, slc, bytes(ab))
            meta_key = {
                "Strength": "strength",
                "Reflexes": "reflexes",
                "TechnicalAbility": "technicalAbility",
                "Intelligence": "intelligence",
                "Cool": "cool",
            }[attr]
            self._meta_set(meta_key, float(value))
        return value if done else None

    def set_perk_points(self, value):
        """Set unspent Primary (perk) points. Only works if the field exists,
        which it always does for a character that has spent any perk points."""
        value = max(0, int(value))
        slc, db = self._field_raw(self._dev, "devPoints")
        db = bytearray(db)
        for _, fields in self._walk(bytes(db)):
            t = fields.get("type")
            un = fields.get("unspent")
            if not t:
                continue
            tname = self._dev._strings[struct.unpack("<H", t[2][:2])[0]]
            if tname == "Primary" and un:
                off = un[1]
                db[off : off + 4] = struct.pack("<i", value)
                self._set_field_raw(self._dev, slc, bytes(db))
                return value
        return None

    def _meta_set(self, key, value):
        if self._meta:
            self._meta.get("Data", {}).get("metadata", {})[key] = value

    # ---- presets --------------------------------------------------------
    def apply_preset(self, preset):
        """preset: dict with optional keys level, street_cred, attributes{}, perk_points."""
        result = {}
        if "level" in preset:
            result["level"] = self.set_level(preset["level"])
        if "street_cred" in preset:
            result["street_cred"] = self.set_street_cred(preset["street_cred"])
        for attr, val in preset.get("attributes", {}).items():
            result.setdefault("attributes", {})[attr] = self.set_attribute(attr, val)
        if "perk_points" in preset:
            result["perk_points"] = self.set_perk_points(preset["perk_points"])
        return result

    # ---- persist --------------------------------------------------------
    def save(self):
        self._container.__exit__(None, None, None)
        self._config = None
        self.sf.save()  # writes sav.dat, rotates previous to backup_N.dat
        if self._meta is not None:
            self._meta_path.write_text(json.dumps(self._meta, indent=4))
        # reopen so the editor stays usable after a save
        self.sf = SaveFile(self.folder)
        self._open()
        return True
