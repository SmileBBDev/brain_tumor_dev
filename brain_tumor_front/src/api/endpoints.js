// src/api/endpoints.js
export const EP = {
  orthanc: {
    uploadPatient: "/orthanc/upload-patient/",
    patients: "/orthanc/patients/",
    studies: "/orthanc/studies/",
    series: "/orthanc/series/",
    instances: "/orthanc/instances/",
    instanceFile: (orthancId) => `/orthanc/instances/${orthancId}/file/`,
    deletePatient: (patientId) => `/orthanc/patients/${patientId}/`,
    deleteStudy: (studyId) => `/orthanc/studies/${studyId}/`,
    deleteSeries: (seriesId) => `/orthanc/series/${seriesId}/`,
  },
};
