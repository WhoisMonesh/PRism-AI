import { useState, useEffect } from 'react';
import { Save, RefreshCw } from 'lucide-react';

interface Settings {
  llm_provider: string;
  model: string;
  auto_review: boolean;
  min_approval_score: number;
  auto_review_on_open: boolean;
  auto_describe_on_open: boolean;
  auto_label_on_open: boolean;
  auto_security_on_open: boolean;
  inline_comments: boolean;
  collapse_suggestions: boolean;
  rbac_enabled: boolean;
  metrics_enabled: boolean;
}

function SettingsPanel() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/settings');
      const data = await response.json();
      setSettings(data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!settings) return;

    setSaving(true);
    try {
      const response = await fetch('http://localhost:8000/api/v1/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          llm_provider: settings.llm_provider,
          auto_review_on_pr: settings.auto_review,
          min_approval_score: settings.min_approval_score,
          auto_review_on_open: settings.auto_review_on_open,
          auto_describe_on_open: settings.auto_describe_on_open,
          auto_label_on_open: settings.auto_label_on_open,
          auto_security_on_open: settings.auto_security_on_open,
          inline_comments: settings.inline_comments,
          collapse_suggestions: settings.collapse_suggestions,
          rbac_enabled: settings.rbac_enabled,
          metrics_enabled: settings.metrics_enabled,
        }),
      });

      if (response.ok) {
        await fetchSettings();
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!settings) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-700">Failed to load settings</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-slate-900">Settings</h2>
          <button
            onClick={fetchSettings}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <RefreshCw className="h-5 w-5 text-slate-600" />
          </button>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-2">
              LLM Provider
            </label>
            <select
              value={settings.llm_provider}
              onChange={(e) => setSettings({ ...settings, llm_provider: e.target.value })}
              className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="ollama">Ollama (Local)</option>
              <option value="ollama_cloud">Ollama Cloud</option>
              <option value="vertex">Google Vertex AI</option>
              <option value="bedrock">AWS Bedrock</option>
              <option value="openai">OpenAI</option>
            </select>
            <p className="mt-2 text-sm text-slate-500">
              Current model: <span className="font-mono">{settings.model}</span>
            </p>
          </div>

          <div className="border-t border-slate-200 pt-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="font-semibold text-slate-900">Auto-Review on PR</h3>
                <p className="text-sm text-slate-500">
                  Automatically review PRs when webhooks are received
                </p>
              </div>
              <button
                onClick={() => setSettings({ ...settings, auto_review: !settings.auto_review })}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.auto_review ? 'bg-blue-600' : 'bg-slate-300'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.auto_review ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="space-y-4 mt-4 ml-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-800">Auto-Describe on Open</h4>
                  <p className="text-xs text-slate-500">Generate PR summary automatically</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, auto_describe_on_open: !settings.auto_describe_on_open })}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    settings.auto_describe_on_open ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${settings.auto_describe_on_open ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-800">Auto-Label on Open</h4>
                  <p className="text-xs text-slate-500">Apply labels based on changes</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, auto_label_on_open: !settings.auto_label_on_open })}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    settings.auto_label_on_open ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${settings.auto_label_on_open ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-800">Auto-Security on Open</h4>
                  <p className="text-xs text-slate-500">Scan for vulnerabilities on new PRs</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, auto_security_on_open: !settings.auto_security_on_open })}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    settings.auto_security_on_open ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${settings.auto_security_on_open ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-6">
            <h3 className="font-semibold text-slate-900 mb-4">Display & Security</h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-800">Inline Comments</h4>
                  <p className="text-xs text-slate-500">Post review notes directly to code lines</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, inline_comments: !settings.inline_comments })}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    settings.inline_comments ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${settings.inline_comments ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-slate-800">RBAC Enabled</h4>
                  <p className="text-xs text-slate-500">Enforce role-based access control</p>
                </div>
                <button
                  onClick={() => setSettings({ ...settings, rbac_enabled: !settings.rbac_enabled })}
                  className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                    settings.rbac_enabled ? 'bg-blue-600' : 'bg-slate-300'
                  }`}
                >
                  <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${settings.rbac_enabled ? 'translate-x-5' : 'translate-x-1'}`} />
                </button>
              </div>
            </div>
          </div>

          <div className="border-t border-slate-200 pt-6">
            <label className="block text-sm font-medium text-slate-700 mb-2">
              Minimum Approval Score
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="range"
                min="0"
                max="100"
                value={settings.min_approval_score}
                onChange={(e) =>
                  setSettings({ ...settings, min_approval_score: parseInt(e.target.value) })
                }
                className="flex-1"
              />
              <span className="text-2xl font-bold text-slate-900 w-16 text-right">
                {settings.min_approval_score}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-500">
              PRs scoring below this threshold will be marked as needing changes
            </p>
          </div>

          <div className="pt-6">
            <button
              onClick={handleSave}
              disabled={saving}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center space-x-2"
            >
              {saving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  <span>Saving...</span>
                </>
              ) : (
                <>
                  <Save className="h-5 w-5" />
                  <span>Save Settings</span>
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-semibold text-blue-900 mb-2">Environment Variables</h3>
        <p className="text-sm text-blue-700 mb-2">
          Some settings are configured via environment variables in the <code className="bg-white px-1 py-0.5 rounded">.env</code> file:
        </p>
        <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
          <li>LLM API keys and endpoints</li>
          <li>Git provider tokens and webhooks</li>
          <li>Database connections</li>
        </ul>
      </div>
    </div>
  );
}

export default SettingsPanel;
