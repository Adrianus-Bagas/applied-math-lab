// Package contracts menyematkan kontrak JSON Schema bersama milik lab, sehingga
// binary Go membawanya tanpa file tambahan saat runtime.
package contracts

import "embed"

// Jobs berisi skema payload job di jobs/<kind>.v<N>.schema.json.
//
//go:embed jobs/*.schema.json
var Jobs embed.FS
