# MealOps — Glosarium notasi gabungan

> Satu tempat untuk semua notasi di `model.md`. Notasi kanonik tetap glosarium `PROJECT_CONTEXT` MealOps v3.1 §8.1; kolom **Asal** menyebut "v3.1" untuk notasi dari sana dan nomor bagian `model.md` untuk notasi tambahan.
> Semua waktu dalam menit bulat sejak 00:00 hari operasi (B1).

## 1. Himpunan dan indeks

| Notasi                                                  | Arti                                                           | Asal       |
| ------------------------------------------------------- | -------------------------------------------------------------- | ---------- |
| $N$, $n = \lvert N \rvert$                              | Node pengantaran (setelah pemecahan demand)                    | v3.1       |
| $V = \lbrace 0 \rbrace \cup N \cup \lbrace n+1 \rbrace$ | Semua node; $0$ dan $n+1$ adalah dapur (berangkat dan kembali) | §2.1       |
| $\mathcal{A}$                                           | Arc yang diperbolehkan, $\lvert \mathcal{A} \rvert = n(n+1)$   | §2.1       |
| $K$, $\lvert K \rvert$                                  | Armada dan jumlah kendaraan                                    | v3.1       |
| $B$, $\lvert B \rvert$                                  | Slot batch dan jumlahnya (parameter)                           | v3.1, §5.1 |
| $i, j$                                                  | Node                                                           | v3.1       |
| $k$; $(k, r)$                                           | Kendaraan; trip ke-$r$ milik kendaraan $k$                     | v3.1, §4.2 |
| $b$; $b(j)$                                             | Batch; batch tempat node $j$ dimasak                           | v3.1, §5.1 |
| $\sigma(j)$                                             | Titik layanan asal node $j$                                    | v3.1       |

## 2. Parameter

| Notasi                                     | Arti                                                                         | Satuan             | Asal       |
| ------------------------------------------ | ---------------------------------------------------------------------------- | ------------------ | ---------- |
| $q_j$                                      | Demand node $j$, bilangan bulat $1 \le q_j \le \bar Q$                       | porsi              | v3.1, §1.7 |
| $Q$                                        | Kapasitas kendaraan                                                          | porsi              | v3.1       |
| $D^{max}$                                  | Kapasitas batch                                                              | porsi              | v3.1       |
| $\bar Q = \min(Q, D^{max})$                | Batas ukuran potongan saat pemecahan demand                                  | porsi              | §5.6 (K1)  |
| $\rho$                                     | Trip maksimum per kendaraan                                                  | —                  | v3.1       |
| $c_{ij}$                                   | Jarak (biaya)                                                                | meter              | v3.1       |
| $\tau_{ij}$                                | Waktu tempuh                                                                 | menit              | v3.1       |
| $s_j = \lceil s^0 + \eta q_j \rceil$       | Waktu layan                                                                  | menit              | v3.1, §1.2 |
| $a_j$, $d_j$                               | Paling awal menerima; deadline mulai layanan                                 | waktu              | v3.1       |
| $m_{\sigma(j)}$, $\delta_{\sigma(j)}$      | Waktu konsumsi terencana; buffer, $d_j = m_{\sigma(j)} - \delta_{\sigma(j)}$ | waktu, menit       | v3.1       |
| $[e_0, l_0]$                               | Jam operasional dapur untuk armada                                           | waktu              | v3.1       |
| $\lambda$                                  | Waktu muat per trip                                                          | menit              | v3.1       |
| $e_{dapur}$                                | Jam lini masak mulai                                                         | waktu              | v3.1       |
| $\phi^c_0, \phi^c_1$; $\phi^p_0, \phi^p_1$ | Koefisien durasi masak; koefisien durasi packing                             | menit, menit/porsi | v3.1       |
| $H^{max}$                                  | Batas holding (parameter kebijakan, B8)                                      | menit              | v3.1       |

## 3. Variabel keputusan

| Notasi               | Arti                                                 | Asal       |
| -------------------- | ---------------------------------------------------- | ---------- |
| $x_{ij}$             | Model A: arc $(i,j)$ dipakai                         | v3.1, §2.2 |
| $x^{kr}_{ij}$        | Model B/D: trip $(k,r)$ memakai arc $(i,j)$          | v3.1       |
| $X_{ij}$             | $\sum_{k,r} x^{kr}_{ij}$                             | §4.2       |
| $y^{kr}_j$, $w^{kr}$ | Node $j$ dilayani trip $(k,r)$; trip $(k,r)$ dipakai | v3.1       |
| $v_{jb}$, $o_b$      | Node $j$ dimasak di batch $b$; batch $b$ dipakai     | v3.1       |
| $T_j$                | Mulai layanan di node $j$                            | v3.1       |
| $u_j$                | Muatan kumulatif sampai node $j$                     | v3.1       |
| $S^{kr}$, $E^{kr}$   | Jam trip berangkat dari dan kembali ke dapur         | v3.1       |
| $D_b$                | Ukuran batch                                         | v3.1       |
| $\gamma_b$, $f_b$    | Mulai dan selesai masak                              | v3.1       |
| $\pi_b$, $p_b$       | Mulai dan selesai packing                            | v3.1       |
| $h_j$                | Holding, $m_{\sigma(j)} - f_{b(j)}$                  | v3.1, §1.5 |

## 4. Besaran turunan

| Notasi                       | Arti                                                                            | Asal |
| ---------------------------- | ------------------------------------------------------------------------------- | ---- |
| $A_j$, $W_j = T_j - A_j$     | Waktu tiba; lama menunggu                                                       | §1.3 |
| $a'_j$, $d'_j$               | Jendela efektif setelah jam dapur dilebur                                       | §2.3 |
| $T^{\ast}_j$                 | Mulai layanan pada jadwal tercepat (berangkat $e_0$)                            | §2.7 |
| $\Delta_j$, $\Delta$         | Lama berangkat → mulai layanan di $j$, dan durasi trip, tanpa menunggu          | §4.2 |
| $E^{\ast}$, $S^{max}$        | Jam pulang jadwal tercepat; jam berangkat paling lambat                         | §4.2 |
| $\theta^c(D)$, $\theta^p(D)$ | Durasi masak dan packing batch berukuran $D$, dibulatkan ke atas                | §5.1 |
| $\theta^c_b$, $\theta^p_b$   | Singkatan $\theta^c(D_b)$, $\theta^p(D_b)$                                      | §5.1 |
| $\ell_j$                     | Holding minimum node $j$ (batas bawah)                                          | §7.2 |
| $\mathcal{F}_j = [L_j, U_j]$ | Jendela selesai masak untuk batch yang memuat $j$                               | §7.3 |
| $\beta^{\ast}$               | Jumlah batch minimum dari sisi waktu (greedy piercing)                          | §7.5 |
| $t^{cepat}$, $t^{lambat}$    | Jadwal paling cepat dan paling lambat untuk rencana diskret tetap               | §7.7 |
| $h^{min}_j$                  | Holding minimum persis untuk rencana tetap, $m_{\sigma(j)} - f^{lambat}_{b(j)}$ | §7.7 |

## 5. Big-M

| Notasi        | Nilai                                                    | Baris        | Asal |
| ------------- | -------------------------------------------------------- | ------------ | ---- |
| $M$           | $Q$                                                      | F4, G5       | §2.5 |
| $M_{ij}$      | $\max \lbrace 0,\ d'_i + s_i + \tau_{ij} - a'_j \rbrace$ | F6, G6       | §2.5 |
| $M^S_j$       | $l_0 + \tau_{0j} - a'_j$                                 | G6 berangkat | §4.7 |
| $M^E_i$       | $d'_i + s_i + \tau_{i,n+1} - e_0$                        | G6 pulang    | §4.7 |
| $M^{\lambda}$ | $l_0 - e_0 + \lambda$                                    | G8           | §4.7 |
| $M^R$         | $l_0 - e_0$                                              | I1           | §6.2 |
| $M^h_j$       | $m_{\sigma(j)} - e_{dapur}$                              | I3           | §6.3 |

## 6. Label

Label ditulis tegak dengan nomor (B3, K1, F4); notasi matematika ditulis miring dengan subskrip ($B$, $K$, $\mathcal{F}_4$). Beberapa huruf dipakai keduanya:

| Label                 | Isi                      | Jangan tertukar dengan            |
| --------------------- | ------------------------ | --------------------------------- |
| A1–A6                 | Asumsi dari v3.1         | $A_j$ (waktu tiba), $\mathcal{A}$ |
| B1–B8                 | Asumsi MO-1.1            | $B$ (slot batch)                  |
| F0–F8                 | Formulasi Model A        | $\mathcal{F}_j$ (jendela masak)   |
| G0–G10                | Formulasi Model B        | —                                 |
| P1–P8                 | Formulasi Model C        | $p_b$ (selesai packing)           |
| I1–I4                 | Baris penghubung Model D | —                                 |
| C1–C6                 | Keputusan MO-1.2         | Model C                           |
| E1–E3                 | Keputusan MO-1.3         | $E^{kr}$, $E^{\ast}$              |
| J1–J8                 | Keputusan MO-1.4         | —                                 |
| K1–K9                 | Keputusan MO-1.5         | $K$ (armada)                      |
| R1–R5                 | Keputusan review MO-1.6  | $r$ (indeks trip)                 |
| H5, H5-S, H5-P, V1–V6 | Instans fixture          | $H^{max}$                         |
| S1, M1, M2, D1        | Solusi fixture           | $S^{kr}$, $M$                     |
