#!/usr/bin/env python3
"""HGS Filo Takip - Shell CLI"""

import sys
import json
import urllib.request
import urllib.error
from datetime import datetime

BASE_URL = "http://localhost:8000"


def request(method, path, data=None):
    url = BASE_URL + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"HATA: {err.get('detail', e)}")
        sys.exit(1)
    except urllib.error.URLError:
        print("HATA: API'ye bağlanılamadı. Backend çalışıyor mu? → python3 main.py")
        sys.exit(1)


def fmt_tl(amount):
    return f"{amount:.2f} ₺"


def fmt_date(dt_str):
    try:
        dt = datetime.fromisoformat(dt_str)
        return dt.strftime("%d.%m.%Y %H:%M")
    except:
        return dt_str


def print_table(rows, headers):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    fmt = "|" + "|".join(f" {{:<{w}}} " for w in widths) + "|"
    print(sep)
    print(fmt.format(*headers))
    print(sep)
    for row in rows:
        print(fmt.format(*[str(c) for c in row]))
    print(sep)


# ──────────────────────────────────────────
# KOMUTLAR
# ──────────────────────────────────────────

def cmd_arac_ekle(args):
    """Araç ekle: hgs araç-ekle <plaka> [hgs_tag] [isim] [bakiye]"""
    if not args:
        print("Kullanım: hgs araç-ekle <plaka> [hgs_tag] [isim] [bakiye]")
        return
    plate = args[0]
    data = {"plate": plate}
    if len(args) > 1: data["hgs_tag"] = args[1]
    if len(args) > 2: data["owner_name"] = args[2]
    if len(args) > 3: data["balance"] = float(args[3])
    v = request("POST", "/vehicles", data)
    print(f"✓ Araç eklendi: {v['plate']} | {v['owner_name'] or '-'} | Bakiye: {fmt_tl(v['balance'])}")


def cmd_arac_listele(args):
    """Tüm araçları listele"""
    vehicles = request("GET", "/vehicles")
    if not vehicles:
        print("Kayıtlı araç yok.")
        return
    rows = []
    for v in vehicles:
        rows.append([
            v["plate"],
            v["owner_name"] or "-",
            v["hgs_tag"] or "-",
            fmt_tl(v["balance"]),
            fmt_date(v["created_at"])
        ])
    print_table(rows, ["Plaka", "İsim", "HGS Tag", "Bakiye", "Kayıt Tarihi"])


def cmd_arac_sil(args):
    """Araç sil: hgs araç-sil <plaka>"""
    if not args:
        print("Kullanım: hgs araç-sil <plaka>")
        return
    res = request("DELETE", f"/vehicles/{args[0]}")
    print(f"✓ {res['message']}")


def cmd_arac_guncelle(args):
    """Araç güncelle: hgs araç-güncelle <plaka> bakiye=150 isim=Ali"""
    if len(args) < 2:
        print("Kullanım: hgs araç-güncelle <plaka> bakiye=150 isim=Ali hgs=HGS-001")
        return
    plate = args[0]
    data = {}
    for arg in args[1:]:
        k, _, v = arg.partition("=")
        if k == "bakiye":   data["balance"] = float(v)
        elif k == "isim":   data["owner_name"] = v
        elif k == "hgs":    data["hgs_tag"] = v
    v = request("PUT", f"/vehicles/{plate}", data)
    print(f"✓ Güncellendi: {v['plate']} | Bakiye: {fmt_tl(v['balance'])}")


def cmd_gecis_ekle(args):
    """Geçiş ekle: hgs geçiş-ekle <plaka> <konum> <tutar> [not]"""
    if len(args) < 3:
        print("Kullanım: hgs geçiş-ekle <plaka> <konum> <tutar> [not]")
        return
    data = {
        "plate": args[0],
        "location": args[1],
        "amount": float(args[2]),
    }
    if len(args) > 3:
        data["note"] = " ".join(args[3:])
    p = request("POST", "/passages", data)
    print(f"✓ Geçiş kaydedildi: {args[0]} | {p['location']} | {fmt_tl(p['amount'])} | {fmt_date(p['passed_at'])}")


def cmd_gecisler(args):
    """Geçişleri listele: hgs geçişler [plaka]"""
    path = "/passages"
    if args:
        path += f"?plate={args[0]}"
    passages = request("GET", path)
    if not passages:
        print("Geçiş kaydı yok.")
        return
    rows = [
        [p["id"], p["vehicle_id"], p["location"], fmt_tl(p["amount"]), fmt_date(p["passed_at"]), p["note"] or "-"]
        for p in passages
    ]
    print_table(rows, ["ID", "Araç ID", "Konum", "Tutar", "Tarih", "Not"])


def cmd_rapor(args):
    """Araç raporu: hgs rapor <plaka>"""
    if not args:
        print("Kullanım: hgs rapor <plaka>")
        return
    r = request("GET", f"/reports/{args[0]}")
    print(f"\n{'='*50}")
    print(f"  ARAÇ RAPORU: {r['plate']}")
    print(f"{'='*50}")
    print(f"  İsim        : {r['owner_name'] or '-'}")
    print(f"  HGS Tag     : {r['hgs_tag'] or '-'}")
    print(f"  Bakiye      : {fmt_tl(r['balance'])}")
    print(f"  Toplam Geçiş: {r['total_passages']}")
    print(f"  Toplam Harcama: {fmt_tl(r['total_spent'])}")
    print(f"{'='*50}")
    if r["passages"]:
        rows = [
            [p["location"], fmt_tl(p["amount"]), fmt_date(p["passed_at"]), p["note"] or "-"]
            for p in r["passages"]
        ]
        print_table(rows, ["Konum", "Tutar", "Tarih", "Not"])


def cmd_filo(args):
    """Filo özeti: hgs filo"""
    fleet = request("GET", "/reports")
    if not fleet:
        print("Kayıtlı araç yok.")
        return
    rows = [
        [v["plate"], v["owner_name"] or "-", fmt_tl(v["balance"]), v["total_passages"], fmt_tl(v["total_spent"])]
        for v in fleet
    ]
    print_table(rows, ["Plaka", "İsim", "Bakiye", "Geçiş", "Toplam Harcama"])
    total_balance = sum(v["balance"] for v in fleet)
    total_spent = sum(v["total_spent"] for v in fleet)
    print(f"\n  Toplam Bakiye: {fmt_tl(total_balance)}  |  Toplam Harcama: {fmt_tl(total_spent)}")


def cmd_yardim(args):
    print("""
HGS Filo Takip Sistemi - Komutlar
══════════════════════════════════
  araç-ekle  <plaka> [hgs_tag] [isim] [bakiye]
  araç-listele
  araç-güncelle  <plaka>  bakiye=150  isim=Ali  hgs=HGS-001
  araç-sil   <plaka>

  geçiş-ekle  <plaka> <konum> <tutar> [not]
  geçişler    [plaka]

  rapor  <plaka>
  filo

  yardım

Örnek:
  python3 hgs.py araç-ekle 34ABC123 HGS-001 "Ahmet Yılmaz" 200
  python3 hgs.py geçiş-ekle 34ABC123 "Osmangazi Köprüsü" 47.50
  python3 hgs.py rapor 34ABC123
  python3 hgs.py filo
""")


COMMANDS = {
    "araç-ekle":      cmd_arac_ekle,
    "araç-listele":   cmd_arac_listele,
    "araç-sil":       cmd_arac_sil,
    "araç-güncelle":  cmd_arac_guncelle,
    "geçiş-ekle":     cmd_gecis_ekle,
    "geçişler":       cmd_gecisler,
    "rapor":          cmd_rapor,
    "filo":           cmd_filo,
    "yardım":         cmd_yardim,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        cmd_yardim([])
        return
    cmd = sys.argv[1]
    args = sys.argv[2:]
    COMMANDS[cmd](args)


if __name__ == "__main__":
    main()
