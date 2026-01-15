/**
 * AI Viewer Panel
 * - AI 분석 결과 시각화 이미지를 보여주는 뷰어
 * - 전체화면 모드 지원
 */
import { useState, useEffect } from 'react';
import { getPatientAIRequests } from '@/services/ai.api';
import type { AIInferenceRequest } from '@/services/ai.api';
import './AIViewerPanel.css';

interface AIViewerPanelProps {
  ocsId: number;
  patientId?: number;
}

export default function AIViewerPanel({ ocsId, patientId }: AIViewerPanelProps) {
  const [aiRequest, setAiRequest] = useState<AIInferenceRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [fullscreen, setFullscreen] = useState(false);

  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

  useEffect(() => {
    const fetchAIResult = async () => {
      if (!patientId) {
        setLoading(false);
        return;
      }

      setLoading(true);
      try {
        const requests = await getPatientAIRequests(patientId);
        const matchingRequest = requests
          .filter(req => req.ocs_references.includes(ocsId) && req.has_result)
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

        setAiRequest(matchingRequest || null);
      } catch (error) {
        console.error('Failed to fetch AI result:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAIResult();
  }, [ocsId, patientId]);

  const visualizationPaths = aiRequest?.result?.visualization_paths || [];

  if (loading) {
    return (
      <div className="ai-viewer-panel">
        <div className="ai-viewer-header">
          <h3>AI 분석 뷰어</h3>
        </div>
        <div className="ai-viewer-loading">
          <div className="spinner"></div>
          <span>로딩 중...</span>
        </div>
      </div>
    );
  }

  if (!aiRequest || visualizationPaths.length === 0) {
    return (
      <div className="ai-viewer-panel">
        <div className="ai-viewer-header">
          <h3>AI 분석 뷰어</h3>
        </div>
        <div className="ai-viewer-empty">
          <div className="empty-icon">🔬</div>
          <span>AI 분석 결과 이미지 없음</span>
          <p>이 검사에 대한 AI 분석 이미지가 없습니다.</p>
        </div>
      </div>
    );
  }

  const currentImage = visualizationPaths[selectedImageIndex];

  return (
    <>
      <div className="ai-viewer-panel">
        <div className="ai-viewer-header">
          <h3>AI 분석 뷰어</h3>
          <div className="ai-viewer-info">
            <span className="model-badge">{aiRequest.model_name}</span>
            <span className="image-count">{visualizationPaths.length}개 이미지</span>
          </div>
        </div>

        <div className="ai-viewer-content">
          {/* 메인 이미지 영역 */}
          <div className="ai-viewer-main">
            <img
              src={`${baseUrl}${currentImage}`}
              alt={`AI 분석 결과 ${selectedImageIndex + 1}`}
              onClick={() => setFullscreen(true)}
              onError={(e) => {
                (e.target as HTMLImageElement).src = '/placeholder-image.png';
              }}
            />
            <div className="image-controls">
              <button
                className="nav-btn prev"
                onClick={() => setSelectedImageIndex(Math.max(0, selectedImageIndex - 1))}
                disabled={selectedImageIndex === 0}
              >
                &lt;
              </button>
              <span className="image-indicator">
                {selectedImageIndex + 1} / {visualizationPaths.length}
              </span>
              <button
                className="nav-btn next"
                onClick={() => setSelectedImageIndex(Math.min(visualizationPaths.length - 1, selectedImageIndex + 1))}
                disabled={selectedImageIndex === visualizationPaths.length - 1}
              >
                &gt;
              </button>
              <button className="fullscreen-btn" onClick={() => setFullscreen(true)} title="전체화면">
                ⛶
              </button>
            </div>
          </div>

          {/* 썸네일 목록 */}
          {visualizationPaths.length > 1 && (
            <div className="ai-viewer-thumbnails">
              {visualizationPaths.map((path, idx) => (
                <div
                  key={idx}
                  className={`thumbnail-item ${idx === selectedImageIndex ? 'active' : ''}`}
                  onClick={() => setSelectedImageIndex(idx)}
                >
                  <img
                    src={`${baseUrl}${path}`}
                    alt={`썸네일 ${idx + 1}`}
                    onError={(e) => {
                      (e.target as HTMLImageElement).style.display = 'none';
                    }}
                  />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI 결과 요약 정보 */}
        {aiRequest.result && (
          <div className="ai-viewer-summary">
            <div className="summary-item">
              <label>신뢰도</label>
              <span>{aiRequest.result.confidence_score ?? '-'}%</span>
            </div>
            <div className="summary-item">
              <label>검토 상태</label>
              <span className={`review-status ${aiRequest.result.review_status}`}>
                {aiRequest.result.review_status_display}
              </span>
            </div>
            <div className="summary-item">
              <label>분석 완료</label>
              <span>{aiRequest.completed_at ? new Date(aiRequest.completed_at).toLocaleString('ko-KR') : '-'}</span>
            </div>
          </div>
        )}
      </div>

      {/* 전체화면 모달 */}
      {fullscreen && (
        <div className="ai-viewer-fullscreen" onClick={() => setFullscreen(false)}>
          <div className="fullscreen-content" onClick={(e) => e.stopPropagation()}>
            <button className="close-btn" onClick={() => setFullscreen(false)}>
              &times;
            </button>
            <img
              src={`${baseUrl}${currentImage}`}
              alt={`AI 분석 결과 ${selectedImageIndex + 1}`}
            />
            <div className="fullscreen-controls">
              <button
                className="nav-btn"
                onClick={() => setSelectedImageIndex(Math.max(0, selectedImageIndex - 1))}
                disabled={selectedImageIndex === 0}
              >
                &larr; 이전
              </button>
              <span>{selectedImageIndex + 1} / {visualizationPaths.length}</span>
              <button
                className="nav-btn"
                onClick={() => setSelectedImageIndex(Math.min(visualizationPaths.length - 1, selectedImageIndex + 1))}
                disabled={selectedImageIndex === visualizationPaths.length - 1}
              >
                다음 &rarr;
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
