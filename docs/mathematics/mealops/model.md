# MealOps — Model Matematis

> **Status:** §1 selesai (MO-1.1). §2 dan seterusnya ditambahkan di MO-1.2 sampai MO-1.6.
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
6. $q_j \le Q$ untuk setiap node setelah pemecahan demand.
