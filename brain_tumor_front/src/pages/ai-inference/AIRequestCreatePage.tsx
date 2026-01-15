/**
 * AI 추론 통합 페이지
 * - M1: MRI 영상 분석
 * - MG: Gene Expression 분석
 * - MM: 멀티모달 분석
 */
import { useState } from 'react';
import { M1InferencePage, MGInferencePage, MMInferencePage } from './components';
import './AIRequestCreatePage.css';

type TabType = 'm1' | 'mg' | 'mm';

export default function AIRequestCreatePage() {
  const [activeTab, setActiveTab] = useState<TabType>('m1');

  return (
    <div className="ai-inference-container">
      {/* Header */}
      <header className="ai-inference-header">
        <div className="header-content">
          <h1 className="header-title">Brain Tumor CDSS</h1>
          <p className="header-subtitle">AI 기반 뇌종양 분석 시스템</p>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="ai-inference-nav">
        <button
          className={`nav-tab ${activeTab === 'm1' ? 'active m1' : ''}`}
          onClick={() => setActiveTab('m1')}
        >
          <span className="tab-icon">🧠</span>
          <span className="tab-label">M1 MRI 분석</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'mg' ? 'active mg' : ''}`}
          onClick={() => setActiveTab('mg')}
        >
          <span className="tab-icon">🧬</span>
          <span className="tab-label">MG Gene Analysis</span>
        </button>
        <button
          className={`nav-tab ${activeTab === 'mm' ? 'active mm' : ''}`}
          onClick={() => setActiveTab('mm')}
        >
          <span className="tab-icon">🔬</span>
          <span className="tab-label">MM 멀티모달</span>
        </button>
      </nav>

      {/* Main Content */}
      <main className="ai-inference-main">
        {activeTab === 'm1' && <M1InferencePage />}
        {activeTab === 'mg' && <MGInferencePage />}
        {activeTab === 'mm' && <MMInferencePage />}
      </main>
    </div>
  );
}
