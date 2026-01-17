import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { OCSTable, type OCSItem } from '@/components/OCSTable'
import GeneVisualization from '@/components/GeneVisualization'
import type { GeneExpressionData } from '@/components/GeneVisualization/GeneVisualization'
import MGResultViewer from '@/components/MGResultViewer'
import { useAIInferenceWebSocket } from '@/hooks/useAIInferenceWebSocket'
import { ocsApi, aiApi } from '@/services/ai.api'
import './MGInferencePage.css'

interface PatientOption {
  patient_number: string
  patient_name: string
}

interface MGResult {
  patient_id?: string
  survival_risk?: {
    risk_score: number
    risk_percentile?: number
    risk_category?: string
    model_cindex?: number
  }
  survival_time?: {
    predicted_days: number
    predicted_months: number
    confidence_interval?: { lower: number; upper: number }
  }
  grade?: {
    predicted_class: string
    probability: number
    lgg_probability?: number
    hgg_probability?: number
    probabilities?: Record<string, number>
  }
  recurrence?: {
    predicted_class: string
    probability: number
    recurrence_probability?: number
  }
  tmz_response?: {
    predicted_class: string
    probability: number
    responder_probability?: number
  }
  xai?: {
    attention_weights?: number[]
    top_genes?: Array<{
      rank: number
      gene: string
      attention_score: number
      expression_zscore: number
    }>
    gene_importance_summary?: {
      total_genes: number
      attention_mean: number
      attention_std: number
      attention_max: number
      attention_min: number
    }
  }
  processing_time_ms?: number
  input_genes_count?: number
  model_version?: string
}

interface InferenceRecord {
  id: number
  job_id: string
  model_type: string
  status: string
  mode: string
  patient_name: string
  patient_number: string
  gene_ocs: number | null
  result_data: MGResult | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export default function MGInferencePage() {
  const navigate = useNavigate()

  // State
  const [ocsData, setOcsData] = useState<OCSItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedOcs, setSelectedOcs] = useState<OCSItem | null>(null)
  const [inferenceStatus, setInferenceStatus] = useState<string>('')
  const [inferenceResult, setInferenceResult] = useState<MGResult | null>(null)
  const [error, setError] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [isCached, setIsCached] = useState<boolean>(false)

  // 환자 선택 및 연구용 모드
  const [patients, setPatients] = useState<PatientOption[]>([])
  const [selectedPatient, setSelectedPatient] = useState<string>('')
  const [isResearch, setIsResearch] = useState<boolean>(false)

  // Gene Expression 시각화
  const [geneExpData, setGeneExpData] = useState<GeneExpressionData | null>(null)
  const [loadingGeneExp, setLoadingGeneExp] = useState(false)
  const [geneExpError, setGeneExpError] = useState<string>('')

  // 추론 이력
  const [inferenceHistory, setInferenceHistory] = useState<InferenceRecord[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

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
      console.log('Received MG inference result:', lastMessage)

      if (lastMessage.job_id === jobId) {
        if (lastMessage.status === 'COMPLETED') {
          setInferenceStatus('completed')
          if (lastMessage.result) {
            setInferenceResult(lastMessage.result as MGResult)
          }
          setError('')
          loadInferenceHistory()
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

      // 백엔드에서 이미 필터링된 데이터 조회 (LIS + RNA_SEQ + CONFIRMED)
      const response = await ocsApi.getRnaSeqOcsList()
      const rawData = response.results || response || []

      console.log('MG Page - RNA_SEQ CONFIRMED count:', rawData.length)

      // 환자 목록 추출
      const patientMap = new Map<string, PatientOption>()
      rawData.forEach((item: any) => {
        if (item.patient?.patient_number) {
          patientMap.set(item.patient.patient_number, {
            patient_number: item.patient.patient_number,
            patient_name: item.patient.name || '',
          })
        }
      })
      setPatients(Array.from(patientMap.values()))

      // 데이터 매핑
      const mappedData: OCSItem[] = rawData.map((item: any) => ({
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

  // 환자별 OCS 필터링
  const filteredOcsData = useMemo(() => {
    if (isResearch || !selectedPatient) return ocsData
    return ocsData.filter(ocs => ocs.patient_number === selectedPatient)
  }, [ocsData, selectedPatient, isResearch])

  const handlePatientChange = (patientNumber: string) => {
    setSelectedPatient(patientNumber)
    setSelectedOcs(null)
    setInferenceResult(null)
    setError('')
    setInferenceStatus('')
    setJobId('')
    setGeneExpData(null)
  }

  const loadInferenceHistory = async () => {
    try {
      setLoadingHistory(true)
      const data = await aiApi.getInferenceList('MG')
      setInferenceHistory(data || [])
    } catch (err) {
      console.error('Failed to load MG inference history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Gene Expression 데이터 로드
  const loadGeneExpressionData = async (ocsId: number) => {
    try {
      setLoadingGeneExp(true)
      setGeneExpError('')
      const data = await aiApi.getGeneExpressionData(ocsId)
      setGeneExpData(data)
    } catch (err: any) {
      console.error('Failed to load gene expression data:', err)
      setGeneExpError(err.response?.data?.error || '유전자 발현 데이터를 불러오는데 실패했습니다.')
    } finally {
      setLoadingGeneExp(false)
    }
  }

  const handleSelectOcs = (ocs: OCSItem) => {
    setSelectedOcs(ocs)
    setInferenceResult(null)
    setError('')
    setInferenceStatus('')
    setJobId('')
    setIsCached(false)
    loadGeneExpressionData(ocs.id)
  }

  const handleRequestInference = async () => {
    if (!selectedOcs) {
      setError('OCS를 선택해주세요.')
      return
    }

    try {
      setInferenceStatus('requesting')
      setError('')
      setInferenceResult(null)
      setIsCached(false)

      const response = await aiApi.requestMGInference(selectedOcs.id, 'manual')

      setJobId(response.job_id)

      if (response.cached && response.result) {
        console.log('Using cached MG inference result:', response)
        setIsCached(true)
        setInferenceStatus('completed')
        setInferenceResult(response.result as MGResult)
      } else {
        setInferenceStatus('processing')
        console.log('MG Inference request sent:', response)
      }
    } catch (err: any) {
      setInferenceStatus('failed')
      // 다양한 에러 응답 형식 처리
      const errorMessage =
        err.response?.data?.detail ||  // DRF 기본 에러 형식
        err.response?.data?.error ||
        err.response?.data?.message ||
        err.message ||
        '추론 요청에 실패했습니다.'
      setError(errorMessage)
      console.error('MG Inference error:', err.response?.data || err)
    }
  }

  const handleViewDetail = (record: InferenceRecord) => {
    navigate(`/ai/mg/${record.job_id}`)
  }

  const handleSelectHistory = (record: InferenceRecord) => {
    setJobId(record.job_id)
    setInferenceStatus(record.status.toLowerCase())
    setInferenceResult(record.result_data)
    setError(record.error_message || '')
    setIsCached(false)
  }

  const handleDeleteInference = async (record: InferenceRecord) => {
    if (!window.confirm(`${record.job_id} 추론 결과를 삭제하시겠습니까?`)) {
      return
    }

    try {
      await aiApi.deleteInference(record.job_id)
      if (record.job_id === jobId) {
        setJobId('')
        setInferenceResult(null)
        setInferenceStatus('')
        setError('')
      }
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
    <div className="mg-inference-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">MG Gene Expression 분석</h2>
          <p className="page-subtitle">
            RNA-seq 유전자 발현 데이터를 분석하여 생존 예측, Grade, 재발, TMZ 반응을 예측합니다.
          </p>
        </div>
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`} />
          <span className="status-text">
            {isConnected ? 'WebSocket 연결됨' : 'WebSocket 연결 안됨'}
          </span>
        </div>
      </div>

      {/* Patient Selection & Research Mode */}
      <div className="patient-selection-card">
        <div className="card-header">
          <h3 className="card-title">환자 선택</h3>
          <label className="research-toggle">
            <input
              type="checkbox"
              checked={isResearch}
              onChange={(e) => setIsResearch(e.target.checked)}
            />
            <span className="toggle-label">연구용</span>
            <span className="toggle-hint">(모든 환자 데이터 표시)</span>
          </label>
        </div>
        <select
          value={selectedPatient}
          onChange={(e) => handlePatientChange(e.target.value)}
          className="patient-select"
          disabled={isResearch}
        >
          <option value="">{isResearch ? '연구용 모드: 모든 환자 데이터 표시' : '환자를 선택하세요'}</option>
          {patients.map((patient) => (
            <option key={patient.patient_number} value={patient.patient_number}>
              {patient.patient_number} - {patient.patient_name}
            </option>
          ))}
        </select>
        {isResearch && (
          <p className="research-notice">
            연구용 모드: 모든 환자의 RNA-seq 데이터를 조회할 수 있습니다.
          </p>
        )}
      </div>

      {/* OCS Table */}
      {(selectedPatient || isResearch) && (
        <div className="section">
          <div className="section-header">
            <h3 className="section-title">
              LIS RNA_SEQ 목록 ({filteredOcsData.length}건)
            </h3>
            <button onClick={loadOcsData} className="btn-link">
              새로고침
            </button>
          </div>

          <OCSTable
            data={filteredOcsData}
            selectedId={selectedOcs?.id || null}
            onSelect={handleSelectOcs}
            loading={loading}
          />
        </div>
      )}

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
                <dt>파일경로:</dt>
                <dd className="truncate">
                  {selectedOcs.worker_result?.file_path || '-'}
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
              className={`btn-inference mg ${
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing'
                  ? 'disabled'
                  : ''
              }`}
            >
              {(inferenceStatus === 'requesting' || inferenceStatus === 'processing') && jobId
                ? `'${jobId}' 요청 중, 현재 페이지를 벗어나도 괜찮습니다`
                : 'MG 추론 요청'}
            </button>
          </div>
        </div>
      )}

      {/* Gene Expression Data Visualization */}
      {selectedOcs && (
        <GeneVisualization
          data={geneExpData}
          patientId={selectedOcs.patient_number}
          loading={loadingGeneExp}
          error={geneExpError}
        />
      )}

      {/* MG Inference Status */}
      {inferenceStatus === 'processing' && (
        <div className="processing-container mg">
          <div className="spinner mg" />
          <p className="processing-text">MG 모델 추론 중...</p>
          <p className="processing-subtext">Job ID: {jobId}</p>
        </div>
      )}

      {inferenceStatus === 'failed' && (
        <div className="error-container">
          <h3 className="error-title">추론 실패</h3>
          <p className="error-message">{error}</p>
        </div>
      )}

      {inferenceStatus === 'completed' && inferenceResult && (
        <MGResultViewer result={inferenceResult} />
      )}

      {/* Request ID */}
      {jobId && (
        <div className="job-id-display">
          Job ID: {jobId}
          {isCached && (
            <span className="cached-badge">캐시됨</span>
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
              <div className="spinner mg" />
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
                    className={record.job_id === jobId ? 'selected mg' : ''}
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
                        <span className="processing-time mg">
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
                              className="btn-action btn-view mg"
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
