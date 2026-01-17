import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { InferenceResult } from '@/components/InferenceResult'
import SegMRIViewer, { type SegmentationData } from '@/components/SegMRIViewer'
import { aiApi } from '@/services/ai.api'
import { useThumbnailCache } from '@/context/ThumbnailCacheContext'
import './M1DetailPage.css'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'

// 채널별 색상
const CHANNEL_COLORS: Record<string, string> = {
  T1: '#3b82f6',    // 파랑
  T1C: '#ef4444',   // 빨강
  T2: '#10b981',    // 초록
  FLAIR: '#f59e0b', // 주황
}

interface M1Result {
  grade?: {
    predicted_class: string
    probability: number
    probabilities?: Record<string, number>
  }
  idh?: {
    predicted_class: string
    mutant_probability?: number
  }
  mgmt?: {
    predicted_class: string
    methylated_probability?: number
  }
  survival?: {
    risk_score: number
    risk_category: string
  }
  os_days?: {
    predicted_days: number
    predicted_months: number
  }
  processing_time_ms?: number
}

// MRI 썸네일 채널 정보
interface MRIThumbnail {
  channel: 'T1' | 'T1C' | 'T2' | 'FLAIR'
  url: string
  description: string
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
  result_data: M1Result | null
  error_message: string | null
  created_at: string
  completed_at: string | null
  mri_thumbnails?: MRIThumbnail[] | null
}

export default function M1DetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const { markAsCached } = useThumbnailCache()

  // State
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string>('')
  const [inferenceDetail, setInferenceDetail] = useState<InferenceDetail | null>(null)

  // 세그멘테이션 뷰어
  const [segmentationData, setSegmentationData] = useState<SegmentationData | null>(null)
  const [loadingSegmentation, setLoadingSegmentation] = useState(false)
  const [segmentationError, setSegmentationError] = useState<string>('')

  // 데이터 로드
  useEffect(() => {
    if (jobId) {
      loadInferenceDetail(jobId)
      // 보고서 방문 시 캐시에 등록 (목록 페이지에서 썸네일 표시용)
      markAsCached(`ai_${jobId}`)
    }
  }, [jobId, markAsCached])

  const loadInferenceDetail = async (id: string) => {
    try {
      setLoading(true)
      setError('')
      const data = await aiApi.getInferenceDetail(id)
      setInferenceDetail(data)

      // 완료된 경우 세그멘테이션 데이터 로드
      if (data.status === 'COMPLETED') {
        loadSegmentationData(id)
      }
    } catch (err: any) {
      console.error('Failed to load inference detail:', err)
      setError(err.response?.data?.error || '추론 결과를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const loadSegmentationData = async (jobIdToLoad: string) => {
    try {
      setLoadingSegmentation(true)
      setSegmentationError('')
      setSegmentationData(null)

      const data = await aiApi.getSegmentationData(jobIdToLoad)

      const segData: SegmentationData = {
        mri: data.mri,
        groundTruth: data.groundTruth || data.prediction,
        prediction: data.prediction,
        shape: data.shape as [number, number, number],
        mri_channels: data.mri_channels,
      }

      setSegmentationData(segData)
    } catch (err: any) {
      console.error('Failed to load segmentation data:', err)
      setSegmentationError(
        err.response?.data?.error || '세그멘테이션 데이터를 불러오는데 실패했습니다.'
      )
    } finally {
      setLoadingSegmentation(false)
    }
  }

  const handleBack = () => {
    navigate('/ai/m1')
  }

  const handleDelete = async () => {
    if (!jobId || !window.confirm('이 추론 결과를 삭제하시겠습니까?')) {
      return
    }

    try {
      await aiApi.deleteInference(jobId)
      navigate('/ai/m1')
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

  if (loading) {
    return (
      <div className="m1-detail-page">
        <div className="loading-container">
          <div className="spinner" />
          <p className="loading-text">데이터 로딩 중...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="m1-detail-page">
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
      <div className="m1-detail-page">
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
    <div className="m1-detail-page">
      {/* Header */}
      <div className="page-header">
        <div className="header-left">
          <button onClick={handleBack} className="btn-back-icon">
            ← 뒤로
          </button>
          <div>
            <h2 className="page-title">M1 분석 결과 상세</h2>
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
              <div className="info-item">
                <dt>OCS ID</dt>
                <dd>{inferenceDetail.mri_ocs || '-'}</dd>
              </div>
            </dl>
          </div>
          {inferenceDetail.result_data?.processing_time_ms && (
            <div className="info-card">
              <h4 className="card-title">처리 정보</h4>
              <dl className="info-list">
                <div className="info-item">
                  <dt>처리 시간</dt>
                  <dd className="processing-time">
                    {(inferenceDetail.result_data.processing_time_ms / 1000).toFixed(2)}초
                  </dd>
                </div>
                <div className="info-item">
                  <dt>모델 버전</dt>
                  <dd>M1-v2.1.0</dd>
                </div>
              </dl>
            </div>
          )}
        </div>
      </div>

      {/* MRI Thumbnails */}
      {inferenceDetail.status === 'COMPLETED' && (
        <div className="section">
          <h3 className="section-title">MRI 이미지 미리보기</h3>
          <div className="mri-thumbnails-container">
            {/* MRI Channel Thumbnails */}
            {inferenceDetail.mri_thumbnails?.map((thumb) => (
              <div key={thumb.channel} className="mri-thumbnail-card">
                <div className="thumbnail-wrapper">
                  <img
                    src={`${API_BASE_URL}${thumb.url.startsWith('/api/') ? thumb.url.slice(4) : thumb.url}`}
                    alt={thumb.channel}
                    className="thumbnail-image"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement
                      target.style.display = 'none'
                      target.parentElement?.classList.add('thumbnail-error')
                    }}
                  />
                </div>
                <div className="thumbnail-label" style={{ backgroundColor: CHANNEL_COLORS[thumb.channel] }}>
                  {thumb.channel}
                </div>
                <span className="thumbnail-description">{thumb.description}</span>
              </div>
            ))}

            {/* No MRI thumbnails available */}
            {!inferenceDetail.mri_thumbnails?.length && (
              <div className="no-thumbnails-message">
                원본 MRI OCS 연결 정보가 없습니다.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Inference Result */}
      {inferenceDetail.status === 'COMPLETED' && inferenceDetail.result_data && (
        <div className="section">
          <h3 className="section-title">예측 결과</h3>
          <InferenceResult
            result={inferenceDetail.result_data}
            status="completed"
            error=""
            jobId={jobId || ''}
          />
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

      {/* Segmentation Viewer */}
      {inferenceDetail.status === 'COMPLETED' && (
        <div className="section">
          <h3 className="section-title">세그멘테이션 뷰어</h3>

          {loadingSegmentation ? (
            <div className="loading-container">
              <div className="spinner" />
              <p className="loading-text">세그멘테이션 데이터 로딩 중...</p>
            </div>
          ) : segmentationError ? (
            <div className="error-container">
              <h4 className="error-title">세그멘테이션 로드 실패</h4>
              <p className="error-message">{segmentationError}</p>
            </div>
          ) : segmentationData ? (
            <div className="viewer-container">
              <SegMRIViewer
                data={segmentationData}
                title={`세그멘테이션 결과`}
                initialViewMode="axial"
                initialDisplayMode="pred_only"
                maxCanvasSize={600}
              />
            </div>
          ) : (
            <div className="empty-state">
              세그멘테이션 데이터가 없습니다.
            </div>
          )}
        </div>
      )}
    </div>
  )
}
