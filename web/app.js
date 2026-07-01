// RIPPERDOC, front end. Talks to the Python Api in either mode:
//   native window  -> window.pywebview.api.<method>()
//   browser/server -> POST /api/<method>  (server.py, ideal on the Steam Deck)
const RPC = (method, ...args) => {
  if (window.pywebview && window.pywebview.api) return window.pywebview.api[method](...args);
  return fetch("/api/" + method, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(args),
  }).then((r) => r.json());
};
const api = () => new Proxy({}, { get: (_, m) => (...a) => RPC(m, ...a) });
const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

let STATE = null, BUILDS = null, activePreset = null, dirty = false;

// in-game cyberware slot layout (percent of the body stage), matching the
// real Cyberpunk 2077 cyberware screen.
const SLOT_LAYOUT = [
  { cat: "Frontal Cortex",       x: 17, y: 13, side: "l" },
  { cat: "Arms",                 x: 15, y: 31, side: "l" },
  { cat: "Skeleton",             x: 14, y: 49, side: "l" },
  { cat: "Nervous System",       x: 15, y: 66, side: "l" },
  { cat: "Integumentary System", x: 17, y: 83, side: "l" },
  { cat: "Operating System",     x: 83, y: 13, side: "r" },
  { cat: "Face",                 x: 85, y: 30, side: "r" },
  { cat: "Hands",                x: 86, y: 47, side: "r" },
  { cat: "Circulatory System",   x: 85, y: 64, side: "r" },
  { cat: "Legs",                 x: 83, y: 81, side: "r" },
];

const toast = (msg, err = false) => {
  const t = $("#toast");
  t.textContent = msg;
  t.className = "toast show" + (err ? " err" : "");
  setTimeout(() => (t.className = "toast hidden"), 2800);
};
const loader = (on) => $("#loader").classList.toggle("hidden", !on);

function markDirty(d) {
  dirty = d;
  const n = $("#dirtyNote");
  n.textContent = d ? "CHANGES STAGED, CHROME AIN'T REAL TILL YOU WRITE IT" : "SAVE IS CLEAN, CHOOM";
  n.classList.toggle("clean", !d);
}

// ---------- main menu ----------
async function rescan(extra) {
  $("#saveList").innerHTML = `<div class="menu-empty">jackin' in… scanning your shards</div>`;
  let saves = [];
  try { saves = await api().list_saves(extra || null); } catch (e) {}
  if (!saves.length) {
    $("#saveList").innerHTML = `<div class="menu-empty">Found jack shit, choom. Auto-scan came up dry, so your saves aren't where I looked. Hit BROWSE or paste a path below.</div>`;
    return;
  }
  $("#saveList").innerHTML = "";
  const count = document.createElement("div");
  count.className = "menu-found";
  count.innerHTML = `<span class="mf-ok">◈ AUTO-FOUND ${saves.length} SAVE${saves.length > 1 ? "S" : ""}</span>, newest first. Hit ENTER to jack into the top one`;
  $("#saveList").appendChild(count);
  saves.forEach((s, i) => {
    const d = new Date(s.mtime * 1000);
    const when = d.toLocaleDateString() + " · " + d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    const el = document.createElement("div");
    el.className = "save-row" + (i === 0 ? " latest" : "");
    el.tabIndex = 0;
    el.innerHTML = `<span class="sr-caret">▸</span><span class="sr-name">${s.name}</span>
      <span class="sr-meta">${i === 0 ? '<span class="sr-latest">LATEST</span> ' : ""}<b>${s.size_mb} MB</b><br>${when}</span>`;
    el.onclick = () => loadSave(s.folder);
    el.onkeydown = (e) => { if (e.key === "Enter") loadSave(s.folder); };
    $("#saveList").appendChild(el);
  });
  // preselect the newest so ENTER just works
  $("#saveList .save-row").focus();
}

async function loadSave(folder) {
  loader(true);
  const res = await api().load_save(folder);
  loader(false);
  if (!res.ok) return toast("Load flatlined: " + res.error, true);
  STATE = res.state;
  showEditor();
  toast("Shard cracked, welcome back to Night City");
}

// ---------- editor ----------
function showEditor() {
  $("#picker").classList.add("hidden");
  $("#editor").classList.remove("hidden");
  $("#idName").textContent = STATE.name || "V";
  $("#idLifepath").textContent = STATE.lifepath || "—";
  $("#idPlay").textContent = STATE.play_time_h + "H";
  $("#idPatch").textContent = "PATCH " + STATE.patch;
  renderStats();
  renderAttrs();
  renderPresetTabs();
  renderCyber();
  markDirty(false);
  switchTab("character");
}

function switchTab(name) {
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  $("#tab-character").classList.toggle("hidden", name !== "character");
  $("#tab-cyberware").classList.toggle("hidden", name !== "cyberware");
}

function renderStats() {
  $("#levelNum").textContent = STATE.level ?? 0;
  $("#levelInput").value = STATE.level ?? 0;
  $("#credNum").textContent = STATE.street_cred ?? 0;
  $("#credInput").value = STATE.street_cred ?? 0;
  $("#perkInput").value = STATE.perk_points ?? 0;
}

function renderAttrs() {
  const block = $("#attrBlock");
  block.innerHTML = "";
  BUILDS.attributes.forEach((a) => {
    const label = STATE.attr_labels[a] || a;
    const val = STATE.attributes[a] ?? 3;
    const pct = ((val - 3) / 17) * 100;
    const row = document.createElement("div");
    row.className = "attr-row";
    row.innerHTML = `<div class="attr-name">${label}</div>
      <div class="attr-bar"><i style="width:${pct}%"></i></div>
      <div class="stepper">
        <button data-act="dec" data-target="attr" data-attr="${a}">−</button>
        <input type="number" min="3" max="20" value="${val}" data-attr="${a}">
        <button data-act="inc" data-target="attr" data-attr="${a}">+</button>
      </div>`;
    block.appendChild(row);
  });
  bindSteppers();
}

function renderPresetTabs() {
  const wrap = $("#presetTabs");
  wrap.innerHTML = "";
  Object.entries(BUILDS.presets).forEach(([key, p]) => {
    const b = document.createElement("button");
    b.className = "preset-tab" + (activePreset === key ? " active" : "");
    b.textContent = p.title;
    b.title = p.blurb;
    b.onclick = () => applyPreset(key);
    wrap.appendChild(b);
  });
}

// ---------- cyberware body diagram ----------
function renderCyber() {
  const stage = $("#cwSlots");
  stage.innerHTML = "";
  const preset = activePreset ? BUILDS.presets[activePreset] : null;
  SLOT_LAYOUT.forEach((slot) => {
    const item = preset ? preset.cyberware[slot.cat] : null;
    const el = document.createElement("div");
    el.className = "cw-slot " + slot.side;
    el.style.left = slot.x + "%";
    el.style.top = slot.y + "%";
    el.innerHTML = `<div class="cs-cat">${slot.cat}</div>
      <div class="cs-frame">${item ? `<div class="cs-item">${shortItem(item)}</div>` : `<div class="cs-empty">— empty —</div>`}</div>`;
    if (item) {
      el.querySelector(".cs-frame").onclick = (e) => { e.stopPropagation(); showTip(slot, item, el); };
    }
    stage.appendChild(el);
  });
  // capacity / armor flavor numbers scale a bit with the build
  $("#capNum").textContent = preset ? "186" : "—";
  $("#armorNum").textContent = preset ? "1500" : "—";
  $("#cwTip").classList.add("hidden");
}

function shortItem(s) {
  // trim the parenthetical for the slot frame; full text shows in the tooltip
  return s.replace(/\s*\(.*?\)\s*/g, " ").split(" or ")[0].trim();
}

function showTip(slot, item, el) {
  $$(".cw-slot").forEach((s) => s.classList.remove("active"));
  el.classList.add("active");
  const tip = $("#cwTip");
  tip.innerHTML = `<div class="tip-x">✕</div>
    <div class="tip-cat">${slot.cat}</div>
    <h4>${shortItem(item)}</h4>
    <div class="tip-body">${item}</div>`;
  tip.classList.remove("hidden");
  // position next to the slot, inside the stage
  const stage = $("#cwStage").getBoundingClientRect();
  const r = el.getBoundingClientRect();
  let left = slot.side === "l" ? (r.right - stage.left + 14) : (r.left - stage.left - 314);
  let top = r.top - stage.top;
  left = Math.max(8, Math.min(left, stage.width - 308));
  top = Math.max(8, Math.min(top, stage.height - 140));
  tip.style.left = left + "px";
  tip.style.top = top + "px";
  tip.querySelector(".tip-x").onclick = () => { tip.classList.add("hidden"); el.classList.remove("active"); };
}

// ---------- edits ----------
async function applyPreset(key) {
  loader(true);
  const res = await api().apply_preset(key);
  loader(false);
  if (!res.ok) return toast("Preset choked: " + res.error, true);
  STATE = res.state;
  activePreset = key;
  renderStats(); renderAttrs(); renderPresetTabs(); renderCyber();
  const p = BUILDS.presets[key];
  $("#loadoutDesc").innerHTML = `<span class="ld-title">${p.title.toUpperCase()}</span>, ${p.blurb} `
    + `Set your attributes to this build's spread and loaded its best chrome onto the <b>CYBERWARE</b> tab.`;
  markDirty(true);
  toast(p.title + " jacked in, chrome list's on the CYBERWARE tab");
}

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

async function pushEdit(target, value, attr) {
  let res;
  if (target === "level") res = await api().set_level(value);
  else if (target === "cred") res = await api().set_street_cred(value);
  else if (target === "perk") res = await api().set_perk_points(value);
  else if (target === "attr") res = await api().set_attribute(attr, value);
  if (res && res.ok) {
    STATE = res.state;
    renderStats();
    if (target === "attr") {
      const v = STATE.attributes[attr];
      const inp = document.querySelector(`#attrBlock input[data-attr="${attr}"]`);
      if (inp) { inp.value = v; inp.closest(".attr-row").querySelector(".attr-bar i").style.width = ((v - 3) / 17) * 100 + "%"; }
    }
    markDirty(true);
  } else if (res) toast("Edit bounced: " + res.error, true);
}

function bindSteppers() {
  $$("[data-act]").forEach((btn) => {
    if (btn.dataset.bound) return;
    btn.dataset.bound = "1";
    btn.onclick = () => {
      const t = btn.dataset.target, attr = btn.dataset.attr;
      let inp, lo, hi;
      if (t === "level") { inp = $("#levelInput"); lo = 1; hi = 50; }
      else if (t === "cred") { inp = $("#credInput"); lo = 1; hi = 50; }
      else if (t === "perk") { inp = $("#perkInput"); lo = 0; hi = 9999; }
      else { inp = document.querySelector(`#attrBlock input[data-attr="${attr}"]`); lo = 3; hi = 20; }
      let cur = parseInt(inp.value || "0", 10);
      const a = btn.dataset.act;
      if (a === "inc") cur += 1; else if (a === "dec") cur -= 1;
      else if (a === "max") cur = hi; else if (a === "set") cur += parseInt(btn.dataset.val, 10);
      cur = clamp(cur, lo, hi);
      inp.value = cur;
      pushEdit(t, cur, attr);
    };
  });
  ["#levelInput", "#credInput", "#perkInput"].forEach((sel) => {
    const inp = $(sel);
    if (inp.dataset.bound) return;
    inp.dataset.bound = "1";
    const t = sel.includes("level") ? "level" : sel.includes("cred") ? "cred" : "perk";
    inp.onchange = () => pushEdit(t, parseInt(inp.value || "0", 10));
  });
  $$('#attrBlock input[data-attr]').forEach((inp) => {
    if (inp.dataset.cbound) return;
    inp.dataset.cbound = "1";
    inp.onchange = () => pushEdit("attr", clamp(parseInt(inp.value || "3", 10), 3, 20), inp.dataset.attr);
  });
}

async function writeSave() {
  if (!dirty) return toast("Nothing to write, choom, save's already clean");
  loader(true);
  const res = await api().save_changes();
  loader(false);
  if (!res.ok) return toast("Write flatlined: " + res.error, true);
  STATE = res.state;
  markDirty(false);
  toast("Burned to chrome. Old save's parked as backup_N.dat, you're golden");
}

// ---------- wire up ----------
async function init() {
  if (BUILDS) return;
  BUILDS = await api().get_builds();
  rescan();
}
window.addEventListener("pywebviewready", init);

document.addEventListener("DOMContentLoaded", () => {
  // browser/server mode has no pywebviewready event
  if (!window.pywebview) setTimeout(init, 60);
  $("#rescanBtn").onclick = () => rescan();
  $("#browseBtn").onclick = async () => { const f = await api().browse_folder(); if (f) rescan(f); };
  $("#manualLoad").onclick = () => { const p = $("#manualPath").value.trim(); if (p) loadSave(p); };
  $("#manualPath").addEventListener("keydown", (e) => { if (e.key === "Enter") $("#manualLoad").click(); });
  $("#backBtn").onclick = () => {
    if (dirty && !confirm("You've got unsaved chrome staged. Delta out anyway?")) return;
    $("#editor").classList.add("hidden");
    $("#picker").classList.remove("hidden");
    activePreset = null;
  };
  $("#saveBtn").onclick = writeSave;
  $$(".tab").forEach((t) => (t.onclick = () => switchTab(t.dataset.tab)));
  bindSteppers();
});
