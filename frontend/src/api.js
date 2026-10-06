const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request(path, options = {}) {
  let response;

  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    throw new Error(
      "The analytics API is unavailable. Check that the backend is running."
    );
  }

  const payload = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      payload.detail || "The analytics API returned an error."
    );
  }

  return payload;
}


export function uploadDataset(file) {
  const formData = new FormData();

  formData.append("file", file);

  return request("/datasets/upload", {
    method: "POST",
    body: formData,
  });
}


export function loadDatasetOverview(datasetVersionId) {
  return Promise.all([
    request(
      `/datasets/${datasetVersionId}/validate`,
      { method: "POST" }
    ),
    request(
      `/datasets/${datasetVersionId}/pii-scan`,
      { method: "POST" }
    ),
    request(
      `/datasets/${datasetVersionId}/profile`
    ),
    request(
      `/datasets/${datasetVersionId}/semantics`
    ),
  ]).then(
    ([validation, pii, profile, semantics]) => ({
      validation: validation.validation,
      pii: pii.pii_scan,
      profile: profile.profile,
      semantics: semantics.semantics,
    })
  );
}


export function loadDatasetPlan(datasetVersionId) {
  return request(
    `/datasets/${datasetVersionId}/plan`
  ).then(
    (payload) => payload.analytics_plan
  );
}


export function analyzeDataset(datasetVersionId) {
  return request(
    `/datasets/${datasetVersionId}/analyze`,
    {
      method: "POST",
    }
  );
}


export function loadAnalysisRun(analysisRunId) {
  return request(
    `/analysis-runs/${analysisRunId}`
  );
}


export function loadAnalysisRuns(datasetVersionId) {
  return request(
    `/analysis-runs/dataset-version/${datasetVersionId}`
  );
}

export async function downloadAnalysisRunExport(
  analysisRunId,
  format,
) {
  let response;

  try {
    response = await fetch(
      `${API_BASE_URL}/analysis-runs/${analysisRunId}/export/${format}`
    );
  } catch {
    throw new Error(
      "The analytics API is unavailable. Check that the backend is running."
    );
  }

  if (!response.ok) {
    const payload =
      await response
        .json()
        .catch(() => ({}));

    throw new Error(
      payload.detail ||
      "The report could not be exported."
    );
  }

  const blob =
    await response.blob();

  const disposition =
    response.headers.get(
      "content-disposition"
    );

  const filenameMatch =
    disposition?.match(
      /filename="?([^"]+)"?/i
    );

  const filename =
    filenameMatch?.[1] ??
    `signal-ledger-${analysisRunId}.${format}`;

  const url =
    URL.createObjectURL(blob);

  const anchor =
    document.createElement("a");

  anchor.href = url;
  anchor.download = filename;

  document.body.appendChild(
    anchor
  );

  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(url);

  return filename;
}
