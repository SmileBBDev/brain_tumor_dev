/**
 * AI 분석 결과 패널 (P.82-83)
 * - AI 분석 결과 요약 표시
 * - 실제 AI API 연동
 */
import { useState, useEffect } from 'react';
import { getPatientAIRequests } from '@/services/ai.api';
import type { AIInferenceRequest, AIInferenceResult } from '@/services/ai.api';
import './AIAnalysisPanel.css';

// =============================================================================
// AI 연동 인터페이스 정의 (UI 표시용)
// =============================================================================
export interface AIAnalysisResult {
  analysis_id: string;
  analysis_date: string;
  model_version: string;
  status: 'completed' | 'processing' | 'failed' | 'pending';

  // 위험도 평가
  risk_level: 'high' | 'medium' | 'low' | 'normal';
  risk_score: number; // 0-100
  confidence: number; // 0-100

  // 주요 소견
  findings: AIFinding[];

  // 요약
  summary: string;

  // 상세 분석
  details?: AIAnalysisDetail[];

  // 시각화 이미지 경로 (썸네일용)
  visualization_paths?: string[];
}

export interface AIFinding {
  id: string;
  type: string; // 'lesion', 'abnormality', 'artifact' 등
  description: string;
  location?: string;
  severity: 'critical' | 'major' | 'minor' | 'observation';
  confidence: number;
  bbox?: { x: number; y: number; width: number; height: number };
}

export interface AIAnalysisDetail {
  category: string;
  metrics: { name: string; value: string | number; unit?: string }[];
}


// =============================================================================
// 컴포넌트
// =============================================================================
interface AIAnalysisPanelProps {
  ocsId: number;
  patientId?: number;
  jobType: string;
  compact?: boolean;
}

// AI 추론 결과를 UI 표시용 AIAnalysisResult로 변환
const convertToDisplayResult = (
  request: AIInferenceRequest,
  inferenceResult: AIInferenceResult
): AIAnalysisResult => {
  const resultData = inferenceResult.result_data || {};

  // 결과 데이터에서 정보 추출 (백엔드 result_data 구조에 따라 조정)
  const riskLevel = (resultData.risk_level as string) || 'normal';
  const riskScore = typeof resultData.risk_score === 'number' ? resultData.risk_score : 0;
  const confidence = inferenceResult.confidence_score ?? (typeof resultData.confidence === 'number' ? resultData.confidence : 0);
  const summary = (resultData.summary as string) || (resultData.diagnosis as string) || '분석이 완료되었습니다.';

  // findings 추출
  const rawFindings = (resultData.findings as any[]) || [];
  const findings: AIFinding[] = rawFindings.map((f, idx) => ({
    id: `f${idx + 1}`,
    type: f.type || 'observation',
    description: f.description || f.text || '',
    location: f.location,
    severity: f.severity || 'observation',
    confidence: f.confidence ?? 0,
    bbox: f.bbox,
  }));

  // details 추출
  const rawDetails = (resultData.details as any[]) || [];
  const details: AIAnalysisDetail[] = rawDetails.map((d) => ({
    category: d.category || d.name || '',
    metrics: (d.metrics || []).map((m: any) => ({
      name: m.name,
      value: m.value,
      unit: m.unit,
    })),
  }));

  return {
    analysis_id: request.request_id,
    analysis_date: request.completed_at || request.created_at,
    model_version: request.model_name,
    status: request.status === 'COMPLETED' ? 'completed'
      : request.status === 'PROCESSING' || request.status === 'VALIDATING' ? 'processing'
      : request.status === 'FAILED' ? 'failed' : 'pending',
    risk_level: riskLevel as 'high' | 'medium' | 'low' | 'normal',
    risk_score: riskScore,
    confidence: confidence,
    findings: findings,
    summary: summary,
    details: details.length > 0 ? details : undefined,
    visualization_paths: inferenceResult.visualization_paths || [],
  };
};

export default function AIAnalysisPanel({ ocsId, patientId, jobType: _jobType, compact = false }: AIAnalysisPanelProps) {
  const [result, setResult] = useState<AIAnalysisResult | null>(null);
  const [aiRequest, setAiRequest] = useState<AIInferenceRequest | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    const fetchAIResult = async () => {
      if (!patientId) {
        setLoading(false);
        setResult(null);
        return;
      }

      setLoading(true);
      try {
        // 환자의 AI 추론 요청 목록 조회
        const requests = await getPatientAIRequests(patientId);

        // 현재 OCS를 참조하는 AI 요청 찾기 (가장 최신 것)
        const matchingRequest = requests
          .filter(req => req.ocs_references.includes(ocsId))
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())[0];

        if (matchingRequest && matchingRequest.has_result && matchingRequest.result) {
          setAiRequest(matchingRequest);
          const displayResult = convertToDisplayResult(matchingRequest, matchingRequest.result);
          setResult(displayResult);
        } else if (matchingRequest) {
          // 결과가 아직 없는 경우 (처리 중 등)
          setAiRequest(matchingRequest);
          setResult(null);
        } else {
          setAiRequest(null);
          setResult(null);
        }
      } catch (error) {
        console.error('Failed to fetch AI result:', error);
        setResult(null);
      } finally {
        setLoading(false);
      }
    };

    fetchAIResult();
  }, [ocsId, patientId]);

  if (loading) {
    return (
      <div className={`ai-analysis-panel ${compact ? 'compact' : ''}`}>
        <div className="loading-state">
          <div className="spinner"></div>
          <span>AI 분석 결과 로딩 중...</span>
        </div>
      </div>
    );
  }

  if (!result) {
    // AI 요청이 있지만 결과가 아직 없는 경우 (처리 중)
    if (aiRequest) {
      const statusText = aiRequest.status === 'PENDING' ? '대기 중'
        : aiRequest.status === 'VALIDATING' ? '검증 중'
        : aiRequest.status === 'PROCESSING' ? '분석 중'
        : aiRequest.status === 'FAILED' ? '분석 실패'
        : '처리 중';
      const isFailed = aiRequest.status === 'FAILED';

      return (
        <div className={`ai-analysis-panel ${compact ? 'compact' : ''}`}>
          <div className="panel-header">
            <h3>AI 분석 결과</h3>
            <span className="model-version">{aiRequest.model_name}</span>
          </div>
          <div className={`processing-state ${isFailed ? 'failed' : ''}`}>
            {!isFailed && <div className="spinner"></div>}
            <span>{statusText}</span>
            {isFailed && aiRequest.error_message && (
              <p className="error-message">{aiRequest.error_message}</p>
            )}
            <p className="processing-desc">
              {isFailed ? 'AI 분석에 실패했습니다.' : 'AI 모델이 영상을 분석하고 있습니다.'}
            </p>
          </div>
        </div>
      );
    }

    // AI 요청 자체가 없는 경우
    return (
      <div className={`ai-analysis-panel ${compact ? 'compact' : ''}`}>
        <div className="panel-header">
          <h3>AI 분석 결과</h3>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🔬</div>
          <span>AI 분석 결과 없음</span>
          <p className="empty-desc">이 검사에 대한 AI 분석이 요청되지 않았습니다.</p>
        </div>
      </div>
    );
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high': return '#d32f2f';
      case 'medium': return '#f57c00';
      case 'low': return '#388e3c';
      default: return '#666';
    }
  };

  const getRiskLabel = (level: string) => {
    switch (level) {
      case 'high': return '높음';
      case 'medium': return '중간';
      case 'low': return '낮음';
      default: return '정상';
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return '#d32f2f';
      case 'major': return '#f57c00';
      case 'minor': return '#fbc02d';
      default: return '#666';
    }
  };

  return (
    <div className={`ai-analysis-panel ${compact ? 'compact' : ''}`}>
      <div className="panel-header">
        <h3>AI 분석 결과</h3>
        <span className="model-version">{result.model_version}</span>
      </div>

      {/* 위험도 요약 */}
      <div className="risk-summary">
        <div className="risk-indicator" style={{ borderColor: getRiskColor(result.risk_level) }}>
          <div
            className="risk-score"
            style={{ color: getRiskColor(result.risk_level) }}
          >
            {result.risk_score}
          </div>
          <div className="risk-label">
            위험도: <strong style={{ color: getRiskColor(result.risk_level) }}>
              {getRiskLabel(result.risk_level)}
            </strong>
          </div>
        </div>
        <div className="confidence">
          <span>신뢰도</span>
          <div className="confidence-bar">
            <div
              className="confidence-fill"
              style={{ width: `${result.confidence}%` }}
            />
          </div>
          <span>{result.confidence}%</span>
        </div>
      </div>

      {/* 요약 */}
      <div className="summary-section">
        <h4>요약</h4>
        <p>{result.summary}</p>
      </div>

      {/* 주요 소견 */}
      {!compact && result.findings.length > 0 && (
        <div className="findings-section">
          <h4>주요 소견</h4>
          <ul className="findings-list">
            {result.findings.map((finding) => (
              <li key={finding.id} className="finding-item">
                <span
                  className="severity-dot"
                  style={{ background: getSeverityColor(finding.severity) }}
                />
                <div className="finding-content">
                  <p className="finding-desc">{finding.description}</p>
                  {finding.location && (
                    <span className="finding-location">{finding.location}</span>
                  )}
                </div>
                <span className="finding-confidence">{finding.confidence}%</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 상세 분석 토글 */}
      {!compact && result.details && (
        <>
          <button
            className="toggle-details-btn"
            onClick={() => setShowDetails(!showDetails)}
          >
            {showDetails ? '상세 정보 접기' : '상세 정보 보기'}
          </button>

          {showDetails && (
            <div className="details-section">
              {result.details.map((detail, idx) => (
                <div key={idx} className="detail-category">
                  <h5>{detail.category}</h5>
                  <div className="metrics-grid">
                    {detail.metrics.map((metric, mIdx) => (
                      <div key={mIdx} className="metric-item">
                        <span className="metric-name">{metric.name}</span>
                        <span className="metric-value">
                          {metric.value} {metric.unit || ''}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {/* AI 분석 썸네일 이미지 */}
      {result.visualization_paths && result.visualization_paths.length > 0 && (
        <div className="ai-thumbnails-section">
          <h4>분석 이미지</h4>
          <div className="ai-thumbnails-grid">
            {result.visualization_paths.slice(0, 4).map((path, idx) => (
              <div key={idx} className="ai-thumbnail-item">
                <img
                  src={`${import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}${path}`}
                  alt={`AI 분석 결과 ${idx + 1}`}
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
              </div>
            ))}
          </div>
          {result.visualization_paths.length > 4 && (
            <p className="thumbnails-more">+{result.visualization_paths.length - 4}개 더 보기</p>
          )}
        </div>
      )}

      {/* 면책 조항 */}
      <div className="disclaimer">
        <p>본 AI 분석 결과는 참고 자료이며, 최종 판단은 전문 의료진의 결정에 따릅니다.</p>
      </div>
    </div>
  );
}
