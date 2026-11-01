# syntax=docker/dockerfile:1

# ---------- Tahap 1: compile ----------
FROM golang:1.27-trixie AS build
WORKDIR /src

# Unduh dependensi dulu di layer terpisah: layer ini hanya dibangun ulang
# bila go.mod/go.sum berubah, bukan setiap kali kode berubah.
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download

# Hanya paket yang dibutuhkan hello-api dan jobqueuectl.
COPY contracts ./contracts
COPY packages/go ./packages/go
COPY services/hello/api ./services/hello/api

# VERSION diisi CI (L0.7) dengan tag atau SHA git; lokal tetap "dev".
ARG VERSION=dev
ENV CGO_ENABLED=0
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    LDFLAGS="-s -w -X github.com/Adrianus-Bagas/applied-math-lab/packages/go/buildinfo.Version=${VERSION}" \
 && go build -trimpath -buildvcs=false -ldflags="$LDFLAGS" -o /out/hello-api ./services/hello/api \
 && go build -trimpath -buildvcs=false -ldflags="$LDFLAGS" -o /out/jobqueuectl ./packages/go/jobqueue/cmd/jobqueuectl

# ---------- Tahap 2: runtime ----------
# distroless/static: tanpa shell, tanpa package manager, user nonroot (uid 65532).
FROM gcr.io/distroless/static-debian13:nonroot
COPY --from=build /out/ /usr/local/bin/
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD ["/usr/local/bin/hello-api", "healthcheck"]
ENTRYPOINT ["/usr/local/bin/hello-api"]
