"use client";

import { useJobEvents } from "../lib/use-job-events";
import { progressStage, renderResult } from "../lib/hello-api";

export default function JobProgress({ id }: { id: string }) {
  const { job, connection } = useJobEvents(id);

  if (!job)
    return (
      <>
        <p>Job belum jalan</p>
      </>
    );

  return (
    <>
      {connection && <p>{connection}</p>}
      <p>{job.status}</p>
      {job.progress && progressStage(job.progress) && (
        <p>{progressStage(job.progress)}</p>
      )}
      <p>{renderResult(job.result)}</p>
    </>
  );
}
