#!/usr/bin/env bash
# lab-deploy: satu-satunya perintah yang boleh dijalankan kunci SSH user `deploy` (L0.8).
#
# Dipasang di /usr/local/bin/lab-deploy (milik root, tidak bisa diubah user deploy) dan
# dipaksakan lewat authorized_keys user deploy:
#   restrict,command="/usr/local/bin/lab-deploy" ssh-ed25519 AAAA... github-actions-deploy
#
# Perintah yang diterima (dari SSH_ORIGINAL_COMMAND, atau argumen bila dijalankan manual):
#   deploy <sha-40-hex>   deploy commit main tersebut (image sha-<7> + konfigurasi commit itu)
#   status                tampilkan tag dan status service yang sedang berjalan
set -euo pipefail

readonly REPO="Adrianus-Bagas/applied-math-lab"
readonly APP_DIR="/opt/applied-math-lab"
readonly LOG_FILE="${APP_DIR}/deploy.log"
# Folder sementara deploy. Global (bukan local) karena trap EXIT berjalan setelah
# do_deploy selesai, saat variabel local fungsi itu sudah tidak ada.
tmp=""
trap 'rm -rf -- ${tmp:+"$tmp"}' EXIT

die() {
	echo "lab-deploy: $*" >&2
	exit 1
}

# Catat ke layar dan ke deploy.log (jejak audit: kapan, versi apa, berhasil atau tidak).
log() {
	printf '%s %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG_FILE"
}

do_status() {
	cd "$APP_DIR"
	grep '^IMAGE_TAG=' .env
	docker compose ps --format 'table {{.Service}}\t{{.Status}}'
}

do_deploy() {
	local sha="$1"
	local tag="sha-${sha:0:7}"
	local base="https://raw.githubusercontent.com/${REPO}/${sha}/infrastructure"
	local status running caddy_changed=0

	cd "$APP_DIR"

	# Hanya satu deploy pada satu waktu (file descriptor 9 memegang kunci sampai skrip selesai).
	exec 9>"${APP_DIR}/.deploy.lock"
	flock -n 9 || die "deploy lain sedang berjalan"

	tmp="$(mktemp -d)"

	log "mulai ${tag} (${sha})"

	# 1. SHA harus ada di riwayat main. Commit fork bisa diakses lewat URL repo induk,
	#    jadi tanpa cek ini kunci yang bocor bisa men-deploy konfigurasi dari fork siapa pun.
	#    compare/<sha>...main: "ahead" = main di depan sha (sha leluhur main), "identical" = sama.
	status="$(curl -fsSL --retry 3 -H 'Accept: application/vnd.github+json' \
		"https://api.github.com/repos/${REPO}/compare/${sha}...main" | jq -r '.status')" ||
		die "gagal memeriksa ${sha} ke GitHub API"
	[[ "$status" == "ahead" || "$status" == "identical" ]] ||
		die "${sha} bukan bagian dari riwayat main (status: ${status})"

	# 2. Konfigurasi diambil dari commit yang SAMA dengan image: infrastruktur ikut ter-versi.
	for f in compose.vps.yaml Caddyfile; do
		curl -fsSL --retry 3 -o "${tmp}/${f}" "${base}/${f}" || die "gagal mengunduh ${f} untuk ${sha}"
	done
	sed "s/^IMAGE_TAG=.*/IMAGE_TAG=${tag}/" .env >"${tmp}/.env"
	grep -qx "IMAGE_TAG=${tag}" "${tmp}/.env" || die "baris IMAGE_TAG tidak ada di .env"

	# 3. Validasi dan tarik image dari folder sementara SEBELUM menyentuh stack yang berjalan.
	#    Bila gagal di sini, versi lama tetap melayani tanpa gangguan.
	(cd "$tmp" && docker compose config --quiet) || die "konfigurasi ${tag} tidak valid"
	(cd "$tmp" && docker compose pull --quiet) || die "gagal menarik image ${tag}"

	# 4. Ganti file. Caddyfile di-bind mount sebagai satu file, dan container memegang file
	#    lama (inode lama), jadi Caddy harus dibuat ulang bila isinya berubah.
	cmp -s "${tmp}/Caddyfile" Caddyfile || caddy_changed=1
	install -m 644 "${tmp}/compose.vps.yaml" "${tmp}/Caddyfile" .
	install -m 600 "${tmp}/.env" .env

	# 5. Jalankan. --wait menunggu semua service sehat; gagal bila melewati batas waktu.
	if ! docker compose up -d --remove-orphans --wait --wait-timeout 180; then
		log "GAGAL ${tag}: service tidak sehat; rollback = deploy SHA sukses terakhir di deploy.log"
		exit 1
	fi
	if ((caddy_changed)); then
		docker compose up -d --no-deps --force-recreate caddy
	fi

	# 6. Pastikan setiap container menjalankan image dari tag yang baru ditarik.
	#    Versi yang tertanam di binary tidak dibandingkan dengan tag: image yang
	#    tidak berubah hanya di-retag di CI, jadi binary-nya membawa SHA commit
	#    yang terakhir membangunnya, bukan SHA commit yang di-deploy.
	local svc cid ref running_id expected_id
	for svc in hello-api hello-worker web; do
		cid="$(docker compose ps -q "$svc")"
		[[ -n "$cid" ]] || die "container ${svc} tidak ditemukan"
		ref="$(docker inspect --format '{{.Config.Image}}' "$cid")"
		[[ "$ref" == *":${tag}" ]] || die "${svc} memakai image ${ref}, bukan tag ${tag}"
		running_id="$(docker inspect --format '{{.Image}}' "$cid")"
		expected_id="$(docker image inspect --format '{{.Id}}' "$ref")"
		[[ "$running_id" == "$expected_id" ]] || die "${svc} menjalankan image usang untuk ${ref}"
	done
	# Versi tertanam dicatat sebagai informasi; sekaligus membuktikan binary bisa dijalankan.
	log "build hello-api: $(docker compose exec -T hello-api /usr/local/bin/hello-api version)"

	# 7. Buang image yang tidak dipakai container dan berumur > 7 hari (§4.4).
	#    Rollback ke versi lama tetap bisa: image ditarik ulang dari GHCR.
	docker image prune -af --filter "until=168h" >/dev/null

	log "SUKSES ${tag}"
}

# Perintah asli klien SSH; bila dijalankan manual, pakai argumen skrip.
cmd="${SSH_ORIGINAL_COMMAND:-$*}"
read -r action arg extra <<<"$cmd" || true

case "${action:-}" in
deploy)
	[[ -z "${extra:-}" && "${arg:-}" =~ ^[0-9a-f]{40}$ ]] || die "pemakaian: deploy <sha-40-hex>"
	do_deploy "$arg"
	;;
status)
	[[ -z "${arg:-}" ]] || die "pemakaian: status"
	do_status
	;;
*)
	die "perintah tidak dikenal; yang tersedia: 'deploy <sha-40-hex>' dan 'status'"
	;;
esac
