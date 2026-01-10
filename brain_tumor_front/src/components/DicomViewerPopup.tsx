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

interface DicomViewerPopupProps {
  open: boolean;
  onClose: () => void;
}

export default function DicomViewerPopup({ open, onClose }: DicomViewerPopupProps) {
  const [selection, setSelection] = useState<Selection>({});
  const [refreshKey, setRefreshKey] = useState(0);

  const onUploaded = useCallback(async () => {
    setRefreshKey((k) => k + 1);
  }, []);

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
              <UploadSection onUploaded={onUploaded} />
              <PacsSelector key={refreshKey} onChange={setSelection} />
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
