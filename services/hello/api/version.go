package main

import (
	"encoding/json"
	"fmt"
	"io"

	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/buildinfo"
)

// versionMain dijalankan saat binary dipanggil sebagai `hello-api version`.
// Mencetak info build sebagai satu baris JSON ke stdout, berguna di image
// distroless yang tidak punya shell untuk memeriksa binary. Nilai kembali
// adalah exit code: 0 = berhasil, 1 = gagal menulis output.
func versionMain(stdout, stderr io.Writer) int {
	if err := json.NewEncoder(stdout).Encode(buildinfo.Get()); err != nil {
		// Bila menulis ke stderr pun gagal, tidak ada lagi yang bisa dilakukan.
		_, _ = fmt.Fprintln(stderr, "version:", err)
		return 1
	}
	return 0
}
