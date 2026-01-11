// src/components/UploadSection.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import "./UploadSection.css";
import { uploadPatientFolder } from "../api/orthancApi";

// StudyInstanceUID 생성 함수
// 형식: OCS_{ocsId}_{patientId}_{timestamp}
// 예시: OCS_125_P001234_20260111143052
const generateStudyInstanceUID = (ocsId, patientId = "") => {
  const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
  return `OCS_${ocsId}_${patientId}_${timestamp}`;
};

export default function UploadSection({ onUploaded, ocsInfo }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [seriesPaths, setSeriesPaths] = useState([]);
  const [folderName, setFolderName] = useState(""); // Patient ID (MySQL patient_number)
  const [studyDescription, setStudyDescription] = useState(""); // Study Description
  const [studyInstanceUID, setStudyInstanceUID] = useState(""); // 자동 생성 UID
  const [uploadStatus, setUploadStatus] = useState(null);

  const fileInputRef = useRef(null);
  const [isUploading, setIsUploading] = useState(false);

  // ocsInfo가 전달되면 자동으로 PatientID 설정
  useEffect(() => {
    if (ocsInfo?.patientNumber) {
      setFolderName(ocsInfo.patientNumber);
    }
    if (ocsInfo?.ocsId) {
      setStudyInstanceUID(generateStudyInstanceUID(ocsInfo.ocsId, ocsInfo.patientNumber));
    }
  }, [ocsInfo]);

  const canUpload = useMemo(
    () => Boolean(folderName && selectedFiles.length && !isUploading),
    [folderName, selectedFiles, isUploading]
  );

  const onFolderChange = (e) => {
    const files = Array.from(e.target.files || []);

    if (!files.length) {
      setSelectedFiles([]);
      setSeriesPaths([]);
      return;
    }

    setSelectedFiles(files);

    const sp = files.map((f) => {
      const rel = f.webkitRelativePath || "";
      const parts = rel.split(/[\\/]/);
      return parts[1] || "";
    });
    setSeriesPaths(sp);

    if (!folderName && files.length) {
      const rel = files[0].webkitRelativePath || "";
      setFolderName(rel.split(/[\\/]/)[0]);
    }
  };

  const resetAll = ({ clearPatientId = false, clearStudyDesc = false } = {}) => {
    setSelectedFiles([]);
    setSeriesPaths([]);
    setUploadStatus(null);
    setIsUploading(false);

    if (clearPatientId) setFolderName("");
    if (clearStudyDesc) setStudyDescription("");

    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const onUpload = async () => {
    if (!folderName || !selectedFiles.length) return;

    setIsUploading(true);
    setUploadStatus({ type: "info", text: "업로드 중..." });

    // 업로드 시점에 새 UID 생성 (기존 UID 갱신)
    const newStudyUID = ocsInfo?.ocsId
      ? generateStudyInstanceUID(ocsInfo.ocsId, folderName)
      : studyInstanceUID;
    setStudyInstanceUID(newStudyUID);

    try {
      const result = await uploadPatientFolder({
        patientId: folderName,
        // Orthanc PatientName: 한글 인코딩 문제로 patient_id(영문/숫자) 사용
        // 한글 이름은 UI에서만 표시 (ocsInfo.patientName)
        patientName: folderName,
        studyDescription: studyDescription?.trim() || "",
        studyInstanceUID: newStudyUID,
        ocsId: ocsInfo?.ocsId,
        files: selectedFiles,
        seriesPaths,
      });

      setUploadStatus({ type: "success", text: "업로드 완료" });

      // 업로드 결과를 부모 컴포넌트에 전달
      if (typeof onUploaded === "function") {
        await onUploaded(result);
      }
    } catch (e) {
      console.error("업로드 실패", e);
      setUploadStatus({
        type: "error",
        text: e?.response?.data?.detail || e?.message || "업로드 실패",
      });
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <section className="uploadCard">
      <div className="uploadCardHeader">
        <h2 className="uploadTitle">폴더 업로드</h2>
        <p className="uploadHint">OCS 환자 정보 기반 자동 설정</p>
      </div>

      {/* OCS 연동 정보 표시 */}
      {ocsInfo && (
        <div className="ocsInfoBox">
          <div className="ocsInfoRow">
            <span className="ocsLabel">환자 이름 (DB)</span>
            <span className="ocsValue">{ocsInfo.patientName}</span>
          </div>
          <div className="ocsInfoRow">
            <span className="ocsLabel">OCS ID</span>
            <span className="ocsValue">{ocsInfo.ocsId}</span>
          </div>
          <div className="ocsInfoRow">
            <span className="ocsLabel">Orthanc Patient ID/Name</span>
            <span className="ocsValue mono">{folderName || "-"}</span>
          </div>
          <div className="ocsInfoRow">
            <span className="ocsLabel">Orthanc Study UID</span>
            <span className="ocsValue mono">{studyInstanceUID || "-"}</span>
          </div>
          <div className="ocsInfoRow hint">
            <span className="ocsHint">* Orthanc에는 영문 ID로 저장됩니다 (한글 미지원)</span>
          </div>
        </div>
      )}

      <div className="uploadGrid">
        {/* Patient ID - OCS 연동시 읽기 전용 */}
        <div className="field">
          <label className="label">Patient ID (Orthanc)</label>
          <input
            className="input"
            type="text"
            value={folderName}
            onChange={(e) => setFolderName(e.target.value)}
            placeholder="ex) P001234"
            disabled={isUploading || !!ocsInfo}
            readOnly={!!ocsInfo}
          />
          {ocsInfo && (
            <div className="metaRow subtle">
              <span>MySQL patient_number에서 자동 설정됨</span>
            </div>
          )}
        </div>

        {/* Study Description */}
        <div className="field">
          <label className="label">Study Description (영문만 입력)</label>
          <input
            className="input"
            type="text"
            value={studyDescription}
            onChange={(e) => setStudyDescription(e.target.value)}
            placeholder='ex) Brain MRI, CT Scan (English only)'
            disabled={isUploading}
          />
          <div className="metaRow subtle">
            <span>Orthanc 저장용 - 영문/숫자만 사용</span>
            <span>{studyDescription ? `입력: ${studyDescription}` : "미입력"}</span>
          </div>
        </div>

        {/* Study UID (자동 생성) */}
        <div className="field">
          <label className="label">Study UID (자동 생성)</label>
          <input
            className="input mono"
            type="text"
            value={studyInstanceUID || "(업로드 시 자동 생성)"}
            disabled
            readOnly
          />
          <div className="metaRow subtle">
            <span>StudyInstanceUID(0020,000D) - DICOM 고유 식별자</span>
          </div>
        </div>

        {/* Folder */}
        <div className="field">
          <label className="label">DICOM Folder</label>
          <input
            ref={fileInputRef}
            className="file"
            type="file"
            webkitdirectory="true"
            directory="true"
            multiple
            onChange={onFolderChange}
            disabled={isUploading}
          />
          <div className="metaRow">
            <span>선택 파일: {selectedFiles.length}</span>
            <span>SeriesPath 샘플: {seriesPaths[0] || "-"}</span>
          </div>
        </div>

        {/* actions */}
        <div className="actions">
          <button className="btn" onClick={onUpload} disabled={!canUpload}>
            {isUploading ? "업로드 중..." : "업로드"}
          </button>

          <button
            className="btn ghost"
            onClick={() => resetAll({ clearPatientId: true, clearStudyDesc: true })}
            disabled={isUploading}
            title="파일 선택/상태/PatientID/StudyDescription 모두 초기화"
          >
            전체 초기화
          </button>

          <button
            className="btn ghost"
            onClick={() => resetAll({ clearPatientId: false, clearStudyDesc: false })}
            disabled={isUploading}
            title="파일 선택/상태만 초기화 (PatientID/StudyDescription 유지)"
          >
            파일만 초기화
          </button>
        </div>

        {/* status */}
        {uploadStatus && <div className={`status ${uploadStatus.type}`}>{uploadStatus.text}</div>}
      </div>
    </section>
  );
}
