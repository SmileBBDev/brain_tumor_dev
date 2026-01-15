/**
 * AI 모델 정보 페이지
 * - 사용 가능한 AI 모델 목록
 * - 모델별 상세 정보 및 요구사항
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAIModels } from '@/hooks';
import { LoadingSpinner } from '@/components/common';
import './AIModelsPage.css';

// AI 모델 상세 정보 (확장)
const MODEL_DETAILS: Record<string, {
  icon: string;
  category: string;
  inputDescription: string;
  outputDescription: string;
  processingTime: string;
  accuracy: string;
}> = {
  M1: {
    icon: '🧠',
    category: '영상 분석',
    inputDescription: 'MRI 4채널 영상 (T1, T2, T1C, FLAIR)',
    outputDescription: '종양 위치, 크기, 등급 예측, 세그멘테이션 마스크',
    processingTime: '약 2-5분',
    accuracy: '92.5%',
  },
  MG: {
    icon: '🧬',
    category: '유전자 분석',
    inputDescription: 'RNA 시퀀싱 데이터, 유전자 변이 정보',
    outputDescription: '유전자 마커 분석, 분자 서브타입 분류, 예후 예측',
    processingTime: '약 3-7분',
    accuracy: '88.2%',
  },
  MM: {
    icon: '🔬',
    category: '통합 분석',
    inputDescription: 'MRI 영상 + RNA_seq + 단백질 마커',
    outputDescription: '종합 진단 결과, 치료 권고, 생존율 예측',
    processingTime: '약 5-10분',
    accuracy: '95.1%',
  },
  MP: {
    icon: '🔮',
    category: '단백질 분석',
    inputDescription: '단백질 마커 데이터',
    outputDescription: '단백질 발현 패턴, 바이오마커 분석',
    processingTime: '약 2-4분',
    accuracy: '86.7%',
  },
};

export default function AIModelsPage() {
  const navigate = useNavigate();
  const { models, loading, error } = useAIModels();
  const [selectedModel, setSelectedModel] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="ai-models-page loading">
        <LoadingSpinner />
      </div>
    );
  }

  if (error) {
    return (
      <div className="ai-models-page error-state">
        <p>모델 정보를 불러오는 중 오류가 발생했습니다.</p>
      </div>
    );
  }

  return (
    <div className="ai-models-page">
      {/* 헤더 */}
      <header className="page-header">
        <div>
          <h2>AI 모델 정보</h2>
          <p className="subtitle">사용 가능한 AI 분석 모델 목록 및 상세 정보</p>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={() => navigate('/ai/requests/create')}>
            새 분석 요청
          </button>
        </div>
      </header>

      {/* 모델 목록 */}
      <section className="models-section">
        <div className="models-grid">
          {models.map((model) => {
            const details = MODEL_DETAILS[model.code] || {
              icon: '🤖',
              category: 'AI 분석',
              inputDescription: model.description,
              outputDescription: '분석 결과',
              processingTime: '약 3-5분',
              accuracy: '-',
            };

            return (
              <div
                key={model.code}
                className={`model-card ${selectedModel === model.code ? 'selected' : ''}`}
                onClick={() => setSelectedModel(selectedModel === model.code ? null : model.code)}
              >
                <div className="model-header">
                  <div className="model-icon">{details.icon}</div>
                  <div className="model-title">
                    <h3>{model.name}</h3>
                    <span className="model-code">{model.code}</span>
                  </div>
                  <span className="model-category">{details.category}</span>
                </div>

                <p className="model-description">{model.description}</p>

                <div className="model-meta">
                  <div className="meta-item">
                    <span className="meta-label">처리 시간</span>
                    <span className="meta-value">{details.processingTime}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">정확도</span>
                    <span className="meta-value accuracy">{details.accuracy}</span>
                  </div>
                </div>

                {/* 확장된 상세 정보 */}
                {selectedModel === model.code && (
                  <div className="model-details">
                    <div className="detail-section">
                      <h4>입력 데이터</h4>
                      <p>{details.inputDescription}</p>
                    </div>
                    <div className="detail-section">
                      <h4>출력 결과</h4>
                      <p>{details.outputDescription}</p>
                    </div>
                    <div className="detail-section">
                      <h4>필요 데이터</h4>
                      <div className="required-keys">
                        {Object.keys(model.required_keys || {}).map((key) => (
                          <span key={key} className="key-badge">{key}</span>
                        ))}
                      </div>
                    </div>
                    <button
                      className="btn btn-primary btn-block"
                      onClick={(e) => {
                        e.stopPropagation();
                        navigate(`/ai/requests/create?model=${model.code}`);
                      }}
                    >
                      이 모델로 분석 요청
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* 모델 비교 표 */}
      <section className="comparison-section">
        <h3>모델 비교</h3>
        <div className="comparison-table-wrapper">
          <table className="comparison-table">
            <thead>
              <tr>
                <th>모델</th>
                <th>카테고리</th>
                <th>필요 데이터</th>
                <th>처리 시간</th>
                <th>정확도</th>
                <th>동작</th>
              </tr>
            </thead>
            <tbody>
              {models.map((model) => {
                const details = MODEL_DETAILS[model.code] || {
                  icon: '🤖',
                  category: 'AI 분석',
                  processingTime: '약 3-5분',
                  accuracy: '-',
                };

                return (
                  <tr key={model.code}>
                    <td>
                      <div className="model-cell">
                        <span className="model-icon-small">{details.icon}</span>
                        <div>
                          <div className="model-name">{model.name}</div>
                          <div className="model-code">{model.code}</div>
                        </div>
                      </div>
                    </td>
                    <td>{details.category}</td>
                    <td>
                      <div className="required-keys compact">
                        {Object.keys(model.required_keys || {}).slice(0, 3).map((key) => (
                          <span key={key} className="key-badge small">{key}</span>
                        ))}
                        {Object.keys(model.required_keys || {}).length > 3 && (
                          <span className="key-badge small more">+{Object.keys(model.required_keys || {}).length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td>{details.processingTime}</td>
                    <td className="accuracy-cell">{details.accuracy}</td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline"
                        onClick={() => navigate(`/ai/requests/create?model=${model.code}`)}
                      >
                        분석 요청
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* 안내 섹션 */}
      <section className="info-section">
        <div className="info-card">
          <div className="info-icon">ℹ️</div>
          <div className="info-content">
            <h4>AI 분석 요청 안내</h4>
            <p>
              AI 분석을 요청하려면 환자의 해당 검사 데이터가 필요합니다.
              영상 분석(M1)의 경우 RIS에서 MRI 영상이 업로드되어야 하며,
              유전자 분석(MG)의 경우 LIS에서 유전자 검사 결과가 등록되어야 합니다.
            </p>
            <p>
              통합 분석(MM)은 영상, 유전자, 단백질 데이터가 모두 필요하므로
              해당 검사들이 완료된 후 요청하시기 바랍니다.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
