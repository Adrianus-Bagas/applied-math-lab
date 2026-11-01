"use client";

import JobProgress from "@/src/components/JobProgress";
import { validPayload } from "@/src/constants";
import { createHelloJob, HelloApiError } from "@/src/lib/hello-api";
import { useState } from "react";

export default function HelloPage() {
  const [jobId, setJobId] = useState<string | null>("");
  const [isLoadingJob, setIsLoadingJob] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const handleGetJob = async () => {
    setIsLoadingJob(true);
    try {
      const result = await createHelloJob(validPayload);
      setJobId(result.id);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setError(`Payload bukan JSON valid: ${err.message}`);
      } else if (err instanceof HelloApiError && err.status === 422) {
        setError(`Payload ditolak skema: ${err.message}`);
      } else if (err instanceof HelloApiError) {
        setError(`Server error (${err.status}): ${err.message}`);
      } else {
        setError(err instanceof Error ? err.message : String(err)); // mis. jaringan putus
      }
    } finally {
      setIsLoadingJob(false);
    }
  };

  return (
    <>
      <p>payload</p>
      <textarea disabled value={JSON.stringify(validPayload, null, 2)} />
      <br />
      <button disabled={isLoadingJob} onClick={() => handleGetJob()}>
        Ajukan
      </button>
      {jobId && <JobProgress id={jobId} key={jobId} />}
      {error && <p>Error: {error}</p>}
    </>
  );
}
