# LAB-ADR-014: VPS, deploy otomatis, dan slot job berat

- **Status:** Diterima (L0.8, 2026-11-02)
- **Terkait:** LAB-ADR-010 (antrean, worker crash-only), LAB-ADR-012 (image + Compose lokal), LAB-ADR-013 (CI + GHCR); `PROJECT_CONTEXT` §4; Keputusan Terbuka #10

## Konteks

L0.7 menghasilkan image `hello-api`, `hello-worker`, dan `web` di GHCR. L0.8 perlu menjawab empat hal:

1. Bagaimana server publik (Hostinger, Ubuntu 24.04, 2 vCPU / 8 GB) diamankan.
2. Bagaimana image yang sama persis dengan yang diuji CI dijalankan di VPS dengan HTTPS.
3. Bagaimana CI men-deploy tanpa memegang akses yang setara root.
4. Keputusan Terbuka #10: bagaimana memastikan paling banyak "satu slot" komputasi berat untuk seluruh lab, padahal advisory lock PostgreSQL berlingkup per database dan setiap proyek memakai database sendiri.

## Keputusan

### 1. Hardening host

- **User admin `adrianus`** (grup `sudo`). Login root dan login password SSH dimatikan lewat `/etc/ssh/sshd_config.d/00-hardening.conf` (`PermitRootLogin no`, `PasswordAuthentication no`, `KbdInteractiveAuthentication no`). Prefiks `00-` wajib: OpenSSH memakai **nilai pertama** yang ditemukan, dan `50-cloud-init.conf` bawaan image menyetel `PasswordAuthentication yes`.
- **Firewall dua lapis.** UFW (`deny incoming`, `limit` 22/tcp, `allow` 80/tcp, 443/tcp, 443/udp) **dan** firewall hPanel dengan port yang sama. Lapis luar diperlukan karena port yang dipublikasikan Docker melewati aturan UFW (aturan iptables Docker dievaluasi lebih dulu). Konsekuensinya: **hanya Caddy yang boleh punya `ports:`**.
- **Update keamanan otomatis:** `unattended-upgrades` (bawaan), ditambah `/etc/apt/apt.conf.d/52unattended-upgrades-local` untuk reboot otomatis pukul 20:00 UTC (03:00 WIB) dan pembersihan kernel lama. Untuk opsi apt berlaku nilai terakhir, jadi file `52-` menimpa bawaan tanpa mengedit file milik paket. Jam server tetap UTC.
- **Swap 2 GB** (`/swapfile`) dengan `vm.swappiness = 10` (`/etc/sysctl.d/99-applied-math-lab.conf`): jaring pengaman terhadap OOM killer, bukan memori kerja.
- **Docker Engine dari repo resmi Docker** (29.9 + Compose v5, sama dengan WSL), dengan `/etc/docker/daemon.json`: `log-driver: local` (`max-size 10m`, `max-file 3`) dan `live-restore: true`. Docker tidak di-upgrade otomatis (repo Docker tidak termasuk origin unattended-upgrades).
- **Admin tidak masuk grup `docker`** (grup itu setara root tanpa password sudo); admin memakai `sudo docker`.
- **Tanpa fail2ban:** login password sudah mati dan `ufw limit` meredam bot agresif; layanan tambahan tidak sebanding manfaatnya.

### 2. Domain dan TLS

- Domain lab: **`applied-math-lab.portfolio-bagas.tech`**. Record `A` → IPv4 VPS dan `CAA 0 issue "letsencrypt.org"`. `AAAA` **ditunda**: Let's Encrypt mencoba IPv6 lebih dulu, dan IPv6 masuk lewat firewall hPanel belum teruji; AAAA yang rusak lebih buruk daripada tidak ada.
- `infrastructure/Caddyfile` (VPS): routing sama dengan `Caddyfile.local` (`/api/hello/*` tanpa `encode` + `flush_interval -1`; sisanya ke web dengan `encode zstd gzip`), ditambah TLS otomatis (email ACME dari env), redirect HTTP → HTTPS bawaan, header `Strict-Transport-Security "max-age=86400"` (dinaikkan ke 1 tahun setelah stabil, tanpa `includeSubDomains`), `X-Content-Type-Options`, `Referrer-Policy`, dan header `Server` dihapus. Rute `/api/hello/readyz` → `/readyz` hello-api untuk monitor eksternal.

### 3. Compose VPS

- `infrastructure/compose.vps.yaml` (proyek `lab`) **diturunkan** dari `compose.yaml` lokal: batas CPU/memori, `init`, `stop_grace_period`, dan urutan `postgres → migrate → api/worker` identik. Bedanya: `image: ghcr.io/adrianus-bagas/applied-math-lab/<image>:${IMAGE_TAG}` (tidak ada build di VPS), secret dari `.env`, logging dari bawaan daemon, Caddy di 80/443 (+UDP untuk HTTP/3), volume `caddy_data` (sertifikat + kunci akun ACME; tanpa volume ini setiap pembuatan ulang container meminta sertifikat baru dan cepat terkena batas 5 sertifikat identik per minggu).
- Variabel wajib memakai `${VAR:?pesan}` sehingga Compose menolak jalan bila kosong. Password Postgres wajib hex (`openssl rand -hex 32`) karena dirakit ke dalam URL.
- Postgres untuk RAM kecil: `max_connections=30`, `shared_buffers=256MB`, `work_mem=4MB`, `shm_size: 256m` (titik awal, dikalibrasi dari pemakaian nyata).
- Lokasi: `/opt/applied-math-lab` (milik user `deploy`), berisi `compose.vps.yaml`, `Caddyfile`, `.env` (mode 600, termasuk `COMPOSE_FILE=compose.vps.yaml` dan `IMAGE_TAG`), dan `deploy.log`. Contoh: `infrastructure/.env.vps.example`.

### 4. Deploy: user `deploy` yang dikunci forced command

- User `deploy` tanpa password, anggota grup `docker`. Satu-satunya kunci di `authorized_keys`-nya diawali `restrict,command="/usr/local/bin/lab-deploy"`: apa pun yang diminta klien, server hanya menjalankan skrip itu (perintah klien tersedia sebagai data di `SSH_ORIGINAL_COMMAND`); `restrict` mematikan pty dan semua forwarding.
- `infrastructure/vps/lab-deploy.sh` dipasang sebagai `/usr/local/bin/lab-deploy`, **milik root**, sehingga akun yang dibatasinya tidak bisa mengubahnya. Perintah: `deploy <sha-40-hex>` dan `status`. Alur `deploy`:
  1. validasi format (SHA penuh 40 hex; menolak spasi, `;`, `$(`);
  2. **SHA harus bagian dari riwayat `main`** (GitHub API `compare/<sha>...main` berstatus `ahead` atau `identical`). Commit di fork mana pun dapat diakses lewat URL repo induk; tanpa cek ini kunci yang bocor bisa men-deploy `compose.vps.yaml` jahat dari fork;
  3. unduh `compose.vps.yaml` dan `Caddyfile` **dari commit yang sama** (konfigurasi infrastruktur ter-versi bersama kode);
  4. `config` dan `pull` di folder sementara selagi versi lama masih melayani;
  5. ganti file, `up -d --remove-orphans --wait`; Caddy dibuat ulang bila `Caddyfile` berubah (bind mount satu file memegang inode lama);
  6. verifikasi: ID image container yang berjalan harus sama dengan ID image tag `sha-<7>` untuk ketiga layanan; hello-api version hanya dicatat di log, karena image hasil retag membawa SHA build lama (diperbaiki di L0.9a).;
  7. `docker image prune -af --filter until=168h`; catat ke `deploy.log`. Satu deploy pada satu waktu (`flock`).
- **Rollback** = deploy SHA sukses sebelumnya dari `deploy.log`, baik dari CI maupun dari admin: `sudo -u deploy lab-deploy deploy <sha>`. Migrasi bersifat maju; rollback melewati migrasi yang tidak kompatibel tidak didukung.

### 5. CI (perluasan LAB-ADR-013)

- `changes` menghasilkan `unchanged` (selisih himpunan semua image − image berubah, via `jq`) dan `deploy` (`true` bila ada image berubah atau `compose.vps.yaml`/`Caddyfile`/`ci.yml` berubah). Filter VPS sengaja tidak memuat `lab-deploy.sh`.
- Job **`retag`** (hanya `main`): image yang tidak berubah diberi tag `sha-<7>` yang menunjuk image `main` lewat `docker buildx imagetools create` (tanpa build). Aman karena filter image memuat semua yang disalin Dockerfile-nya; hasilnya setiap commit `main` punya tiga tag lengkap untuk satu `IMAGE_TAG`.
- Job **`deploy`** (hanya `main`, setelah tidak ada job yang `failure`/`cancelled`): environment **`production`** yang dibatasi ke branch `main` (secret `VPS_SSH_KEY`; variabel `VPS_HOST`, `VPS_KNOWN_HOSTS`), `concurrency: deploy-production` tanpa pembatalan, `permissions: {}`, SSH dengan `StrictHostKeyChecking=yes` + `BatchMode=yes`, lalu smoke test publik `/` dan `/hello`. `VPS_KNOWN_HOSTS` hasil `ssh-keyscan` yang sidik jarinya dicocokkan dengan `ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub` di server.
- `deploy` tidak masuk `ci-ok`: `ci-ok` menggerbangi PR, sedangkan deploy hanya terjadi setelah merge. `workflow_dispatch` di `main` = bangun semua image + deploy ulang.

### 6. Slot job berat (menutup Keputusan Terbuka #10)

Yang dibutuhkan §4.4 nomor 3 adalah **batas sumber daya** ("satu core selalu tersisa"), bukan mutual exclusion. Semua container worker diberi `cgroup_parent: lab-workers.slice`; slice systemd itu (`infrastructure/vps/lab-workers.slice` → `/etc/systemd/system/`) memiliki `CPUQuota=100%`, yaitu jatah CFS 100 ms per periode 100 ms untuk **gabungan** seluruh worker. Tanda hubung di nama slice menyatakan hierarki: cgroup-nya `/sys/fs/cgroup/lab.slice/lab-workers.slice`. Tidak ada kode koordinasi, dan lingkup database tidak relevan.

Terverifikasi: dua container pembakar CPU di dalam slice masing-masing ~53% (total ~106%, `nr_throttled` naik hampir setiap periode), di luar slice masing-masing ~97% (total ~194%).

### 7. Monitoring

Uptime dipantau **dari luar** dengan layanan monitor eksternal (paket gratis) terhadap `/` (DNS, TLS, Caddy, web) dan `/api/hello/readyz` (API + Postgres). Monitor di mesin yang sama tidak bisa melaporkan mesinnya sendiri mati, dan Uptime Kuma memakan RAM. Metrik container ditunda ke MO-25; sampai itu `docker stats` dipakai untuk kalibrasi.

## Alternatif yang ditolak

| Alternatif                                                          | Alasan ditolak                                                                    |
| ------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| CI login dengan kunci berakses shell (atau root)                    | Secret GitHub yang bocor = server diambil alih                                    |
| Pull-based (mis. Watchtower memantau tag `main`)                    | Deploy tidak terikat ke hasil CI per commit; rollback dan audit lebih sulit       |
| CI menyalin konfigurasi dengan `scp`                                | Forced command menolak; konfigurasi sudah ter-versi lewat SHA                     |
| Membangun ulang semua image di setiap commit `main`                 | Lambat; `retag` menghasilkan tag yang sama tanpa build                            |
| Database koordinasi bersama / satu database dengan skema per proyek | Butuh kode koordinasi atau mengubah `jobqueue`; kebutuhannya cukup dijawab kernel |
| Hanya `cpus` per container                                          | Tiga worker × 1.0 = 3 core pada mesin 2 vCPU                                      |
| Uptime Kuma di VPS                                                  | Tidak bisa mendeteksi VPS mati; memakan RAM                                       |
| fail2ban                                                            | Manfaat kecil setelah login password dimatikan                                    |

## Konsekuensi

- `lab-deploy.sh` dan `lab-workers.slice` adalah konfigurasi host: perubahannya dipasang manual oleh admin (disengaja: CI tidak bisa melonggarkan batasannya sendiri).
- Bila file slice belum terpasang, systemd membuat slice kosong **tanpa kuota** tanpa error; pemeriksaan `cpu.max` wajib setelah setup host.
- Dua job berat yang berjalan bersamaan saling memperlambat (berbagi satu core), bukan mengantre.
- Deploy membuat ulang container yang berubah; klien SSE tersambung ulang otomatis (`retry: 3000`, snapshot).
- Setelah reboot, Docker menghidupkan container tanpa mengikuti `depends_on`; worker crash-only dengan `restart: unless-stopped` menangani urutan ini (terverifikasi: stack pulih, sertifikat tidak diminta ulang).
- Proyek baru: tambah image ke `ALL` di `ci.yml`, service ke `compose.vps.yaml` (worker dengan `cgroup_parent: lab-workers.slice`), rute `/api/<proyek>/*` dan `readyz` di `Caddyfile`, serta verifikasi versi di `lab-deploy`.

## Verifikasi (L0.8)

- SSH: login `adrianus` dengan kunci berhasil; `root` ditolak; `sshd -T` menunjukkan `permitrootlogin no`, `passwordauthentication no`.
- Dari internet: `http://` → `308`; `https://` → `HTTP/2 200` dengan HSTS tanpa header `Server`; port 5432 dan 8080 timeout.
- SSE lewat TLS: job ditahan dengan menghentikan worker; `: ping` tiba tiap 15 s, lalu `running` → progres → `succeeded` dalam 75 ms setelah worker hidup (menutup pertanyaan terbuka L0.5).
- Reboot: semua service kembali `Up`, `migrate` tetap `Exited (0)`, Caddy memuat sertifikat dari volume.
- `lab-deploy`: `status` berjalan; `bash` dan `deploy 1234; rm -rf /` ditolak; SHA `main` lama lolos cek riwayat dan gagal rapi saat unduh tanpa menyentuh stack; jalur rollback `sudo -u deploy` berfungsi.
- Slice: `CPUQuotaPerSecUSec=1s`, `cpu.max` = `100000 100000`, eksperimen di atas.

## Runbook setup host baru (urutan)

1. `apt full-upgrade`; buat user admin + `sudo`; salin `authorized_keys`; uji login di terminal baru.
2. `00-hardening.conf`, `sshd -t`, `systemctl reload ssh`; uji root ditolak.
3. UFW (aturan SSH sebelum `ufw enable`) + firewall hPanel.
4. `52unattended-upgrades-local`, swap + `99-applied-math-lab.conf`.
5. Docker dari repo resmi + `daemon.json`.
6. DNS `A` + `CAA`.
7. User `deploy` (+ grup `docker`), `/opt/applied-math-lab` milik `deploy`, `.env` (600), `lab-deploy` (root, 755), `authorized_keys` dengan `restrict,command=...`, `lab-workers.slice` + `daemon-reload` + periksa `cpu.max`.
8. Environment `production` di GitHub; deploy pertama lewat `workflow_dispatch` atau merge ke `main`.
