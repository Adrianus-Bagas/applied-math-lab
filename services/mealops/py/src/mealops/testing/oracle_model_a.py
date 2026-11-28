"""Oracle Model A: implementasi pembanding yang sengaja sederhana.

Terpisah dari validator (MO-3.2). Hanya untuk instans kecil di tes.
"""

import copy
from collections.abc import Iterator
from dataclasses import dataclass
from itertools import pairwise, permutations, product
from typing import Any, Literal

Instance = dict[str, Any]  # hasil json.load, sengaja tanpa Pydantic


def effective_window(
    *,
    a: int,
    d: int,
    s: int,
    tau_from_depot: int,
    tau_to_depot: int,
    e0: int,
    l0: int,
) -> tuple[int, int]:
    """Jendela efektif (a'_j, d'_j), model.md §2.3.

    Tidak menolak a' > d'; itu urusan pemanggil (tingkat 2).
    """
    # Langkah 1: hitung jam tiba paling cepat dari dapur, yaitu e0 + tau_from_depot
    a_from_kitchen = e0 + tau_from_depot
    # Langkah 2: a_eff = yang lebih BESAR antara a dan hasil langkah 1
    a_eff = max(a_from_kitchen, a)
    # Langkah 3: hitung batas mulai layanan supaya sempat pulang: l0 - s - tau_to_depot
    d_to_kitchen = l0 - s - tau_to_depot
    # Langkah 4: d_eff = yang lebih KECIL antara d dan hasil langkah 3
    d_eff = min(d_to_kitchen, d)
    # Langkah 5: kembalikan (a_eff, d_eff)
    return (a_eff, d_eff)


@dataclass(frozen=True)
class NodeData:
    """Data satu node yang dipakai oracle (nomor node mulai dari 1)."""

    q: int  # demand
    s: int  # waktu layan
    loc: int  # nomor lokasi = indeks baris/kolom matriks
    a_eff: int  # a'_j
    d_eff: int  # d'_j


def node_data(inst: Instance, j: int) -> NodeData:
    node = inst["nodes"][j - 1]
    loc = node["point"]
    point = inst["points"][loc - 1]
    tau = inst["travel_time"]
    a_eff, d_eff = effective_window(
        a=point["ready"],
        d=point["consume"] - point["buffer"],
        s=node["service"],
        tau_from_depot=tau[0][loc],
        tau_to_depot=tau[loc][0],
        e0=inst["kitchen"]["open"],
        l0=inst["kitchen"]["close"],
    )
    return NodeData(q=node["demand"], s=node["service"], loc=loc, a_eff=a_eff, d_eff=d_eff)


@dataclass(frozen=True)
class RouteCheck:
    """Hasil pemeriksaan satu rute (§2.7)."""

    ok: bool
    reason: Literal["kapasitas", "jendela"] | None
    bad_node: int | None  # node tempat jendela gagal
    load: int
    starts: tuple[int, ...]  # T* sampai node yang gagal (inklusif)
    back: int | None  # jam pulang; None bila gagal
    cost: int  # meter, dihitung walau rute gagal


def route_cost(inst: Instance, route: list[int]) -> int:
    c = inst["distance"]
    locs = [0] + [node_data(inst, j).loc for j in route] + [0]
    return sum(c[u][v] for u, v in pairwise(locs))


def check_route(inst: Instance, route: list[int]) -> RouteCheck:
    """Pemeriksaan satu rute, model.md §2.7. route = nomor node, mis. [2, 1, 5]."""
    nodes = [node_data(inst, j) for j in route]
    cost = route_cost(inst, route)
    tau = inst["travel_time"]

    # Langkah 1: load = jumlah q semua node.
    load = sum(node.q for node in nodes)
    #   Bila load > inst["fleet"]["capacity"]:
    if load > inst["fleet"]["capacity"]:
        return RouteCheck(False, "kapasitas", None, load, (), None, cost)
    #   return RouteCheck(False, "kapasitas", None, load, (), None, cost)
    #   (kapasitas diperiksa DULUAN, starts kosong)
    # Langkah 2: t = a_eff node pertama; simpan t ke list starts.
    t = nodes[0].a_eff
    starts = [t]
    if t > nodes[0].d_eff:
        return RouteCheck(False, "jendela", route[0], load, tuple(starts), None, cost)
    #   Bila t > d_eff node pertama -> gagal "jendela" dengan bad_node = route[0]
    # Langkah 3: untuk k = 1, 2, ..., len(nodes) - 1:
    for k in range(1, len(nodes)):
        #   prev = nodes[k - 1], cur = nodes[k]
        prev = nodes[k - 1]
        cur = nodes[k]
        #   arrive = t + prev.s + tau[prev.loc][cur.loc]   <- s milik prev!
        arrive = t + prev.s + tau[prev.loc][cur.loc]
        #   t = max(arrive, cur.a_eff); simpan t ke starts
        t = max(arrive, cur.a_eff)
        starts.append(t)
        #   Bila t > cur.d_eff -> gagal "jendela", bad_node = route[k], back = None
        if t > cur.d_eff:
            return RouteCheck(False, "jendela", route[k], load, tuple(starts), None, cost)
    # Langkah 4: back = t + s node terakhir + tau[loc terakhir][0]
    last_node = nodes[-1]
    back = t + last_node.s + tau[last_node.loc][0]
    # Langkah 5: return RouteCheck(True, None, None, load, tuple(starts), back, cost)
    return RouteCheck(True, None, None, load, tuple(starts), back, cost)


def set_partitions(items: list[int], max_blocks: int) -> Iterator[list[list[int]]]:
    """Semua partisi `items` menjadi paling banyak `max_blocks` blok, masing-masing tepat sekali.

    Memakai restricted growth string (RGS). Kompleksitas max_blocks^n: hanya untuk n kecil.
    """
    for labels in product(range(max_blocks), repeat=len(items)):
        # Langkah 1: periksa aturan RGS sambil membaca labels dari kiri ke kanan.
        #   highest = -1 (belum ada kelompok)
        highest = -1
        ok = True
        #   untuk setiap lab: bila lab > highest + 1 -> bukan RGS, lewati tuple ini
        #   (pakai flag ok + break, lalu `continue` di luar loop dalam)
        #   selain itu highest = max(highest, lab)
        for lab in labels:
            if lab > highest + 1:
                ok = False
                break
            highest = max(highest, lab)
        if not ok:
            continue
        # Langkah 2: buat highest + 1 list kosong:
        #   blocks: list[list[int]] = [[] for _ in range(highest + 1)]
        blocks: list[list[int]] = [[] for _ in range(highest + 1)]
        # Langkah 3: masukkan item ke bloknya:
        #   for item, lab in zip(items, labels): blocks[lab].append(item)
        for item, lab in zip(items, labels, strict=True):
            blocks[lab].append(item)
        # Langkah 4: yield blocks
        yield blocks


@dataclass(frozen=True)
class Solution:
    """Satu solusi layak Model A dalam bentuk kanonik."""

    routes: tuple[tuple[int, ...], ...]  # diurutkan dengan sorted(); kendaraan tak berlabel
    cost: int  # meter


def enumerate_solutions(inst: Instance) -> list[Solution]:
    """Semua solusi layak Model A, urut menurut (biaya, rute). Hanya untuk n kecil."""
    all_nodes = list(range(1, len(inst["nodes"]) + 1))
    max_vehicles = inst["fleet"]["vehicles"]
    found: list[Solution] = []

    for partition in set_partitions(all_nodes, max_vehicles):
        # Langkah 1: untuk setiap blok, kumpulkan urutan yang layak:
        #   options: list[list[tuple[int, ...]]] = []
        #   feasible = [p for p in permutations(block) if check_route(inst, list(p)).ok]
        #   options.append(feasible)
        options: list[list[tuple[int, ...]]] = []
        for block in partition:
            feasible = [p for p in permutations(block) if check_route(inst, list(p)).ok]
            options.append(feasible)
        # Langkah 2: bila ada blok tanpa urutan layak -> partisi ini menyumbang 0, `continue`
        #   petunjuk: any(len(o) == 0 for o in options)
        if any(len(o) == 0 for o in options):
            continue
        # Langkah 3: for combo in product(*options):
        #   cost = jumlah route_cost(inst, list(r)) untuk setiap r di combo
        #   found.append(Solution(routes=tuple(sorted(combo)), cost=cost))
        for combo in product(*options):
            cost = sum(route_cost(inst, list(r)) for r in combo)
            found.append(Solution(routes=tuple(sorted(combo)), cost=cost))

    # Langkah 4: urutkan found menurut (cost, routes), lalu return
    found.sort(key=lambda s: (s.cost, s.routes))
    return found


def _decode_token(token: str) -> str:
    """Kembalikan escape JSON Pointer (RFC 6901): '~1' -> '/', lalu '~0' -> '~'."""
    return token.replace("~1", "/").replace("~0", "~")


def apply_patch(base: Instance, ops: list[dict[str, Any]]) -> Instance:
    """Terapkan op JSON Patch 'replace' ke salinan `base`. `base` tidak diubah."""
    result = copy.deepcopy(base)
    for op in ops:
        # Langkah 1: bila op["op"] != "replace" -> raise ValueError(...)
        if op["op"] != "replace":
            raise ValueError(f"op tidak didukung: {op['op']}")
        # Langkah 2: path = op["path"]; bila tidak diawali "/" -> raise ValueError(...)
        path = op["path"]
        if not path.startswith("/"):
            raise ValueError(f"path harus diawali '/': {path!r}")
        # Langkah 3: tokens = [_decode_token(t) for t in path[1:].split("/")]
        tokens = [_decode_token(t) for t in path[1:].split("/")]
        # Langkah 4: target: Any = result
        target: Any = result
        #   untuk setiap token di tokens[:-1] (semua kecuali terakhir):
        #     bila target list -> target = target[int(token)]
        #     selain itu      -> target = target[token]
        #   petunjuk: isinstance(target, list)
        for token in tokens[:-1]:
            target = target[int(token)] if isinstance(target, list) else target[token]
        # Langkah 5: last = tokens[-1]
        last = tokens[-1]
        #   bila target list: idx = int(last);
        if isinstance(target, list):
            idx = int(last)
            #     bila idx >= len(target) -> raise IndexError(...); lalu target[idx] = op["value"]
            if not 0 <= idx <= len(target):
                raise IndexError(f"indeks {idx} di luar list panjang {len(target)}")
            target[idx] = op["value"]
        #   bila dict: bila last not in target -> raise KeyError(last)
        #   lalu target[last] = op["value"]
        elif isinstance(target, dict):
            if last not in target:
                raise KeyError(last)
            target[last] = op["value"]
        else:
            raise TypeError(f"{path!r}: induknya bukan list atau dict")
    return result
