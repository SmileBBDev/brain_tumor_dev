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

// 패키지 설치 여부 확인용 플래그 (향후 사용 예정)
// let jspdfAvailable: boolean | null = null;
// let xlsxAvailable: boolean | null = null;

// jspdf 사용 가능 여부 확인 (향후 사용 예정)
// const _checkJspdfAvailable = async (): Promise<boolean> => {
//   if (jspdfAvailable !== null) return jspdfAvailable;
//   try {
//     await import('jspdf');
//     jspdfAvailable = true;
//     return true;
//   } catch {
//     jspdfAvailable = false;
//     return false;
//   }
// };

// xlsx 사용 가능 여부 확인 (향후 사용 예정)
// const _checkXlsxAvailable = async (): Promise<boolean> => {
//   if (xlsxAvailable !== null) return xlsxAvailable;
//   try {
//     await import('xlsx');
//     xlsxAvailable = true;
//     return true;
//   } catch {
//     xlsxAvailable = false;
//     return false;
//   }
// };

// 향후 사용 예정
// interface PDFReportData {
//   title: string;
//   subtitle?: string;
//   patientInfo: {
//     name: string;
//     patientNumber: string;
//     birthDate?: string;
//     gender?: string;
//   };
//   sections: {
//     title: string;
//     content: string | string[];
//   }[];
//   footer?: {
//     author?: string;
//     date?: string;
//     hospital?: string;
//   };
// }

/**
 * RIS 판독 리포트 PDF 생성
 * - html2canvas를 사용하여 한글 폰트 지원
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
    // 동적 import (패키지 설치 필요: npm install jspdf html2canvas)
    const { jsPDF } = await import('jspdf');
    const html2canvas = (await import('html2canvas')).default;

    // 뇌종양 판정 상태
    const tumorStatus = data.tumorDetected === true ? '종양 있음 (+)' :
                        data.tumorDetected === false ? '종양 없음 (-)' : '미판정';
    const tumorClass = data.tumorDetected === true ? 'positive' :
                       data.tumorDetected === false ? 'negative' : 'undetermined';

    // HTML 템플릿 생성
    const container = document.createElement('div');
    container.style.cssText = `
      position: absolute;
      left: -9999px;
      top: 0;
      width: 794px;
      padding: 40px;
      background: white;
      font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
      font-size: 14px;
      line-height: 1.6;
      color: #333;
      box-sizing: border-box;
    `;

    container.innerHTML = `
      <div style="text-align: center; border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 20px;">
        <h1 style="margin: 0 0 8px 0; font-size: 24px; font-weight: bold;">영상 판독 보고서</h1>
        <p style="margin: 0; color: #666; font-size: 13px;">OCS ID: ${data.ocsId}</p>
      </div>

      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 16px; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #ddd;">환자 정보</h2>
        <div style="display: flex; flex-wrap: wrap; gap: 16px;">
          <div style="min-width: 200px;"><span style="color: #666;">환자명:</span> <strong>${data.patientName}</strong></div>
          <div style="min-width: 200px;"><span style="color: #666;">환자번호:</span> <strong>${data.patientNumber}</strong></div>
          <div style="min-width: 200px;"><span style="color: #666;">검사 유형:</span> <strong>${data.jobType}</strong></div>
          <div style="min-width: 200px;"><span style="color: #666;">처방 의사:</span> <strong>${data.doctorName}</strong></div>
          <div style="min-width: 200px;"><span style="color: #666;">판독자:</span> <strong>${data.workerName}</strong></div>
        </div>
      </div>

      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 16px; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #ddd;">판정 결과</h2>
        <div style="padding: 12px 16px; border-radius: 8px; display: inline-block;
          ${tumorClass === 'positive' ? 'background: #ffebee; border: 2px solid #e53935;' :
            tumorClass === 'negative' ? 'background: #e8f5e9; border: 2px solid #43a047;' :
            'background: #f5f5f5; border: 2px solid #757575;'}">
          <span style="font-size: 18px; font-weight: bold;
            ${tumorClass === 'positive' ? 'color: #c62828;' :
              tumorClass === 'negative' ? 'color: #2e7d32;' : 'color: #424242;'}">
            뇌종양 판정: ${tumorStatus}
          </span>
        </div>
      </div>

      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 16px; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #ddd;">판독 소견 (Findings)</h2>
        <div style="padding: 12px; background: #fafafa; border-left: 3px solid #1976d2; border-radius: 4px; white-space: pre-wrap;">
          ${data.findings || '-'}
        </div>
      </div>

      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 16px; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #ddd;">판독 결론 (Impression)</h2>
        <div style="padding: 12px; background: #fafafa; border-left: 3px solid #388e3c; border-radius: 4px; white-space: pre-wrap;">
          ${data.impression || '-'}
        </div>
      </div>

      ${data.recommendation ? `
      <div style="margin-bottom: 24px;">
        <h2 style="font-size: 16px; margin: 0 0 12px 0; padding-bottom: 8px; border-bottom: 1px solid #ddd;">권고 사항 (Recommendation)</h2>
        <div style="padding: 12px; background: #fff8e1; border-left: 3px solid #f57c00; border-radius: 4px; white-space: pre-wrap;">
          ${data.recommendation}
        </div>
      </div>
      ` : ''}

      <div style="margin-top: 32px; padding-top: 16px; border-top: 1px solid #ddd; font-size: 12px; color: #666;">
        <div style="display: flex; justify-content: space-between;">
          <div>
            <p style="margin: 4px 0;">처방일시: ${data.createdAt}</p>
            ${data.confirmedAt ? `<p style="margin: 4px 0;">확정일시: ${data.confirmedAt}</p>` : ''}
          </div>
          <div style="text-align: right;">
            <p style="margin: 4px 0; font-weight: bold;">Brain Tumor CDSS</p>
          </div>
        </div>
      </div>
    `;

    document.body.appendChild(container);

    // HTML을 Canvas로 변환
    const canvas = await html2canvas(container, {
      scale: 2,
      useCORS: true,
      logging: false,
      backgroundColor: '#ffffff',
    });

    document.body.removeChild(container);

    // Canvas를 PDF로 변환
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = pdf.internal.pageSize.getHeight();
    const imgWidth = pdfWidth - 20; // 좌우 여백 10mm씩
    const imgHeight = (canvas.height * imgWidth) / canvas.width;

    // 페이지 높이보다 크면 여러 페이지로 분할
    let heightLeft = imgHeight;
    let position = 10; // 상단 여백

    pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
    heightLeft -= (pdfHeight - 20);

    while (heightLeft > 0) {
      position = heightLeft - imgHeight + 10;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 10, position, imgWidth, imgHeight);
      heightLeft -= (pdfHeight - 20);
    }

    // PDF 다운로드
    pdf.save(`RIS_Report_${data.ocsId}_${data.patientNumber}.pdf`);

  } catch (error) {
    console.error('PDF 생성 실패:', error);
    alert('PDF 생성에 실패했습니다. jspdf, html2canvas 패키지가 설치되어 있는지 확인하세요.\nnpm install jspdf html2canvas');
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
        }
      },
      didParseCell: (data) => {
        if (data.section === 'body' && data.column.index === 4) {
          const value = data.cell.raw;
          if (value === 'Critical') {
            data.cell.styles.textColor = [229, 107, 111];
          } else if (value === '이상') {
            data.cell.styles.textColor = [242, 166, 90];
          } else {
            data.cell.styles.textColor = [95, 179, 162];
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
