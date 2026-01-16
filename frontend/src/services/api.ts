import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - 토큰 추가
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('accessToken')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - 에러 처리
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 토큰 만료 시 로그인 페이지로 이동
      // window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// OCS API
export const ocsApi = {
  // 전체 OCS 목록 조회
  getAllOcsList: async () => {
    const response = await api.get('/ocs/', {
      params: { page_size: 100 }
    })
    return response.data
  },

  // MRI OCS 목록 조회
  getMriOcsList: async () => {
    const response = await api.get('/ocs/', {
      params: {
        job_role: 'RIS',
        job_type: 'MRI',
        ocs_status: 'CONFIRMED',
      },
    })
    return response.data
  },

  // LIS RNA_SEQ OCS 목록 조회
  getRnaSeqOcsList: async () => {
    const response = await api.get('/ocs/', {
      params: {
        job_role: 'LIS',
        job_type: 'RNA_SEQ',
        ocs_status: 'CONFIRMED',
      },
    })
    return response.data
  },

  // OCS 상세 조회
  getOcs: async (id: number) => {
    const response = await api.get(`/ocs/${id}/`)
    return response.data
  },
}

// AI Inference API
export const aiApi = {
  // M1 추론 요청
  requestM1Inference: async (ocsId: number, mode: 'manual' | 'auto' = 'manual') => {
    const response = await api.post('/ai/m1/inference/', {
      ocs_id: ocsId,
      mode,
    })
    return response.data
  },

  // MG 추론 요청
  requestMGInference: async (ocsId: number, mode: 'manual' | 'auto' = 'manual') => {
    const response = await api.post('/ai/mg/inference/', {
      ocs_id: ocsId,
      mode,
    })
    return response.data
  },

  // 추론 목록 조회
  getInferenceList: async (modelType?: string, status?: string) => {
    const params: Record<string, string> = {}
    if (modelType) params.model_type = modelType
    if (status) params.status = status
    const response = await api.get('/ai/inferences/', { params })
    return response.data
  },

  // 추론 상세 조회
  getInferenceDetail: async (jobId: string) => {
    const response = await api.get(`/ai/inferences/${jobId}/`)
    return response.data
  },

  // 추론 결과 파일 목록 조회
  getInferenceFiles: async (jobId: string) => {
    const response = await api.get(`/ai/inferences/${jobId}/files/`)
    return response.data
  },

  // 파일 다운로드 URL 생성
  getFileDownloadUrl: (jobId: string, filename: string) => {
    return `/api/ai/inferences/${jobId}/files/${filename}/`
  },

  // 추론 결과 조회 (legacy)
  getInferenceResult: async (requestId: string) => {
    const response = await api.get(`/ai/requests/${requestId}/`)
    return response.data
  },

  // 추론 요청 목록 (legacy)
  getInferenceRequests: async () => {
    const response = await api.get('/ai/requests/', {
      params: { model_code: 'M1' },
    })
    return response.data
  },

  // 세그멘테이션 데이터 조회 (MRI + Segmentation mask)
  // base64 바이너리 포맷으로 빠르게 로드
  getSegmentationData: async (jobId: string) => {
    const response = await api.get(`/ai/inferences/${jobId}/segmentation/`, {
      params: { enc: 'binary' }
    })
    const data = response.data

    // base64 인코딩된 경우 디코딩
    if (data.encoding === 'base64') {
      const shape = data.shape as [number, number, number]

      // base64 → Float32Array → 3D 배열 변환
      const decodeBase64To3D = (base64: string): number[][][] => {
        const binary = atob(base64)
        const bytes = new Uint8Array(binary.length)
        for (let i = 0; i < binary.length; i++) {
          bytes[i] = binary.charCodeAt(i)
        }
        const float32 = new Float32Array(bytes.buffer)

        // 1D → 3D 변환
        const result: number[][][] = []
        let idx = 0
        for (let x = 0; x < shape[0]; x++) {
          result[x] = []
          for (let y = 0; y < shape[1]; y++) {
            result[x][y] = []
            for (let z = 0; z < shape[2]; z++) {
              result[x][y][z] = float32[idx++]
            }
          }
        }
        return result
      }

      // MRI 및 prediction 디코딩
      if (typeof data.mri === 'string') {
        data.mri = decodeBase64To3D(data.mri)
      }
      if (typeof data.prediction === 'string') {
        data.prediction = decodeBase64To3D(data.prediction)
      }
      if (typeof data.groundTruth === 'string') {
        data.groundTruth = decodeBase64To3D(data.groundTruth)
      }

      // MRI 채널 디코딩 (T1, T1CE, T2, FLAIR)
      if (data.mri_channels) {
        const channels = ['t1', 't1ce', 't2', 'flair']
        for (const ch of channels) {
          if (typeof data.mri_channels[ch] === 'string') {
            data.mri_channels[ch] = decodeBase64To3D(data.mri_channels[ch])
          }
        }
      }
    }

    return data
  },

  // 추론 결과 삭제 (job_id로)
  deleteInference: async (jobId: string) => {
    const response = await api.delete(`/ai/inferences/${jobId}/`)
    return response.data
  },

  // 추론 결과 삭제 (OCS ID로 - 해당 OCS의 모든 추론 삭제)
  deleteInferenceByOcs: async (ocsId: number) => {
    const response = await api.delete(`/ai/inferences/by-ocs/${ocsId}/`)
    return response.data
  },

  // MM 추론 요청 (Multimodal)
  requestMMInference: async (
    mriOcsId: number | null,
    geneOcsId: number | null,
    proteinOcsId: number | null,
    mode: 'manual' | 'auto' = 'manual'
  ) => {
    const response = await api.post('/ai/mm/inference/', {
      mri_ocs_id: mriOcsId,
      gene_ocs_id: geneOcsId,
      protein_ocs_id: proteinOcsId,
      mode,
    })
    return response.data
  },

  // MM 추론 가능 OCS 목록 조회
  getMMAvailableOCS: async (patientId: string) => {
    const response = await api.get(`/ai/mm/available-ocs/${patientId}/`)
    return response.data
  },
}
