'use client';

import { useState, useEffect } from 'react';
import { candidatesAPI, scoringAPI } from '@/lib/api';
import { X, Mail, Phone, MapPin, Linkedin, Award, Briefcase, RefreshCw, FileText, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

interface Props {
  candidateId: string;
  onClose: () => void;
}

export default function CandidateDetail({ candidateId, onClose }: Props) {
  const [candidate, setCandidate] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scoring, setScoring] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'documents' | 'scores' | 'history'>('overview');

  useEffect(() => {
    loadCandidate();
  }, [candidateId]);


  const sendToERP = async () => {
    try {
      const token = localStorage.getItem("token");
      const r = await fetch("/api/admin/sync-erp", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Authorization": "Bearer " + token },
        body: JSON.stringify({ candidate_ids: [candidateId] }),
      });
      const d = await r.json();
      if (d.results?.[0]?.status === "synced") {
        toast.success("Sent to ERPNext!");
        loadCandidate();
      } else {
        toast.error(d.results?.[0]?.error || "Sync failed");
      }
    } catch { toast.error("Sync failed"); }
  };
  const loadCandidate = async () => {
    try {
      const res = await candidatesAPI.get(candidateId);
      setCandidate(res.data);
    } catch {
      toast.error('Failed to load candidate');
    } finally {
      setLoading(false);
    }
  };

  const handleScore = async (requisitionId: string) => {
    setScoring(true);
    try {
      await scoringAPI.score({ candidate_id: candidateId, requisition_id: requisitionId });
      toast.success('Score generated');
      loadCandidate();
    } catch {
      toast.error('Scoring failed');
    } finally {
      setScoring(false);
    }
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black/50 flex justify-end z-50">
        <div className="w-full max-w-xl bg-white h-full animate-pulse p-6">
          <div className="h-6 bg-slate-100 rounded w-48 mb-4"></div>
          <div className="h-4 bg-slate-100 rounded w-32 mb-2"></div>
          <div className="h-4 bg-slate-100 rounded w-40"></div>
        </div>
      </div>
    );
  }

  if (!candidate) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex justify-end z-50" onClick={onClose}>
      <div
        className="w-full max-w-2xl bg-white h-full overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 p-4 flex items-center justify-between z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-800">{candidate.full_name}</h2>
            <p className="text-xs text-slate-500">{candidate.applied_designation || candidate.department_tag || 'No designation'}</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={sendToERP}
              className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-xs font-medium rounded-lg transition flex items-center gap-1.5"
            >
              <Zap className="w-3.5 h-3.5" /> Send to ERP
            </button>
            <button onClick={onClose} className="p-2 hover:bg-slate-100 rounded-lg">
              <X className="w-5 h-5 text-slate-500" />
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="border-b border-slate-100 px-4 flex gap-4">
          {(['overview', 'documents', 'scores', 'history'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 text-sm font-medium capitalize border-b-2 transition ${
                activeTab === tab
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>

        <div className="p-4 space-y-4">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
              {/* Contact */}
              <div className="bg-slate-50 rounded-lg p-4 space-y-2">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Contact</h3>
                {candidate.email && (
                  <div className="flex items-center gap-2 text-sm text-slate-700">
                    <Mail className="w-4 h-4 text-slate-400" /> {candidate.email}
                  </div>
                )}
                {candidate.phone && (
                  <div className="flex items-center gap-2 text-sm text-slate-700">
                    <Phone className="w-4 h-4 text-slate-400" /> {candidate.phone}
                  </div>
                )}
                {candidate.city && (
                  <div className="flex items-center gap-2 text-sm text-slate-700">
                    <MapPin className="w-4 h-4 text-slate-400" /> {candidate.city}
                  </div>
                )}
                {candidate.linkedin_url && (
                  <div className="flex items-center gap-2 text-sm text-blue-600">
                    <Linkedin className="w-4 h-4" />
                    <a href={candidate.linkedin_url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                      LinkedIn Profile
                    </a>
                  </div>
                )}
              </div>

              {/* Details */}
              <div className="bg-slate-50 rounded-lg p-4">
                <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Details</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-slate-500">Source:</span>
                    <span className="ml-2 text-slate-700">{candidate.source_channel || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Career Level:</span>
                    <span className="ml-2 text-slate-700">{candidate.career_level || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Employment Type:</span>
                    <span className="ml-2 text-slate-700">{candidate.employment_type || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Department:</span>
                    <span className="ml-2 text-slate-700">{candidate.department_tag || '—'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500">Date Received:</span>
                    <span className="ml-2 text-slate-700">
                      {candidate.date_received ? new Date(candidate.date_received).toLocaleDateString() : '—'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Skills */}
              {candidate.skills?.length > 0 && (
                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Skills</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.skills.map((s: any) => (
                      <span
                        key={s.skill_id}
                        className={`px-2 py-0.5 rounded text-xs font-medium ${
                          s.jd_keyword_match ? 'bg-green-100 text-green-700' : 'bg-blue-50 text-blue-700'
                        }`}
                      >
                        {s.skill_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Tags */}
              {candidate.tags?.length > 0 && (
                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Tags</h3>
                  <div className="flex flex-wrap gap-1.5">
                    {candidate.tags.map((t: string, i: number) => (
                      <span key={i} className="px-2 py-0.5 bg-slate-200 text-slate-700 rounded text-xs">{t}</span>
                    ))}
                  </div>
                </div>
              )}

              {/* Notes */}
              {candidate.notes_internal && (
                <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                  <h3 className="text-xs font-semibold text-amber-700 uppercase tracking-wider mb-2">Internal Notes</h3>
                  <p className="text-sm text-amber-900">{candidate.notes_internal}</p>
                </div>
              )}

              {/* Sync Status */}
              {candidate.sync_status && (
                <div className="bg-slate-50 rounded-lg p-4">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">ERPNext Sync</h3>
                  <div className="space-y-1 text-sm">
                    <div>
                      Status:
                      <span className={`ml-2 font-medium ${
                        candidate.sync_status.sync_status === 'Synced' ? 'text-green-600' :
                        candidate.sync_status.sync_status === 'Sync Failed' ? 'text-red-600' :
                        'text-slate-600'
                      }`}>
                        {candidate.sync_status.sync_status}
                      </span>
                    </div>
                    {candidate.sync_status.erpnext_applicant_id && (
                      <div>ERPNext ID: <span className="text-slate-700">{candidate.sync_status.erpnext_applicant_id}</span></div>
                    )}
                    {candidate.sync_status.sync_error_log && (
                      <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700">{candidate.sync_status.sync_error_log}</div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Scores Tab */}
          {activeTab === 'scores' && (
            <>
              {candidate.scores?.length > 0 ? (
                candidate.scores.map((score: any) => (
                  <div key={score.score_id} className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <span className="text-2xl font-bold text-slate-800">{score.ranking_score}</span>
                        <span className="text-sm text-slate-500 ml-1">/ 100</span>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        score.confidence_flag === 'High' ? 'bg-green-100 text-green-700' :
                        score.confidence_flag === 'Medium' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {score.confidence_flag} Confidence
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(score.score_breakdown_json || {}).map(([key, val]) => (
                        key !== 'reasoning' && (
                          <div key={key} className="flex items-center justify-between">
                            <span className="text-slate-500 capitalize">{key.replace(/_/g, ' ')}</span>
                            <span className="font-medium text-slate-700">{String(val)}</span>
                          </div>
                        )
                      ))}
                    </div>
                    {score.score_breakdown_json?.reasoning && (
                      <div className="mt-3 p-2 bg-white rounded text-xs text-slate-600 border border-slate-100">
                        {score.score_breakdown_json.reasoning}
                      </div>
                    )}
                    <div className="mt-2 text-[10px] text-slate-400">
                      Model: {score.score_model_version} • {new Date(score.score_generated_at).toLocaleString()}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <Award className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No scores yet</p>
                </div>
              )}
            </>
          )}

          {/* Documents Tab */}
          {activeTab === 'documents' && (
            <>
              {candidate.documents?.length > 0 ? (
                candidate.documents.map((doc: any) => (
                  <div key={doc.doc_id} className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-50 rounded-lg">
                          <FileText className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <div className="font-medium text-slate-800 text-sm">{doc.original_filename || 'Resume'}</div>
                          <div className="text-xs text-slate-400">
                            {doc.file_size ? Math.round(doc.file_size / 1024) + ' KB' : ''}
                            {doc.uploaded_at ? ' • Uploaded ' + new Date(doc.uploaded_at).toLocaleDateString() : ''}
                            {doc.resume_version ? ' • v' + doc.resume_version : ''}
                          </div>
                        </div>
                      </div>
                      <a
                        href={"/api/apply/resume/" + doc.doc_id}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-medium rounded-lg transition"
                      >
                        View Resume
                      </a>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <FileText className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No resume uploaded</p>
                  <p className="text-xs mt-1">Upload a CV from the Database view</p>
                </div>
              )}

              {/* ERPNext Sync Status */}
              {candidate.sync_status && (
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                  <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">ERPNext Sync</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-600">Status:</span>
                      <span className={`font-medium ${candidate.sync_status.sync_status === 'Synced' ? 'text-green-600' : candidate.sync_status.sync_status === 'Sync Failed' ? 'text-red-600' : 'text-slate-600'}`}>
                        {candidate.sync_status.sync_status}
                      </span>
                    </div>
                    {candidate.sync_status.erpnext_applicant_id && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600">ERPNext ID:</span>
                        <span className="text-slate-700 font-mono text-xs">{candidate.sync_status.erpnext_applicant_id}</span>
                      </div>
                    )}
                    {candidate.sync_status.synced_at && (
                      <div className="flex items-center justify-between">
                        <span className="text-slate-600">Synced At:</span>
                        <span className="text-slate-700">{new Date(candidate.sync_status.synced_at).toLocaleString()}</span>
                      </div>
                    )}
                    {candidate.sync_status.sync_error_log && (
                      <div className="mt-2 p-2 bg-red-50 rounded text-xs text-red-700 font-mono">{candidate.sync_status.sync_error_log}</div>
                    )}
                  </div>
                  {candidate.sync_status.sync_status !== 'Synced' && (
                    <button
                      onClick={sendToERP}
                      className="mt-3 w-full px-3 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition flex items-center justify-center gap-2"
                    >
                      <Zap className="w-4 h-4" /> Send to ERPNext
                    </button>
                  )}
                </div>
              )}
            </>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <>
              {candidate.employment_history?.length > 0 ? (
                candidate.employment_history.map((h: any) => (
                  <div key={h.employment_history_id} className="bg-slate-50 rounded-lg p-4 border border-slate-100">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-blue-50 rounded-lg">
                        <Briefcase className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="font-medium text-slate-800">{h.title || 'Untitled'}</div>
                        <div className="text-sm text-slate-600">{h.company || 'Unknown Company'}</div>
                        <div className="text-xs text-slate-400 mt-0.5">{h.duration || 'Duration not specified'}</div>
                        {h.description && (
                          <p className="text-xs text-slate-500 mt-2">{h.description}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-400">
                  <Briefcase className="w-10 h-10 mx-auto mb-3 opacity-30" />
                  <p>No employment history</p>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
