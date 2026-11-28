import pytest
from mealops.testing.oracle_model_a import effective_window

# Data H5 (model.md §3.3): node -> (a, d, s, τ_0j); τ simetris, jadi τ_j0 = τ_0j
H5_NODES = {
    1: (560, 610, 10, 15),
    2: (510, 570, 15, 30),
    3: (600, 650, 10, 25),
    4: (480, 530, 5, 20),
    5: (580, 610, 10, 20),
}
H5_E0, H5_L0 = 480, 680

# Nilai harapan dari tabel §3.3 (kolom a'_j, d'_j)
H5_EXPECTED = {1: (560, 610), 2: (510, 570), 3: (600, 645), 4: (500, 530), 5: (580, 610)}


@pytest.mark.parametrize("node", sorted(H5_NODES))
def test_h5_jendela_efektif(node: int) -> None:
    a, d, s, tau = H5_NODES[node]
    got = effective_window(a=a, d=d, s=s, tau_from_depot=tau, tau_to_depot=tau, e0=H5_E0, l0=H5_L0)
    assert got == H5_EXPECTED[node]


def test_v1_node3_jendela_kosong() -> None:
    # V1 (§3.8): l_0 = 630 -> d'_3 = 595 < a'_3 = 600 (instans tidak layak, tingkat 2)
    a, d, s, tau = H5_NODES[3]
    got = effective_window(a=a, d=d, s=s, tau_from_depot=tau, tau_to_depot=tau, e0=H5_E0, l0=630)
    assert got == (600, 595)


def test_e0_530_node4_jendela_kosong() -> None:
    # Pembanding §3.8: e_0 = 530 -> a'_4 = 550 > d'_4 = 530
    a, d, s, tau = H5_NODES[4]
    got = effective_window(a=a, d=d, s=s, tau_from_depot=tau, tau_to_depot=tau, e0=530, l0=H5_L0)
    assert got == (550, 530)
