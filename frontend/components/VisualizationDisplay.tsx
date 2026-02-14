"use client";

import { useState, useEffect } from 'react';
import {
  Brain, Download, Loader2, Lightbulb, Network,
  BookOpen, Code, GraduationCap, FileText, Share2,
  Eye, CheckCircle, ChevronDown, ChevronUp, Sparkles,
  ArrowRight, BarChart3, Clock, Target
} from 'lucide-react';

interface VisualizationDisplayProps {
  jobId: string;
}

export default function VisualizationDisplay({ jobId }: VisualizationDisplayProps) {
  const [rawData, setRawData] = useState<any>(null);
  const [viz, setViz] = useState<any>(null);
  const [meta, setMeta] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'structured' | 'html' | 'raw'>('structured');
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['concepts', 'ideas', 'relationships', 'connections', 'infographic', 'timeline', 'structure'])
  );
  const [copied, setCopied] = useState(false);

  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  useEffect(() => { 
    fetchVisualization(); 
  }, [jobId]);
  
  const fetchVisualization = async () => {
    try {
      setIsLoading(true);
      setError(null);
  
      const response = await fetch(
        `${API_BASE}/api/visualization/${jobId}?format=json`,
        { headers: { 'Accept': 'application/json' } }
      );
  
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Server error ${response.status}: ${text.slice(0, 100)}`);
      }
  
      const text = await response.text();
  
      if (text.trimStart().startsWith('<')) {
        throw new Error('Backend returned HTML. Make sure your /api/visualization endpoint returns JSONResponse for format=json.');
      }
  
      let data: any;
      try {
        data = JSON.parse(text);
      } catch {
        throw new Error(`Could not parse response: ${text.slice(0, 120)}`);
      }
  
      setRawData(data);
  
      // FIX: Handle nested visualization object
      let vizData: any;
      let metaData: any;
  
      if (data.visualization?.visualization) {
        // Nested case: unwrap the inner visualization
        vizData = data.visualization.visualization;
        metaData = data.visualization.metadata || data.metadata || null;
      } else if (data.visualization) {
        vizData = data.visualization;
        metaData = data.metadata || null;
      } else if (data.title || data.main_ideas || data.key_concepts || data.summary) {
        vizData = data;
        metaData = null;
      } else {
        vizData = data;
        metaData = null;
      }
  
      console.log('✅ Parsed visualization data:', vizData);
      console.log('✅ Parsed metadata:', metaData);
  
      setViz(vizData);
      setMeta(metaData);
  
    } catch (err: any) {
      setError(err.message || 'Failed to load visualization');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleSection = (key: string) => {
    setExpandedSections(prev => {
      const next = new Set(prev);
      next.has(key) ? next.delete(key) : next.add(key);
      return next;
    });
  };

  const handleCopy = async () => {
    await navigator.clipboard.writeText(JSON.stringify(rawData, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([JSON.stringify(rawData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `visualization-${jobId.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getContentTypeIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      academic: <GraduationCap className="w-4 h-4" />,
      technical: <Code className="w-4 h-4" />,
      educational: <BookOpen className="w-4 h-4" />,
      general: <FileText className="w-4 h-4" />,
    };
    return icons[type] || icons.general;
  };

  const SectionHeader = ({ id, icon, title, count }: {
    id: string; icon: React.ReactNode; title: string; count?: number;
  }) => (
    <button
      onClick={() => toggleSection(id)}
      className="w-full flex items-center justify-between p-4 hover:bg-white/5 transition rounded-t-xl"
    >
      <div className="flex items-center gap-3">
        {icon}
        <span className="font-semibold text-white">{title}</span>
        {count !== undefined && (
          <span className="text-xs bg-white/10 text-gray-400 px-2 py-0.5 rounded-full">{count}</span>
        )}
      </div>
      {expandedSections.has(id)
        ? <ChevronUp className="w-4 h-4 text-gray-400" />
        : <ChevronDown className="w-4 h-4 text-gray-400" />}
    </button>
  );

  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white/5 border border-white/10 p-12">
        <div className="flex flex-col items-center gap-4">
          <div className="relative">
            <Brain className="w-12 h-12 text-purple-400" />
            <Loader2 className="w-5 h-5 text-purple-300 animate-spin absolute -top-1 -right-1" />
          </div>
          <p className="text-gray-400 text-sm">Loading visualization...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl bg-red-500/10 border border-red-500/30 p-8 space-y-3">
        <p className="text-red-400 font-medium">Failed to load visualization</p>
        <p className="text-red-300/70 text-sm font-mono break-all">{error}</p>
        <button
          onClick={fetchVisualization}
          className="mt-2 px-4 py-2 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-300 text-sm transition"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!viz) {
    return (
      <div className="rounded-2xl bg-yellow-500/10 border border-yellow-500/30 p-8">
        <p className="text-yellow-400 text-center">No visualization data available</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">

      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-br from-purple-600/15 via-violet-600/10 to-pink-600/15 border border-purple-500/25 p-6">
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div className="flex-1 min-w-0 space-y-3">
            <div className="flex items-center gap-2 flex-wrap">
              {meta?.content_type && (
                <span className="inline-flex items-center gap-1.5 text-xs bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2.5 py-1 rounded-full">
                  {getContentTypeIcon(meta.content_type)}
                  {meta.content_type.toUpperCase()}
                </span>
              )}
              {meta?.pages_processed && (
                <span className="text-xs text-gray-500">{meta.pages_processed} pages</span>
              )}
              {meta?.model && (
                <span className="text-xs text-gray-600 font-mono">{meta.model}</span>
              )}
            </div>
            <h2 className="text-2xl font-bold text-white leading-tight">
              {viz.title || 'Document Visualization'}
            </h2>
            {(viz.summary || viz.overview) && (
              <p className="text-gray-300 text-sm leading-relaxed max-w-2xl">
                {viz.summary || viz.overview}
              </p>
            )}
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={handleCopy}
              className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-gray-300 text-sm flex items-center gap-2 transition"
            >
              <Share2 className="w-4 h-4" />
              {copied ? '✓ Copied' : 'Copy JSON'}
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm flex items-center gap-2 transition"
            >
              <Download className="w-4 h-4" />
              Download
            </button>
          </div>
        </div>
      </div>

      {/* View Tabs */}
      <div className="flex gap-1 bg-white/5 p-1 rounded-xl w-fit">
        {(['structured', 'html', 'raw'] as const).map(mode => (
          <button
            key={mode}
            onClick={() => setViewMode(mode)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition ${
              viewMode === mode
                ? 'bg-purple-600 text-white shadow-lg shadow-purple-900/30'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {mode === 'structured' ? '✦ Structured' : mode === 'html' ? '⊞ Visual' : '{ } Raw'}
          </button>
        ))}
      </div>

      {/* STRUCTURED VIEW */}
      {viewMode === 'structured' && (
        <div className="space-y-4">

          {/* Main Ideas */}
          {viz.main_ideas?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="ideas" icon={<Brain className="w-5 h-5 text-blue-400" />} title="Main Ideas" count={viz.main_ideas.length} />
              {expandedSections.has('ideas') && (
                <div className="px-4 pb-4 grid gap-3">
                  {viz.main_ideas.map((idea: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/15 hover:border-blue-500/30 transition space-y-2">
                      <h4 className="font-semibold text-white text-sm">{idea.idea}</h4>
                      <p className="text-gray-400 text-xs leading-relaxed">{idea.explanation}</p>
                      {idea.visual_suggestion && (
                        <span className="inline-flex items-center gap-1 text-xs bg-blue-500/15 text-blue-400 px-2 py-0.5 rounded-full">
                          <Sparkles className="w-3 h-3" /> {idea.visual_suggestion}
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Key Concepts */}
          {viz.key_concepts?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="concepts" icon={<Lightbulb className="w-5 h-5 text-amber-400" />} title="Key Concepts" count={viz.key_concepts.length} />
              {expandedSections.has('concepts') && (
                <div className="px-4 pb-4 grid gap-3">
                  {viz.key_concepts.map((concept: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-3 rounded-lg bg-amber-500/5 border border-amber-500/15 hover:border-amber-500/30 transition">
                      <div className="w-7 h-7 rounded-full bg-amber-500/20 flex items-center justify-center shrink-0 mt-0.5">
                        <span className="text-amber-400 text-xs font-bold">{idx + 1}</span>
                      </div>
                      <div className="space-y-1">
                        <h4 className="font-semibold text-white text-sm">{concept.concept}</h4>
                        <p className="text-gray-400 text-xs leading-relaxed">{concept.definition}</p>
                        {concept.importance && (
                          <p className="text-amber-400/70 text-xs italic">↳ {concept.importance}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Key Facts / Infographic Elements */}
          {viz.infographic_elements?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="infographic" icon={<Sparkles className="w-5 h-5 text-pink-400" />} title="Key Facts" count={viz.infographic_elements.length} />
              {expandedSections.has('infographic') && (
                <div className="px-4 pb-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {viz.infographic_elements.map((elem: any, idx: number) => (
                    <div key={idx} className="flex gap-3 p-3 rounded-lg bg-pink-500/5 border border-pink-500/15">
                      <span className="text-xs bg-pink-500/20 text-pink-400 px-2 py-0.5 rounded-full h-fit shrink-0 capitalize whitespace-nowrap">
                        {(elem.type || 'fact').split('/')[0]}
                      </span>
                      <p className="text-gray-300 text-sm">{elem.content}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Connections */}
          {viz.connections?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="connections" icon={<Network className="w-5 h-5 text-violet-400" />} title="Connections" count={viz.connections.length} />
              {expandedSections.has('connections') && (
                <div className="px-4 pb-4 space-y-2">
                  {viz.connections.map((conn: any, idx: number) => (
                    <div key={idx} className="flex items-center gap-2 p-3 rounded-lg bg-violet-500/5 border border-violet-500/15 flex-wrap">
                      <span className="text-white text-sm font-medium">{conn.item1}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-violet-400 shrink-0" />
                      <span className="text-xs text-violet-300 bg-violet-500/15 px-2 py-0.5 rounded-full">{conn.connection}</span>
                      <ArrowRight className="w-3.5 h-3.5 text-violet-400 shrink-0" />
                      <span className="text-white text-sm font-medium">{conn.item2}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Relationships */}
          {viz.relationships?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="relationships" icon={<Network className="w-5 h-5 text-cyan-400" />} title="Relationships" count={viz.relationships.length} />
              {expandedSections.has('relationships') && (
                <div className="px-4 pb-4 space-y-2">
                  {viz.relationships.map((rel: any, idx: number) => (
                    <div key={idx} className="flex items-center gap-2 p-3 rounded-lg bg-cyan-500/5 border border-cyan-500/15 flex-wrap">
                      <span className="text-white text-sm font-medium">{rel.from}</span>
                      <span className="text-xs text-cyan-400 bg-cyan-500/15 px-2 py-0.5 rounded-full">{rel.relationship}</span>
                      <span className="text-white text-sm font-medium">{rel.to}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Timeline */}
          {viz.timeline?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="timeline" icon={<Clock className="w-5 h-5 text-emerald-400" />} title="Timeline" count={viz.timeline.length} />
              {expandedSections.has('timeline') && (
                <div className="px-4 pb-4">
                  <div className="relative pl-5 border-l border-emerald-500/25 space-y-4 mt-2">
                    {viz.timeline.map((item: any, idx: number) => (
                      <div key={idx} className="relative">
                        <div className="absolute -left-[1.45rem] top-1.5 w-3 h-3 rounded-full bg-emerald-500/40 border-2 border-emerald-400" />
                        <p className="text-white text-sm font-medium">{item.event}</p>
                        {item.significance && (
                          <p className="text-gray-400 text-xs mt-0.5">{item.significance}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Learning Objectives */}
          {viz.learning_objectives?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="objectives" icon={<Target className="w-5 h-5 text-orange-400" />} title="Learning Objectives" count={viz.learning_objectives.length} />
              {expandedSections.has('objectives') && (
                <ul className="px-4 pb-4 space-y-2">
                  {viz.learning_objectives.map((obj: string, idx: number) => (
                    <li key={idx} className="flex gap-2 text-sm text-gray-300">
                      <CheckCircle className="w-4 h-4 text-orange-400 shrink-0 mt-0.5" />
                      <span>{obj}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Document Structure */}
          {viz.structure?.hierarchy?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="structure" icon={<FileText className="w-5 h-5 text-gray-400" />} title="Document Structure" count={viz.structure.hierarchy.length} />
              {expandedSections.has('structure') && (
                <div className="px-4 pb-4 space-y-2">
                  {viz.structure.hierarchy.map((item: any, idx: number) => (
                    <div
                      key={idx}
                      style={{ marginLeft: item.level === '1' ? 0 : 16 }}
                      className={`p-3 rounded-lg border ${
                        item.level === '1'
                          ? 'bg-white/5 border-white/15'
                          : 'bg-white/[0.02] border-white/8'
                      }`}
                    >
                      <p className={`font-medium text-sm ${item.level === '1' ? 'text-white' : 'text-gray-300'}`}>
                        {item.title}
                      </p>
                      {item.content?.length > 0 && (
                        <ul className="mt-1.5 space-y-1">
                          {item.content.map((point: string, i: number) => (
                            <li key={i} className="text-xs text-gray-500 flex gap-2">
                              <span className="text-gray-600 shrink-0">•</span>
                              {point}
                            </li>
                          ))}
                        </ul>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Data Points */}
          {viz.data_points?.length > 0 && (
            <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
              <SectionHeader id="data" icon={<BarChart3 className="w-5 h-5 text-rose-400" />} title="Data Points" count={viz.data_points.length} />
              {expandedSections.has('data') && (
                <div className="px-4 pb-4 grid grid-cols-2 gap-3">
                  {viz.data_points.map((dp: any, idx: number) => (
                    <div key={idx} className="p-3 rounded-lg bg-rose-500/5 border border-rose-500/15">
                      <p className="text-rose-400 text-lg font-bold">{dp.value}</p>
                      <p className="text-white text-xs font-medium">{dp.metric}</p>
                      {dp.context && <p className="text-gray-500 text-xs mt-1">{dp.context}</p>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

        </div>
      )}

      {/* HTML VIEW */}
      {viewMode === 'html' && (
        <div className="rounded-xl bg-white/5 border border-white/10 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <span className="text-sm text-gray-400">HTML Visual View</span>
            <button
              onClick={() => window.open(`${API_BASE}/api/visualization/${jobId}?format=html`, '_blank')}
              className="text-xs text-purple-400 hover:text-purple-300 flex items-center gap-1 transition"
            >
              <Eye className="w-3 h-3" /> Open in new tab
            </button>
          </div>
          <iframe
            src={`${API_BASE}/api/visualization/${jobId}?format=html`}
            className="w-full h-[700px] border-0 bg-white"
            title="HTML Visualization"
            sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
          />
        </div>
      )}

      {/* RAW JSON VIEW */}
      {viewMode === 'raw' && (
        <div className="rounded-xl bg-black/60 border border-white/10 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <span className="text-sm text-gray-400 font-mono">visualization.json</span>
            <button onClick={handleCopy} className="text-xs text-purple-400 hover:text-purple-300 transition">
              {copied ? '✓ Copied' : 'Copy all'}
            </button>
          </div>
          <pre className="p-4 text-xs text-green-300/80 overflow-auto max-h-[600px] leading-relaxed">
            {JSON.stringify(rawData, null, 2)}
          </pre>
        </div>
      )}

    </div>
  );
}