// src/components/PacsSelector.jsx
import React, { useEffect, useMemo, useState } from "react";
import "./PacsSelector.css";
import { getPatients, getStudies, getSeries } from "../api/orthancApi";

const asText = (v) => (v == null ? "" : String(v));

export default function PacsSelector({ onChange, ocsInfo }) {
  const [patients, setPatients] = useState([]);
  const [studies, setStudies] = useState([]);
  const [seriesList, setSeriesList] = useState([]);

  const [patientId, setPatientId] = useState("");
  const [studyId, setStudyId] = useState("");

  const [baseSeriesId, setBaseSeriesId] = useState("");
  const [baseSeriesName, setBaseSeriesName] = useState(""); // ✅ 추가

  const [overlaySeriesId, setOverlaySeriesId] = useState("");
  const [overlaySeriesName, setOverlaySeriesName] = useState(""); // ✅ 추가

  const [busy, setBusy] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const p = await getPatients();
        setPatients(p);
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

  const emit = (patch = {}) => {
    const next = {
      patientId,
      studyId,
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

    onChange?.({
      patientId,
      studyId: sid,
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
                {asText(p.patientName || p.patientId)} ({p.studiesCount})
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
                {asText(s.description || s.studyInstanceUID)}
              </option>
            ))}
          </select>
          {studyId && (
            <div className="idDisplay">
              <span className="idLabel">Orthanc ID:</span>
              <span className="idValue">{studyId}</span>
            </div>
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
                {asText(s.description || s.seriesInstanceUID)}
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
                {asText(s.description || s.seriesInstanceUID)}
              </option>
            ))}
          </select>
        </div>
      </div>
    </section>
  );
}
