# MealOps — Model Matematis

> **Status:** §1 selesai (MO-1.1), §2 selesai (MO-1.2), §3 selesai (MO-1.3), §4 selesai (MO-1.4), §5–§7 selesai (MO-1.5). Review menyeluruh di MO-1.6.
> **Rujukan:** `PROJECT_CONTEXT` MealOps v3.1 §8. Glosarium §8.1 di sana adalah notasi kanonik; dokumen ini hanya menambah notasi yang belum ada dan menetapkan semantiknya.
> **Catatan:** semua angka di contoh bersifat ilustratif. $H^{max}$ adalah parameter kebijakan, bukan standar keamanan pangan.

## 1. Skenario, satuan, semantik waktu, dan asumsi

### 1.1 Skenario acuan

Satu dapur massal memasak makanan dalam beberapa batch pada satu hari operasi, lalu armada kendaraan mengantarkannya ke $n$ node pengantaran. Perjalanan satu porsi:

```text
γ_b ──masak── f_b ··· π_b ──packing── p_b ──muat λ── S ──jalan── A_j ·tunggu· T_j ··· d_j ──δ── m
              └──────────────────────── holding h_j ────────────────────────────────────────────┘
```

Model A (§8.5 v3.1) hanya melihat bagian $S$ sampai $T_j$. Model C dan D menambahkan bagian dapur dan batas holding. Semantik waktu di bawah ini berlaku untuk keempat model.

### 1.2 Satuan

| Besaran                             | Satuan                         | Tipe           |
| ----------------------------------- | ------------------------------ | -------------- |
| Waktu (jam kejadian)                | menit sejak 00:00 hari operasi | bilangan bulat |
| Durasi (tempuh, layan, muat, masak) | menit                          | bilangan bulat |
| Demand, kapasitas, ukuran batch     | porsi                          | bilangan bulat |
| Jarak (hanya untuk biaya)           | meter                          | bilangan bulat |

Aturan:

1. **Titik nol** adalah 00:00 hari operasi. Contoh: 07:30 ditulis $7 \cdot 60 + 30 = 450$.
2. **Satu hari operasi:** semua waktu berada di $[0, 1440)$. Operasi yang melewati tengah malam berada di luar cakupan MVP.
3. **Pembulatan ke atas, sekali, saat instans dibuat.** Durasi turunan yang bisa pecahan, misalnya $s_j = s^0 + \eta q_j$, disimpan sebagai $\lceil s_j \rceil$. Contoh: $s^0 = 5$, $\eta = 0{,}02$, $q_j = 180$ memberi $8{,}6$, disimpan $9$. Validator dan core hanya melihat bilangan bulat. Durasi batch bergantung pada keputusan $D_b$, jadi dibulatkan saat dihitung (§5.3).

Alasan bilangan bulat: uji kelayakan berbentuk perbandingan ($T_j \le d_j$). Dengan bilangan bulat, validator Python dan evaluator Rust selalu memberi jawaban yang sama tanpa toleransi. Pembulatan ke atas tidak pernah membuat rencana tampak lebih longgar daripada kenyataannya.

### 1.3 Notasi tambahan

Notasi berikut tidak ada di glosarium §8.1 v3.1.

| Notasi | Arti                                | Satuan |
| ------ | ----------------------------------- | ------ |
| $A_j$  | Waktu kendaraan tiba di node $j$    | waktu  |
| $W_j$  | Lama kendaraan menunggu di node $j$ | menit  |

Notasi v3.1 yang dipakai di bagian ini: $\tau_{ij}$ (waktu tempuh), $s_j$ (waktu layan), $a_j$ (paling awal menerima), $d_j$ (deadline), $T_j$ (mulai layanan), $m_{\sigma(j)}$ (waktu konsumsi terencana), $\delta_{\sigma(j)}$ (buffer), $\lambda$ (waktu muat), $S^{kr}$ (berangkat dari dapur), $f_b$ (selesai masak), $\pi_b$ dan $p_b$ (mulai dan selesai packing), $h_j$ (holding), $H^{max}$ (batas holding).

### 1.4 Jam kejadian di sepanjang rute

Misalkan $i$ adalah node tepat sebelum $j$ pada rute.

$$A_j = T_i + s_i + \tau_{ij}, \qquad T_j = \max(A_j,\ a_j), \qquad W_j = T_j - A_j$$

Untuk node pertama pada trip $(k, r)$: $A_j = S^{kr} + \tau_{0j}$. Kendaraan berangkat dari $j$ pada $T_j + s_j$.

Node $j$ **layak** bila $T_j \le d_j$, dengan $d_j = m_{\sigma(j)} - \delta_{\sigma(j)}$. Jendela bersifat keras: tiba terlalu awal boleh (menunggu), terlambat tidak boleh.

**Batas pada mulai layanan setara dengan batas pada waktu tiba.** Bila $a_j \le d_j$, maka $T_j \le d_j \iff A_j \le d_j$:

- Jika $A_j \le d_j$: $T_j$ adalah yang terbesar dari $A_j$ dan $a_j$, dan keduanya $\le d_j$, jadi $T_j \le d_j$.
- Jika $T_j \le d_j$: karena $T_j \ge A_j$, maka $A_j \le d_j$.

Ini adalah konvensi Solomon, sehingga hasil dapat dibandingkan langsung dengan BKS.

**Contoh.** Rute $0 \to 1 \to 2 \to 0$ dengan $\tau_{01} = 20$, $\tau_{12} = 15$, $\tau_{20} = 25$, $s_1 = s_2 = 10$, jendela node 1 $[570, 600]$ dan node 2 $[600, 615]$.

| Berangkat | $A_1$ | $T_1$ | $W_1$ | $A_2$ | $T_2$ | $W_2$ | Kembali | Layak                   |
| --------: | ----: | ----: | ----: | ----: | ----: | ----: | ------: | ----------------------- |
|       540 |   560 |   570 |    10 |   595 |   600 |     5 |     635 | ya                      |
|       560 |   580 |   580 |     0 |   605 |   605 |     0 |     640 | ya                      |
|       570 |   590 |   590 |     0 |   615 |   615 |     0 |     650 | ya, tepat di batas      |
|       575 |   595 |   595 |     0 |   620 |   620 |     0 |       — | tidak, node 2 ($> 615$) |

Jam berangkat paling lambat diperoleh dengan mundur dari deadline: $T_2 \le 615 \Rightarrow T_1 \le 615 - 10 - 15 = 590$, digabung dengan batas node 1 sendiri menjadi $T_1 \le \min(600, 590) = 590$, sehingga berangkat $\le 590 - 20 = 570$. Ini cikal bakal _forward time slack_ (MO-7.1b).

### 1.5 Holding time

$$h_j = m_{\sigma(j)} - f_b$$

dengan $b$ batch yang melayani node $j$. Jam mulai saat batch selesai dimasak dan berhenti pada waktu konsumsi **terencana**. Holding adalah proxy kebijakan, bukan ukuran keamanan pangan.

**Dekomposisi.** Dengan menyisipkan semua jam kejadian di antara $f_b$ dan $m$:

$$h_j = (\pi_b - f_b) + (p_b - \pi_b) + (S - p_b) + (A_j - S) + (T_j - A_j) + (d_j - T_j) + (m - d_j)$$

Sukunya berturut-turut: tunggu packing, packing, muat dan tunggu berangkat ($\ge \lambda$), perjalanan, tunggu $W_j$, slack, dan buffer $\delta$. Suku tengah saling menghapus dan tersisa $m - f_b$. Semua suku $\ge 0$ pada rencana yang layak.

**Jendela selesai masak.** Untuk satu batch $b$:

- Batas bawah, dari $h_j \le H^{max}$: $f_b \ge \max_j m_{\sigma(j)} - H^{max}$, maksimum atas node di batch.
- Batas atas, dari rute: bila trip paling lambat boleh berangkat pada $S$, maka $f_b \le S - \lambda - (\text{durasi packing})$, karena $S \ge p_b + \lambda$ dan $p_b \ge f_b + (\text{durasi packing})$.

Bila batas bawah melebihi batas atas, instans tidak layak. Bentuk umumnya (lower bound holding) diturunkan di §7.

**Contoh.** Lanjutan rute di atas, dengan $\delta = 15$ (jadi $m_1 = 615$, $m_2 = 630$), durasi packing 30, $\lambda = 10$, $H^{max} = 120$, satu batch untuk kedua node, packing langsung, berangkat secepat mungkin.

| $f_b$ | $p_b$ | $S$ | $T_1$ | $T_2$ | $h_1$ | $h_2$ | Layak                  |
| ----: | ----: | --: | ----: | ----: | ----: | ----: | ---------------------- |
|   500 |   530 | 540 |   570 |   600 |   115 |   130 | tidak, $h_2 > 120$     |
|   505 |   535 | 545 |   570 |   600 |   110 |   125 | tidak, $h_2 > 120$     |
|   510 |   540 | 550 |   570 |   600 |   105 |   120 | ya                     |
|   530 |   560 | 570 |   590 |   615 |    85 |   100 | ya, berangkat di batas |

Jendelanya $510 \le f_b \le 530$. Dengan $H^{max} = 100$ jendela menyusut menjadi $f_b = 530$; dengan $H^{max} = 90$ jendela kosong. Holding minimum instans ini adalah $630 - 530 = 100$ menit.

### 1.6 Asumsi (MVP)

Dari MealOps v3.1 §8.2 dan §8.4:

| #   | Asumsi                                                                               |
| --- | ------------------------------------------------------------------------------------ |
| A1  | Armada homogen dengan kapasitas $Q$ porsi                                            |
| A2  | $\tau_{ij}$ deterministik dan boleh asimetris; ketidakpastian hanya di simulasi      |
| A3  | Kendaraan boleh menunggu sebelum jendela waktu terbuka                               |
| A4  | Satu sopir per kendaraan; sopir bukan variabel keputusan                             |
| A5  | Satu lini masak dan satu lini packing; batch diproses sesuai urutan indeks           |
| A6  | Demand $q_i > Q$ dipecah menjadi $\lceil q_i / Q \rceil$ node dengan ukuran terkunci |

Ditetapkan di MO-1.1:

| #   | Asumsi                                                                                                            |
| --- | ----------------------------------------------------------------------------------------------------------------- |
| B1  | Waktu dalam menit bulat sejak 00:00; durasi turunan dibulatkan ke atas saat instans dibuat (§1.2)                 |
| B2  | Satu hari operasi; semua waktu di $[0, 1440)$                                                                     |
| B3  | $d_j$ membatasi mulai layanan $T_j$; jendela keras (§1.4)                                                         |
| B4  | $h_j = m_{\sigma(j)} - f_b$: seluruh batch selesai pada satu saat $f_b$; jam berhenti di waktu konsumsi terencana |
| B5  | Buffer menutup waktu layan: $\delta_{\sigma(j)} \ge s_j$                                                          |
| B6  | Ketaksamaan segitiga: $\tau_{ij} \le \tau_{ik} + \tau_{kj}$ untuk semua $i, j, k$                                 |
| B7  | Waktu muat $\lambda$ tetap per trip, tidak bergantung jumlah porsi                                                |
| B8  | $H^{max}$ adalah parameter kebijakan ilustratif                                                                   |

Catatan:

- **B5.** Bongkar selesai pada $T_j + s_j$, yang bisa melewati $d_j$. Dengan $\delta_{\sigma(j)} \ge s_j$, bongkar selalu selesai sebelum $m_{\sigma(j)}$, karena $T_j + s_j \le d_j + \delta_{\sigma(j)} = m_{\sigma(j)}$.
- **B6.** Dipakai oleh lower bound (§7, MO-6.3). Pembulatan ke atas mempertahankannya, karena $\lceil x + y \rceil \le \lceil x \rceil + \lceil y \rceil$.
- **A6.** Sejak MO-1.5 batas pemecahan adalah $\bar Q = \min(Q, D^{max})$ (K1, §5.6).

### 1.7 Pemeriksaan instans

Instans ditolak saat validasi input bila salah satu syarat berikut dilanggar (diimplementasikan di MO-2.1 dan MO-3.2):

1. Semua waktu dan durasi adalah bilangan bulat tak negatif, dan semua waktu berada di $[0, 1440)$.
2. $a_j \le d_j$ untuk setiap node.
3. $\delta_{\sigma(j)} \ge s_j$ untuk setiap node (B5).
4. $\tau_{ii} = 0$, dan $\tau_{jj'} = 0$ bila $\sigma(j) = \sigma(j')$.
5. $\tau_{ij} \le \tau_{ik} + \tau_{kj}$ untuk semua $i, j, k$ (B6).
6. $q_j$ bilangan bulat dengan $1 \le q_j \le \bar Q$ untuk setiap node setelah pemecahan demand, dengan $\bar Q = \min(Q, D^{max})$. Batas bawah ditetapkan di MO-1.2 (C1, §2.10), batas atas di MO-1.5 (K1, §5.6).
7. Parameter produksi: $e_{dapur}$, $H^{max}$, dan $\lambda$ bilangan bulat tak negatif; $\phi^c_0, \phi^c_1, \phi^p_0, \phi^p_1 \ge 0$; $D^{max} \ge 1$ dan $\lvert B \rvert \ge 1$ bilangan bulat (MO-1.5).

## 2. Model A — CVRPTW (single-trip)

Model A adalah lapisan pertama. Setiap kendaraan menjalani **satu rute**: berangkat dari dapur, melayani beberapa node, lalu kembali. Belum ada multi-trip, waktu muat $\lambda$, produksi, maupun holding; $m$ dan $\delta$ hanya masuk lewat $d_j$. Tujuannya membangun intuisi dan menjadi dasar verifikasi pada instans kecil (v3.1 §8.5).

Formulasi di bawah adalah **spesifikasi**: ia mendefinisikan apa yang layak dan apa yang dioptimasi, dan tidak diselesaikan dengan solver MILP. Validator dan core mengimplementasikan semantik yang sama lewat pemeriksaan rute di §2.7.

### 2.1 Graf dan notasi tambahan

| Notasi                                                  | Arti                                                                 |
| ------------------------------------------------------- | -------------------------------------------------------------------- |
| $V = \lbrace 0 \rbrace \cup N \cup \lbrace n+1 \rbrace$ | Semua node; $0$ dan $n+1$ adalah dapur (titik berangkat dan kembali) |
| $\mathcal{A}$                                           | Himpunan arc yang diperbolehkan                                      |
| $a'_j,\ d'_j$                                           | Jendela efektif node $j$ setelah jam dapur dilebur (§2.3)            |
| $T^{\ast}_j$                                            | Mulai layanan di node $j$ pada jadwal tercepat (§2.7)                |

Notasi v3.1 yang dipakai di bagian ini: $x_{ij}$, $T_j$, $u_j$, $c_{ij}$, $q_j$, $Q$, $K$, $[e_0, l_0]$, $M_{ij}$.

Dapur dibuat dua salinan supaya setiap rute berupa **lintasan** dari $0$ ke $n+1$, bukan lingkaran. Arc yang diperbolehkan ada tiga jenis: berangkat, antar-node, dan pulang.

$$\mathcal{A} = \lbrace (0, j) : j \in N \rbrace \ \cup\ \lbrace (i, j) : i, j \in N,\ i \ne j \rbrace \ \cup\ \lbrace (i, n+1) : i \in N \rbrace$$

$$\lvert \mathcal{A} \rvert = n + n(n-1) + n = n(n+1)$$

Tidak ada arc $(j, j)$, arc masuk ke $0$, arc keluar dari $n+1$, maupun arc $(0, n+1)$ (rute kosong).

### 2.2 Variabel keputusan

| Variabel | Tipe    | Arti                                                          |
| -------- | ------- | ------------------------------------------------------------- |
| $x_{ij}$ | biner   | $1$ bila ada kendaraan yang berjalan langsung dari $i$ ke $j$ |
| $T_j$    | kontinu | Waktu mulai layanan di node $j$                               |
| $u_j$    | kontinu | Muatan kumulatif: porsi yang sudah diturunkan sampai node $j$ |

Variabel $x$ tidak berindeks kendaraan. Itu cukup karena armada homogen (A1): menukar dua kendaraan tidak mengubah biaya maupun kelayakan, jadi yang penting hanya bentuk rutenya.

### 2.3 Jendela efektif: jam dapur dilebur ke node

Model dua-indeks hanya punya satu node $0$ untuk semua kendaraan, padahal setiap kendaraan berangkat pada jam yang berbeda. Karena itu jam operasional dapur $[e_0, l_0]$ tidak diberi variabel sendiri, tetapi dilebur ke jendela setiap node:

$$a'_j = \max(a_j,\ e_0 + \tau_{0j}), \qquad d'_j = \min(d_j,\ l_0 - s_j - \tau_{j,n+1})$$

**Mengapa $a'\_j$ sah.** Kendaraan berangkat paling cepat pada $e_0$. Lewat rute mana pun ia tiba di $j$ paling cepat pada $e_0 + \tau_{0j}$: menurut ketaksamaan segitiga (B6) jalan memutar tidak pernah lebih singkat, dan waktu layan serta waktu tunggu tidak negatif.

**Mengapa $d'\_j$ sah.** Setelah selesai di $j$ pada $T_j + s_j$, kendaraan tiba kembali di dapur paling cepat pada $T_j + s_j + \tau_{j,n+1}$, lagi-lagi karena B6. Nilai itu harus $\le l_0$, jadi syaratnya **perlu** untuk setiap node. Untuk node terakhir pada rute, syarat itu persis "pulang sebelum $l_0$", jadi syaratnya juga **cukup**.

Akibatnya:

- Model A tidak memerlukan baris khusus dapur, sesuai v3.1 §8.5.
- Bila $a'_j > d'_j$, node $j$ tidak dapat dilayani bahkan oleh kendaraan khusus, sehingga instans tidak layak. Ini dilaporkan sebagai ketidaklayakan beserta nodenya, bukan sebagai input yang tidak valid.

### 2.4 Formulasi

**(F0) Objektif:** total jarak.

$$\min \sum_{(i,j) \in \mathcal{A}} c_{ij} x_{ij}$$

Suku $c_{ij} x_{ij}$ bernilai $c_{ij}$ bila arc dipakai dan $0$ bila tidak, jadi yang terjumlah hanya arc yang dipakai.

**(F1) Tepat satu arc masuk** ke setiap node, dari dapur atau dari node lain.

$$x_{0j} + \sum_{i \in N,\ i \ne j} x_{ij} = 1 \qquad \forall j \in N$$

**(F2) Tepat satu arc keluar** dari setiap node, ke node lain atau ke dapur.

$$\sum_{i \in N,\ i \ne j} x_{ji} + x_{j,n+1} = 1 \qquad \forall j \in N$$

**(F3) Armada.** Setiap kendaraan yang dipakai menyalakan tepat satu arc keluar dari $0$.

$$\sum_{j \in N} x_{0j} \le \lvert K \rvert$$

**(F4) Propagasi muatan.**

$$u_j \ge u_i + q_j - Q (1 - x_{ij}) \qquad \forall i, j \in N,\ i \ne j$$

**(F5) Batas muatan.**

$$q_j \le u_j \le Q \qquad \forall j \in N$$

**(F6) Propagasi waktu.**

$$T_j \ge T_i + s_i + \tau_{ij} - M_{ij} (1 - x_{ij}) \qquad \forall i, j \in N,\ i \ne j$$

$$M_{ij} = \max \lbrace 0,\ d'_i + s_i + \tau_{ij} - a'_j \rbrace$$

**(F7) Jendela waktu.**

$$a'_j \le T_j \le d'_j \qquad \forall j \in N$$

**(F8) Domain.** $x_{ij} \in \lbrace 0, 1 \rbrace$ untuk setiap $(i,j) \in \mathcal{A}$.

Arc dari dapur $(0, j)$ tidak memerlukan baris F4 maupun F6: dengan muatan awal $0$ dan berangkat paling cepat $e_0$, barisnya menjadi $u_j \ge q_j$ dan $T_j \ge e_0 + \tau_{0j}$, yang sudah dijamin F5 dan F7. Arc pulang $(i, n+1)$ sudah ditangani $d'_i$.

**Ukuran model.**

| $n$ | Variabel biner $n(n+1)$ | Variabel kontinu $2n$ | Baris F1–F3 ($2n + 1$) | Baris F4 + F6 ($2n(n-1)$) |
| --: | ----------------------: | --------------------: | ---------------------: | ------------------------: |
|  10 |                     110 |                    20 |                     21 |                       180 |
|  25 |                     650 |                    50 |                     51 |                      1200 |
| 100 |                   10100 |                   200 |                    201 |                     19800 |

### 2.5 Big-M: menulis aturan bersyarat

Aturan "**jika** $x_{ij} = 1$ **maka** $u_j \ge u_i + q_j$" tidak linear. Triknya: tambahkan suku $-M(1 - x_{ij})$, yang bernilai $0$ saat arc dipakai (aturan aktif) dan $-M$ saat arc tidak dipakai. $M$ harus cukup besar agar baris arc yang tidak dipakai **tidak melarang apa pun**, dan sebaiknya tidak lebih besar dari itu.

**Kapasitas.** Saat $x_{ij} = 0$, baris F4 menuntut $M \ge u_i + q_j - u_j$ untuk semua nilai yang diizinkan F5. Ruas kanan terbesar saat $u_i$ terbesar ($Q$) dan $u_j$ terkecil ($q_j$):

$$u_i + q_j - u_j \le Q + q_j - q_j = Q$$

Jadi $M = Q$.

**Waktu.** Saat $x_{ij} = 0$, baris F6 menuntut $M_{ij} \ge T_i + s_i + \tau_{ij} - T_j$ untuk semua nilai yang diizinkan F7. Ruas kanan terbesar saat $T_i$ terbesar ($d'_i$) dan $T_j$ terkecil ($a'_j$):

$$T_i + s_i + \tau_{ij} - T_j \le d'_i + s_i + \tau_{ij} - a'_j$$

Bila nilai itu negatif, baris tanpa peredam pun selalu benar, sehingga $M_{ij} = 0$ cukup. Digabung: $M_{ij} = \max \lbrace 0,\ d'_i + s_i + \tau_{ij} - a'_j \rbrace$. Berbeda dengan kapasitas, nilainya berbeda untuk setiap arc.

**$M$ terlalu besar** hanya membuat model longgar. **$M$ terlalu kecil membuat model salah**, karena baris arc yang tidak dipakai ikut membuang solusi yang layak (contoh di §2.9).

### 2.6 Struktur solusi dan eliminasi subtour

**Yang berangkat sama banyak dengan yang pulang.** Hitung jumlah semua arc yang dipakai dengan dua cara. Menurut ujungnya: setiap node menerima tepat satu (F1), sisanya berujung di $n+1$. Menurut pangkalnya: setiap node mengeluarkan tepat satu (F2), sisanya berpangkal di $0$.

$$n + \sum_{i \in N} x_{i,n+1} = n + \sum_{j \in N} x_{0j} \quad\Longrightarrow\quad \sum_{i \in N} x_{i,n+1} = \sum_{j \in N} x_{0j}$$

**F1 dan F2 saja belum cukup.** Setiap $x$ yang memenuhi F1, F2, F8 terurai menjadi lintasan $0 \to \dots \to n+1$ ditambah nol atau lebih siklus di antara node-node $N$ (_subtour_):

1. Setiap node punya tepat satu penerus. Mulai dari arc $(0, j)$ yang dipakai dan ikuti penerusnya.
2. Perjalanan itu tidak bisa kembali ke node yang sudah dilewati, karena node tersebut akan punya dua arc masuk. Jadi ia berakhir di $n+1$: satu lintasan.
3. Node yang tidak terjangkau dari $0$ tetap punya satu penerus dan satu pendahulu, semuanya di $N$. Mengikuti penerusnya pasti kembali ke node awal: satu siklus.

**Kapasitas menghapus siklus.** Ambil siklus $j_1 \to j_2 \to \dots \to j_m \to j_1$ dan tulis $j_{m+1} = j_1$. Baris F4 setiap arcnya: $u_{j_{t+1}} \ge u_{j_t} + q_{j_{t+1}}$ untuk $t = 1, \dots, m$. Jumlahkan semuanya; setiap $u$ muncul tepat sekali di kiri dan tepat sekali di kanan:

$$\sum_{t=1}^{m} u_{j_t} \ge \sum_{t=1}^{m} u_{j_t} + \sum_{t=1}^{m} q_{j_t} \quad\Longrightarrow\quad 0 \ge \sum_{t=1}^{m} q_{j_t}$$

Mustahil karena $q_j \ge 1$ (C1). Lintasan dari dapur lolos karena tidak ada baris yang menutup lingkaran: node pertama hanya muncul di ruas kanan dan node terakhir hanya di ruas kiri.

**Waktu juga menghapus siklus, dengan syarat.** Menjumlahkan baris F6 di sepanjang siklus dengan cara yang sama memberi

$$0 \ge \sum_{t=1}^{m} \left( s_{j_t} + \tau_{j_t j_{t+1}} \right)$$

yang mustahil bila ada satu saja arc pada siklus dengan $s + \tau > 0$. Syarat ini bisa gagal: node hasil pemecahan demand dari titik layanan yang sama punya $\tau_{jj'} = 0$ (§1.7 nomor 4), dan bila $s_j = 0$ jumlahnya nol. Karena itu eliminasi subtour **bersandar pada kapasitas**; waktu adalah penjamin kedua.

### 2.7 Kesetaraan dengan pemeriksaan rute

F4 dan F6 memakai $\ge$, jadi $u_j$ dan $T_j$ boleh lebih besar dari nilai sebenarnya. Bagian ini menunjukkan bahwa kelonggaran itu tidak mengubah apa yang layak.

Untuk rute $0 \to j_1 \to j_2 \to \dots \to j_m \to n+1$, **jadwal tercepat** adalah

$$T^{\ast}_{j_1} = a'_{j_1}, \qquad T^{\ast}_{j_{t+1}} = \max \left( T^{\ast}_{j_t} + s_{j_t} + \tau_{j_t j_{t+1}},\ a'_{j_{t+1}} \right)$$

Ini rumus §1.4 dengan keberangkatan secepat mungkin. Yang dibawa ke node berikutnya selalu jam **mulai layanan** $T^{\ast}$ (sudah termasuk menunggu), bukan jam tiba $A$.

**Proposisi.** Misalkan $x$ memenuhi F1–F3 dan F8. Ada $T$ dan $u$ yang memenuhi F4–F7 jika dan hanya jika $x$ tidak memuat siklus dan setiap rutenya memenuhi

$$\sum_{t=1}^{m} q_{j_t} \le Q \qquad \text{dan} \qquad T^{\ast}_{j_t} \le d'_{j_t} \quad \text{untuk } t = 1, \dots, m$$

**Bukti, arah ⇒.** Siklus sudah ditolak §2.6. Untuk muatan, substitusi berantai baris F4 di sepanjang rute memberi $u_{j_m} \ge q_{j_1} + \dots + q_{j_m}$, dan $u_{j_m} \le Q$. Untuk waktu, tunjukkan $T^{\ast}_j \le T_j$ di setiap node:

1. Node pertama: $T_{j_1} \ge a'_{j_1} = T^{\ast}_{j_1}$ (F7).
2. Andaikan $T^{\ast}_{j_t} \le T_{j_t}$. Dari F6, $T_{j_{t+1}} \ge T_{j_t} + s_{j_t} + \tau_{j_t j_{t+1}} \ge T^{\ast}_{j_t} + s_{j_t} + \tau_{j_t j_{t+1}}$. Dari F7, $T_{j_{t+1}} \ge a'_{j_{t+1}}$. Jadi $T_{j_{t+1}}$ tidak kurang dari yang terbesar di antara keduanya, yaitu $T^{\ast}_{j_{t+1}}$.

Maka $T^{\ast}_j \le T_j \le d'_j$.

**Bukti, arah ⇐.** Pilih $u$ sebagai muatan kumulatif sebenarnya dan $T = T^{\ast}$. Baris arc yang dipakai terpenuhi menurut definisi, baris arc yang tidak dipakai terpenuhi karena pilihan $M$ (§2.5), dan batas F5 serta F7 terpenuhi menurut syarat. ∎

**Akibat: pemeriksaan satu rute** (dipakai validator MO-3.2 dan evaluator core, satu lintasan maju, $O(m)$):

1. Jumlahkan $q_j$ di rute. Gagal bila hasilnya $> Q$.
2. Set $t \leftarrow a'_{j_1}$. Gagal bila $t > d'_{j_1}$.
3. Untuk setiap node berikutnya $j$ dengan pendahulu $i$: hitung $A_j = t + s_i + \tau_{ij}$, lalu $t \leftarrow \max(A_j,\ a'_j)$. Gagal bila $t > d'_j$.
4. Bila sampai akhir tanpa gagal, rute layak.

Jam berangkat rute itu adalah $T^{\ast}_{j_1} - \tau_{0 j_1} \ge e_0$ dan jam kembalinya $T^{\ast}_{j_m} + s_{j_m} + \tau_{j_m, n+1} \le l_0$. Karena semua data bilangan bulat (B1), $T^{\ast}$ juga bilangan bulat.

### 2.8 Praproses: arc yang mustahil

Arc $(i, j)$ dengan $i, j \in N$ pasti tidak dipakai, sehingga $x_{ij} = 0$ dapat ditetapkan sebelum pencarian, bila salah satu berlaku:

- **Waktu:** $a'_i + s_i + \tau_{ij} > d'_j$. Berangkat secepat mungkin dari pangkal $i$ pun sudah melewati deadline di ujung $j$.
- **Kapasitas:** $q_i + q_j > Q$.

Pembandingnya selalu deadline node **tujuan**. Uji ini syarat perlu saja: arc yang lolos belum tentu dapat dipakai pada rute tertentu. Dipakai di MO-5 (konstruktif) dan MO-6.2 (pemangkasan).

### 2.9 Contoh ($n = 4$)

Data: $\lvert K \rvert = 2$, $Q = 100$, $s_j = 10$, dapur buka $[e_0, l_0] = [480, 720]$, node $5$ adalah dapur sebagai titik kembali. Jarak simetris $c_{ij}$ dalam ratusan meter agar angkanya kecil, dan $\tau_{ij} = 5 c_{ij}$ menit.

| $c_{ij}$ |   0 |   1 |   2 |   3 |   4 |
| -------- | --: | --: | --: | --: | --: |
| **0**    |   – |   4 |   5 |   6 |   3 |
| **1**    |   4 |   – |   2 |   6 |   6 |
| **2**    |   5 |   2 |   – |   4 |   7 |
| **3**    |   6 |   6 |   4 |   – |   5 |
| **4**    |   3 |   6 |   7 |   5 |   – |

| Node | $q_j$ | $a_j$ | $d_j$ | $e_0 + \tau_{0j}$ | $l_0 - s_j - \tau_{j5}$ | $a'_j$ | $d'_j$ |
| ---- | ----: | ----: | ----: | ----------------: | ----------------------: | -----: | -----: |
| 1    |    30 |   510 |   560 |               500 |                     690 |    510 |    560 |
| 2    |    50 |   520 |   570 |               505 |                     685 |    520 |    570 |
| 3    |    40 |   540 |   600 |               510 |                     680 |    540 |    600 |
| 4    |    20 |   480 |   540 |               495 |                     695 |    495 |    540 |

Hanya $a_4$ yang berubah. Total demand $140$, jadi dibutuhkan paling sedikit $\lceil 140 / 100 \rceil = 2$ kendaraan.

**Arc mustahil (§2.8).** Empat dari dua belas arc antar-node:

| Arc     | $a'_i + s_i + \tau_{ij}$ | $d'_j$ |
| ------- | -----------------------: | -----: |
| $(1,4)$ |    $510 + 10 + 30 = 550$ |    540 |
| $(2,4)$ |    $520 + 10 + 35 = 565$ |    540 |
| $(3,4)$ |    $540 + 10 + 25 = 575$ |    540 |
| $(3,1)$ |    $540 + 10 + 30 = 580$ |    560 |

Tidak ada node yang boleh mendahului node 4, jadi node 4 pasti node pertama di rutenya. Arc $(3,2)$ lolos tepat di batas: $540 + 10 + 20 = 570$, tidak lebih dari $570$.

**Solusi P:** rute $0 \to 1 \to 2 \to 5$ dan $0 \to 4 \to 3 \to 5$. Arc yang dipakai: $x_{01}, x_{12}, x_{25}, x_{04}, x_{43}, x_{35}$. Setiap node punya satu arc masuk dan satu arc keluar; $x_{01} + x_{04} = 2 \le 2$.

| Rute | Node | $u_j$          | $A_j$                 | $T^{\ast}_j$ | $W_j$ | $\le d'_j$ |
| ---- | ---- | -------------- | --------------------- | -----------: | ----: | ---------- |
| 1    | 1    | $30$           | $480 + 20 = 500$      |          510 |    10 | ya (560)   |
| 1    | 2    | $30 + 50 = 80$ | $510 + 10 + 10 = 530$ |          530 |     0 | ya (570)   |
| 2    | 4    | $20$           | $480 + 15 = 495$      |          495 |     0 | ya (540)   |
| 2    | 3    | $20 + 40 = 60$ | $495 + 10 + 25 = 530$ |          540 |    10 | ya (600)   |

Kembali ke dapur pada $530 + 10 + 25 = 565$ dan $540 + 10 + 30 = 580$. Biaya $(4 + 2 + 5) + (3 + 5 + 6) = 25$, yaitu $2500$ m. P layak.

**Baris arc yang tidak dipakai tidak mengganggu.** Untuk arc $(2,3)$: F4 memberi $60 \ge 80 + 40 - 100 = 20$, dan F6 dengan $M_{23} = \max \lbrace 0,\ 570 + 10 + 20 - 540 \rbrace = 60$ memberi $540 \ge 530 + 10 + 20 - 60 = 500$.

**Solusi Q:** $x_{01}, x_{12}, x_{25}, x_{34}, x_{43}$, yaitu satu rute ditambah siklus $3 \to 4 \to 3$. Q memenuhi F1–F3 dan biayanya hanya $(4 + 2 + 5) + (5 + 5) = 21$, tetapi F4 menuntut $u_4 \ge u_3 + 20$ dan $u_3 \ge u_4 + 40$, yang bila dijumlahkan memberi $0 \ge 60$. F6 juga menolaknya: $T_4 \ge T_3 + 35$ dan $T_3 \ge T_4 + 35$ memberi $0 \ge 70$.

**Satu kendaraan.** Tanpa kapasitas dan jendela waktu, rute tunggal termurah adalah $0 \to 1 \to 2 \to 3 \to 4 \to 5$ dengan biaya $18 < 25$. Dengan ketaksamaan segitiga, menggabung rute tidak pernah menambah jarak, jadi kendaraan kedua dipakai semata-mata karena kapasitas dan waktu.

**$M$ terlalu kecil.** Bila F4 memakai $M = 50$, bukan $Q = 100$, Solusi P tertolak meski layak. Rantainya: $u_3 \ge u_4 + 40 \ge 60$ (arc dipakai); baris $(3,1)$ memberi $u_1 \ge u_3 + 30 - 50 \ge 40$; lalu $u_2 \ge u_1 + 50 \ge 90$ (arc dipakai); baris $(2,3)$ memberi $u_3 \ge u_2 + 40 - 50 \ge 80$; ulangi, $u_1 \ge 60$ dan $u_2 \ge 110 > Q$.

**Optimum.** Enumerasi semua pembagian dan urutan memberi 8 solusi layak. Yang termurah berbiaya $25$: Solusi P dan variannya dengan rute pertama $0 \to 2 \to 1 \to 5$. Terbaik berikutnya berbiaya $28$.

### 2.10 Keputusan MO-1.2

| #   | Keputusan                                                                                                      |
| --- | -------------------------------------------------------------------------------------------------------------- |
| C1  | $q_j$ bilangan bulat $\ge 1$; node tanpa demand ditolak saat validasi instans (§1.7 nomor 6)                   |
| C2  | Jam dapur $[e_0, l_0]$ dilebur ke jendela efektif $a'_j$, $d'_j$ (§2.3); bersandar pada B6                     |
| C3  | Eliminasi subtour bersandar pada kapasitas (C1); propagasi waktu adalah penjamin kedua                         |
| C4  | Big-M memakai nilai terkecil yang sah: $Q$ untuk muatan, $M_{ij}$ per arc untuk waktu                          |
| C5  | Objektif Model A adalah total jarak; jumlah kendaraan hanya dibatasi $\lvert K \rvert$, belum menjadi objektif |
| C6  | Kelayakan satu rute diperiksa dengan satu lintasan maju jadwal tercepat (§2.7), setara dengan F4–F7            |

Yang belum dicakup Model A: lebih dari satu trip per kendaraan dan waktu muat $\lambda$ (Model B, §4), produksi batch (Model C, §5), serta release date dan holding (Model D, §6).

## 3. Contoh hitung tangan Model A: layak dan tidak layak

Bagian ini tidak menambah rumus. Isinya satu instans kecil (H5) yang dikerjakan lengkap dengan tangan, beserta contoh solusi dan instans yang tidak layak. Semua angka diverifikasi dengan enumerasi, dan instans beserta nilai harapannya menjadi fixture di MO-2.3.

### 3.1 Tiga tingkat kegagalan

| Tingkat             | Artinya                                                  | Contoh                    | Yang menolak                |
| ------------------- | -------------------------------------------------------- | ------------------------- | --------------------------- |
| Input tidak valid   | Data melanggar §1.7; soalnya sendiri salah               | $a_j > d_j$, $q_j > Q$    | Validasi instans (MO-2.1)   |
| Instans tidak layak | Data sah, tetapi tidak ada satu pun solusi yang layak    | Dapur tutup terlalu cepat | Solver melapor _infeasible_ |
| Solusi tidak layak  | Instans punya solusi, tetapi solusi ini melanggar aturan | Muatan $115 > 100$        | Validator (MO-3.2)          |

Cara memilih tingkat, ditanyakan berurutan:

1. Apakah datanya melanggar daftar §1.7? Jika ya: input tidak valid.
2. Apakah ada minimal satu solusi yang lolos? Jika tidak: instans tidak layak.
3. "Solusi tidak layak" hanya dipakai saat menilai satu solusi tertentu.

**Beban bukti tidak simetris.** Menunjukkan instans layak cukup dengan satu solusi yang lolos pemeriksaan (satu saksi). Menunjukkan instans tidak layak memerlukan argumen yang menutup semua kemungkinan solusi sekaligus.

### 3.2 Resep hitung tangan

1. **Periksa input** terhadap §1.7.
2. **Jendela efektif** setiap node: $a'_j = \max(a_j,\ e_0 + \tau_{0j})$ dan $d'_j = \min(d_j,\ l_0 - s_j - \tau_{j,n+1})$. Bila ada $a'_j > d'_j$, instans tidak layak.
3. **Batas bawah kendaraan:** $\lceil \sum_j q_j / Q \rceil$. Bila melebihi $\lvert K \rvert$, instans tidak layak.
4. **Uji arc** (§2.8). Tulis dulu ujung $j$ dan $d'_j$-nya, baru hitung $a'_i + s_i + \tau_{ij}$ dari pangkal $i$.
5. **Periksa setiap rute** (§2.7) dalam tabel berkolom $A_j$, $a'_j$, $T^{\ast}_j = \max(A_j, a'_j)$, $W_j$, $d'_j$. Kolom $a'_j$ ditulis supaya $\max$ tidak terlewat.
6. **Periksa struktur dan armada** (setiap node tepat sekali, jumlah rute $\le \lvert K \rvert$), lalu hitung biaya.

### 3.3 Instans H5

Data: $n = 5$, $\lvert K \rvert = 2$, $Q = 100$, dapur buka $[e_0, l_0] = [480, 680]$. Jarak simetris $c_{ij}$ dalam ratusan meter, $\tau_{ij} = 5 c_{ij}$ menit. Di tabel, node $0$ adalah dapur, baik sebagai titik berangkat maupun titik kembali.

| $c_{ij}$ |   0 |   1 |   2 |   3 |   4 |   5 |
| -------- | --: | --: | --: | --: | --: | --: |
| **0**    |   – |   3 |   6 |   5 |   4 |   4 |
| **1**    |   3 |   – |   3 |   6 |   5 |   5 |
| **2**    |   6 |   3 |   – |   5 |   8 |   8 |
| **3**    |   5 |   6 |   5 |   – |   5 |   9 |
| **4**    |   4 |   5 |   8 |   5 |   – |   8 |
| **5**    |   4 |   5 |   8 |   9 |   8 |   – |

| Node | $q_j$ | $s_j$ | $a_j$ | $d_j$ | $e_0 + \tau_{0j}$ | $l_0 - s_j - \tau_{j0}$ | $a'_j$ | $d'_j$ |
| ---- | ----: | ----: | ----: | ----: | ----------------: | ----------------------: | -----: | -----: |
| 1    |    25 |    10 |   560 |   610 |               495 |                     655 |    560 |    610 |
| 2    |    40 |    15 |   510 |   570 |               510 |                     635 |    510 |    570 |
| 3    |    20 |    10 |   600 |   650 |               505 |                     645 |    600 |    645 |
| 4    |    35 |     5 |   480 |   530 |               500 |                     655 |    500 |    530 |
| 5    |    15 |    10 |   580 |   610 |               500 |                     650 |    580 |    610 |

Dua nilai berubah:

- $a'_4 = 500$: node 4 menerima sejak 480, tetapi kendaraan baru bisa sampai pada $480 + 20 = 500$.
- $d'_3 = 645$: node 3 menerima sampai 650, tetapi layanan harus mulai paling lambat 645 agar kendaraan pulang sebelum $l_0$ ($645 + 10 + 25 = 680$).

Total demand $135$, jadi dibutuhkan paling sedikit $\lceil 135 / 100 \rceil = 2$ kendaraan.

### 3.4 Uji arc

Isi sel adalah $a'_i + s_i + \tau_{ij}$ untuk pangkal $i$ (baris) dan ujung $j$ (kolom). Arc mustahil, dicetak tebal, bila nilainya melebihi $d'_j$ di baris kedua.

| Pangkal $i$ ($a'_i + s_i$) |   $j=1$ |   $j=2$ | $j=3$ |   $j=4$ |   $j=5$ |
| -------------------------- | ------: | ------: | ----: | ------: | ------: |
| $d'_j$                     |     610 |     570 |   645 |     530 |     610 |
| 1 ($560 + 10$)             |       – | **585** |   600 | **595** |     595 |
| 2 ($510 + 15$)             |     540 |       – |   550 | **565** |     565 |
| 3 ($600 + 10$)             | **640** | **635** |     – | **635** | **655** |
| 4 ($500 + 5$)              |     530 |     545 |   530 |       – |     545 |
| 5 ($580 + 10$)             | **615** | **630** |   635 | **630** |       – |

Sepuluh dari dua puluh arc mustahil; tidak ada yang mustahil karena kapasitas (pasangan terbesar $40 + 35 = 75$). Akibatnya:

- Kolom 4 seluruhnya tebal: node 4 selalu node **pertama** di rutenya.
- Baris 3 seluruhnya tebal: node 3 selalu node **terakhir** di rutenya.
- Di kolom 2 hanya arc $(4,2)$ yang lolos: node 2 adalah node pertama, atau tepat setelah node 4.

### 3.5 Solusi layak S1

Rute $0 \to 2 \to 1 \to 5 \to 0$ dan $0 \to 4 \to 3 \to 0$.

| Rute | Node | Muatan | $A_j$                 | $a'_j$ | $T^{\ast}_j$ | $W_j$ | $\le d'_j$ |
| ---- | ---- | -----: | --------------------- | -----: | -----------: | ----: | ---------- |
| 1    | 2    |     40 | $480 + 30 = 510$      |    510 |          510 |     0 | ya (570)   |
| 1    | 1    |     65 | $510 + 15 + 15 = 540$ |    560 |          560 |    20 | ya (610)   |
| 1    | 5    |     80 | $560 + 10 + 25 = 595$ |    580 |          595 |     0 | ya (610)   |
| 2    | 4    |     35 | $480 + 20 = 500$      |    500 |          500 |     0 | ya (530)   |
| 2    | 3    |     55 | $500 + 5 + 25 = 530$  |    600 |          600 |    70 | ya (645)   |

Kembali ke dapur pada $595 + 10 + 20 = 625$ dan $600 + 10 + 25 = 635$. Biaya $(6 + 3 + 5 + 4) + (4 + 5 + 5) = 32$, yaitu $3200$ m. S1 layak.

**Semua solusi layak.** Enumerasi memberi 9 solusi layak; S1 satu-satunya yang termurah.

| Biaya | Rute 1    | Rute 2    |
| ----: | --------- | --------- |
|    32 | $(2,1,5)$ | $(4,3)$   |
|    34 | $(1,5)$   | $(4,2,3)$ |
|    34 | $(4,1,5)$ | $(2,3)$   |
|    36 | $(2,1,3)$ | $(4,5)$   |
|    36 | $(4,2,1)$ | $(5,3)$   |
|    38 | $(1,3)$   | $(4,2,5)$ |
|    38 | $(2,1)$   | $(4,5,3)$ |
|    38 | $(4,1,3)$ | $(2,5)$   |
|    40 | $(4,1)$   | $(2,5,3)$ |

### 3.6 Jebakan hitung tangan

**Rute $0 \to 2 \to 1 \to 5 \to 3 \to 0$** (muatan tepat $100$, masih boleh karena syaratnya $\le Q$). Hitungan yang benar melanjutkan tabel S1: $A_3 = 595 + 10 + 45 = 650$, $T^{\ast}_3 = 650 > d'_3 = 645$, rute gagal. Tiga kekeliruan yang membuatnya tampak layak:

| Kekeliruan                                                        | Hitungan                                                              | Putusan keliru |
| ----------------------------------------------------------------- | --------------------------------------------------------------------- | -------------- |
| Membawa $A_1 = 540$, atau lupa $\max$ dengan $a'_1$ ($T_1 = 540$) | $A_5 = 540 + 10 + 25 = 575$, $T_5 = 580$, $A_3 = 580 + 10 + 45 = 635$ | $635 \le 645$  |
| Memakai $d_3 = 650$, bukan $d'_3$                                 | $650 \le 650$, padahal pulang pada $650 + 10 + 25 = 685 > 680$        | tampak layak   |
| Memakai waktu layan node tujuan ($s_1 = 10$) di arc $(2,1)$       | $A_1 = 510 + 10 + 15 = 535$, bukan $540$                              | angka bergeser |

Kekeliruan pertama selalu membuat jadwal tampak **lebih cepat**, jadi kesalahannya searah: rute yang gagal bisa tampak layak, tidak pernah sebaliknya.

**Uji arc memakai deadline node tujuan.** Arc $(2,4)$: $510 + 15 + 40 = 565$ dibandingkan dengan $d'_4 = 530$, jadi mustahil. Membandingkannya dengan $610$ (deadline node lain) memberi putusan keliru.

**Uji arc hanya syarat perlu.** Pada rute $0 \to 1 \to 5 \to 3 \to 0$, arc $(1,5)$ dan $(5,3)$ keduanya lolos ($595 \le 610$ dan $635 \le 645$), tetapi rutenya gagal: $T^{\ast}_5 = 595$, sehingga $A_3 = 650 > 645$. Arc $(5,3)$ lolos karena dihitung dari $a'_5 = 580$, sedangkan di rute ini node 5 baru mulai dilayani pada 595.

### 3.7 Solusi tidak layak

Instansnya tetap H5; setiap baris adalah satu solusi yang melanggar satu aturan.

| Solusi                      | Yang dilanggar         | Hitungan                                                                             |
| --------------------------- | ---------------------- | ------------------------------------------------------------------------------------ |
| $(4,2,1,5)$ dan $(3)$       | Kapasitas              | $35 + 40 + 25 + 15 = 115 > 100$; waktunya lolos, node 5 tepat di $610$               |
| $(2,1)$ dan $(4,3,5)$       | Jendela waktu          | $A_5 = 600 + 10 + 45 = 655 > 610$                                                    |
| $(2,1,5,3)$ dan $(4)$       | Jendela waktu ($d'_3$) | $T^{\ast}_3 = 650 \le d_3$, tetapi $> d'_3 = 645$: kendaraan pulang pada $685 > l_0$ |
| $(2,1,5)$ dan $(4)$         | Struktur (F1)          | Node 3 tidak dikunjungi                                                              |
| $(2,1)$, $(4,3)$, dan $(5)$ | Armada (F3)            | 3 rute $> \lvert K \rvert = 2$, walau setiap rutenya layak (biaya 34)                |

### 3.8 Instans tidak layak

Setiap varian mengubah H5 seperlunya; datanya tetap sah menurut §1.7.

**V1, satu node mustahil.** $l_0 = 630$. Maka $d'_3 = \min(650,\ 630 - 10 - 25) = 595 < a'_3 = 600$. Kendaraan khusus pun paling cepat mulai melayani pada 600, selesai 610, dan pulang 635 $> 630$.

**V2, kapasitas total.** $\lvert K \rvert = 1$. Total demand $135 > 1 \cdot 100$.

**V3, kapasitas tidak bisa dibagi.** $q = (60, 60, 10, 60, 10)$. Total $200 \le 2 \cdot 100$, jadi hitungan total lolos. Tetapi node 1, 2, 4 masing-masing berdemand 60 dan harus masuk ke dua kendaraan, sehingga ada dua di antaranya yang sekendaraan (prinsip sarang merpati): $60 + 60 = 120 > 100$.

**V4, waktu tidak bisa dibagi.** Node 2, 3, 5 berjendela sama, $[540, 560]$. Keenam arc di antara mereka mustahil:

| Arc     | $a'_i + s_i + \tau_{ij}$ | $d'_j$ |
| ------- | -----------------------: | -----: |
| $(2,3)$ |    $540 + 15 + 25 = 580$ |    560 |
| $(2,5)$ |    $540 + 15 + 40 = 595$ |    560 |
| $(3,2)$ |    $540 + 10 + 25 = 575$ |    560 |
| $(3,5)$ |    $540 + 10 + 45 = 595$ |    560 |
| $(5,2)$ |    $540 + 10 + 40 = 590$ |    560 |
| $(5,3)$ |    $540 + 10 + 45 = 595$ |    560 |

Tidak ada dua dari ketiga node itu yang bisa serute, jadi dibutuhkan 3 rute, padahal $\lvert K \rvert = 2$.

**Pola umum.** V3 dan V4 memakai argumen yang sama: bila ada sekelompok node yang **berpasangan tidak bisa serute** (arc di antara dua node mustahil di kedua arah, atau $q_i + q_j > Q$), maka ukuran kelompok itu adalah batas bawah jumlah kendaraan. Digabung dengan langkah 3 resep:

$$\text{jumlah kendaraan} \ \ge\ \max \left( \left\lceil \frac{\sum_j q_j}{Q} \right\rceil,\ \text{ukuran kelompok saling tak serute terbesar} \right)$$

Dengan $\lvert K \rvert = 3$, V3 dan V4 menjadi layak (optimum 36 dan 34). Tidak semua instans tidak layak punya bukti sependek ini; untuk instans tiny, solver exact (MO-6.2) yang memutuskan.

**Pembanding: input tidak valid dan instans layak.** Perubahan lain pada H5:

| Perubahan   | Tingkat             | Alasan                                                                 |
| ----------- | ------------------- | ---------------------------------------------------------------------- |
| $q_2 = 120$ | Input tidak valid   | $q_2 > Q$; demand harus dipecah dulu (A6, §1.7 nomor 6)                |
| $Q = 30$    | Input tidak valid   | $q_2 = 40$ dan $q_4 = 35$ melebihi $Q$                                 |
| $d_5 = 570$ | Input tidak valid   | $a_5 = 580 > d_5$ (§1.7 nomor 2)                                       |
| $e_0 = 530$ | Instans tidak layak | $a'_4 = 530 + 20 = 550 > d'_4 = 530$                                   |
| $d_4 = 495$ | Instans tidak layak | $a_4 \le d_4$ sah, tetapi $a'_4 = 500 > d'_4 = 495$                    |
| $d_2 = 540$ | Layak               | Saksi S1: $T^{\ast}_2 = 510 \le 540$                                   |
| $l_0 = 640$ | Layak               | $d'_3 = 605$; saksi S1: $T^{\ast}_3 = 600 \le 605$, pulang 625 dan 635 |

### 3.9 Keputusan MO-1.3

| #   | Keputusan                                                                                                                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| E1  | Tiga tingkat kegagalan dibedakan dan dilaporkan terpisah: input tidak valid, instans tidak layak, solusi tidak layak (§3.1)                 |
| E2  | H5, solusi di §3.5 dan §3.7, serta varian V1–V4 menjadi fixture hitung tangan (MO-2.3); nilai harapannya adalah angka di bagian ini         |
| E3  | Batas bawah jumlah kendaraan: yang terbesar dari $\lceil \sum q / Q \rceil$ dan ukuran kelompok saling tak serute (§3.8); dipakai di MO-6.3 |

Pertanyaan terbuka untuk MO-3.2: apakah "pulang setelah $l_0$" dilaporkan sebagai pelanggaran tersendiri atau sebagai pelanggaran jendela efektif $d'_j$.

## 4. Model B — multi-trip dan pemecahan demand

Model B memperluas Model A ke dua arah. Pertama, titik layanan yang demandnya melebihi $Q$ dipecah menjadi beberapa node (§4.1). Kedua, setiap kendaraan boleh menjalani sampai $\rho$ trip dalam sehari, dengan waktu muat $\lambda$ sebelum setiap trip berikutnya (§4.3–4.5). Produksi, release date, dan holding masuk di Model C dan D (§5, §6).

Seperti Model A, formulasi di §4.5 adalah spesifikasi. Validator dan core memeriksa solusi lewat ringkasan trip (§4.3) dan rantai trip (§4.4).

### 4.1 Pemecahan demand

> Sejak MO-1.5, $Q$ di bagian ini dibaca $\bar Q = \min(Q, D^{max})$ (K1, §5.6). Bila $D^{max} \ge Q$, tidak ada yang berubah.

Notasi: $q$ = demand satu titik layanan, $k$ = jumlah potongan, $r$ = ukuran potongan terakhir.

**Jumlah potongan paling sedikit.**

1. Setiap potongan paling besar $Q$, jadi $k$ potongan memuat paling banyak $kQ$ porsi.
2. Semua porsi harus termuat: $kQ \ge q$, yaitu $k \ge q / Q$.
3. $k$ bilangan bulat, dan bilangan bulat terkecil yang $\ge q / Q$ adalah $\lceil q / Q \rceil$.

**Ukuran potongan: aturan "penuh dulu".** Potongan ke-1 sampai ke-$(k-1)$ berukuran $Q$; potongan terakhir adalah sisanya.

$$k = \left\lceil \frac{q}{Q} \right\rceil, \qquad r = q - (k-1)Q$$

**Bukti $1 \le r \le Q$** (sehingga setiap potongan sah menurut §1.7 nomor 6):

1. Arti $k = \lceil q / Q \rceil$ adalah $k - 1 < q / Q \le k$.
2. Kalikan dengan $Q > 0$: $(k-1)Q < q \le kQ$.
3. Kurangi dengan $(k-1)Q$: $0 < r \le Q$.
4. $r$ bilangan bulat dan positif, jadi $r \ge 1$.

**Yang diwarisi potongan** dari titik asalnya $\sigma(j)$: jendela $a_j$, $d_j$, waktu konsumsi $m_{\sigma(j)}$, dan buffer $\delta_{\sigma(j)}$. Antar-potongan $\tau_{jj'} = 0$ dan $c_{jj'} = 0$; jarak dan waktu tempuh ke node lain sama dengan milik titik asalnya, sehingga ketaksamaan segitiga (B6) tetap berlaku. Waktu layan dihitung ulang per potongan, $s_j = \lceil s^0 + \eta q_j \rceil$, karena setiap potongan adalah pemberhentian tersendiri.

**Contoh** dengan $Q = 100$, $s^0 = 5$, $\eta = 0{,}02$:

| $q$ | $k$ | Potongan          | $s_j$      |
| --: | --: | ----------------- | ---------- |
| 250 |   3 | 100, 100, 50      | 7, 7, 6    |
| 330 |   4 | 100, 100, 100, 30 | 7, 7, 7, 6 |

Potongan 30 memberi $5 + 0{,}6 = 5{,}6$, disimpan $6$ (B1).

**Akibat.** Potongan berukuran $Q$ selalu sendirian di tripnya ($0 \to j \to n+1$), karena menambah node apa pun membuat muatan $\ge Q + 1$. Dengan aturan "penuh dulu", setiap titik punya paling banyak satu potongan yang tidak penuh, jadi dua potongan dari titik yang sama tidak pernah serute.

**Ini aproksimasi, bukan split delivery sebenarnya** (A6, v3.1 §8.4). Ukuran potongan dikunci sebelum optimasi, jadi sebagian solusi hilang. Contoh dengan $Q = 100$, titik X berdemand 120, ditambah titik lain (jumlah trip minimum dihitung dengan enumerasi pengepakan):

| Titik lain | $\lceil \sum q / Q \rceil$ | Penuh dulu $(100, 20)$ | Rata $(60, 60)$ | Pemecahan bebas                 |
| ---------- | -------------------------: | ---------------------: | --------------: | ------------------------------- |
| 80         |                          2 |                      2 |               3 | 2                               |
| 40, 40     |                          2 |                      2 |               2 | 2                               |
| 70, 70, 40 |                          3 |                      4 |               4 | 3, lewat tiga potong 30, 30, 60 |

- Baris 1: "rata" kalah karena $60 + 80 > 100$.
- Baris 3: tidak ada pemecahan dua potong yang mencapai 3 trip. Batas bawah $\lceil \sum q / Q \rceil$ tetap sah, tetapi belum tentu tercapai.

Alasan memilih "penuh dulu": deterministik, sisa $r$ sekecil mungkin sehingga paling mudah digabung, dan trip potongan penuh sudah pasti bentuknya.

### 4.2 Notasi tambahan

| Notasi                        | Arti                                                                                 | Satuan |
| ----------------------------- | ------------------------------------------------------------------------------------ | ------ |
| $(k, r)$                      | Trip ke-$r$ milik kendaraan $k$, dengan $r = 1, \dots, \rho$                         | —      |
| $X_{ij}$                      | $\sum_{k,r} x^{kr}_{ij}$: bernilai 1 bila arc $(i,j)$ dipakai trip mana pun          | —      |
| $\Delta_j$                    | Lama dari berangkat sampai mulai layanan di $j$ bila kendaraan tidak pernah menunggu | menit  |
| $\Delta$                      | Durasi satu trip bila kendaraan tidak pernah menunggu                                | menit  |
| $E^{\ast}$                    | Jam pulang trip pada jadwal tercepat (berangkat $e_0$)                               | waktu  |
| $S^{max}$                     | Jam berangkat paling lambat yang masih layak untuk trip itu                          | waktu  |
| $M^S_j,\ M^E_i,\ M^{\lambda}$ | Big-M baris berangkat, pulang, dan urutan trip (§4.7)                                | menit  |

Huruf $\Delta$ dipakai, bukan $D$, karena $D_b$ dan $D^{max}$ sudah berarti ukuran batch di v3.1 §8.1. $T^{\ast}_j$ adalah jadwal tercepat §2.7, dihitung per trip.

Notasi v3.1 yang dipakai di bagian ini: $\rho$, $x^{kr}_{ij}$, $y^{kr}_j$, $w^{kr}$, $S^{kr}$, $E^{kr}$, $\lambda$.

### 4.3 Satu trip sebagai fungsi jam berangkat

Di Model A kendaraan selalu bisa berangkat pada $e_0$. Trip kedua berangkat pada jam $S$ yang bergantung pada trip pertama, jadi diperlukan rumus $T_j$ untuk sembarang $S \ge e_0$.

Untuk trip $0 \to j_1 \to \dots \to j_m \to n+1$:

$$\Delta_{j_1} = \tau_{0 j_1}, \qquad \Delta_{j_{t+1}} = \Delta_{j_t} + s_{j_t} + \tau_{j_t j_{t+1}}, \qquad \Delta = \Delta_{j_m} + s_{j_m} + \tau_{j_m, n+1}$$

$$E^{\ast} = T^{\ast}_{j_m} + s_{j_m} + \tau_{j_m, n+1}$$

Di setiap langkah, waktu layan yang dijumlahkan adalah milik node yang **ditinggalkan** ($s_{j_t}$ pada arc dari $j_t$), termasuk $s_{j_m}$ pada arc pulang.

**Proposisi.** Untuk setiap $S \ge e_0$:

$$T_j(S) = \max \left( S + \Delta_j,\ T^{\ast}_j \right), \qquad E(S) = \max \left( S + \Delta,\ E^{\ast} \right)$$

**Bukti.** Pakai §1.4: $T_{j_1} = \max(S + \tau_{0 j_1},\ a_{j_1})$ dan $T_j = \max(T_i + s_i + \tau_{ij},\ a_j)$.

1. **Node pertama.** Karena $S \ge e_0$, berlaku $S + \tau_{0 j_1} \ge e_0 + \tau_{0 j_1}$. Menambahkan $e_0 + \tau_{0 j_1}$ ke dalam $\max$ tidak mengubah hasilnya, jadi $T_{j_1} = \max(S + \tau_{0 j_1},\ a_{j_1},\ e_0 + \tau_{0 j_1}) = \max(S + \Delta_{j_1},\ a'_{j_1}) = \max(S + \Delta_{j_1},\ T^{\ast}_{j_1})$.
2. **Langkah induksi.** Andaikan $T_i = \max(S + \Delta_i,\ T^{\ast}_i)$, dan tulis $g = s_i + \tau_{ij}$ untuk node berikutnya $j$.
3. **$a_j$ boleh diganti $a'\_j$.** $T_i + g \ge S + \Delta_j \ge e_0 + \Delta_j \ge e_0 + \tau_{0j}$; langkah terakhir dari B6 (jalan memutar tidak lebih singkat) dan $s \ge 0$. Jadi, seperti langkah 1, $T_j = \max(T_i + g,\ a_j) = \max(T_i + g,\ a'_j)$.
4. **Konstanta masuk ke $\max$.** $T_i + g = \max(S + \Delta_i + g,\ T^{\ast}_i + g) = \max(S + \Delta_j,\ T^{\ast}_i + g)$.
5. **Gabung.** $T_j = \max(S + \Delta_j,\ T^{\ast}_i + g,\ a'_j) = \max(S + \Delta_j,\ T^{\ast}_j)$, karena dua suku terakhir adalah definisi $T^{\ast}_j$.
6. **Pulang.** Dapur tidak punya jendela, jadi $E = T_{j_m} + s_{j_m} + \tau_{j_m, n+1}$; tambahkan konstanta itu ke kedua isi $\max$. ∎

Artinya: selama $S$ kecil, $T_j$ tertahan di $T^{\ast}_j$ (kendaraan menunggu); setelah itu setiap menit telat berangkat menjadi satu menit telat di node.

**Akibat.**

- **Model A adalah kasus $S = e_0$.** Dari definisi, $T^{\ast}_j \ge e_0 + \Delta_j$, jadi $T_j(e_0) = T^{\ast}_j$.
- **Monoton.** $T_j(S)$ dan $E(S)$ tidak pernah turun bila $S$ naik.
- **Kelayakan.** $T_j(S) \le d'_j$ berarti kedua isi $\max$ harus $\le d'_j$: (i) $T^{\ast}_j \le d'_j$ di semua node, yang tidak bergantung pada $S$, dan (ii) $S \le d'_j - \Delta_j$ di semua node. Jadi

$$S^{max} = \min_{t = 1, \dots, m} \left( d'_{j_t} - \Delta_{j_t} \right)$$

dan trip layak untuk jam berangkat $S$ jika dan hanya jika $T^{\ast}_j \le d'_j$ di semua node dan $e_0 \le S \le S^{max}$.

- Bila (i) terpenuhi, otomatis $S^{max} \ge e_0$, karena $d'_j \ge T^{\ast}_j \ge e_0 + \Delta_j$. Pulang sebelum $l_0$ juga otomatis, karena sudah termuat dalam $d'_{j_m}$ (§2.3).

Jadi satu trip yang layak cukup diwakili tiga angka $(\Delta,\ E^{\ast},\ S^{max})$.

**Contoh, trip $(4, 2, 1)$ di H5.**

| Node | $\Delta_j$          | $T^{\ast}_j$                      | $d'_j$ | $d'_j - \Delta_j$ |
| ---- | ------------------- | --------------------------------- | -----: | ----------------: |
| 4    | $20$                | $a'_4 = 500$                      |    530 |               510 |
| 2    | $20 + 5 + 40 = 65$  | $\max(500 + 5 + 40,\ 510) = 545$  |    570 |               505 |
| 1    | $65 + 15 + 15 = 95$ | $\max(545 + 15 + 15,\ 560) = 575$ |    610 |               515 |

$\Delta = 95 + 10 + 15 = 120$, $E^{\ast} = 575 + 10 + 15 = 600$, $S^{max} = 505$. Berangkat 480 memberi $E = 600$; berangkat 505 memberi $E = \max(625, 600) = 625$, dengan $T_2 = 570$ tepat di batas.

### 4.4 Rantai trip pada satu kendaraan

$$S^{k1} \ge e_0, \qquad S^{k,r+1} \ge E^{kr} + \lambda$$

Trip pertama tidak dikenai $\lambda$: muatnya dianggap selesai sebelum $e_0$ (diatur Model D lewat release date, §6.1). Dengan begitu Model B dengan $\rho = 1$ persis Model A.

**Berangkat secepat mungkin tidak pernah merugikan.** Menunda trip $r$ tidak pernah memajukan $E^{kr}$ (monoton, §4.3), jadi tidak pernah memajukan $S^{k,r+1}$ yang paling awal, sehingga syarat $S \le S^{max}$ di trip-trip berikutnya hanya bisa makin sulit. Bila suatu jadwal layak, jadwal "secepat mungkin" juga layak.

**Pemeriksaan satu kendaraan**, untuk urutan trip yang sudah ditentukan:

1. $S \leftarrow e_0$.
2. Untuk setiap trip berurutan: gagal bila $S > S^{max}$; hitung $E = \max(S + \Delta,\ E^{\ast})$; lalu $S \leftarrow E + \lambda$.
3. Bila sampai akhir tanpa gagal, kendaraan layak.

**Contoh di H5, $\lambda = 10$.** Trip $(3)$: $\Delta = 60$, $E^{\ast} = 635$, $S^{max} = 645 - 25 = 620$. Trip $(2, 1)$: $\Delta = 85$, $E^{\ast} = 585$, $S^{max} = 540$.

| Urutan           | Trip 1: $S \to E$ | Trip 2: $S$ vs $S^{max}$ | Trip 2: $E$            | Hasil |
| ---------------- | ----------------- | ------------------------ | ---------------------- | ----- |
| $(4,2,1)$, $(3)$ | $480 \to 600$     | $610 \le 620$            | $\max(670, 635) = 670$ | layak |
| $(3)$, $(4,2,1)$ | $480 \to 635$     | $645 > 505$              | —                      | gagal |
| $(2,1)$, $(3)$   | $480 \to 585$     | $595 \le 620$            | $\max(655, 635) = 655$ | layak |

Urutan trip ikut menentukan kelayakan, jadi urutan adalah bagian dari keputusan (MO-11.2). Pada baris ketiga, $\lambda$ terbesar yang masih layak adalah $620 - 585 = 35$.

### 4.5 Formulasi

**Variabel.**

| Variabel          | Tipe    | Arti                                                                   |
| ----------------- | ------- | ---------------------------------------------------------------------- |
| $x^{kr}_{ij}$     | biner   | Trip $(k,r)$ berjalan langsung dari $i$ ke $j$                         |
| $y^{kr}_j$        | biner   | Node $j$ dilayani trip $(k,r)$                                         |
| $w^{kr}$          | biner   | Trip $(k,r)$ dipakai                                                   |
| $S^{kr},\ E^{kr}$ | kontinu | Jam trip berangkat dari dan kembali ke dapur                           |
| $T_j$             | kontinu | Mulai layanan di node $j$ (satu indeks: setiap node dikunjungi sekali) |
| $u_j$             | kontinu | Muatan kumulatif sampai node $j$ di tripnya                            |

**(G0) Objektif:** total jarak semua trip.

$$\min \sum_{k,r} \sum_{(i,j) \in \mathcal{A}} c_{ij}\, x^{kr}_{ij}$$

**(G1) Setiap node dilayani tepat satu trip.**

$$\sum_{k,r} y^{kr}_j = 1 \qquad \forall j \in N$$

**(G2) Arc masuk dan keluar mengikuti $y$.** Trip yang melayani $j$ masuk sekali dan keluar sekali; trip lain tidak menyentuh $j$.

$$x^{kr}_{0j} + \sum_{i \in N,\ i \ne j} x^{kr}_{ij} = y^{kr}_j = \sum_{i \in N,\ i \ne j} x^{kr}_{ji} + x^{kr}_{j,n+1} \qquad \forall j, k, r$$

**(G3) Trip yang dipakai berangkat tepat sekali.** Pulang tepat sekali mengikuti dari G2 dengan hitungan dua cara (§2.6).

$$\sum_{j \in N} x^{kr}_{0j} = w^{kr} \qquad \forall k, r$$

**(G4) Kapasitas per trip.** Trip yang tidak dipakai tidak boleh melayani siapa pun.

$$\sum_{j \in N} q_j\, y^{kr}_j \le Q\, w^{kr} \qquad \forall k, r$$

**(G5) Propagasi muatan.**

$$u_j \ge u_i + q_j - Q (1 - X_{ij}), \qquad q_j \le u_j \le Q \qquad \forall i, j \in N,\ i \ne j$$

**(G6) Propagasi waktu: berangkat, antar-node, pulang.**

$$T_j \ge S^{kr} + \tau_{0j} - M^S_j (1 - x^{kr}_{0j}) \qquad \forall j, k, r$$

$$T_j \ge T_i + s_i + \tau_{ij} - M_{ij} (1 - X_{ij}) \qquad \forall i, j \in N,\ i \ne j$$

$$E^{kr} \ge T_i + s_i + \tau_{i,n+1} - M^E_i (1 - x^{kr}_{i,n+1}) \qquad \forall i, k, r$$

**(G7) Jendela dan jam dapur.**

$$a'_j \le T_j \le d'_j, \qquad e_0 \le S^{kr} \le l_0, \qquad e_0 \le E^{kr} \le l_0$$

**(G8) Urutan trip pada satu kendaraan**, aktif hanya bila trip berikutnya dipakai.

$$S^{k,r+1} \ge E^{kr} + \lambda - M^{\lambda} (1 - w^{k,r+1}) \qquad \forall k,\ r < \rho$$

**(G9) Slot dipakai berurutan; pemecah simetri antar-kendaraan.**

$$w^{k,r+1} \le w^{kr}, \qquad w^{k+1,1} \le w^{k,1}$$

**(G10) Domain.** $x^{kr}_{ij},\ y^{kr}_j,\ w^{kr} \in \lbrace 0, 1 \rbrace$.

Karena $E^{kr} \le l_0$ tertulis eksplisit di G7, jendela $a_j$, $d_j$ biasa sudah cukup untuk kebenaran; $a'_j$, $d'_j$ dipakai karena tersirat oleh G6–G7 dan memperkecil Big-M.

### 4.6 Dua perbaikan terhadap v3.1 §8.6

**Propagasi muatan G5 ditambahkan.** Formulasi v3.1 tidak punya $u_j$, jadi siklus hanya dicegah propagasi waktu. Ambil dua node $j$, $j'$ dengan $\tau_{jj'} = \tau_{j'j} = 0$ dan $s_j = s_{j'} = 0$ (dua titik di lokasi yang sama, atau potongan selokasi dari aturan pemecahan lain), lalu siklus $j \to j' \to j$ di samping rute yang sah pada trip yang sama. G1–G4 terpenuhi, dan jumlah baris waktu di siklus memberi $0 \ge s_j + s_{j'} = 0$, yang lolos: dua node "terlayani" tanpa pernah dikunjungi. Jumlah baris G5 memberi $0 \ge q_j + q_{j'} \ge 2$, mustahil tanpa syarat. Ini sejalan dengan C3.

**Urutan trip G8 dibuat bersyarat.** Tanpa suku Big-M, kendaraan yang pulang pada $l_0$ memaksa slot kosong berikutnya "berangkat" pada $l_0 + \lambda > l_0$, melanggar G7, sehingga solusi yang sah tertolak.

### 4.7 Big-M

Semua baris memakai resep §2.5: saat arc atau trip tidak dipakai, $M$ harus $\ge$ ruas kanan terbesar yang diizinkan batas G5 dan G7.

| Baris          | Saat tidak aktif, $M \ge$           | Terbesar saat                     | $M$                                                              |
| -------------- | ----------------------------------- | --------------------------------- | ---------------------------------------------------------------- |
| G5 muatan      | $u_i + q_j - u_j$                   | $u_i = Q$, $u_j = q_j$            | $Q$                                                              |
| G6 berangkat   | $S^{kr} + \tau_{0j} - T_j$          | $S^{kr} = l_0$, $T_j = a'_j$      | $M^S_j = l_0 + \tau_{0j} - a'_j$                                 |
| G6 antar-node  | $T_i + s_i + \tau_{ij} - T_j$       | $T_i = d'_i$, $T_j = a'_j$        | $M_{ij} = \max\lbrace 0,\ d'_i + s_i + \tau_{ij} - a'_j \rbrace$ |
| G6 pulang      | $T_i + s_i + \tau_{i,n+1} - E^{kr}$ | $T_i = d'_i$, $E^{kr} = e_0$      | $M^E_i = d'_i + s_i + \tau_{i,n+1} - e_0$                        |
| G8 urutan trip | $E^{kr} + \lambda - S^{k,r+1}$      | $E^{kr} = l_0$, $S^{k,r+1} = e_0$ | $M^{\lambda} = l_0 - e_0 + \lambda$                              |

Menurut definisi $d'_i$, berlaku $d'_i + s_i + \tau_{i,n+1} \le l_0$, jadi $M^E_i \le l_0 - e_0$.

### 4.8 Hubungan dengan Model A dan batas bawah

- **$\rho = 1$ sama dengan Model A.** G8 dan bagian pertama G9 hilang, dan $X_{ij}$ berperan sebagai $x_{ij}$. Pada H5 dengan $\rho = 1$, enumerasi Model B memberi 9 solusi layak dengan optimum 32, sama dengan §3.5.
- **Menambah $\rho$ tidak pernah memperburuk optimum**, karena setiap solusi dengan $\rho$ trip juga solusi dengan $\rho + 1$ trip. Pada H5 dengan $\rho = 2$ dan $\lambda = 10$, solusi layak naik menjadi 32 tetapi optimum tetap 32.
- **Batas bawah kini dalam satuan trip.** Instans tidak layak bila $\lceil \sum_j q_j / Q \rceil > \lvert K \rvert \cdot \rho$. Kelompok node yang saling tak serute (E3) kini membatasi jumlah **trip**, bukan jumlah kendaraan.

### 4.9 Pemeriksaan solusi Model B

Dipakai validator MO-3.2 dan evaluator core:

1. **Struktur:** setiap node tepat di satu trip; kendaraan terpakai $\le \lvert K \rvert$; trip per kendaraan $\le \rho$.
2. **Per trip:** muatan $\le Q$; hitung $\Delta_j$ dan $T^{\ast}_j$; gagal bila ada $T^{\ast}_j > d'_j$; simpan $(\Delta,\ E^{\ast},\ S^{max})$.
3. **Per kendaraan:** rantai §4.4. Kegagalan $S > S^{max}$ di trip $r \ge 2$ adalah pelanggaran jendela waktu yang **disebabkan trip sebelumnya**; trip itu sendiri layak bila berangkat pada $e_0$.

### 4.10 Contoh: instans H5-S

H5 dengan demand titik 2 dinaikkan dari 40 menjadi **120**. Aturan "penuh dulu" memecahnya menjadi node 2 ($q = 100$) dan node 6 ($q = 20$), selokasi. Data lain tetap: $\lvert K \rvert = 2$, $\rho = 2$, $\lambda = 10$, $Q = 100$, $[e_0, l_0] = [480, 680]$, $\tau_{ij} = 5 c_{ij}$.

| $c_{ij}$ |   0 |   1 |   2 |   3 |   4 |   5 |   6 |
| -------- | --: | --: | --: | --: | --: | --: | --: |
| **0**    |   – |   3 |   6 |   5 |   4 |   4 |   6 |
| **1**    |   3 |   – |   3 |   6 |   5 |   5 |   3 |
| **2**    |   6 |   3 |   – |   5 |   8 |   8 |   0 |
| **3**    |   5 |   6 |   5 |   – |   5 |   9 |   5 |
| **4**    |   4 |   5 |   8 |   5 |   – |   8 |   8 |
| **5**    |   4 |   5 |   8 |   9 |   8 |   – |   8 |
| **6**    |   6 |   3 |   0 |   5 |   8 |   8 |   – |

| Node | $q_j$ | $s_j$ | $a_j$ | $d_j$ | $e_0 + \tau_{0j}$ | $l_0 - s_j - \tau_{j0}$ | $a'_j$ | $d'_j$ |
| ---- | ----: | ----: | ----: | ----: | ----------------: | ----------------------: | -----: | -----: |
| 1    |    25 |    10 |   560 |   610 |               495 |                     655 |    560 |    610 |
| 2    |   100 |    15 |   510 |   570 |               510 |                     635 |    510 |    570 |
| 3    |    20 |    10 |   600 |   650 |               505 |                     645 |    600 |    645 |
| 4    |    35 |     5 |   480 |   530 |               500 |                     655 |    500 |    530 |
| 5    |    15 |    10 |   580 |   610 |               500 |                     650 |    580 |    610 |
| 6    |    20 |    10 |   510 |   570 |               510 |                     640 |    510 |    570 |

- H5 tidak memakai rumus $s^0 + \eta q_j$, jadi $s_2 = 15$ dan $s_6 = 10$ bersifat ilustratif.
- Total demand 215, jadi paling sedikit $\lceil 2{,}15 \rceil = 3$ trip, dari $\lvert K \rvert \cdot \rho = 4$ slot. Dengan $\rho = 1$ instans ini tidak layak (3 trip $> 2$).

**Uji arc.** Isi sel adalah $a'_i + s_i + \tau_{ij}$. **W** = mustahil karena waktu ($> d'_j$), **Q** = mustahil karena kapasitas ($q_i + q_j > 100$).

| Pangkal $i$ ($a'_i + s_i$) |     $j=1$ |        $j=2$ |     $j=3$ |        $j=4$ |     $j=5$ |     $j=6$ |
| -------------------------- | --------: | -----------: | --------: | -----------: | --------: | --------: |
| $d'_j$                     |       610 |          570 |       645 |          530 |       610 |       570 |
| 1 ($560 + 10$)             |         – | 585 **W, Q** |       600 |    595 **W** |       595 | 585 **W** |
| 2 ($510 + 15$)             | 540 **Q** |            – | 550 **Q** | 565 **W, Q** | 565 **Q** | 525 **Q** |
| 3 ($600 + 10$)             | 640 **W** | 635 **W, Q** |         – |    635 **W** | 655 **W** | 635 **W** |
| 4 ($500 + 5$)              |       530 |    545 **Q** |       530 |            – |       545 |       545 |
| 5 ($580 + 10$)             | 615 **W** | 630 **W, Q** |       635 |    630 **W** |         – | 630 **W** |
| 6 ($510 + 10$)             |       535 |    520 **Q** |       545 |    560 **W** |       560 |         – |

Dua puluh dari tiga puluh arc mustahil. Node 2 selalu sendirian (trip $(2)$), termasuk terhadap potongan selokasinya: arc $(2,6)$ dan $(6,2)$ mustahil walau $\tau = 0$. Node 4 selalu pertama, node 3 selalu terakhir, dan node 6 adalah node pertama atau tepat setelah node 4.

**Ringkasan trip yang dipakai di bawah.**

| Trip           | $\Delta$ | $E^{\ast}$ | $S^{max}$ | Biaya |
| -------------- | -------: | ---------: | --------: | ----: |
| $(2)$          |       75 |        555 |       540 |    12 |
| $(3)$          |       60 |        635 |       620 |    10 |
| $(5, 3)$       |      110 |        670 |       570 |    18 |
| $(6, 1)$       |       80 |        585 |       540 |    12 |
| $(4, 6, 1)$    |      115 |        595 |       505 |    18 |
| $(4, 6, 1, 5)$ |      155 |        635 |       485 |    24 |

Rincian trip $(4, 6, 1, 5)$, muatan $35 + 20 + 25 + 15 = 95$:

| Node | $\Delta_j$           | $T^{\ast}_j$                      | $d'_j$ | $d'_j - \Delta_j$ |
| ---- | -------------------- | --------------------------------- | -----: | ----------------: |
| 4    | $20$                 | $500$                             |    530 |               510 |
| 6    | $20 + 5 + 40 = 65$   | $\max(500 + 5 + 40,\ 510) = 545$  |    570 |               505 |
| 1    | $65 + 10 + 15 = 90$  | $\max(545 + 10 + 15,\ 560) = 570$ |    610 |               520 |
| 5    | $90 + 10 + 25 = 125$ | $\max(570 + 10 + 25,\ 580) = 605$ |    610 |               485 |

$\Delta = 125 + 10 + 20 = 155$, $E^{\ast} = 605 + 10 + 20 = 635$, $S^{max} = 485$.

**Solusi M1 (optimum, biaya 46).**

| Kendaraan | Trip           | $S$              | $S^{max}$ | $E$                    |
| --------- | -------------- | ---------------- | --------: | ---------------------- |
| 1         | $(2)$          | 480              |       540 | $\max(555, 555) = 555$ |
| 1         | $(3)$          | $555 + 10 = 565$ |       620 | $\max(625, 635) = 635$ |
| 2         | $(4, 6, 1, 5)$ | 480              |       485 | $\max(635, 635) = 635$ |

Biaya $12 + 10 + 24 = 46$.

**Solusi M2 (biaya 48).**

| Kendaraan | Trip        | $S$              | $S^{max}$ | $E$                    |
| --------- | ----------- | ---------------- | --------: | ---------------------- |
| 1         | $(2)$       | 480              |       540 | 555                    |
| 1         | $(5, 3)$    | $555 + 10 = 565$ |       570 | $\max(675, 670) = 675$ |
| 2         | $(4, 6, 1)$ | 480              |       505 | $\max(595, 595) = 595$ |

Biaya $12 + 18 + 18 = 48$. Trip kedua kendaraan 1 hanya punya kelonggaran 5 menit, jadi M2 tetap layak sampai $\lambda = 15$ ($S = 570$, pulang tepat $l_0 = 680$) dan gagal pada $\lambda = 16$.

**Hasil enumerasi** (semua pembagian, urutan dalam trip, penugasan dan urutan trip ke kendaraan):

| $\lvert K \rvert$ | $\rho$ | $\lambda$ | Solusi layak | Optimum                       |
| ----------------: | -----: | --------: | -----------: | ----------------------------- |
|                 2 |      1 |         — |            0 | tidak layak (perlu 3 trip)    |
|                 2 |      2 |        10 |            8 | 46 (M1 dan satu solusi lain)  |
|                 2 |      2 |        20 |            4 | 46                            |
|                 2 |      3 |        10 |           11 | 46                            |
|                 3 |      1 |         — |           11 | 44: $(2)$, $(4,3)$, $(6,1,5)$ |
|                 1 |  bebas |     bebas |            0 | tidak layak                   |

Solusi optimum kedua adalah $(2)$ lalu $(5)$ pada kendaraan 1 dan $(4, 6, 1, 3)$ pada kendaraan 2. Multi-trip menghemat satu kendaraan dengan tambahan jarak 2 (46 dibanding 44).

**V5, satu kendaraan tidak cukup berapa pun $\rho$ dan $\lambda \ge 0$.**

1. Trip yang memuat node 4 punya $S^{max} \le d'_4 - \Delta_4 = 530 - 20 = 510$. Setiap trip lain pulang paling cepat pada $E^{\ast} \ge 550$ (trip $(6)$; trip lain lebih lambat). Jadi trip node 4 harus yang **pertama**.
2. Trip $(2)$ punya $S^{max} = 540$, jadi ia trip kedua dan trip pertama harus pulang $\le 540 - \lambda \le 540$. Hanya trip $(4)$ yang memenuhi ($E^{\ast} = 505$, $\Delta = 45$).
3. Trip $(2)$ berangkat $505 + \lambda$ dan pulang pada $\max(580 + \lambda,\ 555) \ge 580$.
4. Node 6 kini baru bisa dilayani pada $\ge 580 + \tau_{06} = 610 > d'_6 = 570$. Tidak layak. ∎

Pola yang sama dengan V4: node 2, 4, dan 6 sama-sama berdeadline awal, dan trip yang melayaninya terlalu panjang untuk dirantai satu kendaraan.

### 4.11 Keputusan MO-1.4

| #   | Keputusan                                                                                                                                                                                          |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| J1  | Pemecahan demand "penuh dulu": $k = \lceil q/Q \rceil$, $k-1$ potongan berukuran $Q$ dan sisa $r = q - (k-1)Q$; potongan mewarisi jendela, $m$, $\delta$; $s_j$ dihitung ulang per potongan (§4.1) |
| J2  | Trip pertama tidak dikenai $\lambda$; $\lambda$ hanya di antara dua trip berurutan. Model B dengan $\rho = 1$ sama dengan Model A (§4.4, §4.8)                                                     |
| J3  | Formulasi G0–G10: v3.1 §8.6 ditambah propagasi muatan G5 (eliminasi subtour tetap bersandar pada kapasitas, C3) dan urutan trip bersyarat G8 (§4.5, §4.6)                                          |
| J4  | Big-M per baris dengan nilai terkecil yang sah: $Q$, $M^S_j$, $M_{ij}$, $M^E_i$, $M^{\lambda}$ (§4.7)                                                                                              |
| J5  | Satu trip diringkas $(\Delta, E^{\ast}, S^{max})$ dengan $T_j(S) = \max(S + \Delta_j, T^{\ast}_j)$; kendaraan diperiksa dengan rantai berangkat secepat mungkin (§4.3, §4.4, §4.9)                 |
| J6  | Batas bawah dalam satuan trip: $\lceil \sum q/Q \rceil \le \lvert K \rvert \rho$; kelompok saling tak serute membatasi jumlah trip (§4.8)                                                          |
| J7  | H5-S, ringkasan trip, M1, M2, tabel enumerasi, dan V5 menjadi fixture MO-2.3 (§4.10)                                                                                                               |
| J8  | Notasi $\Delta_j$, $\Delta$ untuk durasi tanpa menunggu (bukan $D$, yang berarti ukuran batch di v3.1)                                                                                             |

Yang belum dicakup Model B: urutan trip terbaik per kendaraan sebagai masalah optimasi (MO-11.2), serta produksi batch, release date, dan holding (Model C dan D, §5 dan §6).

Pertanyaan terbuka untuk MO-3.2: apakah kegagalan $S > S^{max}$ di trip $r \ge 2$ dilaporkan sebagai jenis pelanggaran tersendiri ("terlambat karena trip sebelumnya") atau sebagai pelanggaran jendela waktu biasa di node yang gagal.

## 5. Model C — produksi batch

Model C menambahkan dapur: makanan dimasak dalam beberapa **batch** di satu lini masak, lalu dipacking di satu lini packing (A5). Model ini belum terhubung ke trip; penghubungnya ada di Model D (§6).

```text
lini masak:    γ_b ──── masak θᶜ(D_b) ────> f_b
lini packing:                        f_b ··tunggu··> π_b ── packing θᵖ(D_b) ──> p_b
```

### 5.1 Notasi tambahan

| Notasi                    | Arti                                                                      | Satuan |
| ------------------------- | ------------------------------------------------------------------------- | ------ |
| $\theta^c(D)$             | Durasi masak batch berukuran $D$: $\lceil \phi^c_0 + \phi^c_1 D \rceil$   | menit  |
| $\theta^p(D)$             | Durasi packing batch berukuran $D$: $\lceil \phi^p_0 + \phi^p_1 D \rceil$ | menit  |
| $\theta^c_b,\ \theta^p_b$ | Singkatan $\theta^c(D_b)$, $\theta^p(D_b)$                                | menit  |
| $\lvert B \rvert$         | Jumlah slot batch per hari (parameter, seperti $\rho$ untuk trip)         | —      |
| $b(j)$                    | Batch tempat node $j$ dimasak                                             | —      |
| $\bar Q$                  | Batas ukuran node setelah pemecahan demand: $\min(Q, D^{max})$ (§5.6)     | porsi  |

Untuk batch kosong, $\theta^c(0) = \theta^p(0) = 0$. Huruf $\theta$ dipilih karena belum dipakai di v3.1.

Notasi v3.1 yang dipakai di bagian ini: $B$, $v_{jb}$, $o_b$, $D_b$, $D^{max}$, $\gamma_b$, $f_b$, $\pi_b$, $p_b$, $e_{dapur}$, $\phi^c_0$, $\phi^c_1$, $\phi^p_0$, $\phi^p_1$.

### 5.2 Formulasi

**(P1) Setiap node dimasak di tepat satu batch.** Porsi satu node tidak dipecah ke dua batch.

$$\sum_{b \in B} v_{jb} = 1 \qquad \forall j \in N$$

**(P2) Ukuran batch** adalah jumlah demand node yang masuk ke batch itu.

$$D_b = \sum_{j \in N} q_j\, v_{jb} \qquad \forall b$$

**(P3) Kapasitas batch.** Batch yang tidak dipakai harus kosong.

$$D_b \le D^{max}\, o_b \qquad \forall b$$

**(P4) Durasi masak.**

$$f_b \ge \gamma_b + \phi^c_0\, o_b + \phi^c_1\, D_b \qquad \forall b$$

**(P5) Durasi packing.**

$$p_b \ge \pi_b + \phi^p_0\, o_b + \phi^p_1\, D_b \qquad \forall b$$

**(P6) Packing baru bisa mulai setelah seluruh batch matang** (B4).

$$\pi_b \ge f_b \qquad \forall b$$

**(P7) Setiap lini mengerjakan satu batch pada satu waktu, sesuai urutan indeks.**

$$\gamma_{b+1} \ge f_b, \qquad \pi_{b+1} \ge p_b \qquad \forall b < \lvert B \rvert$$

**(P8) Jam buka dapur dan batch dipakai berurutan.**

$$\gamma_1 \ge e_{dapur}, \qquad o_{b+1} \le o_b$$

Domain: $v_{jb},\ o_b \in \lbrace 0, 1 \rbrace$; semua jam bilangan bulat (B1).

### 5.3 Durasi bulat: "≥" menggantikan "="

v3.1 §8.7 menulis $f_b = \gamma_b + \phi^c_0 o_b + \phi^c_1 D_b$. Bentuk ini bertabrakan dengan B1: $\phi^c_0 = 30$, $\phi^c_1 = 0{,}02$, $D_b = 135$ memberi durasi $32{,}7$, sehingga $f_b$ menjadi pecahan. P4 dan P5 karena itu memakai "≥" (K2).

1. **"≥" ditambah syarat bulat menghasilkan pembulatan ke atas.** Bila $\gamma_b$ bulat, maka $\lceil \gamma_b + x \rceil = \gamma_b + \lceil x \rceil$. Bilangan bulat terkecil yang memenuhi P4 adalah $f_b = \gamma_b + \theta^c_b$. Contoh: $\gamma_b = 400$ memberi $f_b \ge 432{,}7$, jadi $f_b = 433$.
2. **Kelonggaran "≥" tidak menambah solusi.** Misalkan suatu solusi memakai $f_b > \gamma_b + \theta^c_b$. Geser mulainya ke $\gamma'_b = f_b - \theta^c_b$. Dari P4, $\gamma'_b \ge \gamma_b \ge f_{b-1}$, jadi P7 tetap terpenuhi; jam selesai $f_b$ sama, dan lini masak terpakai lebih singkat. "Memasak lebih lama" setara dengan "mulai memasak lebih telat". Contoh: $f_b = 440$ dengan $\gamma_b = 400$ setara dengan $\gamma'_b = 440 - 33 = 407$. Argumen yang sama berlaku untuk P5.

Ini pola yang sama dengan §2.7: "≥" boleh dipakai selama kelonggarannya tidak mengubah himpunan solusi yang layak.

### 5.4 Yang tersirat dari formulasi

**Node tidak bisa masuk batch yang tidak dipakai.** Baris $v_{jb} \le o_b$ tidak perlu ditulis. Andaikan $o_b = 0$ tetapi $v_{jb} = 1$ untuk suatu $j$:

1. Dari P2, semua suku tidak negatif, jadi $D_b \ge q_j v_{jb} = q_j \ge 1$ (C1).
2. Dari P3 dengan $o_b = 0$: $D_b \le 0$.
3. Langkah 1 dan 2 memberi $1 \le D_b \le 0$, mustahil. ∎

Lagi-lagi $q_j \ge 1$ yang menutup celahnya, seperti eliminasi subtour di §2.6.

**Urutan indeks.** A5 menetapkan bahwa kedua lini memproses batch dalam urutan yang sama, yaitu urutan indeks. Karena isi batch adalah keputusan ($v_{jb}$), urutan masak tetap bebas dipilih lewat cara menomori batch.

### 5.5 Jadwal tercepat

Bila isi dan urutan batch sudah ditentukan, jadwal paling cepat dihitung dengan satu lintasan maju:

1. $\gamma_1 = e_{dapur}$, lalu $\gamma_{b+1} = f_b$.
2. $f_b = \gamma_b + \theta^c_b$.
3. $\pi_b = \max(f_b,\ p_{b-1})$: packing menunggu batchnya matang **dan** lini packing kosong. Untuk batch pertama, $\pi_1 = f_1$.
4. $p_b = \pi_b + \theta^p_b$.

**Contoh.** Demand H5, $q = (25, 40, 20, 35, 15)$, total 135. Data produksi ilustratif: $e_{dapur} = 300$, $D^{max} = 100$, $\phi^c_0 = 30$, $\phi^c_1 = 0{,}2$, $\phi^p_0 = 10$, $\phi^p_1 = 0{,}1$. Dibutuhkan paling sedikit $\lceil 135/100 \rceil = 2$ batch.

| Urutan | Batch | Node    | $D_b$ | $\theta^c$ | $\theta^p$ | $\gamma_b$ | $f_b$ | $\pi_b$                | $p_b$ |
| ------ | ----- | ------- | ----: | ---------: | ---------: | ---------: | ----: | ---------------------- | ----: |
| I      | 1     | 2, 4    |    75 |         45 |         18 |        300 |   345 | 345                    |   363 |
| I      | 2     | 1, 3, 5 |    60 |         42 |         16 |        345 |   387 | $\max(387, 363) = 387$ |   403 |
| II     | 1     | 1, 3, 5 |    60 |         42 |         16 |        300 |   342 | 342                    |   358 |
| II     | 2     | 2, 4    |    75 |         45 |         18 |        342 |   387 | $\max(387, 358) = 387$ |   405 |

- **$f$ batch terakhir tidak bergantung pada urutan.** Lini masak tidak pernah menunggu, jadi $f_{\text{akhir}} = e_{dapur} + \sum_b \theta^c_b = 300 + 87 = 387$.
- **$p$ batch terakhir bergantung pada urutan.** Packing batch terakhir menunggu masak, jadi $p_{\text{akhir}} = 387 + \theta^p(\text{batch terakhir})$: 403 di urutan I, 405 di urutan II. Penjadwalan dua mesin ini (_flow shop_) dibahas di MO-12.
- Lini packing menganggur 363–387 (urutan I) dan 358–387 (urutan II).

**Jadwal tercepat bukan jadwal terbaik untuk dapur.** Di rute, berangkat secepat mungkin tidak pernah merugikan (§4.4). Di dapur kebalikannya: holding mendorong masak **selambat mungkin**, selama makanan masih siap sebelum trip berangkat (§7.7).

### 5.6 Pemecahan demand dan ukuran batch (K1)

P1 melarang porsi satu node dipecah ke dua batch, sehingga node dengan $q_j > D^{max}$ tidak muat di batch mana pun. Contoh: $Q = 100$, $D^{max} = 80$, dan potongan penuh $q_j = 100$ dari aturan §4.1.

Kasus seperti ini adalah **input tidak valid**, sama seperti $q_j > Q$ di §3.8: soalnya sendiri salah karena pemecahan demand belum cocok dengan batasan dapur. Pilihan yang diambil:

| Opsi            | Aturan                                                                                                  | Catatan                                                                    |
| --------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| A               | §1.7: $Q \le D^{max}$                                                                                   | Paling sederhana, tetapi menolak dapur dengan batch lebih kecil dari mobil |
| **B (dipilih)** | Pemecahan "penuh dulu" memakai $\bar Q = \min(Q, D^{max})$; §1.7 nomor 6 menjadi $1 \le q_j \le \bar Q$ | Umum; bila $D^{max} \ge Q$ hasilnya sama persis dengan J1                  |

Bukti $1 \le r \le Q$ di §4.1 tetap berlaku dengan $Q$ diganti $\bar Q$. Dengan opsi B, setiap node muat di batch mana pun dan di trip mana pun.

## 6. Model D — model terintegrasi

Model D = Model B (G1–G10) + Model C (P1–P8) + baris penghubung I1–I4, dengan objektif di §6.4. Inilah model akhir MVP (v3.1 §8.8).

### 6.1 Release date (I1)

Trip tidak boleh berangkat sebelum semua makanan yang dibawanya selesai dipacking dan dimuat:

$$\text{(I1)} \qquad S^{kr} \ge p_b + \lambda - M^R \left( 2 - v_{jb} - y^{kr}_j \right) \qquad \forall j, b, k, r$$

**Mengapa "$2 - v - y$".** Baris ini harus aktif hanya bila node $j$ dimasak di batch $b$ **dan** dibawa trip $(k,r)$.

| $v_{jb}$ | $y^{kr}_j$ | $2 - v - y$ | Baris                             |
| -------: | ---------: | ----------: | --------------------------------- |
|        1 |          1 |           0 | aktif: $S^{kr} \ge p_b + \lambda$ |
|        1 |          0 |           1 | diredam $M^R$                     |
|        0 |          1 |           1 | diredam $M^R$                     |
|        0 |          0 |           2 | diredam $2M^R$                    |

Bentuk yang paling langsung, $M(1 - v_{jb}\, y^{kr}_j)$, memuat perkalian dua variabel sehingga tidak linear. $2 - v - y$ bernilai $0$ tepat saat keduanya $1$, dan $\ge 1$ di semua kasus lain.

**Satu trip boleh membawa porsi dari beberapa batch** (K3). I1 berlaku untuk setiap node di trip, jadi trip menunggu batch yang paling akhir:

$$S^{kr} \ge \max_{b \text{ di trip } (k,r)} p_b + \lambda$$

**Hanya satu $\lambda$ per trip.** Digabung dengan G8:

$$S^{k,r+1} \ge \max \left( E^{kr},\ \max_b p_b \right) + \lambda, \qquad S^{k1} \ge \max \left( e_0,\ \max_b p_b + \lambda \right)$$

Muat dimulai saat mobil sudah kembali **dan** makanan sudah siap, lalu berlangsung $\lambda$ menit. Ini menuntaskan J2: $\lambda$ trip pertama masuk lewat I1.

### 6.2 Batas atas packing dan Big-M (I2)

$$\text{(I2)} \qquad p_b \le l_0 - \lambda \qquad \forall b$$

I2 tidak membuang solusi layak:

- **Batch yang dipakai** dibawa minimal satu trip yang berangkat $S \le l_0$ (G7), jadi dari I1 $p_b \le S - \lambda \le l_0 - \lambda$.
- **Batch yang tidak dipakai** ada di urutan akhir (P8) dan berdurasi nol; semua jamnya bisa disamakan dengan batch sebelumnya.

Saat I1 diredam, $M^R \ge p_b + \lambda - S^{kr}$. Ruas kanan terbesar saat $p_b = l_0 - \lambda$ dan $S^{kr} = e_0$:

$$M^R = l_0 - e_0$$

**Contoh** (H5, §6.6): $M^R = 680 - 480 = 200$. Baris $j = 2$, $b = 2$, trip B diredam dua kali ($v_{22} = 0$, node 2 tidak di trip B): ruas kanan $403 + 10 - 400 = 13$, jauh di bawah $e_0$.

### 6.3 Holding (I3, I4)

Holding node $j$ adalah $m_{\sigma(j)} - f_{b(j)}$, dan $b(j)$ adalah keputusan. Ditulis langsung, $h_j = \sum_b v_{jb} (m_{\sigma(j)} - f_b)$ memuat perkalian $v_{jb} f_b$. Triknya: satu baris per batch, dan hanya baris batch yang dipilih yang aktif.

$$\text{(I3)} \qquad h_j \ge m_{\sigma(j)} - f_b - M^h_j (1 - v_{jb}) \qquad \forall j, b$$

$$\text{(I4)} \qquad 0 \le h_j \le H^{max} \qquad \forall j$$

**Big-M.** Saat diredam, I3 tidak boleh lebih ketat dari $h_j \ge 0$, jadi $M^h_j \ge m_{\sigma(j)} - f_b$. Terbesar saat $f_b$ terkecil, dan $f_b \ge \gamma_1 \ge e_{dapur}$ (P4, P7, P8):

$$M^h_j = m_{\sigma(j)} - e_{dapur}$$

**Arti I3 + I4.** Baris aktif digabung dengan batas atas memberi $f_b \ge m_{\sigma(j)} - H^{max}$ untuk setiap node di batch $b$. Bila ada beberapa node, yang berlaku adalah yang terbesar:

$$f_b \ge \max_{j : b(j) = b} m_{\sigma(j)} - H^{max}$$

**"≥" di I3 aman karena objektif.** $h_j$ boleh lebih besar dari holding sebenarnya, tetapi holding diminimalkan (§6.4), sehingga di optimum $h_j = m_{\sigma(j)} - f_{b(j)}$ tepat. Validator tidak bergantung pada argumen ini: ia menghitung $h_j$ langsung.

### 6.4 Objektif leksikografis

v3.1 §8.8 punya tiga tingkat: keterlambatan, jarak, holding. Jendela waktu kita keras (B3), jadi keterlambatan selalu $0$ dan tingkat pertama gugur (K4):

$$\min \ \Big( \sum_{k,r} \sum_{(i,j)} c_{ij}\, x^{kr}_{ij},\ \ \sum_{j} q_j h_j \Big) \quad \text{secara leksikografis}$$

Leksikografis berarti dibandingkan seperti urutan kamus: komponen kedua hanya dilihat bila komponen pertama seri.

$$(46,\ 9000) \ <\ (46,\ 9500) \ <\ (48,\ 100)$$

Holding tertimbang porsi ($q_j h_j$, satuan porsi·menit) karena node 100 porsi yang menunggu 60 menit lebih berat daripada node 10 porsi yang menunggu 60 menit. Holding di sini pemecah seri; batas kerasnya tetap I4.

### 6.5 Ringkasan formulasi

| Kelompok   | Baris  | Isi                                                                       |
| ---------- | ------ | ------------------------------------------------------------------------- |
| Objektif   | §6.4   | (jarak, $\sum q_j h_j$) leksikografis                                     |
| Rute       | G1–G10 | Model B (§4.5)                                                            |
| Dapur      | P1–P8  | Model C (§5.2)                                                            |
| Penghubung | I1, I2 | Release date dan batas atas packing; $M^R = l_0 - e_0$                    |
| Holding    | I3, I4 | $h_j \ge m_{\sigma(j)} - f_b$ untuk batch yang dipilih; $h_j \le H^{max}$ |

### 6.6 Contoh: jadwal tercepat dengan rute S1

Data H5 ditambah $\delta_j = 20$ (jadi $m = (630, 590, 670, 550, 630)$; B5 terpenuhi karena $s_j \le 15$), $\lambda = 10$, $H^{max} = 120$, data produksi §5.5. Rute S1 (§3.5): trip A $= (2, 1, 5)$ dan trip B $= (4, 3)$, masing-masing di kendaraan sendiri. Batch 1 $= \lbrace 2, 4 \rbrace$, batch 2 $= \lbrace 1, 3, 5 \rbrace$, jadwal tercepat urutan I.

- **Release.** Kedua trip membawa porsi dari kedua batch: release $= \max(363, 403) + 10 = 413 \le e_0$, jadi keduanya berangkat 480.
- **Holding.**

| Node | Batch | $f_b$ | $h_j = m_j - f_b$ | $q_j h_j$ |
| ---- | ----: | ----: | ----------------: | --------: |
| 1    |     2 |   387 |               243 |      6075 |
| 2    |     1 |   345 |               245 |      9800 |
| 3    |     2 |   387 |               283 |      5660 |
| 4    |     1 |   345 |               205 |      7175 |
| 5    |     2 |   387 |               243 |      3645 |
|      |       |       |         **Total** | **32355** |

Kelima node melanggar $H^{max} = 120$. Dari I3 + I4, batch 1 harus matang $f_1 \ge \max(590, 550) - 120 = 470$ dan batch 2 $f_2 \ge \max(630, 670, 630) - 120 = 550$. §7.1 menunjukkan bahwa rencana ini tidak bisa diperbaiki dengan menggeser jadwal masak.

## 7. Lower bound holding dan jadwal paling lambat

### 7.1 Motivasi

Lanjutan §6.6. Ringkasan trip S1:

| Trip | Node | $\Delta_j$          | $d'_j - \Delta_j$ |
| ---- | ---- | ------------------- | ----------------: |
| A    | 2    | $30$                |               540 |
| A    | 1    | $30 + 15 + 15 = 60$ |               550 |
| A    | 5    | $60 + 10 + 25 = 95$ |               515 |
| B    | 4    | $20$                |               510 |
| B    | 3    | $20 + 5 + 25 = 50$  |               595 |

Jadi $S^{max}_A = 515$ dan $S^{max}_B = 510$. Batch 2 punya node di kedua trip, sehingga batas atasnya dirangkai mundur dari trip yang lebih awal:

1. $S_B \le 510$.
2. Release (I1): $p_2 \le S_B - \lambda \le 500$.
3. Packing (P5, P6): $f_2 \le p_2 - \theta^p(60) \le 484$.

Padahal $f_2 \ge 550$. Rencana ini tidak layak berapa pun jadwal masaknya. Lebih kuat lagi: **rute S1 tidak layak untuk Model D pada $H^{max} = 120$ berapa pun pembagian batchnya.** Node 3 ada di trip B, sehingga batch berisi node 3 harus matang $\le 510 - 10 - \theta^p(20) = 488$, padahal I3 + I4 menuntut $\ge 670 - 120 = 550$. Optimum Model A tidak harus layak di Model D.

Bagian ini menurunkan uji yang mendeteksi masalah seperti ini **sebelum** rute dan batch dipilih (§7.2–§7.6), lalu cara menghitung holding minimum persis setelah semuanya dipilih (§7.7).

### 7.2 Holding minimum satu node, $\ell_j$

Ambil node $j$ di batch $b$, dibawa trip yang berangkat pada $S$. Fakta dari model:

| Langkah | Fakta                                             | Dari                                                     |
| ------- | ------------------------------------------------- | -------------------------------------------------------- |
| 1       | $h_j = m_{\sigma(j)} - f_b$                       | B4                                                       |
| 2       | $T_j \le d'_j$                                    | G7                                                       |
| 3       | $T_j \ge S + \tau_{0j}$                           | B6; menunggu dan layan $\ge 0$                           |
| 4       | $S \ge p_b + \lambda$                             | I1                                                       |
| 5       | $p_b \ge \pi_b + \theta^p_b \ge f_b + \theta^p_b$ | P5, P6                                                   |
| 6       | $\theta^p_b \ge \theta^p(q_j)$                    | $D_b \ge q_j$ (P2); $\theta^p$ tidak turun bila $D$ naik |

Rangkai langkah 2–6:

$$d'_j \ \ge\ T_j \ \ge\ S + \tau_{0j} \ \ge\ p_b + \lambda + \tau_{0j} \ \ge\ f_b + \theta^p(q_j) + \lambda + \tau_{0j}$$

Pindahkan $f_b$ ke kiri dan tambahkan $m_{\sigma(j)}$ di kedua ruas:

$$h_j \ \ge\ \ell_j := (m_{\sigma(j)} - d'_j) + \theta^p(q_j) + \lambda + \tau_{0j}$$

**Cara membacanya.** Setiap suku dekomposisi §1.5 diganti nilai terkecilnya:

| Suku di §1.5                        | Nilai terkecil                                      |
| ----------------------------------- | --------------------------------------------------- |
| tunggu packing $\pi_b - f_b$        | $0$                                                 |
| packing $p_b - \pi_b$               | $\theta^p(q_j)$ (batch hanya berisi node $j$)       |
| muat dan tunggu berangkat $S - p_b$ | $\lambda$                                           |
| perjalanan $A_j - S$                | $\tau_{0j}$ (langsung dari dapur)                   |
| tunggu $W_j$ dan slack $d'_j - T_j$ | $0$                                                 |
| sisa $m_{\sigma(j)} - d'_j$         | buffer $\delta$, ditambah selisih bila $d'_j < d_j$ |

**Dua hasil langsung.**

- **Uji per node:** bila $\ell_j > H^{max}$, instans tidak layak.
- **Batas bawah objektif:** $\sum_j q_j h_j \ge \sum_j q_j \ell_j$. Ini _lower bound holding_ v3.1 §8.10; celah terhadap holding hasil metaheuristik membatasi seberapa jauh kita dari optimum (MO-6.3, MO-13.2).

### 7.3 Jendela selesai masak per node, $F_j$

Langkah yang sama memberi batas jam $f_b$ untuk batch yang memuat node $j$:

$$F_j = [L_j,\ U_j], \qquad L_j = \max \left( m_{\sigma(j)} - H^{max},\ e_{dapur} + \theta^c(q_j) \right), \qquad U_j = m_{\sigma(j)} - \ell_j$$

- $U_j$ dari rangkaian §7.2.
- $m_{\sigma(j)} - H^{max}$ dari I3 + I4.
- $e_{dapur} + \theta^c(q_j)$: batch berisi $j$ paling cepat matang setelah memasak sedikitnya $q_j$ porsi (P4, P8).

Bila $L_j > U_j$, instans tidak layak; uji ini mencakup $\ell_j > H^{max}$. $F_j$ tidak bergantung pada rute maupun batch, sehingga dihitung sekali dalam $O(n)$.

**Contoh, H5 dengan data §6.6.**

| Node | $q_j$ | $m_j - d'_j$ | $\theta^p(q_j)$ | $\tau_{0j}$ | $\ell_j$ | $\theta^c(q_j)$ | $L_j$ | $U_j$ |
| ---- | ----: | -----------: | --------------: | ----------: | -------: | --------------: | ----: | ----: |
| 1    |    25 |           20 |              13 |          15 |       58 |              35 |   510 |   572 |
| 2    |    40 |           20 |              14 |          30 |       74 |              38 |   470 |   516 |
| 3    |    20 |           25 |              12 |          25 |       72 |              34 |   550 |   598 |
| 4    |    35 |           20 |              14 |          20 |       64 |              37 |   430 |   486 |
| 5    |    15 |           20 |              12 |          20 |       62 |              33 |   510 |   568 |

Node 3 memakai $d'_3 = 645$, bukan $d_3 = 650$. $\sum_j q_j \ell_j = 1450 + 2960 + 1440 + 2240 + 930 = 9020$; holding jadwal tercepat §6.6 sekitar 3,6 kali batas ini.

**$F_j$ syarat perlu, bukan cukup.** Batch $\lbrace 1, 3, 5 \rbrace$ punya jam bersama $[550, 568]$, tetapi §7.1 menunjukkan rencana itu tidak layak. $\ell_j$ mengabaikan tiga hal: trip dibatasi deadline **node lain** yang serute (node 4, $S \le 510$), perjalanan tidak langsung ($\Delta_5 = 95 > \tau_{05} = 20$), dan packing satu batch penuh ($\theta^p(60) = 16 > 12$).

### 7.4 Kapan beberapa node bisa satu batch: sifat Helly

**Proposisi (Helly, satu dimensi).** Untuk interval $F_j = [L_j, U_j]$, $j \in G$, ketiga pernyataan ini setara:

1. Semua interval punya titik bersama.
2. Setiap pasang interval beririsan.
3. $\max_{j \in G} L_j \le \min_{j \in G} U_j$.

Titik bersamanya tepat $\left[ \max_j L_j,\ \min_j U_j \right]$.

**Bukti.**

- **1 ⇒ 2.** Titik bersama semua interval juga titik bersama setiap pasang.
- **2 ⇒ 3.** Misalkan $L_i$ ujung kiri terbesar dan $U_k$ ujung kanan terkecil. $F_i$ dan $F_k$ beririsan, jadi ada $t$ dengan $L_i \le t \le U_k$. (Bila $i = k$, pakai $L_i \le U_i$.)
- **3 ⇒ 1.** Ambil $t = \max_j L_j$. Untuk setiap $j$: $L_j \le t$ dan $t \le \min_i U_i \le U_j$. ∎

Akibatnya, sekelompok node bisa satu batch (dari sisi waktu) jika dan hanya jika **setiap pasangnya** bisa. Ini berbeda dengan kelompok saling tak serute (§3.8), yang secara umum sulit dicari.

**Contoh, H5.** Pasangan yang jendelanya lepas: $\lbrace 2, 3 \rbrace$ ($516 < 550$), $\lbrace 4, 1 \rbrace$, $\lbrace 4, 3 \rbrace$, $\lbrace 4, 5 \rbrace$ ($486 < 510$). Batch $\lbrace 2, 4 \rbrace$ punya jam bersama $[470, 486]$, batch $\lbrace 1, 3, 5 \rbrace$ punya $[550, 568]$.

### 7.5 Jumlah batch minimum: greedy piercing

Satu batch adalah satu jam $f_b$, yaitu satu **titik** di garis waktu; node $j$ bisa masuk bila titiknya di $F_j$. Jumlah batch minimum dari sisi waktu adalah jumlah titik paling sedikit yang menusuk semua interval (_interval piercing_).

**Algoritma** ($O(n \log n)$):

1. Urutkan interval menurut ujung kanan $U_j$.
2. Ambil interval pertama yang belum tertusuk; taruh titik $t = U_j$.
3. Tandai semua interval dengan $L_i \le t \le U_i$ sebagai tertusuk.
4. Ulangi sampai semua tertusuk. Jumlah titik $= \beta^{\ast}$.

**Bukti optimal.** Misalkan greedy memilih interval $I_1, \dots, I_{\beta^{\ast}}$.

1. **Saling lepas.** Saat $I_{t+1}$ dipilih, ia tidak memuat titik $U_{I_t}$, padahal $U_{I_{t+1}} \ge U_{I_t}$; jadi $L_{I_{t+1}} > U_{I_t}$.
2. **Interval lepas butuh batch berbeda** (§7.4), jadi setiap rencana butuh $\ge \beta^{\ast}$ batch.
3. **Greedy mencapainya**: setiap node masuk batch titik yang menusuknya. ∎

Jumlah batch minimum sama dengan jumlah interval saling lepas terbanyak, dan greedy memberi keduanya: jawaban dan saksinya.

**Mengapa ujung kanan.** Mengurutkan menurut ujung kiri gagal: pada $[0, 10]$, $[1, 2]$, $[3, 4]$, aturan itu menaruh titik di 10, 2, dan 4 (tiga titik), padahal titik 2 dan 4 cukup.

**Contoh, H5.** Urutan menurut $U$: $F_4, F_2, F_5, F_1, F_3$. Titik 486 menusuk node 4 dan 2; titik 568 menusuk node 5, 1, dan 3. $\beta^{\ast} = 2 = \lceil 135/100 \rceil$, dengan batch $\lbrace 2, 4 \rbrace$ ($D = 75$) dan $\lbrace 1, 3, 5 \rbrace$ ($D = 60$). Pembagian ini persis rencana §7.1 yang tidak layak dengan rute S1: greedy menghitung **berapa** batch yang perlu, bukan pembagian yang pasti cocok dengan rute.

**V6, tidak layak karena jumlah batch.** H5 dengan $H^{max} = 90$ dan $\lvert B \rvert = 3$. $L = (540, 500, 580, 460, 540)$, $U$ tetap. Greedy menaruh titik di 486 (node 4), 516 (node 2), 568 (node 5, 1), dan 598 (node 3): $\beta^{\ast} = 4 > 3$. Saksinya $F_4, F_2, F_5, F_3$, dengan keenam pasang lepas ($486 < 500$, $486 < 540$, $486 < 580$, $516 < 540$, $516 < 580$, $568 < 580$). Uji per node lolos (semua $L_j \le U_j$); yang gagal adalah uji bersama. Enumerasi H5-P (§7.9) dengan $H^{max} = 90$ memberi 0 rencana layak, juga bila $\lvert B \rvert = 4$.

### 7.6 Uji sebelum mencari solusi

$$\lvert B \rvert \ \ge\ \max \left( \left\lceil \frac{\sum_j q_j}{D^{max}} \right\rceil,\ \beta^{\ast} \right)$$

| #   | Uji                                                                              | Gagal berarti                    | Biaya         |
| --- | -------------------------------------------------------------------------------- | -------------------------------- | ------------- |
| 1   | $a'_j \le d'_j$ (§2.3)                                                           | node tidak bisa dilayani         | $O(n)$        |
| 2   | $\lceil \sum q / Q \rceil \le \lvert K \rvert \rho$ (§4.8)                       | trip tidak cukup                 | $O(n)$        |
| 3   | $L_j \le U_j$ (§7.3)                                                             | node tidak bisa diberi jam masak | $O(n)$        |
| 4   | $\max(\lceil \sum q / D^{max} \rceil,\ \beta^{\ast}) \le \lvert B \rvert$ (§7.5) | batch tidak cukup                | $O(n \log n)$ |

Tidak ada uji yang menggantikan uji lain, dan semuanya syarat perlu. Contoh: H5-P dengan $\rho = 1$ lolos keempatnya tetapi tidak layak (§7.9); kasus seperti itu diputuskan solver exact (MO-6.2).

### 7.7 Jadwal paling lambat

**Masalahnya.** Misalkan semua keputusan diskret sudah dipilih: rute, trip per kendaraan beserta urutannya, dan pembagian serta urutan batch. Jarak sudah tetap, jadi yang tersisa adalah memilih jam agar

$$\sum_j q_j h_j = \sum_j q_j \left( m_{\sigma(j)} - f_{b(j)} \right)$$

minimum, yaitu agar jam selesai masak **sebesar mungkin**.

**Semua aturan berbentuk selisih.** Setelah keputusan diskret tetap, $D_b$, $\theta^c_b$, dan $\theta^p_b$ diketahui dan semua Big-M hilang. Setiap aturan berbentuk $t_v - t_u \ge w$ ("jam $v$ paling cepat $w$ menit setelah jam $u$") atau batas $t_v \ge c$, $t_v \le c$:

| Aturan                      | Bentuk                                                                                                           |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Masak, packing (P4, P5)     | $f_b - \gamma_b \ge \theta^c_b$, $\ p_b - \pi_b \ge \theta^p_b$                                                  |
| Packing setelah matang (P6) | $\pi_b - f_b \ge 0$                                                                                              |
| Lini (P7)                   | $\gamma_{b+1} - f_b \ge 0$, $\ \pi_{b+1} - p_b \ge 0$                                                            |
| Release (I1)                | $S - p_b \ge \lambda$ untuk setiap batch di trip                                                                 |
| Rute (§1.4)                 | $T_{j_1} - S \ge \tau_{0 j_1}$, $\ T_j - T_i \ge s_i + \tau_{ij}$, $\ E - T_{j_m} \ge s_{j_m} + \tau_{j_m, n+1}$ |
| Rantai trip (G8)            | $S^{k,r+1} - E^{kr} \ge \lambda$                                                                                 |
| Batas bawah                 | $\gamma_1 \ge e_{dapur}$, $\ S \ge e_0$, $\ T_j \ge a'_j$, $\ f_b \ge m_{\sigma(j)} - H^{max}$                   |
| Batas atas                  | $T_j \le d'_j$, $\ E \le l_0$, $\ p_b \le l_0 - \lambda$                                                         |

Sistem ini disebut **sistem kendala selisih**; polanya sama dengan _critical path method_ (CPM): setiap kegiatan punya jam paling awal dan paling lambat.

**Proposisi (lattice).** Bila $t$ dan $t'$ jadwal layak, maka $\max(t, t')$ dan $\min(t, t')$, diambil per jam, juga layak.

**Bukti untuk maksimum.**

1. **Aturan selisih.** $\max(t_v, t'_v) \ge t_v \ge t_u + w$ dan $\max(t_v, t'_v) \ge t'_v \ge t'_u + w$, jadi $\max(t_v, t'_v) \ge \max(t_u, t'_u) + w$.
2. **Batas bawah.** $\max(t_v, t'_v) \ge t_v \ge c$.
3. **Batas atas.** Keduanya $\le c$, jadi maksimumnya juga.

**Bukti untuk minimum** (cermin).

1. **Aturan selisih.** $t_v \ge t_u + w \ge \min(t_u, t'_u) + w$ dan $t'_v \ge \min(t_u, t'_u) + w$, jadi $\min(t_v, t'_v) \ge \min(t_u, t'_u) + w$.
2. **Batas bawah.** Keduanya $\ge c$.
3. **Batas atas.** $\min(t_v, t'_v) \le t_v \le c$. ∎

**Akibat.** Semua jam bilangan bulat di $[0, 1440)$, jadi jadwal layak berhingga banyaknya. Maksimum semuanya, $t^{lambat}$, dan minimum semuanya, $t^{cepat}$, juga layak, dan setiap jadwal layak memenuhi $t^{cepat}_v \le t_v \le t^{lambat}_v$ di setiap jam $v$. Khususnya $f^{lambat}_b$ adalah $f_b$ terbesar yang mungkin **untuk semua batch sekaligus**:

- Holding setiap node minimum bersamaan: $h^{min}_j = m_{\sigma(j)} - f^{lambat}_{b(j)}$.
- Tidak ada tawar-menawar antar-node; bobot $q_j$ apa pun (tidak negatif) memberi jadwal terbaik yang sama.

Inilah dasar decoder produksi deterministik (v3.1 §9.1, MO-13.1): untuk rencana diskret yang tetap, holding minimum adalah satu perhitungan, bukan pencarian.

**Lintasan mundur.** Aturan $t_v - t_u \ge w$ dibaca terbalik sebagai $t_u \le t_v - w$, lalu dikerjakan dari belakang:

$$t^{lambat}_u = \min \left( \text{batas atas } u,\ \min_{\text{aturan } u \to v} \left( t^{lambat}_v - w \right) \right)$$

Bentuk konkretnya:

- **Trip terakhir kendaraan:** $S^{lambat} = S^{max}$.
- **Trip sebelumnya:** $S^{lambat} = \min \left( S^{max},\ S^{lambat}_{\text{berikut}} - \lambda - \Delta \right)$, karena $E \le S_{\text{berikut}} - \lambda$ dan $E \ge S + \Delta$. Rantai ini hanya di dalam **satu kendaraan**.
- **Batch, dari yang terakhir:**

$$p^{lambat}_b = \min \left( \min_{\text{trip yang membawa } b} S^{lambat} - \lambda,\ \ \pi^{lambat}_{b+1},\ \ l_0 - \lambda \right), \qquad \pi^{lambat}_b = p^{lambat}_b - \theta^p_b$$

$$f^{lambat}_b = \min \left( \pi^{lambat}_b,\ \ \gamma^{lambat}_{b+1} \right), \qquad \gamma^{lambat}_b = f^{lambat}_b - \theta^c_b$$

Untuk batch terakhir, suku $\pi_{b+1}$ dan $\gamma_{b+1}$ tidak ada.

**Kelayakan.** Hitung $t^{cepat}$ dengan lintasan maju yang memakai semua batas bawah, termasuk $f_b \ge \max_{j \in b} m_{\sigma(j)} - H^{max}$.

**Proposisi.** Rencana diskret layak jika dan hanya jika $t^{cepat}_v \le t^{lambat}_v$ di setiap jam $v$.

**Bukti.** Semua aturan selisih menunjuk maju dalam waktu (dapur → trip → node → pulang → trip berikutnya), jadi tidak ada lingkaran dan kedua lintasan terdefinisi.

- **⇒.** Untuk jadwal layak $t$, induksi sepanjang lintasan maju memberi $t^{cepat} \le t$, dan sepanjang lintasan mundur memberi $t \le t^{lambat}$.
- **⇐.** $t^{cepat}$ memenuhi semua aturan selisih dan batas bawah menurut konstruksinya, dan setiap batas atas karena $t^{cepat}_v \le t^{lambat}_v \le c$. Jadi $t^{cepat}$ sendiri adalah saksi. ∎

Selisih $t^{lambat}_v - t^{cepat}_v$ adalah _slack_: berapa menit jam itu masih bisa digeser.

### 7.8 Contoh: rute S1 dengan $H^{max} = 200$

Pada $H^{max} = 120$ rute S1 tidak layak (§7.1), jadi contoh ini memakai $H^{max} = 200$. Data lain seperti §6.6, satu trip per kendaraan.

**Lintasan mundur.** $S^{lambat}_A = 515$, $S^{lambat}_B = 510$.

| Batch | Node    | Trip | $p^{lambat}_b$                  | $\pi^{lambat}_b$ | $f^{lambat}_b$         | $\gamma^{lambat}_b$ |
| ----: | ------- | ---- | ------------------------------- | ---------------: | ---------------------- | ------------------: |
|     2 | 1, 3, 5 | A, B | $\min(515, 510) - 10 = 500$     |              484 | 484                    |                 442 |
|     1 | 2, 4    | A, B | $\min(500,\ \pi_2 = 484) = 484$ |              466 | $\min(466, 442) = 442$ |                 397 |

$f^{lambat}_1$ dibatasi lini masak, bukan packingnya sendiri: batch 1 boleh matang sampai 466, tetapi lini harus kosong pukul 442 agar batch 2 matang pukul 484.

**Holding minimum.**

| Node | Batch | $f^{lambat}$ | $h^{min}_j$ | $q_j h_j$ |
| ---- | ----: | -----------: | ----------: | --------: |
| 1    |     2 |          484 |         146 |      3650 |
| 2    |     1 |          442 |         148 |      5920 |
| 3    |     2 |          484 |         186 |      3720 |
| 4    |     1 |          442 |         108 |      3780 |
| 5    |     2 |          484 |         146 |      2190 |
|      |       |              |   **Total** | **19260** |

| Jadwal                    | $\sum_j q_j h_j$ |
| ------------------------- | ---------------: |
| Tercepat (§6.6)           |            32355 |
| Paling lambat             |            19260 |
| Batas bawah $\sum q \ell$ |             9020 |

Celah terhadap batas bawah berasal dari dua hal: satu batch berbagi satu jam masak yang ditentukan node paling mendesak (node 3 matang pukul 484 padahal makan pukul 670), serta batas dari rute dan lini masak yang tidak terlihat oleh $\ell_j$.

**Kelayakan.** $f^{cepat}_1 = \max(300 + 45,\ 590 - 200) = 390$ dan $f^{cepat}_2 = \max(390 + 42,\ 670 - 200) = 470$. Slack $f_1 = 52$, $f_2 = 14$; rencana layak. $H^{max}$ terkecil yang masih layak adalah holding terbesar di jadwal paling lambat, $h_3 = 186$ (enumerasi: layak pada 186, tidak layak pada 185).

### 7.9 Instans H5-P

**Data:** tabel H5 (§3.3), $\delta_j = 20$, data produksi §5.5, $\lvert K \rvert = 2$, $\rho = 2$, $\lvert B \rvert = 3$, $\lambda = 10$, $H^{max} = 120$.

**Enumerasi.** Semua susunan trip per kendaraan (kendaraan tak berlabel) dan semua pembagian node ke batch berurut; jadwal diselesaikan sebagai sistem kendala selisih (§7.7). Sebuah rencana adalah pasangan (susunan trip, pembagian batch).

| Varian                            | Hasil                                                                               |
| --------------------------------- | ----------------------------------------------------------------------------------- |
| **H5-P**                          | 13 rencana layak (5 susunan trip); optimum unik D1: jarak **38**, holding **12395** |
| $\rho = 1$                        | tidak layak, walau keempat uji §7.6 lolos                                           |
| $\rho = 1$, $\lvert K \rvert = 3$ | optimum jarak 40, holding 11835                                                     |
| V6: $H^{max} = 90$                | tidak layak ($\beta^{\ast} = 4 > 3$); juga tidak layak dengan $\lvert B \rvert = 4$ |
| $H^{max} = 200$                   | optimum jarak 32 (rute S1), holding 18400                                           |

Mengetatkan batas holding dari 200 ke 120 menaikkan jarak optimum dari 32 ke 38: rute dipecah menjadi trip pendek supaya makanan bisa dimasak lebih lambat.

**Rencana optimum D1.**

| Kendaraan | Trip ke-1 | Trip ke-2 |
| --------- | --------- | --------- |
| 1         | $(4)$     | $(2, 1)$  |
| 2         | $(5)$     | $(3)$     |

Jarak $8 + 12 + 8 + 10 = 38$. Batch 1 $= \lbrace 4 \rbrace$, batch 2 $= \lbrace 1, 2, 5 \rbrace$, batch 3 $= \lbrace 3 \rbrace$.

| Trip     | $\Delta$ | $E^{\ast}$ | $S^{max}$ |
| -------- | -------: | ---------: | --------: |
| $(4)$    |       45 |        525 |       510 |
| $(2, 1)$ |       85 |        585 |       540 |
| $(5)$    |       50 |        610 |       590 |
| $(3)$    |       60 |        635 |       620 |

| Batch | Node    | $D_b$ | $\theta^c$ | $\theta^p$ |
| ----: | ------- | ----: | ---------: | ---------: |
|     1 | 4       |    35 |         37 |         14 |
|     2 | 1, 2, 5 |    80 |         46 |         18 |
|     3 | 3       |    20 |         34 |         12 |

**Lintasan mundur, trip** (rantai hanya di dalam satu kendaraan):

| Trip     | Kendaraan, urutan | Hitungan                    | $S^{lambat}$ |
| -------- | ----------------- | --------------------------- | -----------: |
| $(2, 1)$ | 1, ke-2           | $S^{max}$                   |          540 |
| $(4)$    | 1, ke-1           | $\min(510,\ 540 - 10 - 45)$ |          485 |
| $(3)$    | 2, ke-2           | $S^{max}$                   |          620 |
| $(5)$    | 2, ke-1           | $\min(590,\ 620 - 10 - 50)$ |          560 |

**Lintasan mundur, batch:**

| Batch | Trip yang membawanya | $p^{lambat}_b$                          | $\pi^{lambat}_b$ | $f^{lambat}_b$         | $\gamma^{lambat}_b$ |
| ----: | -------------------- | --------------------------------------- | ---------------: | ---------------------- | ------------------: |
|     3 | $(3)$                | $620 - 10 = 610$                        |              598 | 598                    |                 564 |
|     2 | $(2, 1)$, $(5)$      | $\min(\min(540, 560) - 10,\ 598) = 530$ |              512 | $\min(512, 564) = 512$ |                 466 |
|     1 | $(4)$                | $\min(485 - 10,\ 512) = 475$            |              461 | $\min(461, 466) = 461$ |                 424 |

**Holding minimum.**

| Node | Batch | $f^{lambat}$ | $h^{min}_j$ | $q_j h_j$ |
| ---- | ----: | -----------: | ----------: | --------: |
| 1    |     2 |          512 |         118 |      2950 |
| 2    |     2 |          512 |          78 |      3120 |
| 3    |     3 |          598 |          72 |      1440 |
| 4    |     1 |          461 |          89 |      3115 |
| 5    |     2 |          512 |         118 |      1770 |
|      |       |              |   **Total** | **12395** |

Holding terbesar 118 $\le 120$; holding total sekitar 1,4 kali batas bawah 9020.

**Kelayakan.** $f^{cepat}_1 = \max(300 + 37,\ 550 - 120) = 430$, $f^{cepat}_2 = \max(430 + 46,\ 630 - 120) = 510$, $f^{cepat}_3 = \max(510 + 34,\ 670 - 120) = 550$. Slack $31$, $2$, dan $48$: batch 2 hampir terkunci, karena node 1 dan 5 (makan 630) memaksanya matang $\ge 510$, sedangkan trip $(2, 1)$ harus berangkat $\le 540$.

### 7.10 Keputusan MO-1.5

| #   | Keputusan                                                                                                                                                                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| K1  | Pemecahan demand memakai $\bar Q = \min(Q, D^{max})$; §1.7 nomor 6 menjadi $1 \le q_j \le \bar Q$; node yang tidak muat di batch adalah input tidak valid (§5.6)                            |
| K2  | P4 dan P5 memakai "≥" dengan waktu bulat; durasi efektif $\theta^c$, $\theta^p$ dibulatkan ke atas; kelonggarannya setara dengan mulai lebih telat (§5.3)                                   |
| K3  | Satu trip boleh membawa porsi dari beberapa batch; release $= \max_b p_b + \lambda$; satu $\lambda$ per trip, termasuk trip pertama (§6.1)                                                  |
| K4  | Objektif Model D leksikografis: (jarak, $\sum_j q_j h_j$); tingkat keterlambatan gugur karena B3 (§6.4)                                                                                     |
| K5  | I2: $p_b \le l_0 - \lambda$; Big-M $M^R = l_0 - e_0$ dan $M^h_j = m_{\sigma(j)} - e_{dapur}$ (§6.2, §6.3)                                                                                   |
| K6  | Holding minimum per node $\ell_j = (m_{\sigma(j)} - d'_j) + \theta^p(q_j) + \lambda + \tau_{0j}$, jendela $F_j$, dan batas bawah objektif $\sum_j q_j \ell_j$ (§7.2, §7.3; MO-6.3, MO-13.2) |
| K7  | Batas bawah jumlah batch: $\max(\lceil \sum q / D^{max} \rceil,\ \beta^{\ast})$ dengan $\beta^{\ast}$ dari greedy piercing; $\lvert B \rvert$ adalah parameter slot batch (§7.4–§7.6)       |
| K8  | Untuk rencana diskret yang tetap, holding minimum = jadwal paling lambat (lintasan mundur); layak jika dan hanya jika $t^{cepat} \le t^{lambat}$ (§7.7; decoder MO-13.1)                    |
| K9  | H5-P, rencana D1 beserta tabel lintasan mundurnya, contoh §7.8, tabel enumerasi, dan V6 menjadi fixture MO-2.3 (§7.8, §7.9)                                                                 |

Pertanyaan terbuka:

- Urutan batch dan pembagian node ke batch terbaik sebagai masalah optimasi (MO-12, MO-13.1).
- Uji kapasitas lini masak untuk banyak batch, misalnya $e_{dapur} + \sum_b \theta^c_b$ terhadap jendela, untuk lower bound yang lebih ketat (MO-13.2).
- Apakah pelanggaran holding dan release dilaporkan dengan penyebabnya ("batch $b$ terlambat untuk trip $(k,r)$") di validator (MO-3.2).
