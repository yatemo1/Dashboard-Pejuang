"""
transform.py
-------------
Fungsi inti untuk membersihkan & MENYAMARKAN (anonymize) data mentah dari
Google Sheet "Database Pejuangku" menjadi struktur JSON yang aman untuk
ditampilkan di dashboard publik (GitHub Pages).

Prinsip privasi yang diterapkan (lihat README.md bagian "Privasi Data"):
  1. Sheet "Users" (berisi PasswordHash) TIDAK PERNAH diekspor.
  2. Nama anak asuh disamarkan -> hanya nama depan / nama panggilan.
  3. Tanggal lahir disamarkan -> hanya umur (tahun) & kelompok usia, bukan
     tanggal lengkap.
  4. Alamat lengkap, nama wali, dan nomor HP wali TIDAK diekspor.
  5. Nama orang tua (ayah/ibu) TIDAK diekspor secara individual - hanya
     dipakai untuk menghitung status (Yatim/Piatu/Yatim Piatu).
  6. Foto profil individual anak TIDAK diekspor (dipakai avatar ilustrasi
     bergender sebagai gantinya). Foto kegiatan/berita (grup, bukan profil
     1:1 identitas) tetap ditampilkan karena bersifat dokumentasi kegiatan.
  7. Catatan/keterangan personal (kolom Catatan) TIDAK diekspor apa adanya;
     hanya dipakai untuk menandai flag "PerluPendampingan" (boolean),
     bukan teks aslinya.
  8. Data biaya/bantuan dikaitkan ke ID anak (bukan nama) untuk agregasi.
"""

from __future__ import annotations

import datetime
import hashlib
import re
from collections import defaultdict
from typing import Any


TODAY = datetime.date.today()


def first_name(nama_lengkap: str) -> str:
    """Ambil nama depan saja sebagai bentuk penyamaran identitas."""
    if not nama_lengkap or nama_lengkap.strip() in {"-", ""}:
        return "Pejuang"
    return nama_lengkap.strip().split()[0]


def parse_date(value: str) -> datetime.date | None:
    if not value or not re.match(r"^\d{4}-\d{2}-\d{2}$", value.strip()):
        return None
    try:
        return datetime.date.fromisoformat(value.strip())
    except ValueError:
        return None


def age_from_dob(dob: datetime.date | None) -> int | None:
    if not dob:
        return None
    years = TODAY.year - dob.year - ((TODAY.month, TODAY.day) < (dob.month, dob.day))
    return years


def age_bracket(age: int | None) -> str:
    if age is None:
        return "Tidak diketahui"
    if age <= 6:
        return "0-6 (PAUD/TK)"
    if age <= 12:
        return "7-12 (SD)"
    if age <= 15:
        return "13-15 (SMP)"
    if age <= 18:
        return "16-18 (SMA/SMK)"
    return "19+ (Kuliah/Mandiri)"


def anon_id(raw_id: str, salt: str = "pejuang") -> str:
    """ID publik yang stabil tapi tidak reversible ke ID asli sheet."""
    return hashlib.sha1(f"{salt}:{raw_id}".encode()).hexdigest()[:8]


def avatar_for(gender: str, group: str) -> str:
    """Pilih ilustrasi avatar vektor (bukan foto asli) berdasar gender."""
    gender = (gender or "").strip().lower()
    if gender.startswith("perempuan"):
        return "assets/img/avatar-girl.svg"
    if gender.startswith("laki"):
        return "assets/img/avatar-boy.svg"
    return "assets/img/avatar-neutral.svg"


def status_label(status: str) -> str:
    status = (status or "").strip().title()
    mapping = {
        "Yatim": "Yatim",
        "Piatu": "Piatu",
        "Yatim Piatu": "Yatim Piatu",
    }
    return mapping.get(status, status or "Tidak diketahui")


def to_bool(value: Any) -> bool:
    return str(value).strip().upper() in {"TRUE", "1", "YA", "AKTIF"}


def transform_anak_asuh(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        rid = (r.get("ID") or "").strip()
        if not rid:
            continue
        dob = parse_date(r.get("TglLahir", ""))
        age = age_from_dob(dob)
        catatan = (r.get("Catatan") or "").strip()
        perlu_pendampingan = bool(catatan) and catatan != "-"
        out.append(
            {
                "id": anon_id(rid),
                "nama": first_name(r.get("NamaLengkap", "")),
                "gender": (r.get("JenisKelamin") or "").strip(),
                "umur": age,
                "kelompok_usia": age_bracket(age),
                "status_yatim": status_label(r.get("StatusYatim", "")),
                "jenjang": (r.get("Jenjang") or "-").strip() or "-",
                "sekolah_tipe": "Negeri" if "N" in (r.get("Sekolah") or "") else "Swasta/Lainnya",
                "wilayah": (r.get("Group") or "-").strip() or "-",
                "aktif": to_bool(r.get("StatusAktif")),
                "perlu_pendampingan": perlu_pendampingan,
                "avatar": avatar_for(r.get("JenisKelamin", ""), r.get("Group", "")),
                "tgl_bergabung": r.get("TglBergabung", ""),
                "_raw_id": rid,  # dipakai internal utk join biaya/prestasi, dihapus sebelum ekspor akhir
            }
        )
    return out


def transform_biaya(rows: list[dict], id_map: dict[str, str]) -> dict:
    per_kategori = defaultdict(float)
    per_bulan = defaultdict(float)
    per_anak_total = defaultdict(float)
    total = 0.0
    records = []
    for r in rows:
        try:
            jumlah = float(str(r.get("Jumlah", "0")).replace(",", "").strip() or 0)
        except ValueError:
            jumlah = 0.0
        kategori = (r.get("Kategori") or "Lainnya").strip()
        tanggal = r.get("Tanggal", "")
        bulan = tanggal[:7] if re.match(r"^\d{4}-\d{2}", tanggal or "") else "Tidak diketahui"
        id_anak_raw = (r.get("ID_Anak") or "").strip()
        id_anak_pub = id_map.get(id_anak_raw, None)

        per_kategori[kategori] += jumlah
        per_bulan[bulan] += jumlah
        total += jumlah
        if id_anak_pub:
            per_anak_total[id_anak_pub] += jumlah
            records.append(
                {
                    "anak_id": id_anak_pub,
                    "kategori": kategori,
                    "bulan": bulan,
                    "jumlah": jumlah,
                }
            )

    return {
        "total_tersalurkan": round(total, 2),
        "per_kategori": {k: round(v, 2) for k, v in sorted(per_kategori.items(), key=lambda x: -x[1])},
        "per_bulan": dict(sorted(per_bulan.items())),
        "per_anak_total": {k: round(v, 2) for k, v in per_anak_total.items()},
        "jumlah_transaksi": len(rows),
    }


def transform_prestasi(rows: list[dict], name_map: dict[str, str]) -> list[dict]:
    out = []
    for r in rows:
        id_anak_raw = (r.get("ID_Anak") or "").strip()
        out.append(
            {
                "nama": name_map.get(id_anak_raw, "Pejuang"),
                "judul": r.get("Judul", ""),
                "tingkat": r.get("Tingkat", ""),
                "deskripsi": r.get("Deskripsi", ""),
                "tanggal": r.get("Tanggal", ""),
            }
        )
    # urutkan terbaru dulu
    out.sort(key=lambda x: x.get("tanggal", ""), reverse=True)
    return out


def transform_berita(rows: list[dict], local_image_map: dict[str, str] | None = None) -> list[dict]:
    """local_image_map: {FileID -> path relatif ke docs/, mis. 'assets/img/berita/berita-1.jpg'}

    Foto kegiatan diunduh & disimpan lokal di repo (bukan di-hotlink ke Drive)
    supaya tampilan dashboard stabil & tidak bergantung pada status share-link
    Drive. Lihat scripts/fetch_data.py -> download_berita_images().
    """
    local_image_map = local_image_map or {}
    out = []
    for r in rows:
        file_id = (r.get("FileID") or "").strip()
        local_path = local_image_map.get(file_id)
        if local_path:
            image_url = local_path
        elif file_id:
            # fallback: hotlink Drive (butuh file di-share "Anyone with link")
            image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        else:
            image_url = ""
        out.append(
            {
                "isi": r.get("Isi", ""),
                "tanggal": r.get("Tanggal", ""),
                "gambar": image_url,
            }
        )
    out.sort(key=lambda x: x.get("tanggal", ""), reverse=True)
    return out


def finalize_anak_asuh(rows: list[dict]) -> list[dict]:
    """Hapus field internal (_raw_id) sebelum diekspor ke JSON publik."""
    cleaned = []
    for r in rows:
        r = dict(r)
        r.pop("_raw_id", None)
        cleaned.append(r)
    return cleaned


def build_id_maps(anak_asuh_transformed: list[dict]) -> tuple[dict, dict]:
    id_map = {r["_raw_id"]: r["id"] for r in anak_asuh_transformed}
    name_map = {r["_raw_id"]: r["nama"] for r in anak_asuh_transformed}
    return id_map, name_map
