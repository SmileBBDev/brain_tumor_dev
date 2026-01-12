// src/components/UploadSection.jsx
import React, { useEffect, useMemo, useRef, useState } from "react";
import "./UploadSection.css";
import { uploadPatientFolder, deleteStudy } from "../api/orthancApi";

// StudyInstanceUID 생성 함수
// 형식: OCS_{ocsId}_{patientId}_{timestamp}
// 예시: OCS_125_P001234_20260111143052
const generateStudyInstanceUID = (ocsId, patientId = "") => {
  const timestamp = new Date().toISOString().replace(/[-:T.Z]/g, "").slice(0, 14);
  return `OCS_${ocsId}_${patientId}_${timestamp}`;
};

export default function UploadSection({ onUploaded, ocsInfo, existingStudy, onStudyDeleted }) {
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [seriesPaths, setSeriesPaths] = useState([]);
  const [folderName, setFolderName] = useState(""); // Patient ID (MySQL patient_number)
  const [studyDescription, setStudyDescription] = useState(""); // Study Description
  const [descWarning, setDescWarning] = useState(""); // Study Description 한글 경고
  const [studyInstanceUID, setStudyInstanceUID] = useState(""); // 자동 생성 UID
  const [uploadStatus, setUploadStatus] = useState(null);
  const [isDeleting, setIsDeleting] = useState(false); // Orthanc Study 삭제 중

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

  // 기존 Study가 있으면 업로드 비활성화 (삭제 후 업로드 가능)
  const hasExistingStudy = Boolean(existingStudy?.orthanc_study_id);

  const canUpload = useMemo(
    () => Boolean(folderName && selectedFiles.length && !isUploading && !hasExistingStudy),
    [folderName, selectedFiles, isUploading, hasExistingStudy]
  );

  const onFolderChange = (e) => {
    const files = Array.from(e.target.files || []);

    if (!files.length) {
      setSelectedFiles([]);
      setSeriesPaths([]);
      setUploadStatus(null);
      return;
    }

    // DICOM/NIfTI 파일만 필터링 (확장자 체크)
    const validExtensions = ['.dcm', '.dicom', '.nii', '.nii.gz'];
    const dicomFiles = [];
    const invalidFiles = [];

    files.forEach((f) => {
      const name = f.name.toLowerCase();
      // 확장자가 없거나 DICOM 파일인 경우 (DICOM은 확장자 없는 경우도 있음)
      const isValid = validExtensions.some(ext => name.endsWith(ext)) ||
                      !name.includes('.') ||  // 확장자 없는 파일 (DICOM일 수 있음)
                      name.endsWith('.dcm');
      if (isValid) {
        dicomFiles.push(f);
      } else {
        invalidFiles.push(f.name);
      }
    });

    // 유효하지 않은 파일이 있으면 경고 표시
    if (invalidFiles.length > 0) {
      setUploadStatus({
        type: "warning",
        text: `DICOM/NIfTI가 아닌 파일 ${invalidFiles.length}개 제외됨: ${invalidFiles.slice(0, 3).join(', ')}${invalidFiles.length > 3 ? '...' : ''}`
      });
    } else {
      setUploadStatus(null);
    }

    setSelectedFiles(dicomFiles);

    // Series 경로 추출 - 폴더 구조에 따라 적절한 레벨 선택
    // 예: "mri/T1/file.dcm" -> "T1" (parts[1])
    // 예: "환자데이터/TCGA-CS-4944/mri/T1/file.dcm" -> "T1" (마지막에서 두 번째)
    const sp = dicomFiles.map((f) => {
      const rel = f.webkitRelativePath || "";
      const parts = rel.split(/[\\/]/);
      // 파일명을 제외한 마지막 폴더가 시리즈 폴더
      // parts: ["mri", "T1", "file.dcm"] -> "T1"
      // parts: ["환자데이터", "TCGA-CS-4944", "mri", "T1", "file.dcm"] -> "T1"
      const folderIndex = parts.length - 2; // 파일명 바로 위 폴더
      return folderIndex >= 0 ? parts[folderIndex] : parts[0] || "";
    });
    setSeriesPaths(sp);

    // 루트 폴더명 설정 (Patient ID로 사용하지 않음, ocsInfo 사용)
    if (!folderName && dicomFiles.length) {
      const rel = dicomFiles[0].webkitRelativePath || "";
      setFolderName(rel.split(/[\\/]/)[0]);
    }

    // 시리즈별 파일 수 로그 (디버깅용)
    const seriesCounts = sp.reduce((acc, s) => {
      acc[s] = (acc[s] || 0) + 1;
      return acc;
    }, {});
    console.log("Series breakdown:", seriesCounts);
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

  // 기존 Study 삭제 (Orthanc에서 삭제)
  const handleDeleteExistingStudy = async () => {
    if (!existingStudy?.orthanc_study_id) {
      alert("삭제할 Study 정보가 없습니다.");
      return;
    }

    if (!confirm("기존 업로드된 DICOM 영상을 Orthanc에서 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")) {
      return;
    }

    setIsDeleting(true);
    setUploadStatus({ type: "info", text: "Orthanc에서 삭제 중..." });

    try {
      await deleteStudy(existingStudy.orthanc_study_id);
      setUploadStatus({ type: "success", text: "기존 영상이 삭제되었습니다. 새로 업로드할 수 있습니다." });

      // 부모 컴포넌트에 삭제 완료 알림 (worker_result에서 orthanc/dicom 정보 제거)
      if (typeof onStudyDeleted === "function") {
        await onStudyDeleted();
      }
    } catch (e) {
      console.error("Study 삭제 실패", e);
      setUploadStatus({
        type: "error",
        text: e?.response?.data?.detail || e?.message || "삭제 실패",
      });
    } finally {
      setIsDeleting(false);
    }
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

      {/* 기존 업로드된 Study 정보 표시 */}
      {existingStudy && existingStudy.orthanc_study_id && (
        <div className="existingStudyBox">
          <div className="existingStudyHeader">
            <span className="existingStudyTitle">기존 업로드 정보</span>
            <button
              className="btn btnDelete"
              onClick={handleDeleteExistingStudy}
              disabled={isDeleting || isUploading}
              title="Orthanc에서 영상 삭제"
            >
              {isDeleting ? "삭제 중..." : "삭제"}
            </button>
          </div>
          <div className="existingStudyContent">
            <div className="existingStudyRow">
              <span className="existingLabel">Study UID</span>
              <span className="existingValue mono">{existingStudy.study_uid || "-"}</span>
            </div>
            <div className="existingStudyRow">
              <span className="existingLabel">Orthanc Study ID</span>
              <span className="existingValue mono">{existingStudy.orthanc_study_id || "-"}</span>
            </div>
            {existingStudy.series_count > 0 && (
              <div className="existingStudyRow">
                <span className="existingLabel">시리즈 / 인스턴스</span>
                <span className="existingValue">
                  {existingStudy.series_count}개 시리즈 / {existingStudy.instance_count || 0}장
                </span>
              </div>
            )}
            {existingStudy.uploaded_at && (
              <div className="existingStudyRow">
                <span className="existingLabel">업로드 일시</span>
                <span className="existingValue">
                  {new Date(existingStudy.uploaded_at).toLocaleString("ko-KR")}
                </span>
              </div>
            )}
          </div>
          <div className="existingStudyHint">
            * 새로 업로드하려면 기존 영상을 먼저 삭제하세요
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
            className={`input ${descWarning ? "input-warning" : ""}`}
            type="text"
            value={studyDescription}
            onChange={(e) => {
              const val = e.target.value;
              setStudyDescription(val);
              // 한글(가-힣) 또는 비-ASCII 문자 감지
              const hasNonAscii = /[^\x00-\x7F]/.test(val);
              if (hasNonAscii) {
                setDescWarning("한글/특수문자는 저장 시 제거됩니다. 영문만 입력하세요.");
              } else {
                setDescWarning("");
              }
            }}
            placeholder='ex) Brain MRI, CT Scan (English only)'
            disabled={isUploading}
          />
          {descWarning && (
            <div className="metaRow warning">
              <span>{descWarning}</span>
            </div>
          )}
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
          </div>
          {/* 시리즈별 파일 수 표시 */}
          {seriesPaths.length > 0 && (
            <div className="seriesBreakdown">
              <span className="seriesLabel">시리즈 구성:</span>
              {Object.entries(
                seriesPaths.reduce((acc, s) => {
                  acc[s] = (acc[s] || 0) + 1;
                  return acc;
                }, {})
              ).map(([series, count]) => (
                <span key={series} className="seriesTag">
                  {series}: {count}장
                </span>
              ))}
            </div>
          )}
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
