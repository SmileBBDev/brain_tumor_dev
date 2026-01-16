import React, { useState, useEffect } from 'react'
import { aiApi } from '../services/api'

interface GradeResult {
  predicted_class: string
  predicted_value?: number
  probability: number
  probabilities?: Record<string, number>
}

interface BinaryResult {
  predicted_class: string
  mutant_probability?: number
  methylated_probability?: number
}

interface SurvivalResult {
  risk_score: number
  risk_category: string
}

interface OsDaysResult {
  predicted_days: number
  predicted_months: number
}

interface M1Result {
  grade?: GradeResult
  idh?: BinaryResult
  mgmt?: BinaryResult
  survival?: SurvivalResult
  os_days?: OsDaysResult
  processing_time_ms?: number
  visualization_paths?: string[]
}

interface FileInfo {
  name: string
  size: number
  modified: number
  download_url: string
}

interface InferenceResultProps {
  result: M1Result | null
  status?: string
  error?: string
  jobId?: string
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function InferenceResult({ result, status, error, jobId }: InferenceResultProps) {
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loadingFiles, setLoadingFiles] = useState(false)
  const [showRawJson, setShowRawJson] = useState(false)

  // 파일 목록 로드
  useEffect(() => {
    if (jobId && status === 'completed') {
      loadFiles()
    }
  }, [jobId, status])

  const loadFiles = async () => {
    if (!jobId) return
    try {
      setLoadingFiles(true)
      const response = await aiApi.getInferenceFiles(jobId)
      setFiles(response.files || [])
    } catch (err) {
      console.error('Failed to load files:', err)
    } finally {
      setLoadingFiles(false)
    }
  }

  const handleDownload = (file: FileInfo) => {
    const url = file.download_url
    const link = document.createElement('a')
    link.href = url
    link.download = file.name
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <h3 className="text-red-800 font-medium">추론 실패</h3>
        <p className="text-red-600 text-sm mt-1">{error}</p>
      </div>
    )
  }

  if (status === 'processing' || status === 'PROCESSING') {
    return (
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600 mx-auto" />
        <p className="text-blue-600 mt-3">M1 모델 추론 중...</p>
      </div>
    )
  }

  if (!result) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center text-gray-500">
        추론 결과가 없습니다. OCS를 선택하고 추론을 요청하세요.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* 분석 결과 */}
      <div className="bg-white rounded-lg shadow divide-y divide-gray-200">
        {/* Grade */}
        {result.grade && (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">WHO Grade</h3>
            <div className="flex items-center justify-between">
              <span className="text-2xl font-bold text-gray-900">
                {result.grade.predicted_class}
              </span>
              <span className="text-sm text-gray-500">
                확률: {(result.grade.probability * 100).toFixed(1)}%
              </span>
            </div>
            {result.grade.probabilities && (
              <div className="mt-2 space-y-1">
                {Object.entries(result.grade.probabilities).map(([grade, prob]) => (
                  <div key={grade} className="flex items-center text-xs">
                    <span className="w-16 text-gray-500">{grade}</span>
                    <div className="flex-1 bg-gray-200 rounded-full h-2 mx-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full"
                        style={{ width: `${prob * 100}%` }}
                      />
                    </div>
                    <span className="w-12 text-right text-gray-500">
                      {(prob * 100).toFixed(1)}%
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* IDH */}
        {result.idh && (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">IDH 상태</h3>
            <div className="flex items-center justify-between">
              <span
                className={`text-xl font-bold ${
                  result.idh.predicted_class === 'Mutant'
                    ? 'text-orange-600'
                    : 'text-blue-600'
                }`}
              >
                {result.idh.predicted_class}
              </span>
              <span className="text-sm text-gray-500">
                Mutant 확률: {((result.idh.mutant_probability || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* MGMT */}
        {result.mgmt && (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">MGMT 메틸화</h3>
            <div className="flex items-center justify-between">
              <span
                className={`text-xl font-bold ${
                  result.mgmt.predicted_class === 'Methylated'
                    ? 'text-green-600'
                    : 'text-red-600'
                }`}
              >
                {result.mgmt.predicted_class}
              </span>
              <span className="text-sm text-gray-500">
                메틸화 확률:{' '}
                {((result.mgmt.methylated_probability || 0) * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* Survival */}
        {result.survival && (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">생존 위험도</h3>
            <div className="flex items-center justify-between">
              <span
                className={`text-xl font-bold ${
                  result.survival.risk_category === 'High'
                    ? 'text-red-600'
                    : result.survival.risk_category === 'Medium'
                    ? 'text-yellow-600'
                    : 'text-green-600'
                }`}
              >
                {result.survival.risk_category}
              </span>
              <span className="text-sm text-gray-500">
                점수: {result.survival.risk_score.toFixed(3)}
              </span>
            </div>
          </div>
        )}

        {/* OS Days */}
        {result.os_days && (
          <div className="p-4">
            <h3 className="text-sm font-medium text-gray-500 mb-2">예상 생존 기간</h3>
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold text-gray-900">
                {result.os_days.predicted_months.toFixed(1)}개월
              </span>
              <span className="text-sm text-gray-500">
                ({result.os_days.predicted_days}일)
              </span>
            </div>
          </div>
        )}

        {/* Processing Time */}
        {result.processing_time_ms && (
          <div className="p-4 bg-gradient-to-r from-blue-50 to-green-50 border-t border-gray-200">
            <div className="flex items-center justify-center space-x-4">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm font-medium text-gray-700">추론 처리 시간</span>
              </div>
              <span className="text-lg font-bold text-blue-600">
                {(result.processing_time_ms / 1000).toFixed(2)}초
              </span>
              <span className="text-xs text-gray-500">
                ({result.processing_time_ms.toFixed(0)}ms)
              </span>
            </div>
          </div>
        )}
      </div>

      {/* 파일 다운로드 섹션 */}
      {jobId && status === 'completed' && (
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">결과 파일</h3>
            <button
              onClick={loadFiles}
              className="text-xs text-blue-600 hover:text-blue-800"
            >
              새로고침
            </button>
          </div>

          {loadingFiles ? (
            <div className="text-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto" />
            </div>
          ) : files.length > 0 ? (
            <div className="space-y-2">
              {files.map((file) => (
                <div
                  key={file.name}
                  className="flex items-center justify-between p-2 bg-gray-50 rounded hover:bg-gray-100"
                >
                  <div className="flex items-center space-x-2">
                    <svg
                      className="w-5 h-5 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                    <span className="text-sm text-gray-700">{file.name}</span>
                    <span className="text-xs text-gray-400">
                      ({formatFileSize(file.size)})
                    </span>
                  </div>
                  <button
                    onClick={() => handleDownload(file)}
                    className="px-3 py-1 text-xs text-white bg-blue-600 rounded hover:bg-blue-700"
                  >
                    다운로드
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 text-center py-2">
              파일이 없습니다.
            </p>
          )}
        </div>
      )}

      {/* Raw JSON 토글 */}
      <div className="bg-white rounded-lg shadow p-4">
        <button
          onClick={() => setShowRawJson(!showRawJson)}
          className="text-sm text-gray-600 hover:text-gray-800 flex items-center"
        >
          <svg
            className={`w-4 h-4 mr-1 transform transition-transform ${
              showRawJson ? 'rotate-90' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5l7 7-7 7"
            />
          </svg>
          Raw JSON 데이터
        </button>
        {showRawJson && (
          <pre className="mt-3 p-3 bg-gray-50 rounded text-xs overflow-auto max-h-64">
            {JSON.stringify(result, null, 2)}
          </pre>
        )}
      </div>
    </div>
  )
}
