import { useState, useEffect, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import MMResultViewer from '@/components/MMResultViewer'
import { useAIInferenceWebSocket } from '@/hooks/useAIInferenceWebSocket'
import { ocsApi, aiApi } from '@/services/ai.api'
import './MMInferencePage.css'

interface MMResult {
  patient_id?: string
  job_id?: string
  ocs_id?: number
  risk_group?: {
    predicted_class: string
    probabilities: Record<string, number>
  }
  survival?: {
    hazard_ratio: number
    risk_score: number
    survival_probability_6m?: number
    survival_probability_12m?: number
    model_cindex?: number
  }
  os_days?: {
    predicted_days: number
    predicted_months: number
    confidence_interval?: { lower: number; upper: number }
  }
  recurrence?: {
    predicted_class: string
    recurrence_probability: number
  }
  tmz_response?: {
    predicted_class: string
    responder_probability: number
  }
  recommendation?: string
  processing_time_ms?: number
  model_version?: string
  modalities_used?: string[]
}

interface OCSItem {
  id: number
  ocs_id: string
  patient_name: string
  patient_number: string
  job_role: string
  job_type: string
  ocs_status: string
  confirmed_at: string
}

interface PatientOption {
  patient_number: string
  patient_name: string
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
  gene_ocs: number | null
  protein_ocs: number | null
  result_data: MMResult | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export default function MMInferencePage() {
  const navigate = useNavigate()

  // State
  const [_loading, setLoading] = useState(false)
  const [patients, setPatients] = useState<PatientOption[]>([])
  const [selectedPatient, setSelectedPatient] = useState<string>('')

  // 모달리티별 OCS
  const [mriOcsList, setMriOcsList] = useState<OCSItem[]>([])
  const [geneOcsList, setGeneOcsList] = useState<OCSItem[]>([])
  const [proteinOcsList, setProteinOcsList] = useState<OCSItem[]>([])

  const [selectedMriOcs, setSelectedMriOcs] = useState<number | null>(null)
  const [selectedGeneOcs, setSelectedGeneOcs] = useState<number | null>(null)
  const [selectedProteinOcs, setSelectedProteinOcs] = useState<number | null>(null)
  const [isResearch, setIsResearch] = useState<boolean>(false)

  // 추론 상태
  const [inferenceStatus, setInferenceStatus] = useState<string>('')
  const [inferenceResult, setInferenceResult] = useState<MMResult | null>(null)
  const [error, setError] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [isCached, setIsCached] = useState<boolean>(false)

  // 추론 이력
  const [inferenceHistory, setInferenceHistory] = useState<InferenceRecord[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // WebSocket
  const { lastMessage, isConnected } = useAIInferenceWebSocket()

  useEffect(() => {
    loadAllOcsData()
    loadInferenceHistory()
  }, [])

  useEffect(() => {
    if (lastMessage?.type === 'AI_INFERENCE_RESULT') {
      console.log('Received MM inference result:', lastMessage)

      if (lastMessage.job_id === jobId) {
        if (lastMessage.status === 'COMPLETED') {
          setInferenceStatus('completed')
          if (lastMessage.result) {
            setInferenceResult(lastMessage.result as MMResult)
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

  const loadAllOcsData = async () => {
    try {
      setLoading(true)

      // 병렬로 3개 API 호출 (백엔드에서 이미 필터링됨)
      const [mriResponse, geneResponse, proteinResponse] = await Promise.all([
        ocsApi.getMriOcsList(),
        ocsApi.getRnaSeqOcsList(),
        ocsApi.getBiomarkerOcsList(),
      ])

      const mriData = mriResponse.results || mriResponse || []
      const geneData = geneResponse.results || geneResponse || []
      const proteinData = proteinResponse.results || proteinResponse || []

      console.log('MM Page - API Results:', {
        mri: mriData.length,
        gene: geneData.length,
        protein: proteinData.length
      })

      // 환자 목록 추출 (모든 데이터에서)
      const patientMap = new Map<string, PatientOption>()
      const allData = [...mriData, ...geneData, ...proteinData]
      allData.forEach((item: any) => {
        if (item.patient?.patient_number) {
          patientMap.set(item.patient.patient_number, {
            patient_number: item.patient.patient_number,
            patient_name: item.patient.name || '',
          })
        }
      })
      setPatients(Array.from(patientMap.values()))

      // 각 모달리티별 데이터 매핑
      const mriList = mriData.map(mapOcsItem)
      const geneList = geneData.map(mapOcsItem)
      const proteinList = proteinData.map(mapOcsItem)

      console.log('MM Page - Final counts:', { mri: mriList.length, gene: geneList.length, protein: proteinList.length })

      setMriOcsList(mriList)
      setGeneOcsList(geneList)
      setProteinOcsList(proteinList)
    } catch (err) {
      console.error('Failed to load OCS data:', err)
      setError('OCS 데이터를 불러오는데 실패했습니다.')
    } finally {
      setLoading(false)
    }
  }

  const mapOcsItem = (item: any): OCSItem => ({
    id: item.id,
    ocs_id: item.ocs_id,
    patient_name: item.patient?.name || '',
    patient_number: item.patient?.patient_number || '',
    job_role: item.job_role || '',
    job_type: item.job_type || '',
    ocs_status: item.ocs_status || '',
    confirmed_at: item.confirmed_at || '',
  })

  const loadInferenceHistory = async () => {
    try {
      setLoadingHistory(true)
      const data = await aiApi.getInferenceList('MM')
      setInferenceHistory(data || [])
    } catch (err) {
      console.error('Failed to load MM inference history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  const filteredMriOcsList = useMemo(() => {
    if (isResearch || !selectedPatient) return mriOcsList
    return mriOcsList.filter(ocs => ocs.patient_number === selectedPatient)
  }, [mriOcsList, selectedPatient, isResearch])

  const filteredGeneOcsList = useMemo(() => {
    if (isResearch || !selectedPatient) return geneOcsList
    return geneOcsList.filter(ocs => ocs.patient_number === selectedPatient)
  }, [geneOcsList, selectedPatient, isResearch])

  const filteredProteinOcsList = useMemo(() => {
    if (isResearch || !selectedPatient) return proteinOcsList
    return proteinOcsList.filter(ocs => ocs.patient_number === selectedPatient)
  }, [proteinOcsList, selectedPatient, isResearch])

  const selectedModalityCount = useMemo(() => {
    let count = 0
    if (selectedMriOcs) count++
    if (selectedGeneOcs) count++
    if (selectedProteinOcs) count++
    return count
  }, [selectedMriOcs, selectedGeneOcs, selectedProteinOcs])

  const handlePatientChange = (patientNumber: string) => {
    setSelectedPatient(patientNumber)
    setSelectedMriOcs(null)
    setSelectedGeneOcs(null)
    setSelectedProteinOcs(null)
    setInferenceResult(null)
    setError('')
    setInferenceStatus('')
    setJobId('')
  }

  const handleRequestInference = async () => {
    if (selectedModalityCount < 1) {
      setError('최소 1개 이상의 모달리티를 선택해주세요.')
      return
    }

    try {
      setInferenceStatus('requesting')
      setError('')
      setInferenceResult(null)
      setIsCached(false)

      const response = await aiApi.requestMMInference(
        selectedMriOcs,
        selectedGeneOcs,
        selectedProteinOcs,
        'manual',
        isResearch
      )

      setJobId(response.job_id)

      if (response.cached && response.result) {
        console.log('Using cached MM inference result:', response)
        setIsCached(true)
        setInferenceStatus('completed')
        setInferenceResult(response.result as MMResult)
      } else {
        setInferenceStatus('processing')
        console.log('MM Inference request sent:', response)
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
      console.error('MM Inference error:', err.response?.data || err)
    }
  }

  const handleViewDetail = (record: InferenceRecord) => {
    navigate(`/ai/mm/${record.job_id}`)
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
    <div className="mm-inference-page">
      {/* Header */}
      <div className="page-header">
        <div>
          <h2 className="page-title">MM 멀티모달 분석</h2>
          <p className="page-subtitle">
            MRI, Gene, Protein 데이터를 융합하여 종합적인 예후 예측을 수행합니다.
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
            <span className="toggle-hint">(다른 환자 OCS 조합 가능)</span>
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
            연구용 모드: 서로 다른 환자의 MRI, Gene, Protein 데이터를 조합하여 추론할 수 있습니다.
          </p>
        )}
      </div>

      {/* Modality Selection */}
      {(selectedPatient || isResearch) && (
        <div className="modality-grid">
          {/* MRI */}
          <div className="modality-card mri">
            <h4 className="modality-title">
              <span className="modality-icon">🧠</span>
              MRI 영상
              {selectedMriOcs && <span className="selected-indicator">선택됨</span>}
            </h4>
            <select
              value={selectedMriOcs || ''}
              onChange={(e) => setSelectedMriOcs(e.target.value ? Number(e.target.value) : null)}
              className="modality-select"
            >
              <option value="">선택 안함</option>
              {filteredMriOcsList.map((ocs) => (
                <option key={ocs.id} value={ocs.id}>
                  {isResearch
                    ? `${ocs.ocs_id} (${ocs.patient_number} - ${ocs.patient_name})`
                    : ocs.ocs_id
                  }
                </option>
              ))}
            </select>
            <p className="modality-count">
              {filteredMriOcsList.length}건 이용 가능
            </p>
          </div>

          {/* Gene */}
          <div className="modality-card gene">
            <h4 className="modality-title">
              <span className="modality-icon">🧬</span>
              Gene Expression (RNA-seq)
              {selectedGeneOcs && <span className="selected-indicator">선택됨</span>}
            </h4>
            <select
              value={selectedGeneOcs || ''}
              onChange={(e) => setSelectedGeneOcs(e.target.value ? Number(e.target.value) : null)}
              className="modality-select"
            >
              <option value="">선택 안함</option>
              {filteredGeneOcsList.map((ocs) => (
                <option key={ocs.id} value={ocs.id}>
                  {isResearch
                    ? `${ocs.ocs_id} (${ocs.patient_number} - ${ocs.patient_name})`
                    : ocs.ocs_id
                  }
                </option>
              ))}
            </select>
            <p className="modality-count">
              {filteredGeneOcsList.length}건 이용 가능
            </p>
          </div>

          {/* Protein */}
          <div className="modality-card protein">
            <h4 className="modality-title">
              <span className="modality-icon">🔬</span>
              Protein Biomarker
              {selectedProteinOcs && <span className="selected-indicator">선택됨</span>}
            </h4>
            <select
              value={selectedProteinOcs || ''}
              onChange={(e) => setSelectedProteinOcs(e.target.value ? Number(e.target.value) : null)}
              className="modality-select"
            >
              <option value="">선택 안함</option>
              {filteredProteinOcsList.map((ocs) => (
                <option key={ocs.id} value={ocs.id}>
                  {isResearch
                    ? `${ocs.ocs_id} (${ocs.patient_number} - ${ocs.patient_name})`
                    : ocs.ocs_id
                  }
                </option>
              ))}
            </select>
            <p className="modality-count">
              {filteredProteinOcsList.length}건 이용 가능
            </p>
          </div>
        </div>
      )}

      {/* Inference Button */}
      {(selectedPatient || isResearch) && (
        <div className="inference-action">
          <div className="modality-summary">
            선택된 모달리티: <span className="count">{selectedModalityCount}</span>개
            {selectedModalityCount < 2 && (
              <span className="recommendation">(2개 이상 권장)</span>
            )}
          </div>
          <button
            onClick={handleRequestInference}
            disabled={
              selectedModalityCount < 1 ||
              inferenceStatus === 'requesting' ||
              inferenceStatus === 'processing'
            }
            className={`btn-inference mm ${
              selectedModalityCount < 1 ||
              inferenceStatus === 'requesting' ||
              inferenceStatus === 'processing'
                ? 'disabled'
                : ''
            }`}
          >
            {(inferenceStatus === 'requesting' || inferenceStatus === 'processing') && jobId
              ? `'${jobId}' 요청 중, 현재 페이지를 벗어나도 괜찮습니다`
              : 'MM 멀티모달 추론 요청'}
          </button>
        </div>
      )}

      {/* MM Inference Status */}
      {inferenceStatus === 'processing' && (
        <div className="processing-container mm">
          <div className="spinner mm" />
          <p className="processing-text">MM 멀티모달 추론 중...</p>
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
        <MMResultViewer result={inferenceResult} />
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
              <div className="spinner mm" />
            </div>
          ) : inferenceHistory.length > 0 ? (
            <table className="history-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>환자</th>
                  <th>모달리티</th>
                  <th>상태</th>
                  <th>결과</th>
                  <th>생성일시</th>
                  <th>작업</th>
                </tr>
              </thead>
              <tbody>
                {inferenceHistory.map((record) => (
                  <tr
                    key={record.id}
                    className={record.job_id === jobId ? 'selected mm' : ''}
                  >
                    <td>{record.job_id}</td>
                    <td>
                      {record.patient_name} ({record.patient_number})
                    </td>
                    <td>
                      <div className="modality-badges">
                        {record.mri_ocs && (
                          <span className="modality-badge mri">MRI</span>
                        )}
                        {record.gene_ocs && (
                          <span className="modality-badge gene">Gene</span>
                        )}
                        {record.protein_ocs && (
                          <span className="modality-badge protein">Protein</span>
                        )}
                      </div>
                    </td>
                    <td>{getStatusBadge(record.status)}</td>
                    <td>
                      {record.status === 'COMPLETED' && record.result_data?.risk_group ? (
                        <span>
                          Risk: {record.result_data.risk_group.predicted_class}
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
                      {new Date(record.created_at).toLocaleString('ko-KR')}
                    </td>
                    <td>
                      <div className="action-buttons">
                        {record.status === 'COMPLETED' && (
                          <>
                            <button
                              onClick={() => handleSelectHistory(record)}
                              className="btn-action btn-view mm"
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
