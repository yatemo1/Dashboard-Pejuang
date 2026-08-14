#!/usr/bin/env python3
"""
fetch_data.py
--------------
Mengambil data terbaru dari Google Sheet "Database Pejuangku", menyamarkan
data sensitif (lihat transform.py), lalu menuliskan hasilnya ke
docs/data/data.json — file yang dibaca oleh dashboard (index.html).

Script ini dijalankan otomatis oleh GitHub Actions (lihat
.github/workflows/update-data.yml) agar dashboard selalu ter-update
("dinamis") tanpa perlu deploy manual setiap kali data sheet berubah.

Autentikasi:
    Menggunakan Google Service Account. Kredensial JSON diambil dari
    environment variable GOOGLE_SERVICE_ACCOUNT_JSON (disimpan sebagai
    GitHub Actions secret, JANGAN pernah di-commit ke repo).

    Sheet harus di-share (Viewer) ke email service account tsb.

Cara pakai lokal (opsional, untuk uji coba):
    export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json)"
    export SHEET_ID="1aTjYpbSWpsL3sCDEu0ASVA_FxvArlpTok0iydIcAh1w"
    python scripts/fetch_data.py
"""

from __future__ import annotations

import io
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from transform import (
    build_id_maps,
    finalize_anak_asuh,
    transform_anak_asuh,
    transform_berita,
    transform_biaya,
    transform_prestasi,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
OUTPUT_PATH = DOCS_DIR / "data" / "data.json"
BERITA_IMG_DIR = DOCS_DIR / "assets" / "img" / "berita"

# Sheet "Users" berisi PasswordHash -> DILARANG diekspor dalam bentuk apapun.
FORBIDDEN_HEADERS = {"PasswordHash"}


def get_client() -> tuple[gspread.Client, Credentials]:
    raw = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not raw:
        print("ERROR: environment variable GOOGLE_SERVICE_ACCOUNT_JSON belum diset.", file=sys.stderr)
        sys.exit(1)
    info = json.loads(raw)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds), creds


def sheet_rows(ws: gspread.Worksheet) -> list[dict]:
    return ws.get_all_records()


def classify_worksheet(headers: list[str]) -> str | None:
    """Deteksi jenis tabel berdasar nama kolom, bukan nama tab —
    supaya script tetap jalan walau nama tab di-rename."""
    h = set(headers)
    if FORBIDDEN_HEADERS & h:
        return "SKIP_SENSITIVE"
    if {"NamaLengkap", "StatusYatim", "JenisKelamin"} <= h:
        return "anak_asuh"
    if {"ID_Berita"} <= h:
        return "komentar"  # tidak dipakai di dashboard publik saat ini
    if {"Isi", "FileURL", "DibuatOleh"} <= h and "ID_Anak" not in h:
        return "berita"
    if {"ID_Anak", "Kategori", "Jumlah"} <= h:
        return "biaya"
    if {"ID_Anak", "Judul", "Tingkat"} <= h:
        return "prestasi"
    if {"Tipe", "Nilai"} <= h:
        return "referensi"
    return None


def download_berita_images(creds: Credentials, berita_rows: list[dict]) -> dict[str, str]:
    """Unduh foto dokumentasi kegiatan (bukan foto profil individu anak) dan
    simpan lokal di docs/assets/img/berita/, supaya dashboard tidak
    bergantung pada Google Drive hotlink saat sudah live di GitHub Pages.

    Return: {FileID -> path relatif dari docs/, mis. 'assets/img/berita/xxxx.jpg'}
    """
    drive = build("drive", "v3", credentials=creds)
    BERITA_IMG_DIR.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}

    for r in berita_rows:
        file_id = (r.get("FileID") or "").strip()
        mime = (r.get("FileMimeType") or "").strip()
        if not file_id or not mime.startswith("image/"):
            continue
        ext = mime.split("/")[-1].replace("jpeg", "jpg")
        dest = BERITA_IMG_DIR / f"{file_id}.{ext}"
        rel_path = f"assets/img/berita/{dest.name}"
        if dest.exists():
            mapping[file_id] = rel_path
            continue
        try:
            request = drive.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            dest.write_bytes(buf.getvalue())
            mapping[file_id] = rel_path
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: gagal unduh foto berita {file_id}: {exc}", file=sys.stderr)

    return mapping


def main() -> None:
    sheet_id = os.environ.get("SHEET_ID", "1aTjYpbSWpsL3sCDEu0ASVA_FxvArlpTok0iydIcAh1w")
    client, creds = get_client()
    sh = client.open_by_key(sheet_id)

    buckets: dict[str, list[dict]] = {
        "anak_asuh": [],
        "berita": [],
        "biaya": [],
        "prestasi": [],
        "referensi": [],
    }

    for ws in sh.worksheets():
        try:
            rows = sheet_rows(ws)
        except Exception as exc:  # noqa: BLE001
            print(f"WARN: gagal baca tab '{ws.title}': {exc}", file=sys.stderr)
            continue
        if not rows:
            continue
        kind = classify_worksheet(list(rows[0].keys()))
        if kind in (None, "SKIP_SENSITIVE", "komentar"):
            if kind == "SKIP_SENSITIVE":
                print(f"INFO: tab '{ws.title}' dilewati (mengandung data sensitif/kredensial).")
            continue
        buckets[kind].extend(rows)

    anak_asuh_t = transform_anak_asuh(buckets["anak_asuh"])
    id_map, name_map = build_id_maps(anak_asuh_t)
    biaya_t = transform_biaya(buckets["biaya"], id_map)
    prestasi_t = transform_prestasi(buckets["prestasi"], name_map)
    image_map = download_berita_images(creds, buckets["berita"])
    berita_t = transform_berita(buckets["berita"], image_map)
    anak_asuh_final = finalize_anak_asuh(anak_asuh_t)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ringkasan": {
            "total_anak": len(anak_asuh_final),
            "total_aktif": sum(1 for a in anak_asuh_final if a["aktif"]),
            "total_yatim": sum(1 for a in anak_asuh_final if a["status_yatim"] == "Yatim"),
            "total_piatu": sum(1 for a in anak_asuh_final if a["status_yatim"] == "Piatu"),
            "total_yatim_piatu": sum(1 for a in anak_asuh_final if a["status_yatim"] == "Yatim Piatu"),
            "total_wilayah": len({a["wilayah"] for a in anak_asuh_final if a["wilayah"] != "-"}),
            "total_prestasi": len(prestasi_t),
            "total_bantuan": biaya_t["total_tersalurkan"],
        },
        "anak_asuh": anak_asuh_final,
        "biaya": biaya_t,
        "prestasi": prestasi_t,
        "berita": berita_t,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK: data ditulis ke {OUTPUT_PATH} ({len(anak_asuh_final)} anak asuh, {len(berita_t)} berita)")


if __name__ == "__main__":
    main()
