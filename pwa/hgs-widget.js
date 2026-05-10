// ══════════════════════════════════════════
//  HGS Filo Widget  —  Scriptable
// ══════════════════════════════════════════

const API_KEY    = "AIzaSyB6JddjggHwCbK076wGLhZuWN3bQpwPbGk";
const PROJECT_ID = "hgs-system";
const APP_URL    = "https://hgs-system.web.app/index.html";

// ── Kimlik bilgileri ──
async function getCreds() {
  let email = Keychain.contains("hgs_email") ? Keychain.get("hgs_email") : null;
  let pass  = Keychain.contains("hgs_pass")  ? Keychain.get("hgs_pass")  : null;
  if (!email || !pass) {
    const a = new Alert();
    a.title   = "HGS Filo — Giriş";
    a.message = "Hesap bilgilerin bir kere kaydedilir";
    a.addTextField("E-posta");
    a.addSecureTextField("Şifre");
    a.addAction("Kaydet");
    a.addCancelAction("İptal");
    if (await a.present() === -1) throw new Error("Giriş iptal edildi");
    email = a.textFieldValue(0).trim();
    pass  = a.textFieldValue(1);
    Keychain.set("hgs_email", email);
    Keychain.set("hgs_pass",  pass);
  }
  return { email, pass };
}

// ── Firebase Auth ──
async function signIn(email, pass) {
  const r = new Request(`https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=${API_KEY}`);
  r.method  = "POST";
  r.headers = { "Content-Type": "application/json" };
  r.body    = JSON.stringify({ email, password: pass, returnSecureToken: true });
  const res = await r.loadJSON();
  if (!res.idToken) throw new Error("Giriş başarısız");
  return res.idToken;
}

// ── Firestore runQuery ──
async function fsQuery(idToken, structuredQuery) {
  const r = new Request(`https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default)/documents:runQuery`);
  r.method  = "POST";
  r.headers = { "Authorization": `Bearer ${idToken}`, "Content-Type": "application/json" };
  r.body    = JSON.stringify({ structuredQuery });
  return await r.loadJSON();
}

// ── Yardımcılar ──
function todayISO() {
  const d = new Date(); d.setHours(0,0,0,0); return d.toISOString();
}
function monthISO() {
  const d = new Date(); d.setDate(1); d.setHours(0,0,0,0); return d.toISOString();
}
function monthStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-01`;
}
function tl(n) {
  return "₺" + n.toLocaleString("tr-TR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fieldNum(fields, key) {
  const f = fields?.[key];
  return parseFloat(f?.doubleValue ?? f?.integerValue ?? 0);
}
function parseDocs(res) {
  return (res || []).filter(r => r.document).map(r => r.document);
}
function docSum(docs, key = "amount") {
  return docs.reduce((s, d) => s + fieldNum(d.fields, key), 0);
}

// ── Veri çek ──
async function fetchData(idToken) {
  const tsFilter = (ts) => ({
    fieldFilter: { field: { fieldPath: "passed_at" }, op: "GREATER_THAN_OR_EQUAL", value: { timestampValue: ts } }
  });
  const fuelFilter = () => ({
    fieldFilter: { field: { fieldPath: "date" }, op: "GREATER_THAN_OR_EQUAL", value: { stringValue: monthStr() } }
  });

  const [todayRes, monthRes, vehRes, fuelRes] = await Promise.all([
    fsQuery(idToken, { from: [{ collectionId: "passages" }], where: tsFilter(todayISO()), limit: 500  }),
    fsQuery(idToken, { from: [{ collectionId: "passages" }], where: tsFilter(monthISO()), limit: 2000 }),
    fsQuery(idToken, { from: [{ collectionId: "vehicles"  }], limit: 500  }),
    fsQuery(idToken, { from: [{ collectionId: "fuels"     }], where: fuelFilter(), limit: 1000 }),
  ]);

  const todayDocs = parseDocs(todayRes);
  const monthDocs = parseDocs(monthRes);
  const fuelDocs  = parseDocs(fuelRes);

  return {
    todayCount:  todayDocs.length,
    todayTotal:  docSum(todayDocs),
    monthCount:  monthDocs.length,
    monthTotal:  docSum(monthDocs),
    vehCount:    parseDocs(vehRes).length,
    fuelTotal:   docSum(fuelDocs, "amount"),
    fuelLiters:  docSum(fuelDocs, "liters"),
  };
}

// ── Renkler ──
const C = {
  bg:     new Color("#09051a"),
  card:   new Color("#1c1535"),
  va:     new Color("#a78bfa"),
  txt:    new Color("#f0ebff"),
  sub:    new Color("#7c6fa0"),
  muted:  new Color("#3d2f60"),
  orange: new Color("#fb923c"),
  red:    new Color("#ef4444"),
};

// ── Küçük widget ──
function buildSmall(w, data) {
  w.setPadding(16, 16, 16, 16);

  const brand = w.addText("HGS Filo");
  brand.font = Font.boldSystemFont(13);
  brand.textColor = C.va;

  w.addSpacer(4);

  const lbl = w.addText("Bugün");
  lbl.font = Font.systemFont(10);
  lbl.textColor = C.sub;

  w.addSpacer(6);

  const cnt = w.addText(`${data.todayCount} geçiş`);
  cnt.font = Font.boldSystemFont(22);
  cnt.textColor = C.txt;

  w.addSpacer(2);

  const amt = w.addText(tl(data.todayTotal));
  amt.font = Font.boldSystemFont(16);
  amt.textColor = C.va;

  w.addSpacer(6);

  const fuelRow = w.addText(`⛽ ${tl(data.fuelTotal)}`);
  fuelRow.font = Font.systemFont(11);
  fuelRow.textColor = C.orange;

  w.addSpacer();

  const now = new Date();
  const foot = w.addText(`🚗 ${data.vehCount}  ·  ${now.toLocaleTimeString("tr-TR",{hour:"2-digit",minute:"2-digit"})}`);
  foot.font = Font.systemFont(10);
  foot.textColor = C.muted;
}

// ── Orta widget (3 satır) ──
function buildMedium(w, data) {
  w.setPadding(14, 14, 12, 14);

  // Header
  const hdr = w.addStack();
  hdr.layoutHorizontally();
  hdr.centerAlignContent();

  const brand = hdr.addText("HGS Filo");
  brand.font = Font.boldSystemFont(13);
  brand.textColor = C.va;

  hdr.addSpacer();

  const now = new Date();
  const timeT = hdr.addText(now.toLocaleTimeString("tr-TR",{hour:"2-digit",minute:"2-digit"}));
  timeT.font = Font.systemFont(10);
  timeT.textColor = C.muted;

  w.addSpacer(8);

  function addRow(ico, label, leftVal, rightVal, rightColor) {
    const row = w.addStack();
    row.layoutHorizontally();
    row.centerAlignContent();
    row.backgroundColor = C.card;
    row.cornerRadius = 9;
    row.setPadding(7, 11, 7, 11);

    const icoT = row.addText(ico);
    icoT.font = Font.systemFont(11);

    row.addSpacer(6);

    const lblT = row.addText(label);
    lblT.font = Font.systemFont(10);
    lblT.textColor = C.sub;

    row.addSpacer(6);

    const lv = row.addText(leftVal);
    lv.font = Font.boldSystemFont(13);
    lv.textColor = C.txt;

    row.addSpacer();

    const rv = row.addText(rightVal);
    rv.font = Font.boldSystemFont(13);
    rv.textColor = rightColor || C.va;
  }

  addRow("🛣️", "Bugün", `${data.todayCount} geçiş`, tl(data.todayTotal));
  w.addSpacer(5);
  addRow("📅", "Bu Ay", `${data.monthCount} geçiş`, tl(data.monthTotal));
  w.addSpacer(5);
  addRow("⛽", "Yakıt",  `${data.fuelLiters.toFixed(0)} lt`, tl(data.fuelTotal), C.orange);

  w.addSpacer(8);

  // Footer
  const ftr = w.addStack();
  ftr.layoutHorizontally();

  const veh = ftr.addText(`🚗  ${data.vehCount} araç`);
  veh.font = Font.systemFont(10);
  veh.textColor = C.sub;

  ftr.addSpacer();

  const dt = ftr.addText(now.toLocaleDateString("tr-TR",{day:"numeric",month:"long"}));
  dt.font = Font.systemFont(10);
  dt.textColor = C.muted;
}

// ── Büyük widget ──
function buildLarge(w, data) {
  buildMedium(w, data);
}

// ── Hata widget ──
function buildError(msg) {
  const w = new ListWidget();
  w.backgroundColor = C.bg;
  w.setPadding(16, 16, 16, 16);
  const t = w.addText("⚠️ " + msg);
  t.font = Font.systemFont(12);
  t.textColor = C.red;
  t.minimumScaleFactor = 0.6;
  return w;
}

// ── Ana ──
async function run() {
  let widget;
  try {
    const { email, pass } = await getCreds();
    const idToken = await signIn(email, pass);
    const data    = await fetchData(idToken);

    widget = new ListWidget();
    widget.backgroundColor = C.bg;
    widget.url = APP_URL;

    const family = config.widgetFamily ?? "medium";
    if      (family === "small") buildSmall(widget, data);
    else if (family === "large") buildLarge(widget, data);
    else                         buildMedium(widget, data);

  } catch (e) {
    widget = buildError(e.message);
  }

  if (config.runsInWidget) {
    Script.setWidget(widget);
  } else {
    const fam = config.widgetFamily ?? "medium";
    fam === "small" ? await widget.presentSmall() : await widget.presentMedium();
  }
  Script.complete();
}

await run();
