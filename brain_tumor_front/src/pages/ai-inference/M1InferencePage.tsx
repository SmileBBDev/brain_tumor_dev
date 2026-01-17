import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { OCSTable, type OCSItem } from '@/components/OCSTable'
import { InferenceResult } from '@/components/InferenceResult'
import SegMRIViewer, { type SegmentationData } from '@/components/SegMRIViewer'
import { useAIInferenceWebSocket } from '@/hooks/useAIInferenceWebSocket'
import { ocsApi, aiApi } from '@/services/ai.api'
import './M1InferencePage.css'

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

interface InferenceRecord {
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
}

export default function M1InferencePage() {
  const navigate = useNavigate()

  // State
  const [ocsData, setOcsData] = useState<OCSItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedOcs, setSelectedOcs] = useState<OCSItem | null>(null)
  const [inferenceStatus, setInferenceStatus] = useState<string>('')
  const [inferenceResult, setInferenceResult] = useState<M1Result | null>(null)
  const [error, setError] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [isCached, setIsCached] = useState<boolean>(false)

  // 추론 이력
  const [inferenceHistory, setInferenceHistory] = useState<InferenceRecord[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // 세그멘테이션 뷰어
  const [segmentationData, setSegmentationData] = useState<SegmentationData | null>(null)
  const [loadingSegmentation, setLoadingSegmentation] = useState(false)
  const [segmentationError, setSegmentationError] = useState<string>('')

  // WebSocket
  const { lastMessage, isConnected } = useAIInferenceWebSocket()

  // OCS 데이터 로드
  useEffect(() => {
    loadOcsData()
    loadInferenceHistory()
  }, [])

  // WebSocket 메시지 처리
  useEffect(() => {
    if (lastMessage?.type === 'AI_INFERENCE_RESULT') {
      console.log('Received inference result:', lastMessage)

      if (lastMessage.job_id === jobId) {
        if (lastMessage.status === 'COMPLETED') {
          setInferenceStatus('completed')
          if (lastMessage.result) {
            setInferenceResult(lastMessage.result as M1Result)
          }
          setError('')
          // 이력 새로고침
          loadInferenceHistory()
          // 세그멘테이션 데이터 로드
          loadSegmentationData(jobId)
        } else if (lastMessage.status === 'FAILED') {
          setInferenceStatus('failed')
          setError(lastMessage.error || '추론 실패')
        }
      }
    }
  }, [lastMessage, jobId])

  const loadOcsData = async () => {
    try {
      setLoading(true)
      const response = await ocsApi.getAllOcsList()
      const rawData = response.results || response || []

      // API 응답을 OCSItem 형태로 변환 (RIS + MRI + CONFIRMED만 필터링)
      const mappedData: OCSItem[] = rawData
        .filter((item: any) => item.job_role === 'RIS' && item.job_type === 'MRI' && item.ocs_status === 'CONFIRMED')
        .map((item: any) => ({
          id: item.id,
          ocs_id: item.ocs_id,
          patient_name: item.patient?.name || '',
          patient_number: item.patient?.patient_number || '',
          job_role: item.job_role || '',
          job_type: item.job_type || '',
          ocs_status: item.ocs_status || '',
          confirmed_at: item.confirmed_at || '',
          ocs_result: item.ocs_result || null,
          attachments: item.attachments || {},
          worker_result: item.worker_result || {},
        }))

      setOcsData(mappedData)
    } catch (err) {
      console.error('Failed to load OCS data:', err)
      setError('OCS 데이터를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const loadInferenceHistory = async () => {
    try {
      setLoadingHistory(true)
      const data = await aiApi.getInferenceList('M1')
      setInferenceHistory(data || [])
    } catch (err) {
      console.error('Failed to load inference history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // 세그멘테이션 데이터 로드
  const loadSegmentationData = async (jobIdToLoad: string) => {
    try {
      setLoadingSegmentation(true)
      setSegmentationError('')
      setSegmentationData(null)

      const data = await aiApi.getSegmentationData(jobIdToLoad)

      // API 응답을 SegmentationData 형식으로 변환
      const segData: SegmentationData = {
        mri: data.mri,
        groundTruth: data.groundTruth || data.prediction,  // GT가 없으면 prediction 사용
        prediction: data.prediction,
        shape: data.shape as [number, number, number],
        mri_channels: data.mri_channels,  // T1, T1CE, T2, FLAIR 4채널
      }

      setSegmentationData(segData)
      console.log('Segmentation data loaded:', segData.shape, 'channels:', data.mri_channels ? Object.keys(data.mri_channels) : 'none')
    } catch (err: any) {
      console.error('Failed to load segmentation data:', err)
      setSegmentationError(
        err.response?.data?.error || '세그멘테이션 데이터를 불러오는데 실패했습니다.'
      )
    } finally {
      setLoadingSegmentation(false)
    }
  }

  const handleSelectOcs = (ocs: OCSItem) => {
    setSelectedOcs(ocs)
    setInferenceResult(null)
    setError('')
    setInferenceStatus('')
    setJobId('')
    setIsCached(false)
    setSegmentationData(null)
    setSegmentationError('')
  }

  const handleRequestInference = async () => {
    if (!selectedOcs) {
      setError('OCS를 선택해주세요.')
      return
    }

    // DICOM 정보 확인
    const dicomInfo = selectedOcs.worker_result?.dicom
    if (!dicomInfo?.study_uid) {
      setError('선택한 OCS에 DICOM 정보가 없습니다.')
      return
    }

    try {
      setInferenceStatus('requesting')
      setError('')
      setInferenceResult(null)
      setIsCached(false)

      const response = await aiApi.requestM1Inference(selectedOcs.id, 'manual')

      setJobId(response.job_id)

      // 캐시된 결과인 경우 바로 표시
      if (response.cached && response.result) {
        console.log('Using cached inference result:', response)
        setIsCached(true)
        setInferenceStatus('completed')
        setInferenceResult(response.result as M1Result)
      } else {
        // 새 추론 요청 - WebSocket으로 결과 대기
        setInferenceStatus('processing')
        console.log('Inference request sent:', response)
      }
    } catch (err: any) {
      setInferenceStatus('failed')
      setError(
        err.response?.data?.error ||
          err.message ||
          '추론 요청에 실패했습니다.'
      )
    }
  }

  const handleViewDetail = (record: InferenceRecord) => {
    navigate(`/ai/m1/${record.job_id}`)
  }

  const handleSelectHistory = (record: InferenceRecord) => {
    setJobId(record.job_id)
    setInferenceStatus(record.status.toLowerCase())
    setInferenceResult(record.result_data)
    setError(record.error_message || '')
    setIsCached(false)

    // 완료된 추론 결과인 경우 세그멘테이션 데이터 로드
    if (record.status === 'COMPLETED') {
      loadSegmentationData(record.job_id)
    } else {
      setSegmentationData(null)
      setSegmentationError('')
    }
  }

  // 추론 이력 삭제
  const handleDeleteInference = async (record: InferenceRecord) => {
    if (!window.confirm(`${record.job_id} 추론 결과를 삭제하시겠습니까?`)) {
      return
    }

    try {
      await aiApi.deleteInference(record.job_id)
      // 현재 선택된 결과가 삭제되는 경우 초기화
      if (record.job_id === jobId) {
        setJobId('')
        setInferenceResult(null)
        setInferenceStatus('')
        setError('')
        setSegmentationData(null)
        setSegmentationError('')
      }
      // 이력 새로고침
      loadInferenceHistory()
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

  return (
    <div className="m1-inference-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">M1 MRI 분석</h2>
          <p className="page-subtitle">
            MRI 영상을 분석하여 Grade, IDH, MGMT, 생존 예측을 수행합니다.
          </p>
        </div>
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
          <span className="status-text">
            {isConnected ? 'WebSocket 연결됨' : 'WebSocket 연결 안됨'}
          </span>
        </div>
      </div>

      {/* OCS Table */}
      <div className="section">
        <div className="section-header">
          <h3 className="section-title">
            RIS MRI 목록 ({ocsData.length}건)
          </h3>
          <button onClick={loadOcsData} className="btn-link">
            새로고침
          </button>
        </div>

        <OCSTable
          data={ocsData}
          selectedId={selectedOcs?.id || null}
          onSelect={handleSelectOcs}
          loading={loading}
        />
      </div>

      {/* Selected OCS Info & Inference Button */}
      {selectedOcs && (
        <div className="ocs-action-grid">
          <div className="ocs-info-card">
            <h4 className="card-title">선택된 OCS</h4>
            <dl className="info-list">
              <div className="info-item">
                <dt>OCS ID:</dt>
                <dd className="font-medium">{selectedOcs.ocs_id}</dd>
              </div>
              <div className="info-item">
                <dt>환자:</dt>
                <dd>
                  {selectedOcs.patient_name} ({selectedOcs.patient_number})
                </dd>
              </div>
              <div className="info-item">
                <dt>검사유형:</dt>
                <dd>{selectedOcs.job_type}</dd>
              </div>
              <div className="info-item">
                <dt>Study UID:</dt>
                <dd className="truncate">
                  {selectedOcs.worker_result?.dicom?.study_uid || '-'}
                </dd>
              </div>
              <div className="info-item">
                <dt>Series 수:</dt>
                <dd>
                  {selectedOcs.worker_result?.dicom?.series?.length || 0}개
                </dd>
              </div>
            </dl>
          </div>
          <div className="action-button-container">
            <button
              onClick={handleRequestInference}
              disabled={
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing'
              }
              className={`btn-inference ${
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing'
                  ? 'disabled'
                  : ''
              }`}
            >
              {(inferenceStatus === 'requesting' || inferenceStatus === 'processing') && jobId
                ? `'${jobId}' 요청 중, 현재 페이지를 벗어나도 괜찮습니다`
                : 'M1 추론 요청'}
            </button>
          </div>
        </div>
      )}

      {/* Inference Result */}
      <div className="section">
        <h3 className="section-title">추론 결과</h3>

        <InferenceResult
          result={inferenceResult}
          status={inferenceStatus}
          error={error}
          jobId={jobId}
        />

        {/* Request ID */}
        {jobId && (
          <div className="job-id-display">
            Job ID: {jobId}
            {isCached && (
              <span className="cached-badge">캐시됨</span>
            )}
          </div>
        )}
      </div>

      {/* Segmentation Viewer */}
      {(inferenceStatus === 'completed' || segmentationData || loadingSegmentation) && (
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
                title={`세그멘테이션 결과 (Job: ${jobId})`}
                initialViewMode="axial"
                initialDisplayMode="pred_only"
                maxCanvasSize={500}
              />
            </div>
          ) : (
            <div className="empty-state">
              추론 이력에서 완료된 결과를 선택하면 세그멘테이션을 표시합니다.
            </div>
          )}
        </div>
      )}

      {/* Inference History */}
      <div className="section">
        <div className="section-header">
          <h3 className="section-title">
            추론 이력 ({inferenceHistory.length}건)
          </h3>
          <button onClick={loadInferenceHistory} className="btn-link">
            새로고침
          </button>
        </div>

        <div className="history-table-container">
          {loadingHistory ? (
            <div className="loading-container">
              <div className="spinner" />
            </div>
          ) : inferenceHistory.length > 0 ? (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>환자</th>
                  <th>상태</th>
                  <th>결과</th>
                  <th>처리시간</th>
                  <th>생성일시</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {inferenceHistory.map((record) => (
                  <tr
                    key={record.id}
                    className={record.job_id === jobId ? 'selected' : ''}
                  >
                    <td>{record.job_id}</td>
                    <td>
                      {record.patient_name} ({record.patient_number})
                    </td>
                    <td>{getStatusBadge(record.status)}</td>
                    <td>
                      {record.status === 'COMPLETED' && record.result_data?.grade ? (
                        <span>
                          Grade: {record.result_data.grade.predicted_class}
                        </span>
                      ) : record.status === 'FAILED' ? (
                        <span className="text-error truncate">
                          {record.error_message || 'Error'}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      {record.status === 'COMPLETED' && record.result_data?.processing_time_ms ? (
                        <span className="processing-time">
                          {(record.result_data.processing_time_ms / 1000).toFixed(2)}초
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      {new Date(record.created_at).toLocaleString('ko-KR')}
                    </td>
                    <td>
                      <div className="action-buttons">
                        {record.status === 'COMPLETED' && (
                          <>
                            <button
                              onClick={() => handleSelectHistory(record)}
                              className="btn-action btn-view"
                            >
                              결과 보기
                            </button>
                            <button
                              onClick={() => handleViewDetail(record)}
                              className="btn-action btn-detail"
                            >
                              상세
                            </button>
                          </>
                        )}
                        <button
                          onClick={() => handleDeleteInference(record)}
                          className="btn-action btn-delete"
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="empty-state">
              추론 이력이 없습니다.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
