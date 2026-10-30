// Package buildinfo melaporkan versi build dari binary yang sedang berjalan.
package buildinfo

import "runtime/debug"

// Version dapat diisi saat build, misalnya di CI:
//
//	go build -ldflags "-X github.com/Adrianus-Bagas/applied-math-lab/packages/go/buildinfo.Version=v0.1.0"
var Version = "dev"

// Info adalah ringkasan build yang aman ditampilkan di endpoint /healthz.
type Info struct {
	Version   string `json:"version"`
	Revision  string `json:"revision"`
	Modified  bool   `json:"modified"`
	GoVersion string `json:"go_version"`
}

// Get membaca metadata build yang disematkan oleh toolchain Go.
func Get() Info {
	bi, ok := debug.ReadBuildInfo()
	if !ok {
		return parse(Version, "", nil)
	}
	return parse(Version, bi.GoVersion, bi.Settings)
}

// parse dipisah dari Get supaya logikanya bisa diuji tanpa bergantung
// pada cara binary ini di-build.
func parse(version, goVersion string, settings []debug.BuildSetting) Info {
	info := Info{Version: version, Revision: "unknown", GoVersion: goVersion}
	for _, s := range settings {
		switch s.Key {
		case "vcs.revision":
			info.Revision = s.Value
		case "vcs.modified":
			info.Modified = s.Value == "true"
		}
	}
	return info
}
