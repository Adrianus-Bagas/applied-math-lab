package contracts

// Tes ini memastikan validator JSON Schema di Go (santhosh-tekuri/jsonschema v6, yang
// sama dengan jobqueue) bisa memakai skema hasil generate Pydantic dan setuju dengan
// Python untuk kasus struktural. Pemeriksaan antar-field (§1.7) hanya ada di Python.

import (
	"bytes"
	"encoding/json"
	"os"
	"testing"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

const (
	instanceSchemaPath = "mealops/instance.v1.schema.json"
	h5FixturePath      = "../datasets/mealops/fixtures/h5.instance.json"
)

func compileInstanceSchema(t *testing.T) *jsonschema.Schema {
	t.Helper()
	raw, err := os.ReadFile(instanceSchemaPath)
	if err != nil {
		t.Fatal(err)
	}
	doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(raw))
	if err != nil {
		t.Fatal(err)
	}
	c := jsonschema.NewCompiler()
	if err := c.AddResource("instance.v1.schema.json", doc); err != nil {
		t.Fatal(err)
	}
	sch, err := c.Compile("instance.v1.schema.json")
	if err != nil {
		t.Fatalf("skema tidak bisa dikompilasi: %v", err)
	}
	return sch
}

// loadH5 membaca fixture H5 sebagai nilai JSON generik (map[string]any).
// Setiap pemanggilan membaca ulang file, jadi setiap kasus bebas mengubahnya.
func loadH5(t *testing.T) map[string]any {
	t.Helper()
	raw, err := os.ReadFile(h5FixturePath)
	if err != nil {
		t.Fatal(err)
	}
	v, err := jsonschema.UnmarshalJSON(bytes.NewReader(raw))
	if err != nil {
		t.Fatal(err)
	}
	m, ok := v.(map[string]any)
	if !ok {
		t.Fatal("fixture bukan objek JSON")
	}
	return m
}

func field(m map[string]any, keys ...string) map[string]any {
	for _, k := range keys {
		m = m[k].(map[string]any)
	}
	return m
}

func TestInstanceSchemaH5(t *testing.T) {
	sch := compileInstanceSchema(t)

	cases := []struct {
		name  string
		edit  func(m map[string]any)
		valid bool
	}{
		{"h5 apa adanya", func(map[string]any) {}, true},
		{"production null", func(m map[string]any) { m["production"] = nil }, true},
		{"production diisi", func(m map[string]any) {
			m["production"] = map[string]any{
				"kitchen_start": json.Number("300"), "batch_capacity": json.Number("100"),
				"max_batches": json.Number("3"), "cook_fixed": json.Number("30"),
				"cook_per_1000": json.Number("200"), "pack_fixed": json.Number("10"),
				"pack_per_1000": json.Number("100"), "holding_max": json.Number("120"),
			}
		}, true},
		{"kapasitas 0", func(m map[string]any) { field(m, "fleet")["capacity"] = json.Number("0") }, false},
		{"jam 1440", func(m map[string]any) { field(m, "kitchen")["close"] = json.Number("1440") }, false},
		{"field asing", func(m map[string]any) { field(m, "fleet")["capasity"] = json.Number("100") }, false},
		{"versi lain", func(m map[string]any) { m["schema_version"] = "mealops.instance.v2" }, false},
		{"tanpa nodes", func(m map[string]any) { delete(m, "nodes") }, false},
		{"demand pecahan", func(m map[string]any) {
			m["nodes"].([]any)[0].(map[string]any)["demand"] = json.Number("2.5")
		}, false},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			m := loadH5(t)
			tc.edit(m)
			err := sch.Validate(m)
			if tc.valid && err != nil {
				t.Fatalf("seharusnya valid: %v", err)
			}
			if !tc.valid && err == nil {
				t.Fatal("seharusnya ditolak skema")
			}
		})
	}
}
