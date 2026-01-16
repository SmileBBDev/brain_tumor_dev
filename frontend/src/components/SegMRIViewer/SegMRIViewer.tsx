/**
 * SegMRIViewer - Standalone Segmentation Comparison Component
 * MRI 세그멘테이션 GT vs Prediction 비교 뷰어
 *
 * 사용법:
 * 1. SegMRIViewer.tsx와 SegMRIViewer.css 두 파일을 프로젝트에 복사
 * 2. import SegMRIViewer from './SegMRIViewer'
 * 3. <SegMRIViewer data={segmentationData} diceScores={diceScores} />
 *
 * 의존성: React만 필요 (MUI, 기타 라이브러리 불필요)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react'
import './SegMRIViewer.css'

// ============== Types (Inline) ==============

/** 3D 볼륨 슬라이스 매핑 정보 */
export interface SliceMapping {
  axial_mapping?: { original_idx_nearest: number }[]
  sagittal_mapping?: { original_idx_nearest: number }[]
  coronal_mapping?: { original_idx_nearest: number }[]
}

/** MRI 채널 타입 */
export type MRIChannel = 't1' | 't1ce' | 't2' | 'flair'

/** 세그멘테이션 데이터 */
export interface SegmentationData {
  mri: number[][][]           // 3D MRI 볼륨 [X][Y][Z] (기본: T1CE)
  groundTruth: number[][][]   // 3D GT 레이블 볼륨
  prediction: number[][][]    // 3D 예측 레이블 볼륨
  shape: [number, number, number]  // [X, Y, Z] 크기
  sliceMapping?: SliceMapping      // 원본 슬라이스 매핑 (선택)
  mri_channels?: {            // 4채널 MRI 데이터 (선택)
    t1?: number[][][]
    t1ce?: number[][][]
    t2?: number[][][]
    flair?: number[][][]
  }
}

/** Dice Score */
export interface DiceScores {
  wt?: number  // Whole Tumor
  tc?: number  // Tumor Core
  et?: number  // Enhancing Tumor
}

/** 뷰 모드 */
export type ViewMode = 'axial' | 'sagittal' | 'coronal'

/** 디스플레이 모드 */
export type DisplayMode = 'difference' | 'gt_only' | 'pred_only' | 'overlay'

// ============== Component Props ==============

export interface SegMRIViewerProps {
  /** 세그멘테이션 데이터 (MRI, GT, Prediction 볼륨) */
  data: SegmentationData
  /** 컴포넌트 제목 */
  title?: string
  /** Dice 점수 (WT, TC, ET) */
  diceScores?: DiceScores
  /** 초기 뷰 모드 */
  initialViewMode?: ViewMode
  /** 초기 디스플레이 모드 */
  initialDisplayMode?: DisplayMode
  /** 캔버스 최대 크기 (px) */
  maxCanvasSize?: number
}

// ============== Constants ==============

/** BraTS 레이블 컬러 */
const LABEL_COLORS = {
  1: { r: 255, g: 0, b: 0, name: 'NCR/NET' },   // Red - Necrotic Core
  2: { r: 0, g: 255, b: 0, name: 'ED' },        // Green - Edema
  3: { r: 0, g: 0, b: 255, name: 'ET' },        // Blue - Enhancing Tumor
}

/** Diff 모드 컬러 */
const DIFF_COLORS = {
  TP: { r: 0, g: 200, b: 0 },      // Green - True Positive
  FN: { r: 255, g: 100, b: 100 },  // Red - False Negative
  FP: { r: 100, g: 100, b: 255 },  // Blue - False Positive
}

// ============== Component ==============

const SegMRIViewer: React.FC<SegMRIViewerProps> = ({
  data,
  title = 'Segmentation Comparison',
  diceScores,
  initialViewMode = 'axial',
  initialDisplayMode = 'pred_only',
  maxCanvasSize = 450,
}) => {
  // Canvas ref
  const canvasRef = useRef<HTMLCanvasElement>(null)

  // State
  const [currentSlice, setCurrentSlice] = useState(0)
  const [viewMode, setViewMode] = useState<ViewMode>(initialViewMode)
  const [displayMode, setDisplayMode] = useState<DisplayMode>(initialDisplayMode)
  const [initialized, setInitialized] = useState(false)
  const [sliceDims, setSliceDims] = useState({ width: 128, height: 128 })

  // Display options
  const [showMRI, setShowMRI] = useState(true)
  const [showGroundTruth, setShowGroundTruth] = useState(true)
  const [showPrediction, setShowPrediction] = useState(true)
  const [segOpacity, setSegOpacity] = useState(0.7)

  // Label visibility
  const [showNCR, setShowNCR] = useState(true)
  const [showED, setShowED] = useState(true)
  const [showET, setShowET] = useState(true)

  // MRI Channel selection
  const [mriChannel, setMriChannel] = useState<MRIChannel>('t1ce')

  // ============== Helper Functions ==============

  const isLabelVisible = (label: number): boolean => {
    if (label === 1) return showNCR
    if (label === 2) return showED
    if (label === 3) return showET
    return false
  }

  /** 선택된 MRI 채널 데이터 가져오기 */
  const getCurrentMriVolume = useCallback((): number[][][] | null => {
    // mri_channels가 있으면 선택된 채널 사용
    if (data.mri_channels) {
      const channelData = data.mri_channels[mriChannel]
      if (channelData) return channelData
    }
    // 없으면 기본 mri 사용
    return data.mri
  }, [data.mri, data.mri_channels, mriChannel])

  /** 사용 가능한 MRI 채널 목록 */
  const getAvailableChannels = useCallback((): MRIChannel[] => {
    if (!data.mri_channels) return []
    const channels: MRIChannel[] = []
    if (data.mri_channels.t1) channels.push('t1')
    if (data.mri_channels.t1ce) channels.push('t1ce')
    if (data.mri_channels.t2) channels.push('t2')
    if (data.mri_channels.flair) channels.push('flair')
    return channels
  }, [data.mri_channels])

  /** 3D 볼륨에서 2D 슬라이스 추출 */
  const getSlice = useCallback((volume: number[][][], sliceIdx: number, mode: ViewMode): number[][] | null => {
    if (!volume || volume.length === 0) return null

    const [X, Y, Z] = [volume.length, volume[0]?.length || 0, volume[0]?.[0]?.length || 0]

    switch (mode) {
      case 'axial': {
        if (sliceIdx >= Z) return null
        const slice: number[][] = []
        for (let y = 0; y < Y; y++) {
          const row: number[] = []
          for (let x = 0; x < X; x++) {
            row.push(volume[x]?.[Y - 1 - y]?.[sliceIdx] || 0)
          }
          slice.push(row)
        }
        return slice
      }
      case 'sagittal': {
        if (sliceIdx >= X) return null
        const slice: number[][] = []
        for (let z = 0; z < Z; z++) {
          const row: number[] = []
          for (let y = 0; y < Y; y++) {
            row.push(volume[sliceIdx]?.[Y - 1 - y]?.[Z - 1 - z] || 0)
          }
          slice.push(row)
        }
        return slice
      }
      case 'coronal': {
        if (sliceIdx >= Y) return null
        const slice: number[][] = []
        for (let z = 0; z < Z; z++) {
          const row: number[] = []
          for (let x = 0; x < X; x++) {
            row.push(volume[x]?.[sliceIdx]?.[Z - 1 - z] || 0)
          }
          slice.push(row)
        }
        return slice
      }
      default:
        return null
    }
  }, [])

  /** 현재 뷰 모드의 최대 슬라이스 수 */
  const getMaxSlices = useCallback((): number => {
    if (!data.shape) return 128
    switch (viewMode) {
      case 'axial': return data.shape[2]
      case 'sagittal': return data.shape[0]
      case 'coronal': return data.shape[1]
      default: return data.shape[2]
    }
  }, [data.shape, viewMode])

  /** 디스플레이 크기 계산 */
  const getDisplaySize = useCallback((): { width: number; height: number } => {
    const { width: sliceW, height: sliceH } = sliceDims
    const aspectRatio = sliceW / sliceH

    if (aspectRatio >= 1) {
      return { width: maxCanvasSize, height: Math.round(maxCanvasSize / aspectRatio) }
    } else {
      return { width: Math.round(maxCanvasSize * aspectRatio), height: maxCanvasSize }
    }
  }, [sliceDims, maxCanvasSize])

  /** 원본 슬라이스 번호 가져오기 */
  const getOriginalSliceNum = useCallback((): number => {
    let originalSliceNum = currentSlice + 1
    if (data.sliceMapping) {
      const mappingKey = `${viewMode}_mapping` as keyof SliceMapping
      const mapping = data.sliceMapping[mappingKey]
      if (mapping && mapping[currentSlice]) {
        originalSliceNum = mapping[currentSlice].original_idx_nearest + 1
      }
    }
    return originalSliceNum
  }, [currentSlice, viewMode, data.sliceMapping])

  // ============== Effects ==============

  /** 초기화: 중간 슬라이스로 설정 */
  useEffect(() => {
    if (data.shape && !initialized) {
      const maxSlices = data.shape[2]
      setCurrentSlice(Math.floor(maxSlices / 2))
      setInitialized(true)
    }
  }, [data.shape, initialized])

  /** 캔버스 렌더링 */
  useEffect(() => {
    const canvas = canvasRef.current
    const currentMri = getCurrentMriVolume()
    if (!canvas || !currentMri) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const mriSlice = getSlice(currentMri, currentSlice, viewMode)
    if (!mriSlice) return

    const height = mriSlice.length
    const width = mriSlice[0]?.length || 0

    // 슬라이스 크기 업데이트
    setSliceDims(prev =>
      prev.width !== width || prev.height !== height
        ? { width, height }
        : prev
    )

    canvas.width = width
    canvas.height = height

    const imageData = ctx.createImageData(width, height)

    // MRI 배경 렌더링
    if (showMRI) {
      let minVal = Infinity
      let maxVal = -Infinity
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const val = mriSlice[y]?.[x] || 0
          if (val < minVal) minVal = val
          if (val > maxVal) maxVal = val
        }
      }

      const range = maxVal - minVal
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const idx = (y * width + x) * 4
          const val = mriSlice[y]?.[x] || 0
          const normalized = range > 0 ? Math.floor(((val - minVal) / range) * 255) : 0
          imageData.data[idx] = normalized
          imageData.data[idx + 1] = normalized
          imageData.data[idx + 2] = normalized
          imageData.data[idx + 3] = 255
        }
      }
    } else {
      // 검은 배경
      for (let i = 0; i < imageData.data.length; i += 4) {
        imageData.data[i] = 0
        imageData.data[i + 1] = 0
        imageData.data[i + 2] = 0
        imageData.data[i + 3] = 255
      }
    }

    ctx.putImageData(imageData, 0, 0)

    // 세그멘테이션 오버레이
    const gtSlice = data.groundTruth ? getSlice(data.groundTruth, currentSlice, viewMode) : null
    const predSlice = data.prediction ? getSlice(data.prediction, currentSlice, viewMode) : null

    ctx.globalAlpha = segOpacity

    if (displayMode === 'difference' && gtSlice && predSlice) {
      // Diff 모드: TP/FN/FP 표시
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const gtLabel = gtSlice[y]?.[x] || 0
          const predLabel = predSlice[y]?.[x] || 0

          if (gtLabel === 0 && predLabel === 0) continue
          if (gtLabel > 0 && !isLabelVisible(gtLabel)) continue
          if (predLabel > 0 && !isLabelVisible(predLabel)) continue

          let color
          if (gtLabel > 0 && predLabel > 0 && gtLabel === predLabel) {
            color = DIFF_COLORS.TP
          } else if (gtLabel > 0 && (predLabel === 0 || gtLabel !== predLabel)) {
            color = DIFF_COLORS.FN
          } else if (predLabel > 0 && (gtLabel === 0 || gtLabel !== predLabel)) {
            color = DIFF_COLORS.FP
          }

          if (color) {
            ctx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`
            ctx.fillRect(x, y, 1, 1)
          }
        }
      }
    } else if (displayMode === 'gt_only' && gtSlice) {
      // GT만 표시
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const label = gtSlice[y]?.[x] || 0
          if (label > 0 && isLabelVisible(label)) {
            const color = LABEL_COLORS[label as keyof typeof LABEL_COLORS]
            if (color) {
              ctx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`
              ctx.fillRect(x, y, 1, 1)
            }
          }
        }
      }
    } else if (displayMode === 'pred_only' && predSlice) {
      // Prediction만 표시
      for (let y = 0; y < height; y++) {
        for (let x = 0; x < width; x++) {
          const label = predSlice[y]?.[x] || 0
          if (label > 0 && isLabelVisible(label)) {
            const color = LABEL_COLORS[label as keyof typeof LABEL_COLORS]
            if (color) {
              ctx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`
              ctx.fillRect(x, y, 1, 1)
            }
          }
        }
      }
    } else if (displayMode === 'overlay') {
      // GT + Prediction 오버레이
      if (showGroundTruth && gtSlice) {
        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            const label = gtSlice[y]?.[x] || 0
            if (label > 0 && isLabelVisible(label)) {
              const color = LABEL_COLORS[label as keyof typeof LABEL_COLORS]
              if (color) {
                ctx.fillStyle = `rgba(${color.r}, ${color.g}, ${color.b}, 0.7)`
                ctx.fillRect(x, y, 1, 1)
              }
            }
          }
        }
      }
      if (showPrediction && predSlice) {
        for (let y = 0; y < height; y++) {
          for (let x = 0; x < width; x++) {
            const label = predSlice[y]?.[x] || 0
            if (label > 0 && isLabelVisible(label)) {
              const color = LABEL_COLORS[label as keyof typeof LABEL_COLORS]
              if (color) {
                ctx.fillStyle = `rgba(${Math.min(255, color.r + 80)}, ${Math.min(255, color.g + 80)}, ${Math.min(255, color.b + 80)}, 0.5)`
                ctx.fillRect(x, y, 1, 1)
              }
            }
          }
        }
      }
    }

    ctx.globalAlpha = 1
  }, [data, currentSlice, viewMode, displayMode, showGroundTruth, showPrediction, showMRI, segOpacity, getSlice, showNCR, showED, showET, getCurrentMriVolume, mriChannel])

  // ============== Handlers ==============

  const handleViewModeChange = (mode: ViewMode) => {
    setViewMode(mode)
    let maxSlices = 128
    if (data.shape) {
      switch (mode) {
        case 'axial': maxSlices = data.shape[2]; break
        case 'sagittal': maxSlices = data.shape[0]; break
        case 'coronal': maxSlices = data.shape[1]; break
      }
    }
    setCurrentSlice(Math.floor(maxSlices / 2))
  }

  const displaySize = getDisplaySize()

  // ============== Render ==============

  return (
    <div className="seg-mri-viewer">
      {/* Header */}
      <div className="seg-mri-viewer__header">
        <h3 className="seg-mri-viewer__title">
          <span className="seg-mri-viewer__title-icon">MRI</span>
          {title}
        </h3>
        {diceScores && (
          <div className="seg-mri-viewer__dice-scores">
            {diceScores.wt !== undefined && (
              <span className="seg-mri-viewer__dice-chip seg-mri-viewer__dice-chip--wt">
                WT: {(diceScores.wt * 100).toFixed(1)}%
              </span>
            )}
            {diceScores.tc !== undefined && (
              <span className="seg-mri-viewer__dice-chip seg-mri-viewer__dice-chip--tc">
                TC: {(diceScores.tc * 100).toFixed(1)}%
              </span>
            )}
            {diceScores.et !== undefined && (
              <span className="seg-mri-viewer__dice-chip seg-mri-viewer__dice-chip--et">
                ET: {(diceScores.et * 100).toFixed(1)}%
              </span>
            )}
          </div>
        )}
      </div>

      {/* Body */}
      <div className="seg-mri-viewer__body">
        {/* Canvas Section */}
        <div className="seg-mri-viewer__canvas-section">
          <div className="seg-mri-viewer__canvas-container">
            <canvas
              ref={canvasRef}
              className="seg-mri-viewer__canvas"
              style={{
                width: `${displaySize.width}px`,
                height: `${displaySize.height}px`,
              }}
            />
          </div>
          <div className="seg-mri-viewer__canvas-info">
            * Preprocessed model input region (Foreground Crop applied)
          </div>

          {/* Slice Control */}
          <div className="seg-mri-viewer__slice-control">
            <div className="seg-mri-viewer__slice-label">
              Slice: {currentSlice + 1} / {getMaxSlices()}
              {data.sliceMapping && (
                <span>(Original: {getOriginalSliceNum()})</span>
              )}
            </div>
            <input
              type="range"
              className="seg-mri-viewer__slider"
              value={currentSlice}
              onChange={(e) => setCurrentSlice(Number(e.target.value))}
              min={0}
              max={getMaxSlices() - 1}
            />
          </div>

          {/* View Mode Buttons */}
          <div className="seg-mri-viewer__view-buttons">
            {(['axial', 'sagittal', 'coronal'] as ViewMode[]).map((mode) => (
              <button
                key={mode}
                className={`seg-mri-viewer__view-btn ${viewMode === mode ? 'seg-mri-viewer__view-btn--active' : ''}`}
                onClick={() => handleViewModeChange(mode)}
              >
                {mode.charAt(0).toUpperCase() + mode.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Controls Panel */}
        <div className="seg-mri-viewer__controls">
          {/* Display Mode - 주석처리 (추후 필요시 해제)
          <div>
            <h4 className="seg-mri-viewer__section-title">Display Mode</h4>
            <div className="seg-mri-viewer__mode-buttons">
              {[
                { mode: 'pred_only', label: 'Pred' },
                { mode: 'overlay', label: 'Overlay' },
              ].map(({ mode, label }) => (
                <button
                  key={mode}
                  className={`seg-mri-viewer__mode-btn ${displayMode === mode ? 'seg-mri-viewer__mode-btn--active' : ''}`}
                  onClick={() => setDisplayMode(mode as DisplayMode)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
          */}

          {/* Diff Legend */}
          {displayMode === 'difference' && (
            <div className="seg-mri-viewer__legend">
              <div className="seg-mri-viewer__legend-title">Difference Legend</div>
              <div className="seg-mri-viewer__legend-item">
                <div className="seg-mri-viewer__legend-color seg-mri-viewer__legend-color--tp" />
                <span>Match (TP)</span>
              </div>
              <div className="seg-mri-viewer__legend-item">
                <div className="seg-mri-viewer__legend-color seg-mri-viewer__legend-color--fn" />
                <span>Missed (FN)</span>
              </div>
              <div className="seg-mri-viewer__legend-item">
                <div className="seg-mri-viewer__legend-color seg-mri-viewer__legend-color--fp" />
                <span>Wrong (FP)</span>
              </div>
            </div>
          )}

          <div className="seg-mri-viewer__divider" />

          {/* MRI Background */}
          <label className="seg-mri-viewer__checkbox">
            <input
              type="checkbox"
              checked={showMRI}
              onChange={(e) => setShowMRI(e.target.checked)}
            />
            MRI Background
          </label>

          {/* MRI Channel Selector */}
          {getAvailableChannels().length > 0 && (
            <div className="seg-mri-viewer__channel-selector">
              <h4 className="seg-mri-viewer__section-title">MRI Channel</h4>
              <div className="seg-mri-viewer__channel-buttons">
                {(['t1', 't1ce', 't2', 'flair'] as MRIChannel[]).map((channel) => {
                  const isAvailable = getAvailableChannels().includes(channel)
                  return (
                    <button
                      key={channel}
                      className={`seg-mri-viewer__channel-btn ${mriChannel === channel ? 'seg-mri-viewer__channel-btn--active' : ''} ${!isAvailable ? 'seg-mri-viewer__channel-btn--disabled' : ''}`}
                      onClick={() => isAvailable && setMriChannel(channel)}
                      disabled={!isAvailable}
                    >
                      {channel.toUpperCase()}
                    </button>
                  )
                })}
              </div>
            </div>
          )}

          {/* Opacity */}
          <div className="seg-mri-viewer__opacity-control">
            <span className="seg-mri-viewer__opacity-label">
              Segmentation Opacity: {Math.round(segOpacity * 100)}%
            </span>
            <input
              type="range"
              className="seg-mri-viewer__slider"
              value={segOpacity}
              onChange={(e) => setSegOpacity(Number(e.target.value))}
              min={0.1}
              max={1}
              step={0.1}
            />
          </div>

          {/* Overlay Options */}
          {displayMode === 'overlay' && (
            <div className="seg-mri-viewer__overlay-options">
              <label className="seg-mri-viewer__checkbox">
                <input
                  type="checkbox"
                  checked={showGroundTruth}
                  onChange={(e) => setShowGroundTruth(e.target.checked)}
                />
                Ground Truth
              </label>
              <label className="seg-mri-viewer__checkbox">
                <input
                  type="checkbox"
                  checked={showPrediction}
                  onChange={(e) => setShowPrediction(e.target.checked)}
                />
                Prediction
              </label>
            </div>
          )}

          <div className="seg-mri-viewer__divider" />

          {/* Labels */}
          <div>
            <h4 className="seg-mri-viewer__section-title">Show Labels</h4>
            <div className="seg-mri-viewer__labels">
              <label className="seg-mri-viewer__checkbox">
                <input
                  type="checkbox"
                  checked={showNCR}
                  onChange={(e) => setShowNCR(e.target.checked)}
                />
                <div className="seg-mri-viewer__label-item">
                  <div className="seg-mri-viewer__label-color seg-mri-viewer__label-color--ncr" />
                  <span className="seg-mri-viewer__label-text">NCR/NET - Necrotic Core</span>
                </div>
              </label>
              <label className="seg-mri-viewer__checkbox">
                <input
                  type="checkbox"
                  checked={showED}
                  onChange={(e) => setShowED(e.target.checked)}
                />
                <div className="seg-mri-viewer__label-item">
                  <div className="seg-mri-viewer__label-color seg-mri-viewer__label-color--ed" />
                  <span className="seg-mri-viewer__label-text">ED - Peritumoral Edema</span>
                </div>
              </label>
              <label className="seg-mri-viewer__checkbox">
                <input
                  type="checkbox"
                  checked={showET}
                  onChange={(e) => setShowET(e.target.checked)}
                />
                <div className="seg-mri-viewer__label-item">
                  <div className="seg-mri-viewer__label-color seg-mri-viewer__label-color--et" />
                  <span className="seg-mri-viewer__label-text">ET - Enhancing Tumor</span>
                </div>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default SegMRIViewer
