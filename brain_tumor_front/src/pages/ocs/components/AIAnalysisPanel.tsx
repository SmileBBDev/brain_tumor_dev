/**
 * AI 분석 결과 패널 (P.82-83)
 * - AI 분석 결과 요약 표시
 * - 목업 데이터 사용 (실제 연동 대비 인터페이스 정의)
 */
import { useState, useEffect } from 'react';
import './AIAnalysisPanel.css';

// =============================================================================
// AI 연동 인터페이스 정의 (향후 실제 연동시 사용)
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
// 목업 데이터 생성 (TODO: 실제 AI 연동 시 제거)
// =============================================================================
// const generateMockAIResult = (jobType: string): AIAnalysisResult => {
//   const isBrainScan = ['MRI', 'CT'].includes(jobType.toUpperCase());
//
//   return {
//     analysis_id: `AI-${Date.now()}`,
//     analysis_date: new Date().toISOString(),
//     model_version: 'BrainTumor-CDSS v2.1.0',
//     status: 'completed',
//
//     risk_level: isBrainScan ? 'medium' : 'low',
//     risk_score: isBrainScan ? 65 : 25,
//     confidence: 87,
//
//     findings: isBrainScan ? [
//       {
//         id: 'f1',
//         type: 'lesion',
//         description: '좌측 측두엽에 불규칙한 조영증강 병변 관찰',
//         location: 'Left temporal lobe',
//         severity: 'major',
//         confidence: 89,
//       },
//       {
//         id: 'f2',
//         type: 'abnormality',
//         description: '주변 부종 소견',
//         location: 'Perilesional area',
//         severity: 'minor',
//         confidence: 78,
//       },
//     ] : [
//       {
//         id: 'f1',
//         type: 'observation',
//         description: '특이 소견 없음',
//         severity: 'observation',
//         confidence: 95,
//       },
//     ],
//
//     summary: isBrainScan
//       ? '좌측 측두엽에 약 2.3cm 크기의 조영증강 병변이 관찰됩니다. 신경교종(Glioma) 가능성이 있으며, 추가 검사를 권고합니다.'
//       : '분석 결과 특이 소견이 발견되지 않았습니다.',
//
//     details: isBrainScan ? [
//       {
//         category: '병변 정보',
//         metrics: [
//           { name: '크기', value: '2.3 x 1.8', unit: 'cm' },
//           { name: '위치', value: 'Left temporal lobe' },
//           { name: '조영증강', value: '불균일' },
//         ],
//       },
//       {
//         category: '정량 분석',
//         metrics: [
//           { name: 'ADC', value: '0.85', unit: '×10⁻³ mm²/s' },
//           { name: 'rCBV', value: '2.1', unit: 'ratio' },
//         ],
//       },
//     ] : undefined,
//   };
// };

// =============================================================================
// 컴포넌트
// =============================================================================
interface AIAnalysisPanelProps {
  ocsId: number;
  jobType: string;
  compact?: boolean;
}

export default function AIAnalysisPanel({ ocsId, jobType, compact = false }: AIAnalysisPanelProps) {
  const [result, setResult] = useState<AIAnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    // TODO: 실제 AI 분석 API 연동 시 구현
    const fetchAIResult = async () => {
      setLoading(true);
      try {
        // TODO: 실제 API 연동
        // const data = await getAIAnalysisResult(ocsId);

        // 현재는 AI 분석 결과가 없음 (API 연동 전)
        await new Promise(resolve => setTimeout(resolve, 300));
        setResult(null);

        // 목업 데이터 사용 (주석 처리됨)
        // const mockData = generateMockAIResult(jobType);
        // setResult(mockData);
      } catch (error) {
        console.error('Failed to fetch AI result:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAIResult();
  }, [ocsId, jobType]);

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
    return (
      <div className={`ai-analysis-panel ${compact ? 'compact' : ''}`}>
        <div className="panel-header">
          <h3>AI 분석 결과</h3>
        </div>
        <div className="empty-state">
          <div className="empty-icon">🔬</div>
          <span>AI 분석 기능 준비 중</span>
          <p className="empty-desc">추후 AI 모델 연동 시 분석 결과가 표시됩니다.</p>
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

      {/* 면책 조항 */}
      <div className="disclaimer">
        <p>본 AI 분석 결과는 참고 자료이며, 최종 판단은 전문 의료진의 결정에 따릅니다.</p>
      </div>
    </div>
  );
}
