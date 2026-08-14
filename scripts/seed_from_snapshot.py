#!/usr/bin/env python3
"""
seed_from_snapshot.py
-----------------------
Snapshot data yang diambil manual (satu kali) dari Google Sheet
"Database Pejuangku" pada 2026-08-14, dipakai untuk mengisi dashboard
dengan data AWAL agar bisa langsung di-preview / di-deploy tanpa perlu
setup Google Service Account terlebih dahulu.

Setelah repo di-deploy dan GitHub Actions (update-data.yml) berjalan
dengan kredensial service account yang sesungguhnya, file
docs/data/data.json akan otomatis digantikan dengan data ter-update
langsung dari Google Sheet (lihat fetch_data.py).

Jalankan:
    python scripts/seed_from_snapshot.py
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from transform import (
    build_id_maps,
    finalize_anak_asuh,
    transform_anak_asuh,
    transform_berita,
    transform_biaya,
    transform_prestasi,
)

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "data" / "data.json"

# --- AnakAsuh -----------------------------------------------------------
ANAK_ASUH = [
    dict(ID="A00001", NamaLengkap="Araya Ratu Herawati", TglLahir="2016-01-04", JenisKelamin="Perempuan", StatusYatim="Yatim", Sekolah="SDN Ngimbang", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00002", NamaLengkap="Irfan Bahdim", TglLahir="2011-08-24", JenisKelamin="Laki-laki", StatusYatim="Piatu", Sekolah="Mts Al-Hidayah", Jenjang="SMP", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="Perlu pendampingan, suka jalan dan malas sekolah"),
    dict(ID="A00003", NamaLengkap="Nevada Diah Lestari", TglLahir="2011-11-15", JenisKelamin="Perempuan", StatusYatim="Piatu", Sekolah="SMPN2 Ngimbang", Jenjang="SMP", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="Hidup mandiri bersama mas-e di ngengkreng, perlu pendampingan ekonominya"),
    dict(ID="A00004", NamaLengkap="Ranggitya", TglLahir="2010-01-01", JenisKelamin="Laki-laki", StatusYatim="Piatu", Sekolah="", Jenjang="", Group="NGB", StatusAktif="FALSE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00005", NamaLengkap="Ridho", TglLahir="2012-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="NGB", StatusAktif="FALSE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00006", NamaLengkap="Fatih", TglLahir="2017-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="NGB", StatusAktif="FALSE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00007", NamaLengkap="Septi Lailatul Badriah", TglLahir="2015-09-01", JenisKelamin="Perempuan", StatusYatim="Piatu", Sekolah="SDN Ngimbang", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00008", NamaLengkap="Dinda Khumairoh Aulia", TglLahir="2021-01-20", JenisKelamin="Perempuan", StatusYatim="Piatu", Sekolah="TK Dharma Wanita", Jenjang="PAUD/TK", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00009", NamaLengkap="Marcellio Bryan Atma Wijaya", TglLahir="2015-03-15", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="SDN Ngimbang", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00010", NamaLengkap="Diortho Gary Gantohe", TglLahir="2010-05-21", JenisKelamin="Laki-laki", StatusYatim="Piatu", Sekolah="SMK Muhammadiyah 3", Jenjang="SMA/SMK", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00011", NamaLengkap="Dinar Aisyah Putri", TglLahir="2013-11-02", JenisKelamin="Perempuan", StatusYatim="Piatu", Sekolah="SMPN 1 Ngimbang", Jenjang="SMP", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00012", NamaLengkap="Putri Falencya", TglLahir="2015-12-31", JenisKelamin="Perempuan", StatusYatim="Yatim", Sekolah="SDN Ngimbang", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00013", NamaLengkap="Dendra", TglLahir="2013-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="NGB", StatusAktif="FALSE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00014", NamaLengkap="Jihan Shanum Fahira", TglLahir="2019-05-25", JenisKelamin="Perempuan", StatusYatim="Yatim", Sekolah="SDN Ngimbang", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00015", NamaLengkap="Andrean", TglLahir="2012-07-29", JenisKelamin="Laki-laki", StatusYatim="Piatu", Sekolah="SMP Muhammadiyah", Jenjang="SMP", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="Drop Out jul 2026"),
    dict(ID="A00016", NamaLengkap="Arvin", TglLahir="2018-01-01", JenisKelamin="Laki-laki", StatusYatim="Piatu", Sekolah="", Jenjang="SD", Group="NGB", StatusAktif="FALSE", TglBergabung="2026-02-01", Catatan="ikut ayahnya ke TURI"),
    dict(ID="A00017", NamaLengkap="Nanda Suryaningtyas", TglLahir="2010-01-10", JenisKelamin="Perempuan", StatusYatim="Piatu", Sekolah="SMPN 1 Ngimbang", Jenjang="SMA/SMK", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00018", NamaLengkap="Priyanka Faezya Iswahyudi", TglLahir="2015-01-19", JenisKelamin="Perempuan", StatusYatim="Yatim", Sekolah="SDN 3 Sendangrejo", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-06-20", Catatan="-"),
    dict(ID="A00019", NamaLengkap="Priyasha Kenzio Iswahyudi", TglLahir="2017-08-19", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="SDN 3 Sendangrejo", Jenjang="SD", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-06-20", Catatan="-"),
    dict(ID="A00020", NamaLengkap="Muhammad Dafa", TglLahir="2016-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00021", NamaLengkap="Zidan", TglLahir="2017-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00022", NamaLengkap="Mustofa", TglLahir="2015-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00023", NamaLengkap="Fatimah", TglLahir="2016-01-01", JenisKelamin="Perempuan", StatusYatim="Yatim Piatu", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00024", NamaLengkap="Kiroh", TglLahir="2018-01-01", JenisKelamin="Perempuan", StatusYatim="Yatim Piatu", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00025", NamaLengkap="Rasyd", TglLahir="2019-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00026", NamaLengkap="Baim", TglLahir="2015-01-01", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="", Jenjang="", Group="SBG", StatusAktif="TRUE", TglBergabung="2026-02-01", Catatan="-"),
    dict(ID="A00028", NamaLengkap="Reyhan Afandi", TglLahir="2010-04-13", JenisKelamin="Laki-laki", StatusYatim="Yatim", Sekolah="SMKN Sambeng", Jenjang="SMA/SMK", Group="NGB", StatusAktif="TRUE", TglBergabung="2026-06-20", Catatan="-"),
]

# --- Biaya / Pengeluaran (ringkas kategori & jumlah per transaksi) ------
BIAYA = [
    dict(ID_Anak="A00002", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00007", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00009", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00010", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00012", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00014", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00015", Tanggal="2026-03-22", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00001", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00003", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00007", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00008", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00009", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00010", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00011", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00012", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00014", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00015", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00017", Tanggal="2026-04-25", Kategori="Uang Saku / Konsumsi", Jumlah="300"),
    dict(ID_Anak="A00001", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00002", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00003", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00007", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00008", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00009", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00010", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00011", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00012", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00014", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00015", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00018", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00019", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00028", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00001", Tanggal="2026-07-07", Kategori="Seragam & Perlengkapan", Jumlah="490"),
    dict(ID_Anak="A00007", Tanggal="2026-07-07", Kategori="Seragam & Perlengkapan", Jumlah="620"),
    dict(ID_Anak="A00009", Tanggal="2026-07-07", Kategori="Seragam & Perlengkapan", Jumlah="610"),
    dict(ID_Anak="A00012", Tanggal="2026-07-07", Kategori="Seragam & Perlengkapan", Jumlah="490"),
    dict(ID_Anak="A00014", Tanggal="2026-07-07", Kategori="Seragam & Perlengkapan", Jumlah="670"),
    dict(ID_Anak="A00017", Tanggal="2026-07-13", Kategori="Seragam & Perlengkapan", Jumlah="389"),
    dict(ID_Anak="A00028", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="68"),
    dict(ID_Anak="A00001", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00007", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00009", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00014", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00018", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00019", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00012", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="58"),
    dict(ID_Anak="A00003", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="68"),
    dict(ID_Anak="A00011", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="68"),
    dict(ID_Anak="A00017", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="68"),
    dict(ID_Anak="A00010", Tanggal="2026-07-11", Kategori="Buku & Alat Tulis", Jumlah="68"),
    dict(ID_Anak="A00028", Tanggal="2026-06-20", Kategori="Uang Saku / Konsumsi", Jumlah="100"),
    dict(ID_Anak="A00011", Tanggal="2026-07-11", Kategori="Seragam & Perlengkapan", Jumlah="100"),
    dict(ID_Anak="A00017", Tanggal="2026-07-11", Kategori="Seragam & Perlengkapan", Jumlah="150"),
    dict(ID_Anak="A00003", Tanggal="2026-07-22", Kategori="Uang Saku / Konsumsi", Jumlah="500"),
    dict(ID_Anak="A00010", Tanggal="2026-07-22", Kategori="Uang Saku / Konsumsi", Jumlah="250"),
    dict(ID_Anak="A00002", Tanggal="2026-07-22", Kategori="Uang Saku / Konsumsi", Jumlah="250"),
    dict(ID_Anak="A00019", Tanggal="2026-07-31", Kategori="Seragam & Perlengkapan", Jumlah="350"),
    dict(ID_Anak="A00018", Tanggal="2026-07-31", Kategori="Seragam & Perlengkapan", Jumlah="350"),
    dict(ID_Anak="A00010", Tanggal="2026-07-31", Kategori="Lainnya", Jumlah="300"),
]

# --- Prestasi ------------------------------------------------------------
PRESTASI = [
    dict(ID_Anak="A00010", Tanggal="2026-07-24", Judul="Paskibraka", Tingkat="Kecamatan/Kota", Deskripsi="Sebagai PASKIBRAKA 17 Agustus 2026 - tingkat kecamatan Ngimbang"),
]

# --- Berita / Kegiatan (foto dokumentasi kegiatan, bukan foto profil) ---
# Foto sudah diunduh & disimpan lokal di docs/assets/img/berita/ (lihat README)
# supaya dashboard tidak bergantung pada status share-link Google Drive.
BERITA = [
    dict(Isi="Pulang haji ba'da dhuhur di rumahe mak-e lagi. Alhamdulillah kembali berkumpul dengan anak-anak untuk saling menguatkan dan berbagi semangat.", Tanggal="2026-06-20", FileID="1Ij40czmK7mhl9GOLbMqwJ_axjnNukudc", DibuatOleh="Administrator", FileURL="x"),
    dict(Isi="Pamitan, mohon doa restu anak-anak untuk rencana safar.", Tanggal="2026-04-25", FileID="1i2WOCxd482ns7G8U4a6P-UrJobbQwP6p", DibuatOleh="Administrator", FileURL="x"),
    dict(Isi="Kebersamaan menjelang keberangkatan.", Tanggal="2026-04-25", FileID="118kkkKDdRUlvnji8GfTp9dDLlsEmhIHj", DibuatOleh="Administrator", FileURL="x"),
    dict(Isi="Lebaran bersama, kumpul pagi hari setelah subuh — momen kekeluargaan bersama anak-anak asuh.", Tanggal="2026-03-22", FileID="1UOSeFE-szzRfKUqmCVRlVyLpTp5R9X9F", DibuatOleh="Administrator", FileURL="x"),
    dict(Isi="Alhamdulillah dapat terus membersamai perkembangan anak-anak.", Tanggal="2026-04-25", FileID="12tm3ndcKYYJ2D4k7ofaTq0V-qN2YeCJQ", DibuatOleh="Administrator", FileURL="x"),
]

BERITA_LOCAL_IMAGES = {
    "1Ij40czmK7mhl9GOLbMqwJ_axjnNukudc": "assets/img/berita/berita-1.jpg",
    "1i2WOCxd482ns7G8U4a6P-UrJobbQwP6p": "assets/img/berita/berita-2.jpg",
    "118kkkKDdRUlvnji8GfTp9dDLlsEmhIHj": "assets/img/berita/berita-3.jpg",
    "1UOSeFE-szzRfKUqmCVRlVyLpTp5R9X9F": "assets/img/berita/berita-4.jpg",
    "12tm3ndcKYYJ2D4k7ofaTq0V-qN2YeCJQ": "assets/img/berita/berita-5.jpg",
}


def main() -> None:
    anak_asuh_t = transform_anak_asuh(ANAK_ASUH)
    id_map, name_map = build_id_maps(anak_asuh_t)
    biaya_t = transform_biaya(BIAYA, id_map)
    prestasi_t = transform_prestasi(PRESTASI, name_map)
    berita_t = transform_berita(BERITA, BERITA_LOCAL_IMAGES)
    anak_asuh_final = finalize_anak_asuh(anak_asuh_t)

    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sumber": "snapshot manual 2026-08-14 (akan digantikan otomatis oleh GitHub Actions setelah service account terhubung)",
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
    print(f"OK: seed data ditulis ke {OUTPUT_PATH}")
    print(json.dumps(data["ringkasan"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
