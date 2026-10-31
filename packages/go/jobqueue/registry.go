package jobqueue

import (
	"bytes"
	"errors"
	"fmt"
	"io/fs"
	"path"
	"regexp"
	"strconv"

	"github.com/santhosh-tekuri/jsonschema/v6"
)

// ErrUnknownKind dikembalikan bila tidak ada skema untuk kind dan versi tersebut.
var ErrUnknownKind = errors.New("jobqueue: unknown job kind or schema version")

// ErrInvalidPayload membungkus setiap kegagalan validasi skema.
var ErrInvalidPayload = errors.New("jobqueue: invalid payload")

// <kind>.v<N>.schema.json, kind = segmen huruf kecil dipisah titik.
var schemaFileRE = regexp.MustCompile(
	`^([a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+)\.v([1-9][0-9]*)\.schema\.json$`)

type schemaKey struct {
	kind    string
	version int
}

// Registry menyimpan skema payload terkompilasi, dikunci oleh kind dan versi skema.
type Registry struct {
	schemas map[schemaKey]*jsonschema.Schema
}

// NewRegistry mengompilasi setiap file <kind>.v<N>.schema.json di direktori dir dari fsys.
func NewRegistry(fsys fs.FS, dir string) (*Registry, error) {
	names, err := fs.Glob(fsys, path.Join(dir, "*.schema.json"))
	if err != nil {
		return nil, fmt.Errorf("jobqueue: list schemas: %w", err)
	}
	if len(names) == 0 {
		return nil, fmt.Errorf("jobqueue: no schemas found in %q", dir)
	}

	c := jsonschema.NewCompiler()
	c.DefaultDraft(jsonschema.Draft2020)

	r := &Registry{schemas: make(map[schemaKey]*jsonschema.Schema, len(names))}
	for _, name := range names {
		base := path.Base(name)
		m := schemaFileRE.FindStringSubmatch(base)
		if m == nil {
			return nil, fmt.Errorf("jobqueue: %q does not match <kind>.v<N>.schema.json", base)
		}
		version, err := strconv.Atoi(m[2])
		if err != nil {
			return nil, fmt.Errorf("jobqueue: bad version in %q: %w", base, err)
		}

		raw, err := fs.ReadFile(fsys, name)
		if err != nil {
			return nil, fmt.Errorf("jobqueue: read %q: %w", name, err)
		}
		doc, err := jsonschema.UnmarshalJSON(bytes.NewReader(raw))
		if err != nil {
			return nil, fmt.Errorf("jobqueue: parse %q: %w", name, err)
		}
		url := "file:///contracts/" + name
		if err := c.AddResource(url, doc); err != nil {
			return nil, fmt.Errorf("jobqueue: add %q: %w", name, err)
		}
		sch, err := c.Compile(url)
		if err != nil {
			return nil, fmt.Errorf("jobqueue: compile %q: %w", name, err)
		}
		r.schemas[schemaKey{kind: m[1], version: version}] = sch
	}
	return r, nil
}

// Validate memeriksa payload terhadap skema yang terdaftar untuk kind pada versi tersebut.
func (r *Registry) Validate(kind string, version int, payload []byte) error {
	sch, ok := r.schemas[schemaKey{kind: kind, version: version}]
	if !ok {
		return fmt.Errorf("%w: %s v%d", ErrUnknownKind, kind, version)
	}
	inst, err := jsonschema.UnmarshalJSON(bytes.NewReader(payload))
	if err != nil {
		return fmt.Errorf("%w: not valid JSON: %w", ErrInvalidPayload, err)
	}
	if err := sch.Validate(inst); err != nil {
		return fmt.Errorf("%w: %w", ErrInvalidPayload, err)
	}
	return nil
}
