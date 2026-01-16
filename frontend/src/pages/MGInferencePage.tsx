import React, { useState, useEffect } from 'react'
import { OCSTable, OCSItem } from '../components/OCSTable'
import MGResultViewer from '../components/MGResultViewer'
import GeneVisualization, { GeneExpressionData } from '../components/GeneVisualization'
import { useAIInferenceWebSocket } from '../hooks/useAIInferenceWebSocket'
import { ocsApi, aiApi } from '../services/api'

interface MGResult {
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
    lgg_probability: number
    hgg_probability: number
    probabilities?: Record<string, number>
  }
  recurrence?: {
    predicted_class: string
    probability: number
    recurrence_probability: number
  }
  tmz_response?: {
    predicted_class: string
    probability: number
    responder_probability: number
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
    deg_cluster_scores?: Record<string, {
      score: number
      gene_count: number
      top_genes: string[]
    }>
    deg_encoded_features?: number[]
    expression_stats?: {
      mean: number
      std: number
      min: number
      max: number
      nonzero_count: number
      positive_count: number
      negative_count: number
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
  rna_ocs: number | null
  result_data: MGResult | null
  error_message: string | null
  created_at: string
  completed_at: string | null
}

export default function MGInferencePage() {
  // State
  const [ocsData, setOcsData] = useState<OCSItem[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedOcs, setSelectedOcs] = useState<OCSItem | null>(null)
  const [inferenceStatus, setInferenceStatus] = useState<string>('')
  const [inferenceResult, setInferenceResult] = useState<MGResult | null>(null)
  const [error, setError] = useState<string>('')
  const [jobId, setJobId] = useState<string>('')
  const [isCached, setIsCached] = useState<boolean>(false)

  // Inference history
  const [inferenceHistory, setInferenceHistory] = useState<InferenceRecord[]>([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // Gene visualization data (서버에서 처리된 데이터)
  const [geneExpressionData, setGeneExpressionData] = useState<GeneExpressionData | null>(null)
  const [geneLoading, setGeneLoading] = useState(false)
  const [geneError, setGeneError] = useState<string | null>(null)

  // WebSocket
  const { lastMessage, isConnected } = useAIInferenceWebSocket()

  // Load OCS data
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
            setInferenceResult(lastMessage.result as MGResult)
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

  const loadOcsData = async () => {
    try {
      setLoading(true)
      const response = await ocsApi.getAllOcsList()
      const rawData = response.results || response || []

      // Filter for LIS + RNA_SEQ + CONFIRMED only
      const mappedData: OCSItem[] = rawData
        .filter((item: any) => item.job_role === 'LIS' && item.job_type === 'RNA_SEQ' && item.ocs_status === 'CONFIRMED')
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
      setError('Failed to load OCS data.')
    } finally {
      setLoading(false)
    }
  }

  const loadInferenceHistory = async () => {
    try {
      setLoadingHistory(true)
      const data = await aiApi.getInferenceList('MG')
      setInferenceHistory(data || [])
    } catch (err) {
      console.error('Failed to load inference history:', err)
    } finally {
      setLoadingHistory(false)
    }
  }

  // Load gene expression data from API (서버에서 처리된 데이터)
  const loadGeneExpressionData = async (ocsId: number) => {
    setGeneLoading(true)
    setGeneError(null)
    try {
      const response = await fetch(`/api/ai/mg/gene-expression/${ocsId}/`)
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Gene Expression 데이터 로드 실패')
      }
      const data: GeneExpressionData = await response.json()
      setGeneExpressionData(data)
    } catch (err: any) {
      console.error('Failed to load gene expression data:', err)
      setGeneError(err.message || 'Gene Expression 데이터 로드 실패')
      setGeneExpressionData(null)
    } finally {
      setGeneLoading(false)
    }
  }

  const handleSelectOcs = (ocs: OCSItem) => {
    setSelectedOcs(ocs)
    setInferenceResult(null)
    setError('')
    setInferenceStatus('')
    setJobId('')
    setIsCached(false)
    // 서버에서 처리된 gene expression 데이터 로드
    loadGeneExpressionData(ocs.id)
  }

  const handleRequestInference = async () => {
    if (!selectedOcs) {
      setError('Please select an OCS.')
      return
    }

    // CSV 파일 체크는 백엔드에서 수행 (CDSS_STORAGE에서 직접 확인)
    // worker_result.files가 없어도 기본 파일명(gene_expression.csv)으로 시도

    try {
      setInferenceStatus('requesting')
      setError('')
      setInferenceResult(null)
      setIsCached(false)

      const response = await aiApi.requestMGInference(selectedOcs.id, 'manual')

      setJobId(response.job_id)

      // If cached result
      if (response.cached && response.result) {
        console.log('Using cached inference result:', response)
        setIsCached(true)
        setInferenceStatus('completed')
        setInferenceResult(response.result as MGResult)
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

    // rna_ocs가 있으면 gene expression 데이터도 로드
    if (record.rna_ocs) {
      loadGeneExpressionData(record.rna_ocs)
    }
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

  // Get CSV filename from worker_result
  const getCsvFilename = (ocs: OCSItem): string => {
    const files = ocs.worker_result?.files
    if (files && files.length > 0) {
      return files[0].name || files[0]
    }
    // 기본 파일명 (백엔드에서도 동일하게 처리)
    return 'gene_expression.csv'
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">MG Gene Expression Analysis</h2>
          <p className="text-sm text-gray-500 mt-1">
            Analyze gene expression data for Survival Risk, Grade, Recurrence, and TMZ Response prediction.
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

      {/* OCS Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            LIS RNA_SEQ OCS List ({ocsData.length} items)
          </h3>
          <button
            onClick={loadOcsData}
            className="text-sm text-purple-600 hover:text-purple-800"
          >
            Refresh
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
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-purple-50 rounded-lg p-4 text-sm">
            <h4 className="font-medium text-gray-900 mb-2">Selected OCS</h4>
            <dl className="space-y-1 text-gray-600">
              <div className="flex justify-between">
                <dt>OCS ID:</dt>
                <dd className="font-medium">{selectedOcs.ocs_id}</dd>
              </div>
              <div className="flex justify-between">
                <dt>Patient:</dt>
                <dd>
                  {selectedOcs.patient_name} ({selectedOcs.patient_number})
                </dd>
              </div>
              <div className="flex justify-between">
                <dt>Job Type:</dt>
                <dd>{selectedOcs.job_type}</dd>
              </div>
              <div className="flex justify-between">
                <dt>CSV File:</dt>
                <dd className="truncate max-w-[200px]">
                  {getCsvFilename(selectedOcs)}
                </dd>
              </div>
            </dl>
          </div>
          <div className="flex items-center">
            <button
              onClick={handleRequestInference}
              disabled={
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing'
              }
              className={`w-full py-3 px-4 rounded-lg font-medium text-white transition ${
                inferenceStatus === 'requesting' ||
                inferenceStatus === 'processing'
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-purple-600 hover:bg-purple-700'
              }`}
            >
              {inferenceStatus === 'requesting'
                ? 'Requesting...'
                : inferenceStatus === 'processing'
                ? 'MG Inference in Progress...'
                : 'Request MG Inference'}
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

      {/* Inference Result with Gene Visualization */}
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
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
            {/* Left: Gene Visualization */}
            <div className="lg:col-span-4">
              <GeneVisualization
                data={geneExpressionData}
                patientId={selectedOcs?.patient_number}
                loading={geneLoading}
                error={geneError}
              />
            </div>
            {/* Right: Result Viewer */}
            <div className="lg:col-span-8">
              <MGResultViewer result={inferenceResult} />
            </div>
          </div>
        </div>
      )}

      {/* Processing Status */}
      {inferenceStatus === 'processing' && (
        <div className="bg-blue-50 rounded-lg p-6 text-center">
          <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-purple-600 mx-auto" />
          <p className="text-gray-600 mt-3">MG Inference in progress...</p>
          <p className="text-sm text-gray-500 mt-1">Job ID: {jobId}</p>
        </div>
      )}

      {/* Inference History */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-900">
            MG Inference History ({inferenceHistory.length} items)
          </h3>
          <button
            onClick={loadInferenceHistory}
            className="text-sm text-purple-600 hover:text-purple-800"
          >
            Refresh
          </button>
        </div>

        <div className="bg-white rounded-lg shadow overflow-hidden">
          {loadingHistory ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto" />
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
                      record.job_id === jobId ? 'bg-purple-50' : ''
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
                      {record.status === 'COMPLETED' && record.result_data?.grade ? (
                        <span>
                          Grade: {record.result_data.grade.predicted_class}
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
                        <span className="font-medium text-purple-600">
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
                            className="text-sm text-purple-600 hover:text-purple-800"
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
