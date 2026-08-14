# Dashboard Pejuang 🌱

Dashboard web dinamis (Python + GitHub) untuk memantau program pendampingan
anak yatim & piatu binaan **Pejuang**, diambil otomatis dari Google Sheet
**"Database Pejuangku"**.

- **Live setelah deploy:** `https://<username-github-anda>.github.io/<nama-repo>/`
- **Tech stack:** Python 3.11 (ETL & anonimisasi) + HTML/CSS/JS statis (tanpa
  framework/CDN eksternal, jadi tetap tampil walau koneksi terbatas) + GitHub
  Actions (penjadwal update) + GitHub Pages (hosting gratis).

---

## 1. Struktur Project

```
pejuang-dashboard/
├── docs/                     ← root GitHub Pages
│   ├── index.html            ← halaman dashboard
│   ├── assets/
│   │   ├── css/style.css
│   │   ├── js/{charts.js, dashboard.js}
│   │   └── img/               ← avatar ilustrasi, hero, & foto kegiatan
│   └── data/data.json         ← data hasil olahan (auto-generated, JANGAN edit manual)
├── scripts/
│   ├── transform.py           ← logika anonimisasi & agregasi (inti privasi)
│   ├── fetch_data.py          ← pipeline LIVE: tarik data dari Google Sheet
│   └── seed_from_snapshot.py  ← data contoh awal (snapshot 14 Agt 2026)
├── .github/workflows/update-data.yml  ← auto-refresh data terjadwal
├── requirements.txt
└── README.md
```

## 2. Privasi Data — WAJIB DIBACA

Dashboard ini dirancang untuk **publik** (GitHub Pages dapat diakses siapa
saja yang punya link), sehingga `scripts/transform.py` secara otomatis
MENYAMARKAN data sebelum masuk ke `data.json`:

| Data asli di Sheet | Ditampilkan di dashboard |
|---|---|
| Nama lengkap anak | Nama depan saja |
| Tanggal lahir lengkap | Hanya kelompok usia (mis. "7–12 (SD)") |
| Alamat, nama wali, No. HP wali | **Tidak ditampilkan sama sekali** |
| Foto profil individu anak (FotoURL) | **Tidak dipakai** — diganti avatar ilustrasi vektor |
| Catatan personal (mis. kondisi keluarga) | Hanya jadi flag umum "Perlu perhatian" (bukan teks aslinya) |
| Sheet `Users` (username & **PasswordHash**) | **Tidak pernah diekspor** — `fetch_data.py` mendeteksi & melewati kolom `PasswordHash` otomatis |
| Foto dokumentasi kegiatan (Berita, foto grup) | Ditampilkan penuh — sesuai keputusan Anda, karena bersifat dokumentasi kegiatan, bukan identitas 1:1 |

Jika suatu saat kebijakan privasi berubah (misal ingin sepenuhnya privat),
tinggal ubah workflow untuk deploy ke repo **private** + tambahkan proteksi
akses (lihat bagian 6).

**Jangan pernah** meng-commit file kredensial (`service-account.json`) ke
repo — sudah ditambahkan ke `.gitignore`.

## 3. Setup Google Service Account (sekali saja)

1. Buka [Google Cloud Console](https://console.cloud.google.com/) → buat
   project baru (atau pakai yang sudah ada).
2. Aktifkan **Google Sheets API** dan **Google Drive API**.
3. Buat **Service Account** (IAM & Admin → Service Accounts → Create).
4. Buat **key** JSON untuk service account tsb → unduh file `.json`-nya.
5. Salin alamat email service account (formatnya
   `xxxx@xxxx.iam.gserviceaccount.com`).
6. Buka Google Sheet **"Database Pejuangku"** → klik **Share** → tempel
   email service account di atas → beri akses **Viewer**.

## 4. Setup Repo GitHub

1. Buat repo baru di GitHub (bisa **public**, karena data yang dipublikasikan
   sudah disamarkan).
2. Upload seluruh isi folder project ini ke repo:
   ```bash
   cd pejuang-dashboard
   git init
   git add .
   git commit -m "Inisialisasi Dashboard Pejuang"
   git branch -M main
   git remote add origin https://github.com/<username-anda>/<nama-repo>.git
   git push -u origin main
   ```
3. Di GitHub repo → **Settings → Secrets and variables → Actions** → tambah
   2 secret:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` → isi dengan seluruh isi file JSON dari
     langkah 3 di atas (copy-paste seluruh teksnya).
   - `SHEET_ID` → `1aTjYpbSWpsL3sCDEu0ASVA_FxvArlpTok0iydIcAh1w`
     (ID sheet "Database Pejuangku" — ganti jika Anda menyalin ke sheet lain).
4. Di **Settings → Pages** → Source: pilih branch `main`, folder `/docs` →
   Save. Setelah beberapa menit, dashboard akan online di
   `https://<username>.github.io/<nama-repo>/`.
5. Di tab **Actions** → jalankan workflow **"Update Dashboard Data"** secara
   manual sekali (tombol *Run workflow*) untuk mengambil data pertama kali
   dari Google Sheet dan menggantikan data contoh (snapshot).

Setelah itu, workflow akan berjalan **otomatis setiap hari jam 06:00 WITA**
(bisa diubah di `.github/workflows/update-data.yml`, bagian `cron`) — setiap
kali data di Google Sheet berubah, dashboard akan ikut ter-update tanpa perlu
deploy manual. Inilah yang membuat dashboard ini **dinamis**.

## 5. Menjalankan / Menguji Secara Lokal (opsional)

```bash
pip install -r requirements.txt

# opsi A — pakai data contoh (tanpa perlu Google API):
python scripts/seed_from_snapshot.py

# opsi B — tarik data live dari Google Sheet (butuh service account, lihat bagian 3):
export GOOGLE_SERVICE_ACCOUNT_JSON="$(cat service-account.json)"
export SHEET_ID="1aTjYpbSWpsL3sCDEu0ASVA_FxvArlpTok0iydIcAh1w"
python scripts/fetch_data.py

# lalu buka docs/index.html lewat local server:
cd docs && python3 -m http.server 8000
# buka http://localhost:8000 di browser
```

## 6. Kalau Ingin Dashboard Privat (bukan publik)

Jika suatu saat Anda ingin datanya **lengkap tanpa disamarkan** (misal hanya
untuk internal tim), opsi termudah:
1. Set repo GitHub jadi **Private**.
2. Gunakan **GitHub Pages dengan private repo** (butuh paket GitHub Pro/Team/
   Enterprise agar Pages private juga bisa diakses), atau
3. Deploy ke platform seperti Streamlit Community Cloud / Vercel dengan
   proteksi login sederhana (password gate), atau
4. Batasi akses lewat VPN internal / Google Workspace SSO jika di-hosting di
   server kantor.

Hubungi kembali sesi ini (atau sesi baru) jika ingin dibantu menyiapkan salah
satu opsi di atas.

## 7. Menambah / Mengubah Data

Karena dashboard ditarik otomatis dari Google Sheet, **cukup edit langsung di
Google Sheet "Database Pejuangku"** — jangan edit `docs/data/data.json`
secara manual (akan tertimpa oleh workflow otomatis). Struktur kolom yang
dikenali script (berdasar nama kolom, bukan nama tab, supaya tab boleh
di-rename):

- **Anak Asuh**: perlu kolom `NamaLengkap`, `StatusYatim`, `JenisKelamin`, dst.
- **Biaya/Bantuan**: perlu kolom `ID_Anak`, `Kategori`, `Jumlah`.
- **Prestasi**: perlu kolom `ID_Anak`, `Judul`, `Tingkat`.
- **Berita/Kegiatan**: perlu kolom `Isi`, `FileURL`, `DibuatOleh` (tanpa `ID_Anak`).
- **Referensi** (lookup nilai): perlu kolom `Tipe`, `Nilai`.
- Tab yang mengandung kolom `PasswordHash` otomatis dilewati (tidak pernah diekspor).

## 8. Kredit Desain

Ilustrasi avatar & hero adalah vektor SVG orisinal (dibuat khusus untuk
project ini, bukan foto anak sungguhan) — dipakai untuk menjaga privasi
sekaligus membuat dashboard tetap hangat & ramah dipandang. Palet warna
kategorikal pada chart divalidasi agar tetap terbaca oleh pengguna dengan
buta warna (contrast & color-vision-deficiency check).
