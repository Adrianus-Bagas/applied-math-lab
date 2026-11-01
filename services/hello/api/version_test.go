package main

import (
	"bytes"
	"encoding/json"
	"os/exec"
	"path/filepath"
	"testing"

	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/buildinfo"
)

// versionVar HARUS sama persis dengan target -X di services/hello/api/Dockerfile.
const versionVar = "github.com/Adrianus-Bagas/applied-math-lab/packages/go/buildinfo.Version"

func TestVersionMain(t *testing.T) {
	var stdout, stderr bytes.Buffer
	if code := versionMain(&stdout, &stderr); code != 0 {
		t.Fatalf("exit code = %d, stderr = %q", code, stderr.String())
	}
	var got buildinfo.Info
	if err := json.Unmarshal(stdout.Bytes(), &got); err != nil {
		t.Fatalf("output bukan JSON valid: %v (%q)", err, stdout.String())
	}
	if got.Version != buildinfo.Version {
		t.Errorf("Version = %q, want %q", got.Version, buildinfo.Version)
	}
}

// TestVersionLdflags membangun binary sungguhan dengan -X seperti di Dockerfile,
// lalu menjalankan `version`. Linker Go diam saja bila target -X tidak ada
// (path salah ketik atau paket dibuang karena tidak dipakai), jadi satu-satunya
// cara membuktikan -X bekerja adalah membangun dan menjalankan binary-nya.
func TestVersionLdflags(t *testing.T) {
	if testing.Short() {
		t.Skip("membangun binary; dilewati di mode -short")
	}
	goBin, err := exec.LookPath("go")
	if err != nil {
		t.Skip("toolchain go tidak ada di PATH")
	}

	const want = "sha-uji1234"
	bin := filepath.Join(t.TempDir(), "hello-api")
	build := exec.Command(goBin, "build", "-trimpath",
		"-ldflags", "-X "+versionVar+"="+want,
		"-o", bin, ".")
	if out, err := build.CombinedOutput(); err != nil {
		t.Fatalf("go build gagal: %v\n%s", err, out)
	}

	out, err := exec.Command(bin, "version").Output()
	if err != nil {
		t.Fatalf("menjalankan `hello-api version` gagal: %v", err)
	}
	var got buildinfo.Info
	if err := json.Unmarshal(out, &got); err != nil {
		t.Fatalf("output bukan JSON valid: %v (%q)", err, out)
	}
	if got.Version != want {
		t.Errorf("Version = %q, want %q: target -X tidak sampai ke binary", got.Version, want)
	}
}
