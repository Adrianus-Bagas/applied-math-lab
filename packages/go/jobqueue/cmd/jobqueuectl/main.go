// Command jobqueuectl adalah alat pengembangan untuk antrean job lab.
//
// Pemakaian:
//
//	jobqueuectl migrate
//	jobqueuectl status
//	jobqueuectl enqueue <kind> <versi> '<payload-json>'
//	jobqueuectl show <id>
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"strconv"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	_ "github.com/jackc/pgx/v5/stdlib" // mendaftarkan driver database/sql bernama "pgx"

	"github.com/Adrianus-Bagas/applied-math-lab/contracts"
	"github.com/Adrianus-Bagas/applied-math-lab/packages/go/jobqueue"
)

const usage = "usage: jobqueuectl <migrate|status|enqueue <kind> <versi> <payload-json>|show <id>>"

func main() {
	if err := run(os.Args[1:]); err != nil {
		fmt.Fprintln(os.Stderr, "jobqueuectl:", err)
		os.Exit(1)
	}
}

func run(args []string) error {
	if len(args) == 0 {
		return errors.New(usage)
	}
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		return errors.New("DATABASE_URL is not set")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	switch args[0] {
	case "migrate", "status":
		if len(args) != 1 {
			return errors.New(usage)
		}
		return runMigrations(ctx, dsn, args[0])
	case "enqueue":
		if len(args) != 4 {
			return errors.New(usage)
		}
		return runEnqueue(ctx, dsn, args[1], args[2], args[3])
	case "show":
		if len(args) != 2 {
			return errors.New(usage)
		}
		return runShow(ctx, dsn, args[1])
	default:
		return fmt.Errorf("unknown command %q", args[0])
	}
}

func runMigrations(ctx context.Context, dsn, cmd string) error {
	db, err := sql.Open("pgx", dsn)
	if err != nil {
		return fmt.Errorf("open db: %w", err)
	}
	defer func() { _ = db.Close() }()

	if cmd == "status" {
		st, err := jobqueue.Status(ctx, db)
		if err != nil {
			return err
		}
		for _, s := range st {
			fmt.Printf("%05d %-8s %s\n", s.Source.Version, s.State, s.Source.Path)
		}
		return nil
	}

	res, err := jobqueue.Migrate(ctx, db)
	if err != nil {
		return err
	}
	if len(res) == 0 {
		fmt.Println("no pending migrations")
	}
	for _, r := range res {
		fmt.Printf("applied %05d %s (%s)\n", r.Source.Version, r.Source.Path, r.Duration)
	}
	return nil
}

func runEnqueue(ctx context.Context, dsn, kind, versionArg, payload string) error {
	version, err := strconv.Atoi(versionArg)
	if err != nil {
		return fmt.Errorf("versi harus bilangan bulat: %w", err)
	}
	reg, err := jobqueue.NewRegistry(contracts.Jobs, "jobs")
	if err != nil {
		return err
	}
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		return fmt.Errorf("pool: %w", err)
	}
	defer pool.Close()

	id, err := jobqueue.Enqueue(ctx, pool, reg, jobqueue.Job{
		Kind:          kind,
		SchemaVersion: version,
		Payload:       json.RawMessage(payload),
	})
	if err != nil {
		return err
	}
	fmt.Println(id)
	return nil
}

func runShow(ctx context.Context, dsn, id string) error {
	pool, err := pgxpool.New(ctx, dsn)
	if err != nil {
		return fmt.Errorf("pool: %w", err)
	}
	defer pool.Close()

	var (
		status           string
		attempts, maxAtt int32
		result, jobErr   *string // NULL di database menjadi nil
	)
	err = pool.QueryRow(ctx, `
		SELECT status, attempts, max_attempts, result::text, error::text
		FROM lab_jobs WHERE id = $1`, id,
	).Scan(&status, &attempts, &maxAtt, &result, &jobErr)
	if err != nil {
		return fmt.Errorf("show %s: %w", id, err)
	}
	fmt.Printf("status:   %s\nattempts: %d/%d\n", status, attempts, maxAtt)
	if result != nil {
		fmt.Printf("result:   %s\n", *result)
	}
	if jobErr != nil {
		fmt.Printf("error:    %s\n", *jobErr)
	}
	return nil
}
