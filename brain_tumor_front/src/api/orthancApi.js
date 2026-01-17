// src/api/orthancApi.js
import { http } from "./http";
import { EP } from "./endpoints";

export async function uploadPatientFolder({
  patientId,
  patientName,
  studyDescription,
  studyInstanceUID,
  ocsId,
  files,
  seriesPaths,
}) {
  const fd = new FormData();

  fd.append("patient_id", patientId);
  fd.append("patient_name", patientName || patientId);  // 환자 이름 추가
  fd.append("study_description", studyDescription || "");
  if (studyInstanceUID) fd.append("study_instance_uid", studyInstanceUID);
  if (ocsId) fd.append("ocs_id", String(ocsId));

  for (const f of files) fd.append("files", f);
  for (const sp of seriesPaths) fd.append("series_path", sp);

  // ✅ 올바른 endpoint 키 사용
  const res = await http.post(EP.orthanc.uploadPatient, fd, {
    headers: { "Content-Type": "multipart/form-data" },
  });

  return res.data;
}

export async function getPatients() {
  const res = await http.get(EP.orthanc.patients);
  return res.data || [];
}

export async function getStudies(patientOrthancId) {
  const res = await http.get(EP.orthanc.studies, {
    params: { patient_id: patientOrthancId },
  });
  return res.data || [];
}

export async function getSeries(studyOrthancId) {
  const res = await http.get(EP.orthanc.series, {
    params: { study_id: studyOrthancId },
  });
  return res.data || [];
}

export async function getInstances(seriesOrthancId) {
  const res = await http.get(EP.orthanc.instances, {
    params: { series_id: seriesOrthancId },
  });
  return res.data || [];
}

export function getInstanceFileUrl(orthancId) {
  const base =
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api";
  return `${base}${EP.orthanc.instanceFile(orthancId)}`;
}

// Orthanc Study 삭제
export async function deleteStudy(studyOrthancId) {
  const res = await http.delete(EP.orthanc.deleteStudy(studyOrthancId));
  return res.data;
}
