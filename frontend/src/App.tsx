import React, { useState, useEffect } from 'react';

interface HealthResponse {
  status: string;
  version: string;
  llm_backend: string;
  llm_healthy: boolean;
}

interface Settings {
  llm_provider: string;
  llm_model: string;
  llm_base_url: string;
  auto_review: boolean;
  min_score_to_approve: number;
  github_token?: string;
  gitlab_token?: string;
  github_api_url?: string;
  gitlab_url?: string;
}

interface ReviewResult {
  pr_number: number;
  repo: string;
  summary: string;
  score: number;
  approved: boolean;
  comments: Array<{
    path: string;
    line: number | null;
    severity: string;
    category: string;
    message: string;
    suggestion: string | null;
  }>;
}

const API_BASE = '/api/v1';

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'review' | 'settings'>('review');
  
  // Review Form State
  const [reviewRepo, setReviewRepo] = useState('');
  const [reviewPr, setReviewPr] = useState('');
  const [reviewProvider, setReviewProvider] = useState('github');
  const [reviewResult, setReviewResult] = useState<ReviewResult | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);

  const fetchData = async () => {
    try {
      const [hRes, sRes] = await Promise.all([
        fetch(`${API_BASE}/health`),
        fetch(`${API_BASE}/settings`)
      ]);
      const hData = await hRes.json();
      const sData = await sRes.json();
      setHealth(hData);
      setSettings(sData);
    } catch (err) {
      console.error('Failed to fetch data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleSaveSettings = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!settings) return;
    try {
      const res = await fetch(`${API_BASE}/settings`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      const data = await res.json();
      setSettings(data);
      alert('Settings saved!');
      fetchData(); // Refresh health status
    } catch (err) {
      alert('Failed to save settings');
    }
  };

  const handleTriggerReview = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsReviewing(true);
    setReviewResult(null);
    try {
      const res = await fetch(`${API_BASE}/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo: reviewRepo,
          pr_number: parseInt(reviewPr),
          provider: reviewProvider
        }),
      });
      if (!res.ok) throw new Error('Review failed');
      const data = await res.json();
      setReviewResult(data);
    } catch (err) {
      alert('Review failed. Check if repo and PR exist and tokens are valid.');
    } finally {
      setIsReviewing(false);
    }
  };

  if (loading) return (
    <div className="flex flex-col items-center justify-center h-screen bg-slate-950 text-slate-400">
      <div className="w-12 h-12 border-4 border-blue-500/20 border-t-blue-500 rounded-full animate-spin mb-4"></div>
      <p className="font-medium animate-pulse">Initializing PRism-AI...</p>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-sans selection:bg-blue-500/30">
      {/* Background Decor */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-blue-500/10 blur-[120px] rounded-full"></div>
        <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full"></div>
      </div>

      <header className="sticky top-0 z-50 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-8 py-4">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/20">
              <span className="text-white font-black text-xl">P</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-white leading-none">PRism-AI</h1>
              <p className="text-[10px] text-slate-500 uppercase font-black tracking-[0.2em] mt-1">AI Review Agent</p>
            </div>
          </div>

          <nav className="flex items-center bg-slate-950/50 p-1 rounded-xl border border-slate-800">
            <button 
              onClick={() => setActiveTab('review')}
              className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'review' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
            >
              Manual Review
            </button>
            <button 
              onClick={() => setActiveTab('settings')}
              className={`px-6 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'settings' ? 'bg-slate-800 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'}`}
            >
              System Settings
            </button>
          </nav>

          <div className="flex items-center gap-6">
            <div className="h-8 w-px bg-slate-800"></div>
            <div className="flex items-center gap-3">
              <div className="text-right hidden sm:block">
                <div className="text-[10px] text-slate-500 uppercase font-bold tracking-widest leading-none mb-1">Engine Status</div>
                <div className="flex items-center justify-end gap-2">
                  <span className={`w-2 h-2 rounded-full ${health?.llm_healthy ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'}`}></span>
                  <span className="font-mono text-[11px] font-bold text-slate-300 uppercase tracking-tight">{health?.llm_backend} {health?.llm_healthy ? 'ONLINE' : 'OFFLINE'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-8 relative">
        {activeTab === 'review' ? (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            {/* Review Form */}
            <div className="lg:col-span-4 space-y-6">
              <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl relative overflow-hidden group">
                <div className="absolute top-0 left-0 w-1 h-full bg-blue-500 group-hover:w-2 transition-all"></div>
                <h2 className="text-xl font-bold mb-6 text-white flex items-center gap-2">
                  New Review Task
                </h2>
                <form onSubmit={handleTriggerReview} className="space-y-5">
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Git Provider</label>
                    <div className="grid grid-cols-2 gap-2">
                      <button 
                        type="button"
                        onClick={() => setReviewProvider('github')}
                        className={`py-2 px-4 rounded-lg text-sm font-bold border transition-all ${reviewProvider === 'github' ? 'bg-blue-500/10 border-blue-500/50 text-blue-400' : 'bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700'}`}
                      >
                        GitHub
                      </button>
                      <button 
                        type="button"
                        onClick={() => setReviewProvider('gitlab')}
                        className={`py-2 px-4 rounded-lg text-sm font-bold border transition-all ${reviewProvider === 'gitlab' ? 'bg-orange-500/10 border-orange-500/50 text-orange-400' : 'bg-slate-950 border-slate-800 text-slate-500 hover:border-slate-700'}`}
                      >
                        GitLab
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Repository Path</label>
                    <input 
                      type="text"
                      required
                      value={reviewRepo}
                      onChange={e => setReviewRepo(e.target.value)}
                      placeholder="owner/repo-name"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm placeholder:text-slate-700 font-medium"
                    />
                  </div>
                  <div className="space-y-2">
                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-[0.15em]">Pull Request Number</label>
                    <input 
                      type="number"
                      required
                      value={reviewPr}
                      onChange={e => setReviewPr(e.target.value)}
                      placeholder="e.g. 42"
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 transition-all text-sm placeholder:text-slate-700 font-medium"
                    />
                  </div>
                  <button 
                    disabled={isReviewing}
                    className="w-full bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 disabled:from-slate-800 disabled:to-slate-800 disabled:cursor-not-allowed text-white font-black py-4 rounded-xl shadow-lg shadow-blue-900/20 transition-all active:scale-[0.98] mt-4 flex items-center justify-center gap-3 uppercase tracking-widest text-xs"
                  >
                    {isReviewing ? (
                      <>
                        <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                        Analyzing Diff...
                      </>
                    ) : (
                      'Start AI Review'
                    )}
                  </button>
                </form>
              </div>

              <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
                <h3 className="text-xs font-black text-slate-500 uppercase tracking-widest mb-4">Quick Help</h3>
                <ul className="space-y-3 text-xs text-slate-400 font-medium">
                  <li className="flex gap-2">
                    <span className="text-blue-500">•</span>
                    Enter the full path like `facebook/react` for GitHub.
                  </li>
                  <li className="flex gap-2">
                    <span className="text-blue-500">•</span>
                    Make sure you have configured a valid token in settings.
                  </li>
                  <li className="flex gap-2">
                    <span className="text-blue-500">•</span>
                    AI will check security, performance, and logic.
                  </li>
                </ul>
              </div>
            </div>

            {/* Results Display */}
            <div className="lg:col-span-8">
              {reviewResult ? (
                <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  <div className={`bg-slate-900 border-l-4 rounded-2xl p-8 shadow-2xl relative overflow-hidden ${reviewResult.approved ? 'border-emerald-500' : 'border-yellow-500'}`}>
                    <div className="absolute top-0 right-0 p-8">
                      <div className={`text-5xl font-black ${reviewResult.score >= 80 ? 'text-emerald-500' : reviewResult.score >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>
                        {reviewResult.score}<span className="text-xl text-slate-700">/100</span>
                      </div>
                    </div>
                    <div className="relative z-10">
                      <div className="flex items-center gap-3 mb-4">
                        <span className={`px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-widest ${reviewResult.approved ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20'}`}>
                          {reviewResult.approved ? 'Approved' : 'Changes Requested'}
                        </span>
                        <span className="text-slate-500 text-sm font-medium">PR #{reviewResult.pr_number} • {reviewResult.repo}</span>
                      </div>
                      <h3 className="text-2xl font-bold text-white mb-4">Review Summary</h3>
                      <p className="text-slate-400 leading-relaxed max-w-2xl whitespace-pre-wrap">{reviewResult.summary}</p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest px-2">Line-level Feedback</h3>
                    {reviewResult.comments.length > 0 ? (
                      reviewResult.comments.map((comment, idx) => (
                        <div key={idx} className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl hover:border-slate-700 transition-all">
                          <div className="bg-slate-950 px-6 py-3 border-b border-slate-800 flex justify-between items-center">
                            <span className="text-xs font-mono text-blue-400 font-bold">{comment.path}:{comment.line || 'global'}</span>
                            <div className="flex gap-2">
                              <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded border ${
                                comment.severity === 'critical' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                comment.severity === 'warning' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' :
                                'bg-blue-500/10 text-blue-400 border-blue-500/20'
                              }`}>
                                {comment.severity}
                              </span>
                              <span className="text-[10px] font-black uppercase px-2 py-0.5 rounded border bg-slate-800 border-slate-700 text-slate-400">
                                {comment.category}
                              </span>
                            </div>
                          </div>
                          <div className="p-6">
                            <p className="text-sm text-slate-300 font-medium leading-relaxed">{comment.message}</p>
                            {comment.suggestion && (
                              <div className="mt-4 space-y-2">
                                <label className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">AI Suggestion</label>
                                <pre className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs font-mono text-emerald-400 overflow-x-auto">
                                  {comment.suggestion}
                                </pre>
                              </div>
                            )}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="bg-slate-900/50 border border-dashed border-slate-800 rounded-2xl p-12 text-center">
                        <p className="text-slate-500 font-medium">No specific issues found. Great job!</p>
                      </div>
                    )}
                  </div>
                </div>
              ) : isReviewing ? (
                <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-20 text-center flex flex-col items-center justify-center space-y-6">
                   <div className="relative">
                     <div className="w-20 h-20 border-4 border-blue-500/10 border-t-blue-500 rounded-full animate-spin"></div>
                     <div className="absolute inset-0 flex items-center justify-center">
                       <span className="text-blue-400 font-bold animate-pulse">AI</span>
                     </div>
                   </div>
                   <div>
                     <h3 className="text-xl font-bold text-white mb-2">Analyzing Codebase</h3>
                     <p className="text-slate-500 text-sm max-w-xs mx-auto leading-relaxed">Our AI is currently examining the diff for security flaws, performance bottlenecks, and style violations.</p>
                   </div>
                </div>
              ) : (
                <div className="bg-slate-900/50 border border-dashed border-slate-800 rounded-2xl p-20 text-center flex flex-col items-center justify-center space-y-4">
                  <div className="w-16 h-16 bg-slate-900 rounded-2xl flex items-center justify-center text-slate-700 text-3xl">🔍</div>
                  <h3 className="text-slate-400 font-bold">No Review Selected</h3>
                  <p className="text-slate-600 text-sm max-w-xs mx-auto">Fill out the form on the left to start a manual AI review of any Pull Request.</p>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-10 shadow-2xl relative overflow-hidden">
              <div className="absolute top-0 right-0 p-10 opacity-10">
                <svg className="w-40 h-40 text-blue-500" fill="currentColor" viewBox="0 0 24 24"><path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/></svg>
              </div>
              
              <h2 className="text-2xl font-bold mb-8 text-white flex items-center gap-3">
                System Configuration
              </h2>
              
              <form onSubmit={handleSaveSettings} className="space-y-10">
                {/* AI Section */}
                <div className="space-y-6">
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center text-blue-400">🤖</div>
                    <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em]">LLM Intelligence</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-12">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">AI Provider</label>
                      <select 
                        value={settings?.llm_provider} 
                        onChange={e => setSettings(s => s ? {...s, llm_provider: e.target.value} : null)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-bold"
                      >
                        <option value="ollama">Ollama (Local)</option>
                        <option value="ollama_cloud">Ollama Cloud</option>
                        <option value="openai">OpenAI / Compatible</option>
                        <option value="vertex">Google Vertex AI</option>
                        <option value="bedrock">AWS Bedrock</option>
                      </select>
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Model Engine</label>
                      <input 
                        type="text"
                        value={settings?.llm_model}
                        onChange={e => setSettings(s => s ? {...s, llm_model: e.target.value} : null)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-mono"
                      />
                    </div>
                    <div className="md:col-span-2 space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">Base Endpoint URL</label>
                      <input 
                        type="text"
                        value={settings?.llm_base_url}
                        onChange={e => setSettings(s => s ? {...s, llm_base_url: e.target.value} : null)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-mono"
                      />
                    </div>
                  </div>
                </div>

                {/* Git Credentials Section */}
                <div className="space-y-6 pt-6 border-t border-slate-800">
                  <div className="flex items-center gap-4">
                    <div className="w-8 h-8 bg-orange-500/10 rounded-lg flex items-center justify-center text-orange-400">🔑</div>
                    <h3 className="text-xs font-black text-slate-500 uppercase tracking-[0.2em]">Git Credentials</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pl-12">
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">GitHub API Token</label>
                      <input 
                        type="password"
                        value={settings?.github_token}
                        onChange={e => setSettings(s => s ? {...s, github_token: e.target.value} : null)}
                        placeholder="ghp_********************"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-mono"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">GitLab Access Token</label>
                      <input 
                        type="password"
                        value={settings?.gitlab_token}
                        onChange={e => setSettings(s => s ? {...s, gitlab_token: e.target.value} : null)}
                        placeholder="glpat-********************"
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-mono"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">GitHub API URL</label>
                      <input 
                        type="text"
                        value={settings?.github_api_url}
                        onChange={e => setSettings(s => s ? {...s, github_api_url: e.target.value} : null)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-mono"
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[10px] font-black text-slate-600 uppercase tracking-widest">GitLab Instance URL</label>
                      <input 
                        type="text"
                        value={settings?.gitlab_url}
                        onChange={e => setSettings(s => s ? {...s, gitlab_url: e.target.value} : null)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all text-sm font-mono"
                      />
                    </div>
                  </div>
                </div>

                <div className="pt-8 border-t border-slate-800 flex justify-between items-center">
                   <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest italic">Changes take effect immediately.</p>
                   <button 
                    type="submit"
                    className="bg-gradient-to-r from-blue-600 to-blue-500 hover:from-blue-500 hover:to-blue-400 text-white font-black py-4 px-12 rounded-2xl shadow-xl shadow-blue-900/30 transition-all active:scale-[0.98] uppercase tracking-widest text-xs"
                  >
                    Apply Changes
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </main>
      
      <footer className="max-w-7xl mx-auto px-8 py-12 border-t border-slate-900 mt-12 flex justify-between items-center text-slate-600">
        <div className="text-xs font-bold uppercase tracking-widest">PRism-AI v1.0.0 • {new Date().getFullYear()}</div>
        <div className="flex gap-6">
          <a href="#" className="hover:text-blue-500 transition-colors">Documentation</a>
          <a href="#" className="hover:text-blue-500 transition-colors">GitHub</a>
          <a href="#" className="hover:text-blue-500 transition-colors">License</a>
        </div>
      </footer>
    </div>
  );
}

export default App;
