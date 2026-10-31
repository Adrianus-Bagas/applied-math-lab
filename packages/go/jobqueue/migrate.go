// Package jobqueue mengimplementasikan antrean job lab di PostgreSQL
// (FOR UPDATE SKIP LOCKED + LISTEN/NOTIFY), lihat LAB-ADR-003 dan LAB-ADR-010.
package jobqueue

import (
	"context"
	"database/sql"
	"embed"
	"fmt"
	"io/fs"

	"github.com/pressly/goose/v3"
)

//go:embed migrations/*.sql
var migrationsFS embed.FS

// VersionTable adalah tabel versi goose milik paket ini. Dipisahkan dari
// riwayat migrasi tiap proyek agar nomor versi tidak pernah bertabrakan.
const VersionTable = "jobqueue_goose_version"

// Migrate menerapkan semua migrasi antrean yang tertunda. Aman dijalankan ulang.
func Migrate(ctx context.Context, db *sql.DB) ([]*goose.MigrationResult, error) {
	p, err := newProvider(db)
	if err != nil {
		return nil, err
	}
	res, err := p.Up(ctx)
	if err != nil {
		return res, fmt.Errorf("jobqueue: migrate up: %w", err)
	}
	return res, nil
}

// Status melaporkan migrasi antrean mana yang sudah diterapkan atau tertunda.
func Status(ctx context.Context, db *sql.DB) ([]*goose.MigrationStatus, error) {
	p, err := newProvider(db)
	if err != nil {
		return nil, err
	}
	st, err := p.Status(ctx)
	if err != nil {
		return nil, fmt.Errorf("jobqueue: migrate status: %w", err)
	}
	return st, nil
}

func migrations() (fs.FS, error) {
	fsys, err := fs.Sub(migrationsFS, "migrations")
	if err != nil {
		return nil, fmt.Errorf("jobqueue: open embedded migrations: %w", err)
	}
	return fsys, nil
}

func newProvider(db *sql.DB) (*goose.Provider, error) {
	fsys, err := migrations()
	if err != nil {
		return nil, err
	}
	p, err := goose.NewProvider(goose.DialectPostgres, db, fsys,
		goose.WithTableName(VersionTable))
	if err != nil {
		return nil, fmt.Errorf("jobqueue: new goose provider: %w", err)
	}
	return p, nil
}
