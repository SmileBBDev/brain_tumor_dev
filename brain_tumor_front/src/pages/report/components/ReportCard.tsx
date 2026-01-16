/**
 * 보고서 카드 컴포넌트
 * - 썸네일 + 정보를 카드 형태로 표시
 * - OCS_RIS: 4채널 DICOM 이미지 썸네일 (T1, T1C, T2, FLAIR)
 */
import { useState, useEffect } from 'react';
import type { UnifiedReport, ChannelThumbnail } from '@/services/report.api';
import './ReportCard.css';

// 아이콘 매핑
const ICON_MAP: Record<string, string> = {
  mri: '\ud83e\udde0',      // 뇌
  brain: '\ud83e\udde0',    // 뇌
  dna: '\ud83e\uddec',      // DNA
  protein: '\ud83e\uddea',  // 시험관
  lab: '\ud83e\uddea',      // 시험관
  document: '\ud83d\udcc4', // 문서
  ai: '\ud83e\udd16',       // 로봇
  multimodal: '\ud83d\udd2c', // 현미경
};

// 채널별 색상
const CHANNEL_COLORS: Record<string, string> = {
  T1: '#3b82f6',    // blue
  T1C: '#ef4444',   // red (contrast)
  T2: '#10b981',    // green
  FLAIR: '#f59e0b', // amber
};

interface ReportCardProps {
  report: UnifiedReport;
  onClick: () => void;
}

export default function ReportCard({ report, onClick }: ReportCardProps) {
  const { thumbnail, type, type_display, sub_type, patient_name, patient_number, title, result_display, completed_at, status_display } = report;
  const [imageErrors, setImageErrors] = useState<Set<string>>(new Set());

  // 날짜 포맷
  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  // 타입별 색상
  const getTypeColor = () => {
    if (type.startsWith('OCS_RIS')) return '#3b82f6'; // blue
    if (type.startsWith('OCS_LIS')) return '#10b981'; // green
    if (type.startsWith('AI_M1')) return '#ef4444';   // red
    if (type.startsWith('AI_MG')) return '#10b981';   // green
    if (type.startsWith('AI_MM')) return '#6366f1';   // indigo
    if (type === 'FINAL') return '#8b5cf6';           // purple
    return '#6b7280';
  };

  // 결과 플래그 색상
  const getResultClass = () => {
    if (result_display === '정상' || result_display === '종양 미발견') return 'result-normal';
    if (result_display === '비정상' || result_display.includes('종양 발견')) return 'result-abnormal';
    return 'result-default';
  };

  // 이미지 에러 핸들러
  const handleImageError = (channel: string) => {
    setImageErrors(prev => new Set(prev).add(channel));
  };

  // DICOM 멀티채널 썸네일 렌더링 (4채널 그리드)
  const renderDicomMultiThumbnail = (channels: ChannelThumbnail[]) => {
    return (
      <div className="thumbnail-dicom-multi">
        {channels.slice(0, 4).map((ch) => (
          <div key={ch.channel} className="dicom-channel">
            {imageErrors.has(ch.channel) ? (
              <div
                className="channel-fallback"
                style={{ backgroundColor: CHANNEL_COLORS[ch.channel] || '#6b7280' }}
              >
                <span className="channel-label">{ch.channel}</span>
              </div>
            ) : (
              <>
                <img
                  src={ch.url}
                  alt={ch.description}
                  onError={() => handleImageError(ch.channel)}
                  loading="lazy"
                />
                <span
                  className="channel-badge"
                  style={{ backgroundColor: CHANNEL_COLORS[ch.channel] || '#6b7280' }}
                >
                  {ch.channel}
                </span>
              </>
            )}
          </div>
        ))}
      </div>
    );
  };

  // 썸네일 렌더링
  const renderThumbnail = () => {
    // DICOM 멀티채널 (4채널 그리드)
    if (thumbnail.type === 'dicom_multi' && thumbnail.channels && thumbnail.channels.length > 0) {
      return renderDicomMultiThumbnail(thumbnail.channels);
    }

    // DICOM 단일 (동적 로드 필요 시)
    if (thumbnail.type === 'dicom' && thumbnail.thumbnails_url) {
      // 아직 channels 정보가 없으면 아이콘 표시 (API에서 동적 로드 필요)
      return (
        <div className="thumbnail-icon" style={{ backgroundColor: '#3b82f6' }}>
          <span className="icon">{ICON_MAP.mri}</span>
          <span className="label">MRI</span>
        </div>
      );
    }

    if (thumbnail.type === 'image' && thumbnail.url) {
      return (
        <div className="thumbnail-image">
          <img src={thumbnail.url} alt="thumbnail" />
        </div>
      );
    }

    if (thumbnail.type === 'segmentation') {
      // 세그멘테이션 미리보기 (간단한 아이콘으로 대체)
      return (
        <div className="thumbnail-segmentation" style={{ backgroundColor: thumbnail.color || '#ef4444' }}>
          <span className="icon">{ICON_MAP.brain}</span>
          <span className="label">3D MRI</span>
        </div>
      );
    }

    if (thumbnail.type === 'chart') {
      return (
        <div className="thumbnail-chart" style={{ backgroundColor: thumbnail.color || '#10b981' }}>
          <span className="icon">{ICON_MAP[thumbnail.icon || 'dna']}</span>
          <span className="label">Gene</span>
        </div>
      );
    }

    // 기본 아이콘
    return (
      <div className="thumbnail-icon" style={{ backgroundColor: thumbnail.color || getTypeColor() }}>
        <span className="icon">{ICON_MAP[thumbnail.icon || 'document']}</span>
      </div>
    );
  };

  return (
    <div className="report-card" onClick={onClick}>
      {/* 썸네일 영역 */}
      <div className="card-thumbnail">
        {renderThumbnail()}
        <span className="type-badge" style={{ backgroundColor: getTypeColor() }}>
          {type_display}
        </span>
      </div>

      {/* 정보 영역 */}
      <div className="card-content">
        <div className="card-header">
          <span className="sub-type">{sub_type}</span>
          <span className={`result-badge ${getResultClass()}`}>{result_display}</span>
        </div>

        <h3 className="card-title">{title}</h3>

        <div className="card-patient">
          <span className="patient-name">{patient_name || '-'}</span>
          <span className="patient-number">{patient_number}</span>
        </div>

        <div className="card-footer">
          <span className="date">{formatDate(completed_at)}</span>
          <span className="status">{status_display}</span>
        </div>
      </div>
    </div>
  );
}
