-- +goose Up
-- Setiap perubahan status atau progres job memicu NOTIFY lab_job_progress
-- (payload: id job) saat transaksi di-commit. Pendengar (SSE) membaca ulang
-- tabel; notifikasi hanya petunjuk (LAB-ADR-010).
-- +goose StatementBegin
CREATE FUNCTION lab_jobs_notify_progress() RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    PERFORM pg_notify('lab_job_progress', NEW.id::text);
    RETURN NULL; -- trigger AFTER: nilai kembalian diabaikan
END;
$$;
-- +goose StatementEnd

-- WHEN menyaring UPDATE yang tidak benar-benar mengubah nilai (mis. heartbeat).
CREATE TRIGGER lab_jobs_progress_notify
    AFTER UPDATE OF status, progress ON lab_jobs
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status
          OR OLD.progress IS DISTINCT FROM NEW.progress)
    EXECUTE FUNCTION lab_jobs_notify_progress();

-- +goose Down
DROP TRIGGER lab_jobs_progress_notify ON lab_jobs;
DROP FUNCTION lab_jobs_notify_progress();
