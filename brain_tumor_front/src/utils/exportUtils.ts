/**
 * PDF 및 Excel 내보내기 유틸리티
 *
 * 필요 패키지 설치:
 * npm install jspdf jspdf-autotable xlsx file-saver
 * npm install -D @types/file-saver
 *
 * 참고: 패키지가 설치되지 않은 경우에도 앱이 정상 동작하도록
 * 동적 import를 사용하며, 실패 시 사용자에게 안내합니다.
 */

// ============================================
// PDF 출력 유틸리티
// ============================================

// 패키지 설치 여부 확인용 플래그
let jspdfAvailable: boolean | null = null;
let xlsxAvailable: boolean | null = null;

// jspdf 사용 가능 여부 확인
const checkJspdfAvailable = async (): Promise<boolean> => {
  if (jspdfAvailable !== null) return jspdfAvailable;
  try {
    await import('jspdf');
    jspdfAvailable = true;
    return true;
  } catch {
    jspdfAvailable = false;
    return false;
  }
};

// xlsx 사용 가능 여부 확인
const checkXlsxAvailable = async (): Promise<boolean> => {
  if (xlsxAvailable !== null) return xlsxAvailable;
  try {
    await import('xlsx');
    xlsxAvailable = true;
    return true;
  } catch {
    xlsxAvailable = false;
    return false;
  }
};

interface PDFReportData {
  title: string;
  subtitle?: string;
  patientInfo: {
    name: string;
    patientNumber: string;
    birthDate?: string;
    gender?: string;
  };
  sections: {
    title: string;
    content: string | string[];
  }[];
  footer?: {
    author?: string;
    date?: string;
    hospital?: string;
  };
}

/**
 * RIS 판독 리포트 PDF 생성
 */
export const generateRISReportPDF = async (data: {
  ocsId: string;
  patientName: string;
  patientNumber: string;
  jobType: string;
  findings: string;
  impression: string;
  recommendation?: string;
  tumorDetected: boolean | null;
  doctorName: string;
  workerName: string;
  createdAt: string;
  confirmedAt?: string;
}): Promise<void> => {
  try {
    // 동적 import (패키지 설치 필요)
    const { jsPDF } = await import('jspdf');

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();

    // 헤더
    doc.setFontSize(18);
    doc.text('영상 판독 보고서', pageWidth / 2, 20, { align: 'center' });

    doc.setFontSize(10);
    doc.text(`OCS ID: ${data.ocsId}`, pageWidth / 2, 28, { align: 'center' });

    // 구분선
    doc.setLineWidth(0.5);
    doc.line(20, 32, pageWidth - 20, 32);

    // 환자 정보
    doc.setFontSize(12);
    doc.text('환자 정보', 20, 42);

    doc.setFontSize(10);
    doc.text(`환자명: ${data.patientName}`, 25, 50);
    doc.text(`환자번호: ${data.patientNumber}`, 25, 56);
    doc.text(`검사 유형: ${data.jobType}`, 25, 62);
    doc.text(`처방 의사: ${data.doctorName}`, 120, 50);
    doc.text(`판독자: ${data.workerName}`, 120, 56);

    // 뇌종양 판정
    doc.setFontSize(12);
    doc.text('판정 결과', 20, 76);

    doc.setFontSize(11);
    const tumorStatus = data.tumorDetected === true ? '종양 있음 (+)' :
                        data.tumorDetected === false ? '종양 없음 (-)' : '미판정';
    doc.text(`뇌종양 판정: ${tumorStatus}`, 25, 84);

    // 판독 소견
    doc.setFontSize(12);
    doc.text('판독 소견 (Findings)', 20, 98);

    doc.setFontSize(10);
    const findingsLines = doc.splitTextToSize(data.findings || '-', pageWidth - 50);
    doc.text(findingsLines, 25, 106);

    let yPos = 106 + (findingsLines.length * 5) + 10;

    // 판독 결론
    doc.setFontSize(12);
    doc.text('판독 결론 (Impression)', 20, yPos);

    doc.setFontSize(10);
    const impressionLines = doc.splitTextToSize(data.impression || '-', pageWidth - 50);
    doc.text(impressionLines, 25, yPos + 8);

    yPos = yPos + 8 + (impressionLines.length * 5) + 10;

    // 권고 사항
    if (data.recommendation) {
      doc.setFontSize(12);
      doc.text('권고 사항 (Recommendation)', 20, yPos);

      doc.setFontSize(10);
      const recLines = doc.splitTextToSize(data.recommendation, pageWidth - 50);
      doc.text(recLines, 25, yPos + 8);

      yPos = yPos + 8 + (recLines.length * 5) + 10;
    }

    // 푸터
    doc.setLineWidth(0.3);
    doc.line(20, yPos + 10, pageWidth - 20, yPos + 10);

    doc.setFontSize(9);
    doc.text(`처방일시: ${data.createdAt}`, 25, yPos + 18);
    if (data.confirmedAt) {
      doc.text(`확정일시: ${data.confirmedAt}`, 25, yPos + 24);
    }
    doc.text('Brain Tumor CDSS', pageWidth - 20, yPos + 24, { align: 'right' });

    // PDF 다운로드
    doc.save(`RIS_Report_${data.ocsId}_${data.patientNumber}.pdf`);

  } catch (error) {
    console.error('PDF 생성 실패:', error);
    alert('PDF 생성에 실패했습니다. jspdf 패키지가 설치되어 있는지 확인하세요.\nnpm install jspdf');
    throw error;
  }
};

/**
 * LIS 검사 결과 PDF 생성
 */
export const generateLISReportPDF = async (data: {
  ocsId: string;
  patientName: string;
  patientNumber: string;
  jobType: string;
  results: Array<{
    itemName: string;
    value: string;
    unit: string;
    refRange: string;
    flag: string;
  }>;
  interpretation?: string;
  doctorName: string;
  workerName: string;
  createdAt: string;
  confirmedAt?: string;
}): Promise<void> => {
  try {
    const { jsPDF } = await import('jspdf');
    const { default: autoTable } = await import('jspdf-autotable');

    const doc = new jsPDF();
    const pageWidth = doc.internal.pageSize.getWidth();

    // 헤더
    doc.setFontSize(18);
    doc.text('검사 결과 보고서', pageWidth / 2, 20, { align: 'center' });

    doc.setFontSize(10);
    doc.text(`OCS ID: ${data.ocsId}`, pageWidth / 2, 28, { align: 'center' });

    // 구분선
    doc.setLineWidth(0.5);
    doc.line(20, 32, pageWidth - 20, 32);

    // 환자 정보
    doc.setFontSize(12);
    doc.text('환자 정보', 20, 42);

    doc.setFontSize(10);
    doc.text(`환자명: ${data.patientName}`, 25, 50);
    doc.text(`환자번호: ${data.patientNumber}`, 25, 56);
    doc.text(`검사 유형: ${data.jobType}`, 25, 62);
    doc.text(`처방 의사: ${data.doctorName}`, 120, 50);
    doc.text(`검사자: ${data.workerName}`, 120, 56);

    // 검사 결과 테이블
    doc.setFontSize(12);
    doc.text('검사 결과', 20, 76);

    autoTable(doc, {
      startY: 80,
      head: [['검사 항목', '결과값', '단위', '참고 범위', '판정']],
      body: data.results.map(r => [
        r.itemName,
        r.value,
        r.unit,
        r.refRange,
        r.flag === 'normal' ? '정상' : r.flag === 'abnormal' ? '이상' : 'Critical'
      ]),
      styles: { fontSize: 9 },
      headStyles: { fillColor: [91, 111, 214] },
      columnStyles: {
        4: {
          fontStyle: 'bold',
          textColor: (cell: any) => {
            const value = cell.raw;
            if (value === 'Critical') return [229, 107, 111];
            if (value === '이상') return [242, 166, 90];
            return [95, 179, 162];
          }
        }
      }
    });

    // 해석
    if (data.interpretation) {
      const finalY = (doc as any).lastAutoTable.finalY + 10;
      doc.setFontSize(12);
      doc.text('결과 해석', 20, finalY);

      doc.setFontSize(10);
      const interpLines = doc.splitTextToSize(data.interpretation, pageWidth - 50);
      doc.text(interpLines, 25, finalY + 8);
    }

    // PDF 다운로드
    doc.save(`LIS_Report_${data.ocsId}_${data.patientNumber}.pdf`);

  } catch (error) {
    console.error('PDF 생성 실패:', error);
    alert('PDF 생성에 실패했습니다. jspdf, jspdf-autotable 패키지가 설치되어 있는지 확인하세요.\nnpm install jspdf jspdf-autotable');
    throw error;
  }
};

// ============================================
// Excel 내보내기 유틸리티
// ============================================

interface ExcelColumn {
  header: string;
  key: string;
  width?: number;
}

/**
 * 데이터를 Excel 파일로 내보내기
 */
export const exportToExcel = async <T extends Record<string, any>>(
  data: T[],
  columns: ExcelColumn[],
  filename: string,
  sheetName: string = 'Sheet1'
): Promise<void> => {
  try {
    const XLSX = await import('xlsx');

    // 헤더 행 생성
    const headers = columns.map(col => col.header);

    // 데이터 행 생성
    const rows = data.map(item =>
      columns.map(col => item[col.key] ?? '')
    );

    // 워크시트 생성
    const ws = XLSX.utils.aoa_to_sheet([headers, ...rows]);

    // 열 너비 설정
    ws['!cols'] = columns.map(col => ({ wch: col.width || 15 }));

    // 워크북 생성
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, sheetName);

    // 파일 다운로드
    XLSX.writeFile(wb, `${filename}.xlsx`);

  } catch (error) {
    console.error('Excel 내보내기 실패:', error);
    alert('Excel 내보내기에 실패했습니다. xlsx 패키지가 설치되어 있는지 확인하세요.\nnpm install xlsx');
    throw error;
  }
};

/**
 * 데이터를 CSV 파일로 내보내기
 */
export const exportToCSV = async <T extends Record<string, any>>(
  data: T[],
  columns: ExcelColumn[],
  filename: string
): Promise<void> => {
  try {
    // 헤더 행
    const headers = columns.map(col => col.header).join(',');

    // 데이터 행
    const rows = data.map(item =>
      columns.map(col => {
        const value = item[col.key] ?? '';
        // 쉼표, 줄바꿈, 따옴표가 포함된 경우 따옴표로 감싸기
        if (typeof value === 'string' && (value.includes(',') || value.includes('\n') || value.includes('"'))) {
          return `"${value.replace(/"/g, '""')}"`;
        }
        return value;
      }).join(',')
    );

    // BOM 추가 (한글 인코딩)
    const BOM = '\uFEFF';
    const csvContent = BOM + [headers, ...rows].join('\n');

    // Blob 생성 및 다운로드
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = `${filename}.csv`;
    link.click();
    URL.revokeObjectURL(link.href);

  } catch (error) {
    console.error('CSV 내보내기 실패:', error);
    throw error;
  }
};

// ============================================
// 프리셋: 자주 사용하는 내보내기
// ============================================

/**
 * 환자 목록 Excel 내보내기
 */
export const exportPatientList = async (patients: any[]): Promise<void> => {
  const columns: ExcelColumn[] = [
    { header: '환자번호', key: 'patient_number', width: 15 },
    { header: '환자명', key: 'name', width: 12 },
    { header: '생년월일', key: 'birth_date', width: 12 },
    { header: '성별', key: 'gender', width: 8 },
    { header: '연락처', key: 'phone', width: 15 },
    { header: '등록일', key: 'created_at', width: 12 },
  ];

  await exportToExcel(patients, columns, `환자목록_${formatDateForFilename()}`, '환자목록');
};

/**
 * OCS 목록 Excel 내보내기
 */
export const exportOCSList = async (ocsList: any[]): Promise<void> => {
  const columns: ExcelColumn[] = [
    { header: 'OCS ID', key: 'ocs_id', width: 15 },
    { header: '환자번호', key: 'patient_number', width: 15 },
    { header: '환자명', key: 'patient_name', width: 12 },
    { header: 'OCS 유형', key: 'ocs_class', width: 10 },
    { header: '검사 유형', key: 'job_type', width: 12 },
    { header: '상태', key: 'ocs_status', width: 12 },
    { header: '우선순위', key: 'priority_display', width: 10 },
    { header: '처방 의사', key: 'doctor_name', width: 12 },
    { header: '담당자', key: 'worker_name', width: 12 },
    { header: '처방일시', key: 'created_at', width: 18 },
  ];

  // 데이터 변환
  const formattedData = ocsList.map(ocs => ({
    ...ocs,
    patient_number: ocs.patient?.patient_number || '',
    patient_name: ocs.patient?.name || '',
    doctor_name: ocs.doctor?.name || '',
    worker_name: ocs.worker?.name || '-',
  }));

  await exportToExcel(formattedData, columns, `OCS목록_${formatDateForFilename()}`, 'OCS목록');
};

/**
 * 진료 기록 목록 Excel 내보내기
 */
export const exportEncounterList = async (encounters: any[]): Promise<void> => {
  const columns: ExcelColumn[] = [
    { header: '진료ID', key: 'id', width: 10 },
    { header: '환자번호', key: 'patient_number', width: 15 },
    { header: '환자명', key: 'patient_name', width: 12 },
    { header: '진료유형', key: 'encounter_type', width: 10 },
    { header: '상태', key: 'status', width: 10 },
    { header: '담당의', key: 'doctor_name', width: 12 },
    { header: '예약일시', key: 'scheduled_date', width: 18 },
    { header: '시작일시', key: 'start_date', width: 18 },
    { header: '종료일시', key: 'end_date', width: 18 },
  ];

  const formattedData = encounters.map(enc => ({
    ...enc,
    patient_number: enc.patient?.patient_number || '',
    patient_name: enc.patient?.name || '',
    doctor_name: enc.doctor?.name || '',
  }));

  await exportToExcel(formattedData, columns, `진료기록_${formatDateForFilename()}`, '진료기록');
};

/**
 * 감사 로그 Excel 내보내기
 */
export const exportAuditLog = async (logs: any[]): Promise<void> => {
  const columns: ExcelColumn[] = [
    { header: '일시', key: 'created_at', width: 20 },
    { header: '사용자ID', key: 'user_id', width: 12 },
    { header: '사용자명', key: 'user_name', width: 12 },
    { header: '액션', key: 'action', width: 15 },
    { header: '대상', key: 'target', width: 20 },
    { header: 'IP 주소', key: 'ip_address', width: 15 },
    { header: '상세', key: 'detail', width: 30 },
  ];

  await exportToExcel(logs, columns, `감사로그_${formatDateForFilename()}`, '감사로그');
};

// ============================================
// 헬퍼 함수
// ============================================

/**
 * 파일명용 날짜 포맷
 */
const formatDateForFilename = (): string => {
  const now = new Date();
  return now.toISOString().slice(0, 10).replace(/-/g, '');
};

/**
 * 날짜 포맷 (표시용)
 */
export const formatDateTime = (dateStr: string | null): string => {
  if (!dateStr) return '-';
  const date = new Date(dateStr);
  return date.toLocaleString('ko-KR', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
};
