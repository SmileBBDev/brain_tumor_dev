import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import MMResultViewer from '@/components/MMResultViewer'
import { aiApi } from '@/services/ai.api'
import './MMDetailPage.css'

interface MMResult {
  patient_id?: string
  // 멀티모달 통합 결과
  integrated_prediction?: {
    grade: {
      predicted_class: string
      probability: number
      probabilities?: Record<string, number>
    }
    survival_risk?: {
      risk_score: number
      risk_category?: string
      risk_percentile?: number
    }
    survival_time?: {
      predicted_days: number
      predicted_months: number
      confidence_interval?: { lower: number; upper: number }
    }
  }
  // 모달리티별 기여도
  modality_contributions?: {
    mri?: { weight: number; confidence: number }
    gene?: { weight: number; confidence: number }
    protein?: { weight: number; confidence: number }
  }
  // 개별 모달리티 결과
  mri_result?: {
    grade?: { predicted_class: string; probability: number }
    segmentation_available?: boolean
  }
  gene_result?: {
    grade?: { predicted_class: string; probability: number }
    top_genes_count?: number
  }
  protein_result?: {
    grade?: { predicted_class: string; probability: number }
    markers_analyzed?: number
  }
  // XAI
  xai?: {
    integrated_attention?: {
      mri_regions?: Array<{ region: string; attention: number }>
      top_genes?: Array<{ gene: string; attention: number }>
      key_proteins?: Array<{ protein: string; attention: number }>
    }
    cross_modal_correlations?: Array<{
      modality_pair: string
      correlation: number
      significance: number
    }>
  }
  processing_time_ms?: number
  model_version?: string
}

interface InferenceDetail {
  id: number
  job_id: string
  model_type: string
  status: string
  mode: string
  patient_name: string
  patient_number: string
  mri_ocs: number | null
  gene_ocs: number | null
  protein_ocs: number | null
  result_data: MMResult | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export default function MMDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()

  // State
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [inferenceDetail, setInferenceDetail] = useState<InferenceDetail | null>(null)

  // 데이터 로드
  useEffect(() => {
    if (jobId) {
      loadInferenceDetail(jobId)
    }
  }, [jobId])

  const loadInferenceDetail = async (id: string) => {
    try {
      setLoading(true)
      setError('')
      const data = await aiApi.getInferenceDetail(id)
      setInferenceDetail(data)
    } catch (err: any) {
      console.error('Failed to load inference detail:', err)
      setError(err.response?.data?.error || '추론 결과를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const handleBack = () => {
    navigate('/ai/mm')
  }

  const handleDelete = async () => {
    if (!jobId || !window.confirm('이 추론 결과를 삭제하시겠습니까?')) {
      return
    }

    try {
      await aiApi.deleteInference(jobId)
      navigate('/ai/mm')
    } catch (err: any) {
      console.error('Failed to delete inference:', err)
      alert(err.response?.data?.error || '삭제에 실패했습니다.')
    }
  }

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { className: string; label: string }> = {
      COMPLETED: { className: 'status-badge status-completed', label: '완료' },
      PROCESSING: { className: 'status-badge status-processing', label: '처리중' },
      PENDING: { className: 'status-badge status-pending', label: '대기' },
      FAILED: { className: 'status-badge status-failed', label: '실패' },
    }
    const { className, label } = statusMap[status] || { className: 'status-badge status-pending', label: status }
    return <span className={className}>{label}</span>
  }

  const getModalityCount = () => {
    if (!inferenceDetail) return 0
    let count = 0
    if (inferenceDetail.mri_ocs) count++
    if (inferenceDetail.gene_ocs) count++
    if (inferenceDetail.protein_ocs) count++
    return count
  }

  const getModalityBadges = () => {
    if (!inferenceDetail) return null
    return (
      <div className="modality-badges">
        {inferenceDetail.mri_ocs && <span className="modality-badge mri">MRI</span>}
        {inferenceDetail.gene_ocs && <span className="modality-badge gene">Gene</span>}
        {inferenceDetail.protein_ocs && <span className="modality-badge protein">Protein</span>}
      </div>
    )
  }

  if (loading) {
    return (
      <div className="mm-detail-page">
        <div className="loading-container">
          <div className="spinner mm" />
          <p className="loading-text">데이터 로딩 중...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="mm-detail-page">
        <div className="error-container">
          <h4 className="error-title">오류 발생</h4>
          <p className="error-message">{error}</p>
          <button onClick={handleBack} className="btn-back">
            목록으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  if (!inferenceDetail) {
    return (
      <div className="mm-detail-page">
        <div className="error-container">
          <h4 className="error-title">결과를 찾을 수 없습니다</h4>
          <button onClick={handleBack} className="btn-back">
            목록으로 돌아가기
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="mm-detail-page">
      {/* Header */}
      <div className="page-header">
        <div className="header-left">
          <button onClick={handleBack} className="btn-back-icon">
            ← 뒤로
          </button>
          <div>
            <h2 className="page-title">MM 분석 결과 상세</h2>
            <p className="page-subtitle">Job ID: {jobId}</p>
          </div>
        </div>
        <div className="header-actions">
          <button onClick={handleDelete} className="btn-delete">
            삭제
          </button>
        </div>
      </div>

      {/* Job Info */}
      <div className="info-section">
        <div className="info-grid">
          <div className="info-card">
            <h4 className="card-title">요청 정보</h4>
            <dl className="info-list">
              <div className="info-item">
                <dt>Job ID</dt>
                <dd>{inferenceDetail.job_id}</dd>
              </div>
              <div className="info-item">
                <dt>상태</dt>
                <dd>{getStatusBadge(inferenceDetail.status)}</dd>
              </div>
              <div className="info-item">
                <dt>모드</dt>
                <dd>{inferenceDetail.mode === 'auto' ? '자동' : '수동'}</dd>
              </div>
              <div className="info-item">
                <dt>요청일</dt>
                <dd>{new Date(inferenceDetail.created_at).toLocaleString('ko-KR')}</dd>
              </div>
              {inferenceDetail.completed_at && (
                <div className="info-item">
                  <dt>완료일</dt>
                  <dd>{new Date(inferenceDetail.completed_at).toLocaleString('ko-KR')}</dd>
                </div>
              )}
            </dl>
          </div>

          <div className="info-card">
            <h4 className="card-title">환자 정보</h4>
            <dl className="info-list">
              <div className="info-item">
                <dt>환자명</dt>
                <dd>{inferenceDetail.patient_name || '-'}</dd>
              </div>
              <div className="info-item">
                <dt>환자번호</dt>
                <dd>{inferenceDetail.patient_number || '-'}</dd>
              </div>
            </dl>
          </div>

          <div className="info-card">
            <h4 className="card-title">멀티모달 정보</h4>
            <dl className="info-list">
              <div className="info-item">
                <dt>사용 모달리티</dt>
                <dd>{getModalityBadges()}</dd>
              </div>
              <div className="info-item">
                <dt>모달리티 수</dt>
                <dd>{getModalityCount()}개</dd>
              </div>
              {inferenceDetail.mri_ocs && (
                <div className="info-item">
                  <dt>MRI OCS</dt>
                  <dd>{inferenceDetail.mri_ocs}</dd>
                </div>
              )}
              {inferenceDetail.gene_ocs && (
                <div className="info-item">
                  <dt>Gene OCS</dt>
                  <dd>{inferenceDetail.gene_ocs}</dd>
                </div>
              )}
              {inferenceDetail.protein_ocs && (
                <div className="info-item">
                  <dt>Protein OCS</dt>
                  <dd>{inferenceDetail.protein_ocs}</dd>
                </div>
              )}
            </dl>
          </div>

          {inferenceDetail.result_data && (
            <div className="info-card">
              <h4 className="card-title">처리 정보</h4>
              <dl className="info-list">
                {inferenceDetail.result_data.processing_time_ms && (
                  <div className="info-item">
                    <dt>처리 시간</dt>
                    <dd className="processing-time mm">
                      {(inferenceDetail.result_data.processing_time_ms / 1000).toFixed(2)}초
                    </dd>
                  </div>
                )}
                {inferenceDetail.result_data.model_version && (
                  <div className="info-item">
                    <dt>모델 버전</dt>
                    <dd>{inferenceDetail.result_data.model_version}</dd>
                  </div>
                )}
              </dl>
            </div>
          )}
        </div>
      </div>

      {/* MM Result Viewer */}
      {inferenceDetail.status === 'COMPLETED' && inferenceDetail.result_data && (
        <div className="section">
          <h3 className="section-title">통합 분석 결과</h3>
          <MMResultViewer result={inferenceDetail.result_data} />
        </div>
      )}

      {/* Error Message */}
      {inferenceDetail.status === 'FAILED' && inferenceDetail.error_message && (
        <div className="section">
          <h3 className="section-title">오류 정보</h3>
          <div className="error-container">
            <p className="error-message">{inferenceDetail.error_message}</p>
          </div>
        </div>
      )}

      {/* Modality Contributions */}
      {inferenceDetail.result_data?.modality_contributions && (
        <div className="section">
          <h3 className="section-title">모달리티 기여도</h3>
          <div className="contributions-card">
            <div className="contributions-grid">
              {inferenceDetail.result_data.modality_contributions.mri && (
                <div className="contribution-item mri">
                  <div className="contribution-header">
                    <span className="modality-icon">🧠</span>
                    <span className="modality-name">MRI</span>
                  </div>
                  <div className="contribution-bar-container">
                    <div
                      className="contribution-bar mri"
                      style={{ width: `${inferenceDetail.result_data.modality_contributions.mri.weight * 100}%` }}
                    />
                  </div>
                  <div className="contribution-values">
                    <span>가중치: {(inferenceDetail.result_data.modality_contributions.mri.weight * 100).toFixed(1)}%</span>
                    <span>신뢰도: {(inferenceDetail.result_data.modality_contributions.mri.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              )}
              {inferenceDetail.result_data.modality_contributions.gene && (
                <div className="contribution-item gene">
                  <div className="contribution-header">
                    <span className="modality-icon">🧬</span>
                    <span className="modality-name">Gene</span>
                  </div>
                  <div className="contribution-bar-container">
                    <div
                      className="contribution-bar gene"
                      style={{ width: `${inferenceDetail.result_data.modality_contributions.gene.weight * 100}%` }}
                    />
                  </div>
                  <div className="contribution-values">
                    <span>가중치: {(inferenceDetail.result_data.modality_contributions.gene.weight * 100).toFixed(1)}%</span>
                    <span>신뢰도: {(inferenceDetail.result_data.modality_contributions.gene.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              )}
              {inferenceDetail.result_data.modality_contributions.protein && (
                <div className="contribution-item protein">
                  <div className="contribution-header">
                    <span className="modality-icon">🔬</span>
                    <span className="modality-name">Protein</span>
                  </div>
                  <div className="contribution-bar-container">
                    <div
                      className="contribution-bar protein"
                      style={{ width: `${inferenceDetail.result_data.modality_contributions.protein.weight * 100}%` }}
                    />
                  </div>
                  <div className="contribution-values">
                    <span>가중치: {(inferenceDetail.result_data.modality_contributions.protein.weight * 100).toFixed(1)}%</span>
                    <span>신뢰도: {(inferenceDetail.result_data.modality_contributions.protein.confidence * 100).toFixed(1)}%</span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cross-Modal Correlations */}
      {inferenceDetail.result_data?.xai?.cross_modal_correlations && (
        <div className="section">
          <h3 className="section-title">모달리티 간 상관관계</h3>
          <div className="correlations-card">
            <table className="correlations-table">
              <thead>
                <tr>
                  <th>모달리티 쌍</th>
                  <th>상관계수</th>
                  <th>유의성</th>
                </tr>
              </thead>
              <tbody>
                {inferenceDetail.result_data.xai.cross_modal_correlations.map((corr, idx) => (
                  <tr key={idx}>
                    <td className="modality-pair">{corr.modality_pair}</td>
                    <td>
                      <div className="correlation-bar-container">
                        <div
                          className={`correlation-bar ${corr.correlation >= 0 ? 'positive' : 'negative'}`}
                          style={{ width: `${Math.abs(corr.correlation) * 100}%` }}
                        />
                        <span className="correlation-value">
                          {corr.correlation > 0 ? '+' : ''}{corr.correlation.toFixed(3)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <span className={`significance ${corr.significance < 0.05 ? 'significant' : ''}`}>
                        p = {corr.significance.toFixed(4)}
                        {corr.significance < 0.05 && ' *'}
                        {corr.significance < 0.01 && '*'}
                        {corr.significance < 0.001 && '*'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Individual Modality Results */}
      {inferenceDetail.result_data && (
        <div className="section">
          <h3 className="section-title">개별 모달리티 결과</h3>
          <div className="individual-results-grid">
            {inferenceDetail.result_data.mri_result && (
              <div className="individual-result-card mri">
                <div className="result-header">
                  <span className="result-icon">🧠</span>
                  <h4>MRI 분석</h4>
                </div>
                {inferenceDetail.result_data.mri_result.grade && (
                  <div className="result-content">
                    <div className="result-item">
                      <span className="label">Grade 예측:</span>
                      <span className="value">{inferenceDetail.result_data.mri_result.grade.predicted_class}</span>
                    </div>
                    <div className="result-item">
                      <span className="label">확률:</span>
                      <span className="value">{(inferenceDetail.result_data.mri_result.grade.probability * 100).toFixed(1)}%</span>
                    </div>
                    {inferenceDetail.result_data.mri_result.segmentation_available && (
                      <div className="result-item">
                        <span className="label">세그멘테이션:</span>
                        <span className="value available">가능</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {inferenceDetail.result_data.gene_result && (
              <div className="individual-result-card gene">
                <div className="result-header">
                  <span className="result-icon">🧬</span>
                  <h4>Gene 분석</h4>
                </div>
                {inferenceDetail.result_data.gene_result.grade && (
                  <div className="result-content">
                    <div className="result-item">
                      <span className="label">Grade 예측:</span>
                      <span className="value">{inferenceDetail.result_data.gene_result.grade.predicted_class}</span>
                    </div>
                    <div className="result-item">
                      <span className="label">확률:</span>
                      <span className="value">{(inferenceDetail.result_data.gene_result.grade.probability * 100).toFixed(1)}%</span>
                    </div>
                    {inferenceDetail.result_data.gene_result.top_genes_count && (
                      <div className="result-item">
                        <span className="label">주요 유전자:</span>
                        <span className="value">{inferenceDetail.result_data.gene_result.top_genes_count}개</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {inferenceDetail.result_data.protein_result && (
              <div className="individual-result-card protein">
                <div className="result-header">
                  <span className="result-icon">🔬</span>
                  <h4>Protein 분석</h4>
                </div>
                {inferenceDetail.result_data.protein_result.grade && (
                  <div className="result-content">
                    <div className="result-item">
                      <span className="label">Grade 예측:</span>
                      <span className="value">{inferenceDetail.result_data.protein_result.grade.predicted_class}</span>
                    </div>
                    <div className="result-item">
                      <span className="label">확률:</span>
                      <span className="value">{(inferenceDetail.result_data.protein_result.grade.probability * 100).toFixed(1)}%</span>
                    </div>
                    {inferenceDetail.result_data.protein_result.markers_analyzed && (
                      <div className="result-item">
                        <span className="label">분석 마커:</span>
                        <span className="value">{inferenceDetail.result_data.protein_result.markers_analyzed}개</span>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
