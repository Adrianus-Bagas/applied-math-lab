package buildinfo

import (
	"runtime/debug"
	"testing"
)

func TestParse(t *testing.T) {
	tests := []struct {
		name     string
		settings []debug.BuildSetting
		want     Info
	}{
		{
			name:     "tanpa info vcs",
			settings: nil,
			want:     Info{Version: "dev", Revision: "unknown", GoVersion: "go1.27"},
		},
		{
			name: "commit bersih",
			settings: []debug.BuildSetting{
				{Key: "vcs.revision", Value: "abc123"},
				{Key: "vcs.modified", Value: "false"},
			},
			want: Info{Version: "dev", Revision: "abc123", GoVersion: "go1.27"},
		},
		{
			name: "working tree kotor",
			settings: []debug.BuildSetting{
				{Key: "GOOS", Value: "linux"},
				{Key: "vcs.revision", Value: "abc123"},
				{Key: "vcs.modified", Value: "true"},
			},
			want: Info{Version: "dev", Revision: "abc123", Modified: true, GoVersion: "go1.27"},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := parse("dev", "go1.27", tt.settings)
			if got != tt.want {
				t.Errorf("parse() = %+v, want %+v", got, tt.want)
			}
		})
	}
}

func TestGetUsesPackageVersion(t *testing.T) {
	got := Get()
	if got.Version != Version {
		t.Errorf("Version = %q, want %q", got.Version, Version)
	}
	if got.Revision == "" {
		t.Error("Revision kosong; seharusnya hash commit atau \"unknown\"")
	}
}
