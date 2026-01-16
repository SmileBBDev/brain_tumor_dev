import React, { useState, useEffect, useMemo } from 'react'
import MMResultViewer from '../components/MMResultViewer'
import { useAIInferenceWebSocket } from '../hooks/useAIInferenceWebSocket'
import { ocsApi, aiApi } from '../services/api'

// OCS Item type
interface OCSItem {
  id: number
  ocs_id: string
  patient_name: string
  patient_number: string
  job_role: string
  job_type: string
  ocs_status: string
  confirmed_at: string
  worker_result?: any
}

// MM Result type
interface MMResult {
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
  recurrence?: {
    predicted_class: string
    probability: number
    recurrence_probability?: number
  }
  modality_contributions?: {
    mri: number
    gene: number
    protein: number
  }
  cross_attention_weights?: {
    mri_gene?: number[]
    mri_protein?: number[]
    gene_protein?: number[]
  }
  xai?: any
  processing_time_ms?: number
  model_version?: string
  input_modalities?: string[]
}

interface InferenceRecord {
  id: number
  job_id: string
  model_type: string
  status: string
  mode: string
  patient_name: string
  patient_number: string
  result_data: MMResult | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

// Available OCS by category (from API)
interface AvailableOCS {
  patient_id: string
  patient_name: string
  mri_ocs: Array<{
    ocs_id: number
    ocs_number: string
    job_role: string
    job_type: string
    job_date: string | null
  }>
  rna_ocs: Array<{
    ocs_id: number
    ocs_number: string
    job_role: string
    job_type: string
    job_date: string | null
  }>
  protein_ocs: Array<{
    ocs_id: number
    ocs_number: string
    job_role: string
    job_type: string
    job_date: string | null
  }>
}

export default function MMInferencePage() {
  // All OCS data for patient list
  const [allOcsData, setAllOcsData] = useState<OCSItem[]>([])
  const [loading, setLoading] = useState(true)

  // Available OCS for MM
  const [availableOCS, setAvailableOCS] = useState<AvailableOCS | null>(null)
  const [loadingAvailable, setLoadingAvailable] = useState(false)

  // Selected patient
  const [selectedPatient, setSelectedPatient] = useState<string>('')

  // Selected OCS for each modality
  const [selectedMriOcs, setSelectedMriOcs] = useState<number | null>(null)
  const [selectedGeneOcs, setSelectedGeneOcs] = useState<number | null>(null)
  const [selectedProteinOcs, setSelectedProteinOcs] = useState<number | null>(null)

  // Inference state
  const [inferenceStatus, setInferenceStatus] = useState<string>('')
  const [inferenceResult, setInferenceResult] = useState<MMResult | null>(null)
  const [error, setError] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [isCached, setIsCached] = useState<boolean>(false)

  // Inference history
  const [inferenceHistory, setInferenceHistory] = useState<InferenceRecord[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // WebSocket
  const { lastMessage, isConnected } = useAIInferenceWebSocket()

  // Load all OCS data
  useEffect(() => {
    loadOcsData()
    loadInferenceHistory()
  }, [])

  // WebSocket message handling
  useEffect(() => {
    if (lastMessage?.type === 'AI_INFERENCE_RESULT') {
      console.log('Received inference result:', lastMessage)

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
          setError(lastMessage.error || 'Inference failed')
        }
      }
    }
  }, [lastMessage, jobId])

  // Load available OCS when patient changes
  useEffect(() => {
    if (selectedPatient) {
      loadAvailableOCS(selectedPatient)
    } else {
      setAvailableOCS(null)
      setSelectedMriOcs(null)
      setSelectedGeneOcs(null)
      setSelectedProteinOcs(null)
    }
  }, [selectedPatient])

  // Get unique patients from OCS data
  const uniquePatients = useMemo(() => {
    const patientMap = new Map<string, { name: string; number: string }>()
    allOcsData.forEach(ocs => {
      if (!patientMap.has(ocs.patient_number)) {
        patientMap.set(ocs.patient_number, {
          name: ocs.patient_name,
          number: ocs.patient_number
        })
      }
    })
    return Array.from(patientMap.values()).sort((a, b) => a.number.localeCompare(b.number))
  }, [allOcsData])

  const loadOcsData = async () => {
    try {
      setLoading(true)
      const response = await ocsApi.getAllOcsList()
      const rawData = response.results || response || []

      // Map all OCS data
      const mappedData: OCSItem[] = rawData.map((item: any) => ({
        id: item.id,
        ocs_id: item.ocs_id,
        patient_name: item.patient?.name || '',
        patient_number: item.patient?.patient_number || '',
        job_role: item.job_role || '',
        job_type: item.job_type || '',
        ocs_status: item.ocs_status || '',
        confirmed_at: item.confirmed_at || '',
        worker_result: item.worker_result || {},
      }))

      setAllOcsData(mappedData)
    } catch (err) {
      console.error('Failed to load OCS data:', err)
      setError('Failed to load OCS data.')
    } finally {
      setLoading(false)
    }
  }

  const loadAvailableOCS = async (patientId: string) => {
    try {
      setLoadingAvailable(true)
      const data = await aiApi.getMMAvailableOCS(patientId)
      setAvailableOCS(data)

      // Reset selections
      setSelectedMriOcs(null)
      setSelectedGeneOcs(null)
      setSelectedProteinOcs(null)
    } catch (err: any) {
      console.error('Failed to load available OCS:', err)
      setError(err.response?.data?.error || 'Failed to load available OCS.')
      setAvailableOCS(null)
    } finally {
      setLoadingAvailable(false)
    }
  }

  const loadInferenceHistory = async () => {
    try {
      setLoadingHistory(true)
      const data = await aiApi.getInferenceList('MM')
      setInferenceHistory(data || [])
    } catch (err) {
      console.error('Failed to load inference history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  const handlePatientChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const patientNumber = e.target.value
    setSelectedPatient(patientNumber)
    setInferenceResult(null)
    setError('')
    setInferenceStatus('')
    setJobId('')
    setIsCached(false)
  }

  const handleRequestInference = async () => {
    // At least one modality must be selected
    if (!selectedMriOcs && !selectedGeneOcs && !selectedProteinOcs) {
      setError('최소 하나의 모달리티를 선택해주세요.')
      return
    }

    // At least two modalities recommended for multimodal
    const selectedCount = [selectedMriOcs, selectedGeneOcs, selectedProteinOcs].filter(Boolean).length
    if (selectedCount < 2) {
      const confirmSingle = window.confirm(
        '멀티모달 분석을 위해 2개 이상의 모달리티를 선택하는 것을 권장합니다.\n' +
        '선택한 모달리티만으로 진행하시겠습니까?'
      )
      if (!confirmSingle) return
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
        'manual'
      )

      setJobId(response.job_id)

      // If cached result
      if (response.cached && response.result) {
        console.log('Using cached inference result:', response)
        setIsCached(true)
        setInferenceStatus('completed')
        setInferenceResult(response.result as MMResult)
      } else {
        // New inference - wait for WebSocket
        setInferenceStatus('processing')
        console.log('Inference request sent:', response)
      }
    } catch (err: any) {
      setInferenceStatus('failed')
      setError(
        err.response?.data?.error ||
          err.message ||
          'Inference request failed.'
      )
    }
  }

  const handleSelectHistory = async (record: InferenceRecord) => {
    setJobId(record.job_id)
    setInferenceStatus(record.status.toLowerCase())
    setInferenceResult(record.result_data)
    setError(record.error_message || '')
    setIsCached(false)
  }

  // Delete inference
  const handleDeleteInference = async (record: InferenceRecord) => {
    if (!window.confirm(`Delete inference ${record.job_id}?`)) {
      return
    }

    try {
      await aiApi.deleteInference(record.job_id)
      // Reset if current result is deleted
      if (record.job_id === jobId) {
        setJobId('')
        setInferenceResult(null)
        setInferenceStatus('')
        setError('')
      }
      loadInferenceHistory()
    } catch (err: any) {
      console.error('Failed to delete inference:', err)
      alert(err.response?.data?.error || 'Delete failed.')
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
        return <span className="px-2 py-1 text-xs rounded bg-green-100 text-green-800">Completed</span>
      case 'PROCESSING':
        return <span className="px-2 py-1 text-xs rounded bg-blue-100 text-blue-800">Processing</span>
      case 'PENDING':
        return <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">Pending</span>
      case 'FAILED':
        return <span className="px-2 py-1 text-xs rounded bg-red-100 text-red-800">Failed</span>
      default:
        return <span className="px-2 py-1 text-xs rounded bg-gray-100 text-gray-800">{status}</span>
    }
  }

  // Get modality info text
  const getModalityInfoText = () => {
    const parts = []
    if (selectedMriOcs) parts.push('MRI')
    if (selectedGeneOcs) parts.push('Gene')
    if (selectedProteinOcs) parts.push('Protein')
    return parts.length > 0 ? parts.join(' + ') : '선택된 모달리티 없음'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">MM Multimodal Analysis</h2>
          <p className="text-sm text-gray-500 mt-1">
            MRI + Gene Expression + Protein 데이터를 융합하여 생존 및 재발 예측을 수행합니다.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <span
            className={`h-2 w-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-red-500'
            }`}
          />
          <span className="text-sm text-gray-500">
            {isConnected ? 'WebSocket Connected' : 'WebSocket Disconnected'}
          </span>
        </div>
      </div>

      {/* Patient Selection */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">1. 환자 선택</h3>

        {loading ? (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto" />
            <p className="text-gray-500 mt-2">Loading patients...</p>
          </div>
        ) : (
          <select
            value={selectedPatient}
            onChange={handlePatientChange}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-teal-500 focus:border-teal-500"
          >
            <option value="">-- 환자를 선택하세요 --</option>
            {uniquePatients.map(patient => (
              <option key={patient.number} value={patient.number}>
                {patient.name} ({patient.number})
              </option>
            ))}
          </select>
        )}
      </div>

      {/* OCS Selection - 3 Combo Boxes */}
      {selectedPatient && (
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">2. 모달리티별 OCS 선택</h3>

          {loadingAvailable ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto" />
              <p className="text-gray-500 mt-2">Loading available OCS...</p>
            </div>
          ) : availableOCS ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* MRI OCS Selection */}
              <div className="space-y-2">
                <label className="flex items-center text-sm font-medium text-gray-700">
                  <span className="text-xl mr-2">🧠</span>
                  MRI
                  <span className="ml-2 text-xs text-gray-400">
                    ({availableOCS.mri_ocs?.length || 0}개)
                  </span>
                </label>
                <select
                  value={selectedMriOcs || ''}
                  onChange={(e) => setSelectedMriOcs(e.target.value ? Number(e.target.value) : null)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-indigo-50"
                >
                  <option value="">-- MRI OCS 선택 (선택사항) --</option>
                  {availableOCS.mri_ocs?.map(item => (
                    <option key={item.ocs_id} value={item.ocs_id}>
                      OCS #{item.ocs_id} ({item.ocs_number})
                    </option>
                  ))}
                </select>
                {availableOCS.mri_ocs?.length === 0 && (
                  <p className="text-xs text-orange-600">MRI OCS가 없습니다.</p>
                )}
              </div>

              {/* Gene OCS Selection */}
              <div className="space-y-2">
                <label className="flex items-center text-sm font-medium text-gray-700">
                  <span className="text-xl mr-2">🧬</span>
                  Gene Expression (RNA_SEQ)
                  <span className="ml-2 text-xs text-gray-400">
                    ({availableOCS.rna_ocs?.length || 0}개)
                  </span>
                </label>
                <select
                  value={selectedGeneOcs || ''}
                  onChange={(e) => setSelectedGeneOcs(e.target.value ? Number(e.target.value) : null)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 bg-green-50"
                >
                  <option value="">-- Gene OCS 선택 (선택사항) --</option>
                  {availableOCS.rna_ocs?.map(item => (
                    <option key={item.ocs_id} value={item.ocs_id}>
                      OCS #{item.ocs_id} ({item.ocs_number})
                    </option>
                  ))}
                </select>
                {availableOCS.rna_ocs?.length === 0 && (
                  <p className="text-xs text-orange-600">RNA_SEQ OCS가 없습니다.</p>
                )}
              </div>

              {/* Protein OCS Selection */}
              <div className="space-y-2">
                <label className="flex items-center text-sm font-medium text-gray-700">
                  <span className="text-xl mr-2">🔬</span>
                  Protein
                  <span className="ml-2 text-xs text-gray-400">
                    ({availableOCS.protein_ocs?.length || 0}개)
                  </span>
                </label>
                <select
                  value={selectedProteinOcs || ''}
                  onChange={(e) => setSelectedProteinOcs(e.target.value ? Number(e.target.value) : null)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 bg-amber-50"
                >
                  <option value="">-- Protein OCS 선택 (선택사항) --</option>
                  {availableOCS.protein_ocs?.map(item => (
                    <option key={item.ocs_id} value={item.ocs_id}>
                      OCS #{item.ocs_id} ({item.ocs_number})
                    </option>
                  ))}
                </select>
                {availableOCS.protein_ocs?.length === 0 && (
                  <p className="text-xs text-orange-600">Protein OCS가 없습니다.</p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-gray-500 text-center py-4">
              사용 가능한 OCS 정보를 불러올 수 없습니다.
            </p>
          )}
        </div>
      )}

      {/* Inference Request Button */}
      {selectedPatient && availableOCS && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">3. 추론 요청</h3>
              <p className="text-sm text-gray-500 mt-1">
                선택된 모달리티: <span className="font-medium text-teal-600">{getModalityInfoText()}</span>
              </p>
            </div>
            <button
              onClick={handleRequestInference}
              disabled={
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing' ||
                (!selectedMriOcs && !selectedGeneOcs && !selectedProteinOcs)
              }
              className={`py-3 px-8 rounded-lg font-medium text-white transition ${
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing' ||
                (!selectedMriOcs && !selectedGeneOcs && !selectedProteinOcs)
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-teal-600 hover:bg-teal-700'
              }`}
            >
              {inferenceStatus === 'requesting'
                ? 'Requesting...'
                : inferenceStatus === 'processing'
                ? 'MM Inference in Progress...'
                : 'Request MM Inference'}
            </button>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-600">{error}</p>
        </div>
      )}

      {/* Processing Status */}
      {inferenceStatus === 'processing' && (
        <div className="bg-teal-50 rounded-lg p-6 text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-teal-600 mx-auto" />
          <p className="text-gray-600 mt-3">MM Multimodal Inference in progress...</p>
          <p className="text-sm text-gray-500 mt-1">Job ID: {jobId}</p>
        </div>
      )}

      {/* Inference Result */}
      {(inferenceStatus === 'completed' && inferenceResult) && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">추론 결과</h3>
            {jobId && (
              <div className="text-xs text-gray-500">
                Job ID: {jobId}
                {isCached && (
                  <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-700 rounded">
                    Cached
                  </span>
                )}
              </div>
            )}
          </div>
          <MMResultViewer result={inferenceResult} />
        </div>
      )}

      {/* Inference History */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            MM Inference History ({inferenceHistory.length} items)
          </h3>
          <button
            onClick={loadInferenceHistory}
            className="text-sm text-teal-600 hover:text-teal-800"
          >
            Refresh
          </button>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loadingHistory ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600 mx-auto" />
            </div>
          ) : inferenceHistory.length > 0 ? (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Job ID
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Patient
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Result
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Processing Time
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {inferenceHistory.map((record) => (
                  <tr
                    key={record.id}
                    className={`hover:bg-gray-50 ${
                      record.job_id === jobId ? 'bg-teal-50' : ''
                    }`}
                  >
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {record.job_id}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {record.patient_name} ({record.patient_number})
                    </td>
                    <td className="px-4 py-3">
                      {getStatusBadge(record.status)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {record.status === 'COMPLETED' && record.result_data?.survival_risk ? (
                        <span>
                          Risk: {record.result_data.survival_risk.risk_score?.toFixed(3)}
                        </span>
                      ) : record.status === 'FAILED' ? (
                        <span className="text-red-600 truncate max-w-[150px] block">
                          {record.error_message || 'Error'}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600">
                      {record.status === 'COMPLETED' && record.result_data?.processing_time_ms ? (
                        <span className="font-medium text-teal-600">
                          {(record.result_data.processing_time_ms / 1000).toFixed(2)}s
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500">
                      {new Date(record.created_at).toLocaleString('ko-KR')}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center space-x-2">
                        {record.status === 'COMPLETED' && (
                          <button
                            onClick={() => handleSelectHistory(record)}
                            className="text-sm text-teal-600 hover:text-teal-800"
                          >
                            결과보기
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteInference(record)}
                          className="text-sm text-red-600 hover:text-red-800"
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
            <div className="text-center py-8 text-gray-500">
              No inference history.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
