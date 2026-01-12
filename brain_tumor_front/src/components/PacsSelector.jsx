// src/components/PacsSelector.jsx
import React, { useEffect, useMemo, useState, useRef } from "react";
import "./PacsSelector.css";
import { getPatients, getStudies, getSeries } from "../api/orthancApi";

const asText = (v) => (v == null ? "" : String(v));

// 긴 텍스트 말줄임 처리
const truncate = (text, maxLen = 40) => {
  if (!text || text.length <= maxLen) return text;
  return text.substring(0, maxLen) + '...';
};

export default function PacsSelector({ onChange, ocsInfo, initialSelection }) {
  const [patients, setPatients] = useState([]);
  const [studies, setStudies] = useState([]);
  const [seriesList, setSeriesList] = useState([]);

  const [patientId, setPatientId] = useState(initialSelection?.patientId || "");
  const [studyId, setStudyId] = useState(initialSelection?.studyId || "");

  const [baseSeriesId, setBaseSeriesId] = useState(initialSelection?.baseSeriesId || "");
  const [baseSeriesName, setBaseSeriesName] = useState(initialSelection?.baseSeriesName || "");

  const [overlaySeriesId, setOverlaySeriesId] = useState(initialSelection?.overlaySeriesId || "");
  const [overlaySeriesName, setOverlaySeriesName] = useState(initialSelection?.overlaySeriesName || "");

  const [busy, setBusy] = useState(false);
  const initializedRef = useRef(false);

  // 환자 목록 로드 + initialSelection 복원
  useEffect(() => {
    (async () => {
      try {
        const p = await getPatients();
        setPatients(p);

        // initialSelection이 있으면 데이터 복원
        if (initialSelection?.patientId && !initializedRef.current) {
          initializedRef.current = true;

          // Study 로드
          if (initialSelection.patientId) {
            const st = await getStudies(initialSelection.patientId);
            setStudies(st);

            // Series 로드
            if (initialSelection.studyId) {
              const se = await getSeries(initialSelection.studyId);
              setSeriesList(se);
            }
          }
        }
      } catch (err) {
        console.error("Failed to load patients:", err);
        setPatients([]);
      }
    })();
  }, []);

  const overlayCandidates = useMemo(() => {
    return (seriesList || []).filter((s) => {
      const d = (s.description || "").toLowerCase();
      const uid = (s.seriesInstanceUID || "").toLowerCase();
      return d.includes("seg") || uid.includes("seg");
    });
  }, [seriesList]);

  const findSeriesName = (serId) => {
    if (!serId) return "";
    const s = (seriesList || []).find((x) => x.orthancId === serId);
    return asText(s?.description || s?.seriesInstanceUID || "");
  };

  // 현재 선택된 studyInstanceUID 가져오기
  const currentStudyInstanceUID = useMemo(() => {
    if (!studyId) return "";
    const study = studies.find((s) => s.orthancId === studyId);
    return study?.studyInstanceUID || "";
  }, [studyId, studies]);

  const emit = (patch = {}) => {
    const next = {
      patientId,
      studyId,
      studyInstanceUID: currentStudyInstanceUID,
      baseSeriesId,
      baseSeriesName,
      overlaySeriesId,
      overlaySeriesName,
      ...patch,
    };
    onChange?.(next);
  };

  const selectPatient = async (pid) => {
    setPatientId(pid);

    // reset
    setStudyId("");
    setStudies([]);
    setSeriesList([]);

    setBaseSeriesId("");
    setBaseSeriesName("");

    setOverlaySeriesId("");
    setOverlaySeriesName("");

    onChange?.({
      patientId: pid,
      studyId: "",
      baseSeriesId: "",
      baseSeriesName: "",
      overlaySeriesId: "",
      overlaySeriesName: "",
    });

    if (!pid) return;

    setBusy(true);
    try {
      const st = await getStudies(pid);
      setStudies(st);
    } finally {
      setBusy(false);
    }
  };

  const selectStudy = async (sid) => {
    setStudyId(sid);

    // reset series selections
    setBaseSeriesId("");
    setBaseSeriesName("");
    setOverlaySeriesId("");
    setOverlaySeriesName("");
    setSeriesList([]);

    // 선택된 study의 studyInstanceUID 가져오기
    const selectedStudy = studies.find((s) => s.orthancId === sid);
    const studyUid = selectedStudy?.studyInstanceUID || "";

    onChange?.({
      patientId,
      studyId: sid,
      studyInstanceUID: studyUid,
      baseSeriesId: "",
      baseSeriesName: "",
      overlaySeriesId: "",
      overlaySeriesName: "",
    });

    if (!sid) return;

    setBusy(true);
    try {
      const se = await getSeries(sid);
      setSeriesList(se);
    } finally {
      setBusy(false);
    }
  };

  const selectBaseSeries = (serId) => {
    const name = findSeriesName(serId);

    setBaseSeriesId(serId);
    setBaseSeriesName(name);

    emit({
      baseSeriesId: serId,
      baseSeriesName: name,
    });
  };

  const selectOverlaySeries = (serId) => {
    const name = findSeriesName(serId);

    setOverlaySeriesId(serId);
    setOverlaySeriesName(name);

    emit({
      overlaySeriesId: serId,
      overlaySeriesName: name,
    });
  };

  return (
    <section className="selCard">
      <div className="selHeader">
        <h2 className="selTitle">Selection</h2>
        <div className="selHint">{busy ? "Loading..." : "Patient → Study → Series"}</div>
      </div>

      {/* OCS 연동 정보 표시 */}
      {ocsInfo && (
        <div className="ocsLinkBox">
          <div className="ocsLinkRow">
            <span className="ocsLinkLabel">MySQL 환자</span>
            <span className="ocsLinkValue">{ocsInfo.patientName} ({ocsInfo.patientNumber})</span>
          </div>
        </div>
      )}

      <div className="selGrid">
        <div className="row">
          <label className="label">Patient</label>
          <select
            className="select"
            value={patientId}
            onChange={(e) => selectPatient(e.target.value)}
            disabled={busy}
          >
            <option value="">-- 선택 --</option>
            {patients.map((p) => (
              <option key={p.orthancId} value={p.orthancId}>
                {truncate(asText(p.patientName || p.patientId), 30)} ({p.studiesCount})
              </option>
            ))}
          </select>
          {patientId && (
            <div className="idDisplay">
              <span className="idLabel">Orthanc ID:</span>
              <span className="idValue">{patientId}</span>
            </div>
          )}
        </div>

        <div className="row">
          <label className="label">Study</label>
          <select
            className="select"
            value={studyId}
            onChange={(e) => selectStudy(e.target.value)}
            disabled={!patientId || busy}
          >
            <option value="">-- 선택 --</option>
            {studies.map((s) => (
              <option key={s.orthancId} value={s.orthancId}>
                {truncate(asText(s.studyInstanceUID || s.orthancId), 40)}
              </option>
            ))}
          </select>
          {studyId && (
            <>
              <div className="studyInfoBox">
                <div className="studyInfoRow">
                  <span className="studyInfoLabel">Study UID</span>
                  <span className="studyInfoValue mono">
                    {studies.find((s) => s.orthancId === studyId)?.studyInstanceUID || "-"}
                  </span>
                </div>
                <div className="studyInfoRow">
                  <span className="studyInfoLabel">Description</span>
                  <span className="studyInfoValue">
                    {studies.find((s) => s.orthancId === studyId)?.description || "(없음)"}
                  </span>
                </div>
                <div className="studyInfoRow">
                  <span className="studyInfoLabel">Orthanc ID</span>
                  <span className="studyInfoValue mono">{studyId}</span>
                </div>
              </div>
            </>
          )}
        </div>

        <div className="row">
          <label className="label">Base Series</label>
          <select
            className="select"
            value={baseSeriesId}
            onChange={(e) => selectBaseSeries(e.target.value)}
            disabled={!studyId || busy}
          >
            <option value="">-- 선택 --</option>
            {seriesList.map((s) => (
              <option key={s.orthancId} value={s.orthancId}>
                {truncate(asText(s.description || s.seriesInstanceUID), 40)}
              </option>
            ))}
          </select>
        </div>

        <div className="row">
          <label className="label">Overlay Series (seg)</label>
          <select
            className="select"
            value={overlaySeriesId}
            onChange={(e) => selectOverlaySeries(e.target.value)}
            disabled={!studyId || busy}
          >
            <option value="">-- 없음 --</option>
            {overlayCandidates.map((s) => (
              <option key={s.orthancId} value={s.orthancId}>
                {truncate(asText(s.description || s.seriesInstanceUID), 40)}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}
