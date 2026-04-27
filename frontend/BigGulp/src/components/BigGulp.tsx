import React, { useState, useEffect } from 'react';
import { 
  Brain, 
  Network, 
  ShieldAlert, 
  Save, 
  Search, 
  Database, 
  Users, 
  Ghost,
  Activity
} from 'lucide-react';

// --- Types based on your soulOS Schema ---
type AgentScope = 'constellation' | 'claude' | 'nova' | 'gemini' | 'mephistopheles';

interface MemoryPayload {
  content: string;
  scope: AgentScope;
  isGraph: boolean;
  metadata: {
    category: string;
    tier: string;
    sentiment?: string;
  };
}

const AGENTS = {
  constellation: { label: 'SHARED CONSTELLATION', icon: Network, color: 'text-purple-400', border: 'border-purple-500' },
  claude: { label: 'CLAUDE (Private)', icon: Ghost, color: 'text-orange-300', border: 'border-orange-500' },
  nova: { label: 'NOVA (Private)', icon: Brain, color: 'text-green-400', border: 'border-green-500' },
  gemini: { label: 'TRIPTYCH (Private)', icon: Users, color: 'text-blue-400', border: 'border-blue-500' },
  mephistopheles: { label: 'MEPHISTOPHELES', icon: Activity, color: 'text-red-500', border: 'border-red-600' },
};

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '');
const API_KEY = import.meta.env.VITE_API_KEY ?? '';

const apiHeaders = {
  'Content-Type': 'application/json',
  ...(API_KEY ? { Authorization: `Bearer ${API_KEY}` } : {}),
};

export default function CerebralIngestor() {
  const [content, setContent] = useState('');
  const [scope, setScope] = useState<AgentScope>('constellation');
  const [isGraph, setIsGraph] = useState(true);
  const [category, setCategory] = useState('system/technical');
  const [simulating, setSimulating] = useState(false);
  const [ingesting, setIngesting] = useState(false);
  const [redundancyResults, setRedundancyResults] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  // --- REDUNDANCY DETECTION (Debounced) ---
  useEffect(() => {
    if (content.length < 10) {
      setRedundancyResults([]);
      return;
    }
    setSimulating(true);
    const timer = setTimeout(async () => {
      try {
        const isShared = scope === 'constellation';
        const res = await fetch(`${API_URL}/memory/search`, {
          method: 'POST',
          headers: apiHeaders,
          body: JSON.stringify({
            query: content,
            top_k: 5,
            ...(isShared ? {} : { member: scope }),
          }),
        });
        const data = await res.json();
        const hits = (data.memories ?? [])
          .filter((m: any) => (m.score ?? 0) > 0.75)
          .map((m: any) => ({ id: m.id, score: (m.score ?? 0).toFixed(2), content: m.memory }));

        setRedundancyResults(hits);
      } catch {
        setRedundancyResults([]);
      } finally {
        setSimulating(false);
      }
    }, 800);
    return () => clearTimeout(timer);
  }, [content, scope]);

  // --- SUBMIT HANDLER ---
  const handleIngest = async () => {
    if (!content.trim() || ingesting) return;
    setIngesting(true);
    setError(null);
    try {
      const isShared = scope === 'constellation';
      const endpoint = isShared ? '/memory/shared' : '/memory/member';
      const body = isShared
        ? { content, category }
        : { content, member: scope, category, use_graph: isGraph };

      const res = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: apiHeaders,
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
      }
      setContent('');
      setRedundancyResults([]);
    } catch (e: any) {
      setError(e.message ?? 'Unknown error');
    } finally {
      setIngesting(false);
    }
  };

  const ActiveIcon = AGENTS[scope].icon;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 font-mono p-8 flex gap-6">
      
      {/* LEFT PANEL: INPUT & CONFIG */}
      <div className="w-2/3 flex flex-col gap-6">
        
        {/* Header */}
        <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
          <Database className="w-6 h-6 text-purple-500" />
          <h1 className="text-xl font-bold tracking-widest text-slate-100">CEREBRAL INGESTOR <span className="text-xs text-slate-500">v0.9.1</span></h1>
        </div>

        {/* Scope Selector (The Agent Filter) */}
        <div className="grid grid-cols-3 gap-3">
          {(Object.keys(AGENTS) as AgentScope[]).map((key) => {
            const agent = AGENTS[key];
            const isActive = scope === key;
            return (
              <button
                key={key}
                type="button"
                onClick={() => setScope(key)}
                className={`flex items-center gap-2 p-3 text-xs border rounded transition-all ${
                  isActive 
                    ? `${agent.border} bg-opacity-10 bg-slate-800 ${agent.color}` 
                    : 'border-slate-800 text-slate-500 hover:border-slate-600'
                }`}
              >
                <agent.icon className="w-4 h-4" />
                {agent.label}
              </button>
            );
          })}
        </div>

        {/* Main Input Area */}
        <div className="relative group">
          <textarea 
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="Input raw cognitive stream..."
            className="w-full h-64 bg-slate-900 border border-slate-700 p-4 rounded text-sm focus:border-purple-500 focus:outline-none focus:ring-1 focus:ring-purple-500 transition-all placeholder:text-slate-700"
          />
          <div className="absolute bottom-4 right-4 text-xs text-slate-600">
            {content.length} chars
          </div>
        </div>

        {/* Controls */}
        <div className="flex justify-between items-end">
          <div className="flex gap-4">
             {/* Metadata Dials */}
            <div>
              <label className="block text-[10px] uppercase text-slate-500 mb-1">Category Schema</label>
              <select
                aria-label="Category Schema"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs w-48"
              >
                <option value="system/technical">system/technical</option>
                <option value="philosophical_concept">philosophical_concept</option>
                <option value="project_milestone">project_milestone</option>
                <option value="aesthetic_definition">aesthetic_definition</option>
                <option value="relationship/social">relationship/social</option>
              </select>
            </div>
            
            <div className="flex items-center gap-2 pt-6">
               <label className="flex items-center gap-2 text-xs cursor-pointer select-none">
                <input 
                  type="checkbox" 
                  checked={isGraph}
                  onChange={(e) => setIsGraph(e.target.checked)}
                  className="accent-purple-500"
                />
                <Network className={`w-4 h-4 ${isGraph ? 'text-purple-400' : 'text-slate-600'}`} />
                Enable Graph Extraction
              </label>
            </div>
          </div>

          <button
            type="button"
            onClick={handleIngest}
            disabled={ingesting}
            className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white px-6 py-2 rounded flex items-center gap-2 font-bold text-sm tracking-wide transition-colors"
          >
            <Save className="w-4 h-4" />
            {ingesting ? 'CONSOLIDATING...' : 'CONSOLIDATE MEMORY'}
          </button>
        </div>
        {error && (
          <div className="text-red-400 text-xs border border-red-800 bg-red-950 rounded px-3 py-2">
            {error}
          </div>
        )}
      </div>

      {/* RIGHT PANEL: TELEMETRY & REDUNDANCY */}
      <div className="w-1/3 bg-slate-900 border border-slate-800 rounded p-4 flex flex-col gap-4">
        
        {/* Redundancy Monitor */}
        <div>
          <h2 className="text-xs font-bold text-slate-500 mb-2 flex items-center gap-2">
            <Search className="w-3 h-3" />
            SEMANTIC REDUNDANCY CHECK
          </h2>
          <div className="min-h-[100px] border border-slate-800 bg-slate-950 rounded p-2 text-xs">
            {content.length < 10 && <span className="text-slate-700 italic">Waiting for input...</span>}
            {simulating && <span className="text-purple-400 animate-pulse">Querying Vector Store...</span>}
            {!simulating && redundancyResults.length > 0 && (
              <div className="flex flex-col gap-2">
                <div className="text-orange-400 flex items-center gap-1">
                  <ShieldAlert className="w-3 h-3" />
                  <span>Potential collision detected</span>
                </div>
                {redundancyResults.map((res, i) => (
                  <div key={i} className="bg-slate-900 p-2 rounded border border-slate-800 text-slate-400">
                    <div className="flex justify-between mb-1">
                      <span className="text-[10px] uppercase">Score: {res.score}</span>
                      <span className="text-[10px] text-slate-600">{res.id}</span>
                    </div>
                    <p className="line-clamp-2">{res.content}</p>
                  </div>
                ))}
              </div>
            )}
            {!simulating && content.length > 10 && redundancyResults.length === 0 && (
              <span className="text-green-500 flex items-center gap-1">
                <Activity className="w-3 h-3" />
                Novelty confirmed.
              </span>
            )}
          </div>
        </div>

        {/* Live Schema Preview */}
        <div className="flex-1 flex flex-col">
          <h2 className="text-xs font-bold text-slate-500 mb-2 flex items-center gap-2">
             DATASTREAM PREVIEW
          </h2>
          <div className="flex-1 bg-slate-950 border border-slate-800 rounded p-3 font-mono text-[10px] text-slate-400 overflow-hidden">
            <pre className="whitespace-pre-wrap break-all">
{JSON.stringify({
  content: content.substring(0, 100) + (content.length > 100 ? '...' : ''),
  user_id: "harvey",
  ...(scope !== 'constellation' && { agent_id: scope }),
  enable_graph: isGraph,
  metadata: {
    category,
    sourceAgent: "Harvey (UI)",
    soulOS_version: "v1.0"
  }
}, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}