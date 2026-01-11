/**
 * DicomViewerPopup - DICOM 영상 조회 팝업
 * RISStudyDetailPage에서 '영상 조회' 버튼 클릭 시 세로 팝업으로 표시
 */
import { useState, useCallback } from 'react';
import UploadSection from './UploadSection';
import PacsSelector from './PacsSelector';
import ViewerSection from './ViewerSection';
import './DicomViewerPopup.css';

interface Selection {
  patientId?: string;
  studyId?: string;
  baseSeriesId?: string;
  baseSeriesName?: string;
  overlaySeriesId?: string;
  overlaySeriesName?: string;
}

interface OcsPatientInfo {
  ocsId: number;
  patientNumber: string;
  patientName: string;
}

// 업로드 결과 정보 (Orthanc 응답)
export interface UploadResult {
  patientId: string;
  studyUid: string;
  studyId: string;
  studyDescription: string;
  ocsId: number | null;
  uploaded: number;
  failedFiles: string[];
  orthancSeriesIds: string[];
}

interface DicomViewerPopupProps {
  open: boolean;
  onClose: () => void;
  ocsInfo?: OcsPatientInfo;
  onUploadComplete?: (result: UploadResult) => void;  // 업로드 완료 콜백
}

export default function DicomViewerPopup({ open, onClose, ocsInfo, onUploadComplete }: DicomViewerPopupProps) {
  const [selection, setSelection] = useState<Selection>({});
  const [refreshKey, setRefreshKey] = useState(0);

  const onUploaded = useCallback(async (result?: UploadResult) => {
    setRefreshKey((k) => k + 1);
    // 업로드 완료 시 부모 컴포넌트에 알림
    if (result && onUploadComplete) {
      onUploadComplete(result);
    }
  }, [onUploadComplete]);

  if (!open) return null;

  return (
    <div className="dicom-popup-overlay" onClick={onClose}>
      <div className="dicom-popup-container" onClick={(e) => e.stopPropagation()}>
        {/* 헤더 */}
        <header className="dicom-popup-header">
          <h2>DICOM 영상 조회</h2>
          <button className="dicom-popup-close" onClick={onClose}>
            &times;
          </button>
        </header>

        {/* 본문 */}
        <div className="dicom-popup-body">
          <aside className="dicom-popup-left">
            <div className="dicom-popup-stack">
              <UploadSection onUploaded={onUploaded} ocsInfo={ocsInfo} />
              <PacsSelector key={refreshKey} onChange={setSelection} ocsInfo={ocsInfo} />
            </div>
          </aside>

          <main className="dicom-popup-right">
            <ViewerSection
              baseSeriesId={selection.baseSeriesId}
              baseSeriesName={selection.baseSeriesName}
              overlaySeriesId={selection.overlaySeriesId}
              overlaySeriesName={selection.overlaySeriesName}
            />
          </main>
        </div>
      </div>
    </div>
  );
}
