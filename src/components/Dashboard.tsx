import { useEffect, useState } from 'react';
import { Activity, CheckCircle, AlertCircle, Cpu, GitBranch } from 'lucide-react';

interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  llm_backend: string;
  llm_available: boolean;
  git_providers: Record<string, boolean>;
  version: string;
}

function Dashboard() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/health');
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      console.error('Failed to fetch health:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const statusColor = {
    healthy: 'text-emerald-600',
    degraded: 'text-amber-600',
    unhealthy: 'text-red-600',
  }[health?.status || 'unhealthy'];

  const statusBg = {
    healthy: 'bg-emerald-50',
    degraded: 'bg-amber-50',
    unhealthy: 'bg-red-50',
  }[health?.status || 'unhealthy'];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900">System Status</h2>
          <div className={`flex items-center space-x-2 px-4 py-2 rounded-lg ${statusBg}`}>
            {health?.status === 'healthy' ? (
              <CheckCircle className={`h-5 w-5 ${statusColor}`} />
            ) : (
              <AlertCircle className={`h-5 w-5 ${statusColor}`} />
            )}
            <span className={`font-semibold ${statusColor} capitalize`}>
              {health?.status || 'Unknown'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
            <div className="flex items-center space-x-3 mb-4">
              <Cpu className="h-6 w-6 text-blue-600" />
              <h3 className="font-semibold text-slate-900">LLM Backend</h3>
            </div>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Provider:</span>
                <span className="font-mono text-sm bg-white px-2 py-1 rounded border border-blue-200">
                  {health?.llm_backend || 'N/A'}
                </span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-600">Status:</span>
                <span className={`font-semibold ${health?.llm_available ? 'text-emerald-600' : 'text-red-600'}`}>
                  {health?.llm_available ? 'Available' : 'Unavailable'}
                </span>
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-slate-50 to-slate-100 rounded-lg p-6 border border-slate-200">
            <div className="flex items-center space-x-3 mb-4">
              <GitBranch className="h-6 w-6 text-slate-600" />
              <h3 className="font-semibold text-slate-900">Git Providers</h3>
            </div>
            <div className="space-y-2">
              {health?.git_providers && Object.entries(health.git_providers).map(([provider, available]) => (
                <div key={provider} className="flex justify-between items-center">
                  <span className="text-slate-600 capitalize">{provider}:</span>
                  <span className={`font-semibold ${available ? 'text-emerald-600' : 'text-slate-400'}`}>
                    {available ? 'Connected' : 'Not configured'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center space-x-3 mb-6">
          <Activity className="h-6 w-6 text-slate-600" />
          <h2 className="text-2xl font-bold text-slate-900">Quick Start</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
            <h3 className="font-semibold text-blue-900 mb-2">1. Configure Webhooks</h3>
            <p className="text-sm text-blue-700">
              Set up webhooks in your Git provider to send PR events to PRism AI.
            </p>
          </div>

          <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
            <h3 className="font-semibold text-emerald-900 mb-2">2. Manual Review</h3>
            <p className="text-sm text-emerald-700">
              Use the Review tab to manually trigger AI reviews on specific PRs.
            </p>
          </div>

          <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
            <h3 className="font-semibold text-amber-900 mb-2">3. Adjust Settings</h3>
            <p className="text-sm text-amber-700">
              Configure LLM provider, models, and approval thresholds in Settings.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;
