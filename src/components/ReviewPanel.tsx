import { useState } from 'react';
import { Send, AlertCircle, CheckCircle, Info, Lightbulb } from 'lucide-react';

interface ReviewComment {
  path: string;
  line: number | null;
  severity: 'critical' | 'warning' | 'info' | 'suggestion';
  category: string;
  message: string;
  suggestion: string | null;
}

interface ReviewResult {
  score: number;
  approved: boolean;
  summary: string;
  comments: ReviewComment[];
}

function ReviewPanel() {
  const [provider, setProvider] = useState('github');
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [prNumber, setPrNumber] = useState('');
  const [tool, setTool] = useState('review');
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReviewResult | string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setResult(null);

    try {
      const requestBody = {
        pr: {
          provider,
          owner,
          repo,
          number: parseInt(prNumber),
        },
        tool,
        ...(tool === 'ask' && question ? { question } : {}),
      };

      const response = await fetch('http://localhost:8000/api/v1/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      setResult(`Error: ${message}`);
    } finally {
      setLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertCircle className="h-5 w-5 text-red-600" />;
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-amber-600" />;
      case 'info':
        return <Info className="h-5 w-5 text-blue-600" />;
      case 'suggestion':
        return <Lightbulb className="h-5 w-5 text-emerald-600" />;
      default:
        return <Info className="h-5 w-5 text-slate-600" />;
    }
  };

  const getSeverityBg = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-50 border-red-200';
      case 'warning':
        return 'bg-amber-50 border-amber-200';
      case 'info':
        return 'bg-blue-50 border-blue-200';
      case 'suggestion':
        return 'bg-emerald-50 border-emerald-200';
      default:
        return 'bg-slate-50 border-slate-200';
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h2 className="text-2xl font-bold text-slate-900 mb-6">Manual PR Review</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Git Provider
              </label>
              <select
                value={provider}
                onChange={(e) => setProvider(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="github">GitHub</option>
                <option value="gitlab">GitLab</option>
                <option value="gitea">Gitea</option>
                <option value="bitbucket">Bitbucket</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Tool
              </label>
              <select
                value={tool}
                onChange={(e) => setTool(e.target.value)}
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="review">Review</option>
                <option value="describe">Describe</option>
                <option value="improve">Improve</option>
                <option value="security">Security</option>
                <option value="changelog">Changelog</option>
                <option value="ask">Ask</option>
                <option value="labels">Labels</option>
                <option value="test_gen">Test Generation</option>
                <option value="perf">Performance</option>
                <option value="self_review">Self Review</option>
                <option value="auto_issue">Auto-Issue Creation</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Owner/Org
              </label>
              <input
                type="text"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="facebook"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                Repository
              </label>
              <input
                type="text"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="react"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-2">
                PR Number
              </label>
              <input
                type="number"
                value={prNumber}
                onChange={(e) => setPrNumber(e.target.value)}
                placeholder="123"
                className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {tool === 'ask' && (
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Question
                </label>
                <input
                  type="text"
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  placeholder="What does this PR do?"
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required={tool === 'ask'}
                />
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold py-3 px-6 rounded-lg transition-colors flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Send className="h-5 w-5" />
                <span>Run {tool.charAt(0).toUpperCase() + tool.slice(1)}</span>
              </>
            )}
          </button>
        </form>
      </div>

      {result && (
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h3 className="text-xl font-bold text-slate-900 mb-4">Results</h3>

          {typeof result === 'string' ? (
            <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
              <pre className="whitespace-pre-wrap text-sm text-slate-700">{result}</pre>
            </div>
          ) : tool === 'auto_issue' ? (
            <div className="space-y-6">
              <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-6">
                <div className="flex items-center space-x-3 mb-4">
                  <CheckCircle className="h-8 w-8 text-emerald-600" />
                  <h4 className="text-xl font-bold text-emerald-900">Issue Creation Complete</h4>
                </div>
                <p className="text-emerald-800 mb-6">{(result as any).summary}</p>
                
                {((result as any).issues_created || []).length > 0 && (
                  <div className="space-y-3">
                    <h5 className="font-semibold text-emerald-900">Created Issues:</h5>
                    <div className="grid gap-2">
                      {((result as any).issues_created || []).map((url: string, idx: number) => (
                        <a 
                          key={idx}
                          href={url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center space-x-2 p-3 bg-white border border-emerald-200 rounded-lg hover:bg-emerald-50 transition-colors text-blue-600 hover:text-blue-800"
                        >
                          <span className="truncate flex-1 font-mono text-sm">{url}</span>
                          <Send className="h-4 w-4 flex-shrink-0" />
                        </a>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="flex items-center space-x-4">
                <div className="relative w-32 h-32">
                  <svg className="w-32 h-32 transform -rotate-90">
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke="#e2e8f0"
                      strokeWidth="8"
                      fill="none"
                    />
                    <circle
                      cx="64"
                      cy="64"
                      r="56"
                      stroke={result.score >= 70 ? '#10b981' : '#ef4444'}
                      strokeWidth="8"
                      fill="none"
                      strokeDasharray={`${(result.score / 100) * 352} 352`}
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-3xl font-bold text-slate-900">{result.score}</span>
                  </div>
                </div>

                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    {result.approved ? (
                      <CheckCircle className="h-6 w-6 text-emerald-600" />
                    ) : (
                      <AlertCircle className="h-6 w-6 text-red-600" />
                    )}
                    <span className={`text-lg font-semibold ${result.approved ? 'text-emerald-600' : 'text-red-600'}`}>
                      {result.approved ? 'Approved' : 'Changes Requested'}
                    </span>
                  </div>
                  <p className="text-slate-700">{result.summary}</p>
                </div>
              </div>

              {result.comments && result.comments.length > 0 && (
                <div className="space-y-3">
                  <h4 className="font-semibold text-slate-900">Comments ({result.comments.length})</h4>
                  {result.comments.map((comment, idx) => (
                    <div
                      key={idx}
                      className={`rounded-lg p-4 border ${getSeverityBg(comment.severity)}`}
                    >
                      <div className="flex items-start space-x-3">
                        {getSeverityIcon(comment.severity)}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="font-mono text-sm text-slate-600">
                              {comment.path}:{comment.line || '?'}
                            </span>
                            <span className="text-xs font-semibold uppercase px-2 py-1 bg-white rounded">
                              {comment.category}
                            </span>
                          </div>
                          <p className="text-sm text-slate-800 mb-2">{comment.message}</p>
                          {comment.suggestion && (
                            <div className="bg-white rounded border border-slate-200 p-3 mt-2">
                              <p className="text-xs font-semibold text-slate-600 mb-1">Suggestion:</p>
                              <pre className="text-sm text-slate-700 whitespace-pre-wrap">{comment.suggestion}</pre>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ReviewPanel;
