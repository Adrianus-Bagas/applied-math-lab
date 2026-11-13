# MealOps — Model Matematis

> **Status:** §1 selesai (MO-1.1), §2 selesai (MO-1.2). §3 dan seterusnya ditambahkan di MO-1.3 sampai MO-1.6.
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
3. **Pembulatan ke atas, sekali, saat instans dibuat.** Durasi turunan yang bisa pecahan, misalnya $s_j = s^0 + \eta q_j$, disimpan sebagai $\lceil s_j \rceil$. Contoh: $s^0 = 5$, $\eta = 0{,}02$, $q_j = 180$ memberi $8{,}6$, disimpan $9$. Validator dan core hanya melihat bilangan bulat.

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

Bila batas bawah melebihi batas atas, instans tidak layak. Bentuk umumnya (lower bound holding) diturunkan di MO-1.5.

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
- **B6.** Dipakai oleh lower bound (MO-1.5, MO-6.3). Pembulatan ke atas mempertahankannya, karena $\lceil x + y \rceil \le \lceil x \rceil + \lceil y \rceil$.

### 1.7 Pemeriksaan instans

Instans ditolak saat validasi input bila salah satu syarat berikut dilanggar (diimplementasikan di MO-2.1 dan MO-3.2):

1. Semua waktu dan durasi adalah bilangan bulat tak negatif, dan semua waktu berada di $[0, 1440)$.
2. $a_j \le d_j$ untuk setiap node.
3. $\delta_{\sigma(j)} \ge s_j$ untuk setiap node (B5).
4. $\tau_{ii} = 0$, dan $\tau_{jj'} = 0$ bila $\sigma(j) = \sigma(j')$.
5. $\tau_{ij} \le \tau_{ik} + \tau_{kj}$ untuk semua $i, j, k$ (B6).
6. $q_j$ bilangan bulat dengan $1 \le q_j \le Q$ untuk setiap node setelah pemecahan demand. Batas bawah ditetapkan di MO-1.2 (C1, §2.10).

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

Yang belum dicakup Model A: lebih dari satu trip per kendaraan dan waktu muat $\lambda$ (Model B, MO-1.4), produksi batch (Model C), serta release date dan holding (Model D, MO-1.5).
