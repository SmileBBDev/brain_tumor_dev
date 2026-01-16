import React from 'react'

export interface OCSItem {
  id: number
  ocs_id: string
  patient_name: string
  patient_number: string
  job_role: string
  job_type: string
  ocs_status: string
  confirmed_at: string
  ocs_result?: string | null
  attachments?: {
    files?: Array<{
      path: string
      name: string
      size?: number
    }>
    zip_url?: string
  }
  worker_result?: {
    impression?: string
    findings?: string
    dicom?: {
      study_uid: string
      series?: Array<{
        orthanc_id: string
        description: string
        path?: string
      }>
    }
    // LIS 결과 경로
    file_path?: string
  }
}

interface OCSTableProps {
  data: OCSItem[]
  selectedId: number | null
  onSelect: (ocs: OCSItem) => void
  loading?: boolean
}

export function OCSTable({ data, selectedId, onSelect, loading }: OCSTableProps) {
  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <div className="animate-pulse space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-10 bg-gray-200 rounded" />
          ))}
        </div>
      </div>
    )
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
        OCS 데이터가 없습니다.
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              선택
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              OCS ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              환자명
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              환자번호
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              작업유형
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              검사유형
            </th>
            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
              Result
            </th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((ocs) => (
              <tr
                key={ocs.id}
                className={`cursor-pointer hover:bg-gray-50 ${
                  selectedId === ocs.id ? 'bg-blue-50' : ''
                }`}
                onClick={() => onSelect(ocs)}
              >
                <td className="px-4 py-3">
                  <input
                    type="radio"
                    name="ocs-select"
                    checked={selectedId === ocs.id}
                    onChange={() => onSelect(ocs)}
                    className="h-4 w-4 text-blue-600"
                  />
                </td>
                <td className="px-4 py-3 text-sm font-medium text-gray-900">
                  {ocs.ocs_id}
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{ocs.patient_name}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{ocs.patient_number}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{ocs.job_role}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{ocs.job_type}</td>
                <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate" title={ocs.worker_result?.impression || ''}>
                  {ocs.worker_result?.impression || '-'}
                </td>
              </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
