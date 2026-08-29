'use client';

import { useState, useEffect, useCallback } from 'react';
import { candidatesAPI, filtersAPI, searchAPI, documentsAPI } from '@/lib/api';
import { useDropzone } from 'react-dropzone';
import toast from 'react-hot-toast';
import {
  Search, Filter, Download, Upload, ChevronLeft, ChevronRight,
  ArrowUpDown, ArrowUp, ArrowDown, X, Plus, Save, Trash2,
  Eye, RefreshCw, SlidersHorizontal, FileText
} from 'lucide-react';
import CandidateDetail from './CandidateDetail';
import FilterBuilder from './FilterBuilder';

interface Candidate {
  candidate_id: string;
  full_name: string;
  email: string | null;
  phone: string | null;
  city: string | null;
  source_channel: string | null;
  department_tag: string | null;
  career_level: string | null;
  employment_type: string | null;
  applied_designation: string | null;
  tags: string[];
  created_at: string;
  latest_score: number | null;
  confidence_flag: string | null;
  sync_status: string | null;
  skill_names: string[];
}

export default function DatabaseView() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(25);
  const [totalPages, setTotalPages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortOrder, setSortOrder] = useState('desc');
  const [department, setDepartment] = useState('');
  const [careerLevel, setCareerLevel] = useState('');
  const [source, setSource] = useState('');
  const [showFilter, setShowFilter] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedCandidate, setSelectedCandidate] = useState<string | null>(null);
  const [savedFilters, setSavedFilters] = useState<any[]>([]);
  const [semanticQuery, setSemanticQuery] = useState('');
  const [isSemantic, setIsSemantic] = useState(false);

  const loadCandidates = useCallback(async () => {
    setLoading(true);
    try {
      const res = await candidatesAPI.list({
        page,
        page_size: pageSize,
        sort_by: sortBy,
        sort_order: sortOrder,
        search: search || undefined,
        department: department || undefined,
        career_level: careerLevel || undefined,
        source: source || undefined,
      });
      setCandidates(res.data.items);
      setTotal(res.data.total);
      setTotalPages(res.data.total_pages);
    } catch (err) {
      toast.error('Failed to load candidates');
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, sortBy, sortOrder, search, department, careerLevel, source]);

  useEffect(() => {
    loadCandidates();
  }, [loadCandidates]);

  useEffect(() => {
    loadSavedFilters();
  }, []);

  const loadSavedFilters = async () => {
    try {
      const res = await filtersAPI.list();
      setSavedFilters(res.data);
    } catch {}
  };

  const handleSemanticSearch = async () => {
    if (!semanticQuery.trim()) return;
    setIsSemantic(true);
    setLoading(true);
    try {
      const res = await searchAPI.semantic(semanticQuery);
      setCandidates(res.data);
      setTotal(res.data.length);
      setTotalPages(1);
    } catch (err) {
      toast.error('Semantic search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSort = (field: string) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleExport = async () => {
    try {
      const res = await candidatesAPI.export({ search, department });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'candidates_export.xlsx';
      a.click();
      toast.success('Export downloaded');
    } catch {
      toast.error('Export failed');
    }
  };

  const onDrop = async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      try {
        toast.loading(`Uploading ${file.name}...`, { id: file.name });
        await documentsAPI.uploadCV(file);
        toast.success(`${file.name} uploaded and parsed`, { id: file.name });
        loadCandidates();
      } catch {
        toast.error(`Failed to upload ${file.name}`, { id: file.name });
      }
    }
    setShowUpload(false);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'], 'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'] },
    maxFiles: 10,
  });

  const columns = [
    { key: 'full_name', label: 'Name', sortable: true },
    { key: 'email', label: 'Email', sortable: true },
    { key: 'phone', label: 'Phone', sortable: false },
    { key: 'city', label: 'City', sortable: true },
    { key: 'department_tag', label: 'Department', sortable: true },
    { key: 'career_level', label: 'Level', sortable: true },
    { key: 'source_channel', label: 'Source', sortable: true },
    { key: 'latest_score', label: 'Score', sortable: true },
    { key: 'confidence_flag', label: 'Confidence', sortable: true },
    { key: 'sync_status', label: 'Sync', sortable: true },
    { key: 'skill_names', label: 'Skills', sortable: false },
    { key: 'actions', label: '', sortable: false },
  ];

  const scoreBadge = (score: number | null) => {
    if (score === null) return <span className="text-slate-400">—</span>;
    const color = score >= 80 ? 'bg-green-100 text-green-800' :
                  score >= 60 ? 'bg-blue-100 text-blue-800' :
                  score >= 40 ? 'bg-amber-100 text-amber-800' :
                  'bg-red-100 text-red-800';
    return <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${color}`}>{score}</span>;
  };

  const confidenceBadge = (flag: string | null) => {
    if (!flag) return <span className="text-slate-400">—</span>;
    const color = flag === 'High' ? 'bg-green-100 text-green-700' :
                  flag === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700';
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>{flag}</span>;
  };

  const syncBadge = (status: string | null) => {
    if (!status) return <span className="text-slate-400">—</span>;
    const color = status === 'Synced' ? 'bg-green-100 text-green-700' :
                  status === 'Sync Failed' ? 'bg-red-100 text-red-700' :
                  'bg-slate-100 text-slate-600';
    return <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${color}`}>{status}</span>;
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex flex-wrap items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
              placeholder="Search candidates..."
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-sm"
            />
          </div>

          {/* Semantic Search */}
          <div className="relative flex-1 min-w-[200px] max-w-md">
            <input
              type="text"
              value={semanticQuery}
              onChange={(e) => setSemanticQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSemanticSearch()}
              placeholder="AI Search: e.g. Python devs in Dubai"
              className="w-full pl-4 pr-10 py-2 rounded-lg border border-violet-200 bg-violet-50/50 focus:ring-2 focus:ring-violet-500 focus:border-transparent outline-none text-sm"
            />
            <button
              onClick={handleSemanticSearch}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-violet-100"
            >
              <Search className="w-4 h-4 text-violet-500" />
            </button>
          </div>

          {/* Filters */}
          <button
            onClick={() => setShowFilter(!showFilter)}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border transition ${
              showFilter ? 'bg-blue-50 text-blue-700 border-blue-300' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <SlidersHorizontal className="w-4 h-4" />
            Filters
          </button>

          {/* Quick Filters */}
          <select
            value={department}
            onChange={(e) => { setDepartment(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="">All Departments</option>
            <option value="Engineering">Engineering</option>
            <option value="Marketing">Marketing</option>
            <option value="Sales">Sales</option>
            <option value="Finance">Finance</option>
            <option value="HR">HR</option>
            <option value="IT">IT</option>
            <option value="Operations">Operations</option>
          </select>

          <select
            value={careerLevel}
            onChange={(e) => { setCareerLevel(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="">All Levels</option>
            <option value="Entry">Entry</option>
            <option value="Mid">Mid</option>
            <option value="Senior">Senior</option>
            <option value="Lead">Lead</option>
            <option value="Managerial">Managerial</option>
          </select>

          <select
            value={source}
            onChange={(e) => { setSource(e.target.value); setPage(1); }}
            className="px-3 py-2 rounded-lg border border-slate-200 text-sm bg-white focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="">All Sources</option>
            <option value="LinkedIn">LinkedIn</option>
            <option value="Indeed">Indeed</option>
            <option value="Referral">Referral</option>
            <option value="Agency">Agency</option>
            <option value="Website">Website</option>
          </select>

          {/* Actions */}
          <div className="flex items-center gap-2 ml-auto">
            <button
              onClick={() => setShowUpload(true)}
              className="flex items-center gap-2 px-3 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
            >
              <Upload className="w-4 h-4" />
              Upload CV
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 text-slate-600 rounded-lg text-sm font-medium hover:bg-slate-50 transition"
            >
              <Download className="w-4 h-4" />
              Export
            </button>
            <button
              onClick={() => { setIsSemantic(false); loadCandidates(); }}
              className="p-2 rounded-lg hover:bg-slate-100 text-slate-500"
              title="Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Advanced Filter Builder */}
        {showFilter && (
          <div className="mt-4 pt-4 border-t border-slate-100">
            <FilterBuilder
              onApply={(config) => {
                // Apply filter via API
                filtersAPI.apply(config, { page, page_size: pageSize }).then((res) => {
                  setCandidates(res.data.items);
                  setTotal(res.data.total);
                  setTotalPages(res.data.total_pages);
                }).catch(() => toast.error('Filter failed'));
              }}
              savedFilters={savedFilters}
              onLoadSaved={async (filterId) => {
                const filter = savedFilters.find((f) => f.filter_id === filterId);
                if (filter) {
                  filtersAPI.apply(filter.filter_config, { page, page_size: pageSize }).then((res) => {
                    setCandidates(res.data.items);
                    setTotal(res.data.total);
                    setTotalPages(res.data.total_pages);
                  });
                }
              }}
            />
          </div>
        )}
      </div>

      {/* Data Table */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full data-table">
            <thead>
              <tr>
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={col.sortable ? 'cursor-pointer select-none' : ''}
                    onClick={() => col.sortable && handleSort(col.key)}
                  >
                    <div className="flex items-center gap-1">
                      {col.label}
                      {col.sortable && sortBy === col.key && (
                        sortOrder === 'desc' ? <ArrowDown className="w-3 h-3" /> : <ArrowUp className="w-3 h-3" />
                      )}
                      {col.sortable && sortBy !== col.key && <ArrowUpDown className="w-3 h-3 opacity-30" />}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {loading ? (
                [...Array(10)].map((_, i) => (
                  <tr key={i}>
                    {columns.map((col) => (
                      <td key={col.key}>
                        <div className="h-4 bg-slate-100 rounded animate-pulse" style={{ width: col.key === 'skill_names' ? '120px' : '80px' }}></div>
                      </td>
                    ))}
                  </tr>
                ))
              ) : candidates.length === 0 ? (
                <tr>
                  <td colSpan={columns.length} className="text-center py-12 text-slate-400">
                    <FileText className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    No candidates found
                  </td>
                </tr>
              ) : (
                candidates.map((c) => (
                  <tr
                    key={c.candidate_id}
                    className="cursor-pointer"
                    onClick={() => setSelectedCandidate(c.candidate_id)}
                  >
                    <td className="font-medium text-slate-900">{c.full_name}</td>
                    <td className="text-slate-500">{c.email || '—'}</td>
                    <td className="text-slate-500">{c.phone || '—'}</td>
                    <td>{c.city || '—'}</td>
                    <td>
                      {c.department_tag && (
                        <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs">{c.department_tag}</span>
                      )}
                    </td>
                    <td>
                      {c.career_level && (
                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                          c.career_level === 'Senior' || c.career_level === 'Lead' ? 'bg-blue-100 text-blue-700' :
                          c.career_level === 'Managerial' ? 'bg-purple-100 text-purple-700' :
                          'bg-slate-100 text-slate-700'
                        }`}>{c.career_level}</span>
                      )}
                    </td>
                    <td className="text-slate-500 text-xs">{c.source_channel || '—'}</td>
                    <td>{scoreBadge(c.latest_score)}</td>
                    <td>{confidenceBadge(c.confidence_flag)}</td>
                    <td>{syncBadge(c.sync_status)}</td>
                    <td>
                      <div className="flex flex-wrap gap-1 max-w-[200px]">
                        {c.skill_names?.slice(0, 3).map((s, i) => (
                          <span key={i} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-[10px]">{s}</span>
                        ))}
                        {(c.skill_names?.length || 0) > 3 && (
                          <span className="text-[10px] text-slate-400">+{c.skill_names.length - 3}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <button
                        onClick={(e) => { e.stopPropagation(); setSelectedCandidate(c.candidate_id); }}
                        className="p-1 rounded hover:bg-slate-100"
                      >
                        <Eye className="w-4 h-4 text-slate-400" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        <div className="px-4 py-3 border-t border-slate-100 flex items-center justify-between text-sm">
          <div className="text-slate-500">
            Showing {candidates.length} of {total} candidates
          </div>
          <div className="flex items-center gap-2">
            <select
              value={pageSize}
              onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}
              className="px-2 py-1 border border-slate-200 rounded text-xs"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-30"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="text-slate-600 text-xs">
              Page {page} of {totalPages || 1}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="p-1.5 rounded hover:bg-slate-100 disabled:opacity-30"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Upload Modal */}
      {showUpload && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl w-full max-w-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Upload CVs</h3>
              <button onClick={() => setShowUpload(false)} className="p-1 hover:bg-slate-100 rounded">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition ${
                isDragActive ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-blue-300'
              }`}
            >
              <input {...getInputProps()} />
              <Upload className="w-10 h-10 mx-auto mb-3 text-slate-400" />
              <p className="text-sm text-slate-600">
                Drag & drop CV files here, or click to select
              </p>
              <p className="text-xs text-slate-400 mt-1">PDF, DOCX supported. Max 10 files at once.</p>
            </div>
          </div>
        </div>
      )}

      {/* Candidate Detail Drawer */}
      {selectedCandidate && (
        <CandidateDetail
          candidateId={selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
        />
      )}
    </div>
  );
}
