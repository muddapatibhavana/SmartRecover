import { useState, useEffect, useCallback } from 'react';
import { Navbar } from './components/Navbar';
import { KPICards } from './components/KPICards';
import { StopReasonAnalytics } from './components/StopReasonAnalytics';
import { RecoveryCaseTable } from './components/RecoveryCaseTable';
import { CaseDetailModal } from './components/CaseDetailModal';
import { HumanReviewQueue } from './components/HumanReviewQueue';
import { PaymentSimulatorControls } from './components/PaymentSimulatorControls';
import { DemoScenarioSelector } from './components/DemoScenarioSelector';
import {
  fetchDashboardMetrics,
  fetchRecoveryCases,
  fetchHumanReviews
} from './services/api';
import { DashboardMetrics, RecoveryCaseSummary, HumanReviewItem } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState<string>('dashboard');
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [cases, setCases] = useState<RecoveryCaseSummary[]>([]);
  const [reviews, setReviews] = useState<HumanReviewItem[]>([]);
  const [selectedCaseId, setSelectedCaseId] = useState<string | null>(null);

  const [loadingMetrics, setLoadingMetrics] = useState<boolean>(true);
  const [loadingCases, setLoadingCases] = useState<boolean>(true);
  const [loadingReviews, setLoadingReviews] = useState<boolean>(true);

  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const loadDashboardData = useCallback(async () => {
    try {
      setLoadingMetrics(true);
      const data = await fetchDashboardMetrics();
      setMetrics(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingMetrics(false);
    }
  }, []);

  const loadCasesData = useCallback(async () => {
    try {
      setLoadingCases(true);
      const data = await fetchRecoveryCases(selectedStatus, searchQuery);
      setCases(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCases(false);
    }
  }, [selectedStatus, searchQuery]);

  const loadReviewsData = useCallback(async () => {
    try {
      setLoadingReviews(true);
      const data = await fetchHumanReviews();
      setReviews(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingReviews(false);
    }
  }, []);

  const refreshAll = useCallback(() => {
    loadDashboardData();
    loadCasesData();
    loadReviewsData();
  }, [loadDashboardData, loadCasesData, loadReviewsData]);

  useEffect(() => {
    loadDashboardData();
    loadReviewsData();
  }, [loadDashboardData, loadReviewsData]);

  useEffect(() => {
    loadCasesData();
  }, [loadCasesData]);

  const pendingReviewsCount = reviews.filter((r) => r.status === 'PENDING').length;

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onDataRefresh={refreshAll}
        pendingReviewsCount={pendingReviewsCount}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Tab 1: Executive Dashboard */}
        {activeTab === 'dashboard' && (
          <div className="space-y-8">
            {/* Header Hero */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-gradient-to-r from-blue-950/40 via-slate-900/60 to-purple-950/30 p-6 rounded-2xl border border-slate-800">
              <div>
                <span className="text-xs uppercase font-bold tracking-wider text-blue-400">AI Revenue Recovery Track</span>
                <h1 className="text-2xl font-extrabold text-white tracking-tight mt-1">Failed Mandate & Payment Recovery</h1>
                <p className="text-xs text-slate-400 mt-1 max-w-xl">
                  AI recommends whether, when, and how to recover revenue. Deterministic safety guardrails strictly control execution.
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => setActiveTab('scenarios')}
                  className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg shadow-blue-600/30 transition-all cursor-pointer"
                >
                  🚀 Quick Demo Journeys
                </button>
                <button
                  onClick={() => setSelectedCaseId('SR-1024')}
                  className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition-all cursor-pointer"
                >
                  Inspect Case #SR-1024
                </button>
              </div>
            </div>

            {/* KPI Cards */}
            <KPICards metrics={metrics} loading={loadingMetrics} />

            {/* Stop Reason Analytics */}
            {metrics && (
              <StopReasonAnalytics breakdown={metrics.stop_reasons_breakdown} />
            )}

            {/* Recovery Cases Table Section */}
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-white tracking-tight">Active Recovery Pipeline</h2>
                  <p className="text-xs text-slate-400">Recurring payment mandate failure events and recovery state machine</p>
                </div>
                <button
                  onClick={() => setActiveTab('cases')}
                  className="text-xs font-semibold text-blue-400 hover:text-blue-300"
                >
                  View All Cases →
                </button>
              </div>

              <RecoveryCaseTable
                cases={cases.slice(0, 10)}
                loading={loadingCases}
                onSelectCase={(id) => setSelectedCaseId(id)}
                selectedStatus={selectedStatus}
                setSelectedStatus={setSelectedStatus}
                searchQuery={searchQuery}
                setSearchQuery={setSearchQuery}
              />
            </div>
          </div>
        )}

        {/* Tab 2: Recovery Cases View */}
        {activeTab === 'cases' && (
          <div className="space-y-4">
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">All Recovery Cases</h1>
              <p className="text-xs text-slate-400">Search, filter, and inspect recurring payment mandate failures</p>
            </div>
            <RecoveryCaseTable
              cases={cases}
              loading={loadingCases}
              onSelectCase={(id) => setSelectedCaseId(id)}
              selectedStatus={selectedStatus}
              setSelectedStatus={setSelectedStatus}
              searchQuery={searchQuery}
              setSearchQuery={setSearchQuery}
            />
          </div>
        )}

        {/* Tab 3: Human Review View */}
        {activeTab === 'human-review' && (
          <HumanReviewQueue
            reviews={reviews}
            loading={loadingReviews}
            onRefresh={refreshAll}
            onSelectCase={(id) => setSelectedCaseId(id)}
          />
        )}

        {/* Tab 4: Payment Simulator View */}
        {activeTab === 'simulator' && (
          <div className="space-y-6">
            <PaymentSimulatorControls onSimulationComplete={refreshAll} />
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-white uppercase tracking-wider">Recently Active Cases</h3>
              <RecoveryCaseTable
                cases={cases.slice(0, 5)}
                loading={loadingCases}
                onSelectCase={(id) => setSelectedCaseId(id)}
                selectedStatus="ALL"
                setSelectedStatus={setSelectedStatus}
                searchQuery=""
                setSearchQuery={setSearchQuery}
              />
            </div>
          </div>
        )}

        {/* Tab 5: Demo Scenarios View */}
        {activeTab === 'scenarios' && (
          <DemoScenarioSelector
            onSelectCase={(id) => setSelectedCaseId(id)}
            onRefreshParent={refreshAll}
          />
        )}
      </main>

      {/* Drill-down Detail Modal */}
      {selectedCaseId && (
        <CaseDetailModal
          caseId={selectedCaseId}
          onClose={() => setSelectedCaseId(null)}
          onRefreshParent={refreshAll}
        />
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0B0F19] py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <span className="font-bold text-slate-300">SmartRecover</span>
            <span>•</span>
            <span>AI-powered payment recovery with safe stopping.</span>
          </div>
          <div className="text-slate-400 font-mono text-[11px]">
            AI Advisory • Deterministic Safety Guardrails • Simulation Sandbox
          </div>
        </div>
      </footer>
    </div>
  );
}
