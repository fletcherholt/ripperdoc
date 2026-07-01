"""Grant cyberware by injecting items into the player inventory.

In Cyberpunk 2.x, adding a cyberware item to the player's carried inventory
(sub-inventory 0) makes it show up as owned at any ripperdoc, ready to install
(confirmed behaviour of the game's own AddToInventory path). We do NOT touch the
equipment system, which is the brick-prone part.

Each inventory item is a child node of the "inventory" node: a 16-byte inline
preview (tweakDbId + 8-byte header) followed by the item's data node. Every node
also embeds its own index. We add items as new nodes appended at the END of the
node table (so no existing index shifts and no downstream node-ids need
rewriting), place their bytes in sub-inventory 0's region, shift the offsets of
the nodes that come after, and fix the child chain + item count. Verified to
round-trip a real 2.31 save byte-identically.
"""

import struct
import zlib

from cp77edit._container.cp2077chunk import NodeInfo


def tweakdbid(name):
    """8-byte TweakDBID: crc32(name) little-endian + length byte + 3 zero pad."""
    return struct.pack("<IB", zlib.crc32(name.encode()) & 0xFFFFFFFF, len(name)) + b"\x00\x00\x00"


def _find_template(sf, ni, first, last0):
    """A valid modable item (seed != 2) in sub-inventory 0 to clone from."""
    for i in range(first, last0 + 1):
        n = ni[i]
        seed = struct.unpack("<I", bytes(sf.data[n.offset + 12 : n.offset + 16]))[0]
        if seed != 2 and n.size >= 40:
            return bytes(sf.data[n.offset : n.offset + n.size])
    return None


def add_cyberware(sf, record_names):
    """Inject each 'Items.Xxx' record into the player inventory. Mutates sf.data
    and sf.nodes_info in place; caller then calls the save's persist path.

    Returns the number of items added."""
    ni = list(sf.nodes_info)
    inv_idx = next(i for i, n in enumerate(ni) if n.name == b"inventory")
    inv = ni[inv_idx]
    data = sf.data

    subcount = struct.unpack("<I", bytes(data[inv.offset + 4 : inv.offset + 8]))[0]
    _, item_count0 = struct.unpack("<QI", bytes(data[inv.offset + 8 : inv.offset + 20]))
    first = inv.child
    last0 = first + item_count0 - 1  # last node index of sub-inventory 0

    template = _find_template(sf, ni, first, last0)
    if template is None:
        raise RuntimeError("no modable template item found to clone")

    ins = ni[last0].offset + ni[last0].size  # byte insertion point (end of sub-inv 0)

    blob = bytearray()
    new_nodes = []
    prev_chain = last0  # node whose 'next' we rewire into the new items
    chain_target = ni[last0].next  # what sub-inv 0's last item currently points to

    for rec in record_names:
        new_index = len(ni) + len(new_nodes)
        tid = tweakdbid(rec)
        seed = (zlib.crc32(b"ripperdoc" + tid) & 0xFFFFFFFF) | 1
        if seed == 2:
            seed = 3
        item = bytearray(template)
        item[0:4] = struct.pack("<I", new_index)  # embedded node id = its index
        item[4:12] = tid                           # TweakDBID
        item[12:16] = struct.pack("<I", seed)      # seed (!= 2 keeps it modable)
        preview = bytes(item[4:20])                # 16-byte inline preview
        item_off = ins + len(blob) + 16
        blob += preview + bytes(item)
        new_nodes.append(NodeInfo(name=b"itemData", next=None, child=None,
                                  offset=item_off, size=len(item)))

    delta = len(blob)
    # 1) insert the item bytes into the decompressed blob
    data[ins:ins] = bytes(blob)
    # 2) shift offsets of nodes that come after the insertion point
    out = []
    for i, n in enumerate(ni):
        if i != inv_idx and n.offset >= ins:
            n = n._replace(offset=n.offset + delta)
        out.append(n)
    # 3) grow the inventory node
    out[inv_idx] = out[inv_idx]._replace(size=inv.size + delta)
    # 4) splice the new nodes into sub-inventory 0's child chain
    out[prev_chain] = out[prev_chain]._replace(next=len(out))
    for k, node in enumerate(new_nodes):
        nxt = (len(out) + k + 1) if k < len(new_nodes) - 1 else chain_target
        out.append(node._replace(next=nxt))
    sf.nodes_info = tuple(out)
    # 5) bump sub-inventory 0's item count
    data[inv.offset + 16 : inv.offset + 20] = struct.pack("<I", item_count0 + len(new_nodes))
    return len(new_nodes)
