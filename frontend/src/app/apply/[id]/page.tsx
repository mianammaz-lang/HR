"use client";
import { useState, useEffect } from "react";

export default function ApplyPage({ params }: { params: { id: string } }) {
  const [form, setForm] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [data, setData] = useState({ full_name: "", email: "", phone: "", linkedin_url: "", cover_letter: "" });
  const [resume, setResume] = useState<File | null>(null);

  useEffect(() => {
    fetch("/api/apply/" + params.id)
      .then(r => { if (!r.ok) throw new Error("Form not found"); return r.json(); })
      .then(d => { setForm(d); setLoading(false); })
      .catch(e => { setError(e.message); setLoading(false); });
  }, [params.id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const fd = new FormData();
      fd.append("full_name", data.full_name);
      fd.append("email", data.email);
      fd.append("phone", data.phone);
      fd.append("linkedin_url", data.linkedin_url);
      fd.append("cover_letter", data.cover_letter);
      if (resume) fd.append("resume", resume);
      const r = await fetch("/api/apply/" + params.id, {
        method: "POST",
        body: fd,
      });
      if (r.ok) { setSubmitted(true); } else { const d = await r.json(); setError(d.detail || "Submission failed"); }
    } catch { setError("Network error"); }
    setSubmitting(false);
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="text-slate-400">Loading...</div></div>;
  if (error && !form) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="text-center"><div className="text-4xl mb-4">&#128533;</div><div className="text-slate-600 text-lg">{error}</div></div></div>;
  if (submitted) return <div className="min-h-screen flex items-center justify-center bg-slate-50"><div className="text-center bg-white p-10 rounded-2xl shadow-lg max-w-md"><div className="text-5xl mb-4">&#9989;</div><h2 className="text-2xl font-bold text-slate-800 mb-2">Application Submitted!</h2><p className="text-slate-500">Thank you for applying. We will review your application and get back to you.</p></div></div>;

  const req = form.requisition;
  return (
    <div className="min-h-screen bg-slate-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="bg-gradient-to-r from-blue-600 to-blue-800 p-8 text-white">
            <div className="text-xs font-medium uppercase tracking-wider opacity-80 mb-2">Application Form</div>
            <h1 className="text-2xl font-bold mb-2">{req.designation}</h1>
            <div className="flex flex-wrap gap-2 mt-3 text-sm opacity-90">
              {req.department && <span className="bg-white/20 px-2 py-0.5 rounded">{req.department}</span>}
              {req.location && <span className="bg-white/20 px-2 py-0.5 rounded">{req.location}</span>}
              {req.employment_type && <span className="bg-white/20 px-2 py-0.5 rounded">{req.employment_type}</span>}
              {req.experience_years && <span className="bg-white/20 px-2 py-0.5 rounded">{req.experience_years}+ years</span>}
            </div>
          </div>
          {req.description && (<div className="p-6 border-b border-slate-100"><h3 className="text-sm font-semibold text-slate-700 mb-2">Job Description</h3><p className="text-sm text-slate-600 whitespace-pre-line">{req.description}</p></div>)}
          {req.required_skills?.length > 0 && (<div className="px-6 py-4 border-b border-slate-100"><h3 className="text-sm font-semibold text-slate-700 mb-2">Required Skills</h3><div className="flex flex-wrap gap-1.5">{req.required_skills.map((s: string, i: number) => <span key={i} className="px-2.5 py-1 bg-blue-50 text-blue-700 rounded-full text-xs font-medium">{s}</span>)}</div></div>)}
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <h3 className="text-sm font-semibold text-slate-700">Your Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Full Name *</label><input required value={data.full_name} onChange={e => setData({...data, full_name: e.target.value})} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="Your full name" /></div>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Email *</label><input required type="email" value={data.email} onChange={e => setData({...data, email: e.target.value})} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="your@email.com" /></div>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">Phone</label><input value={data.phone} onChange={e => setData({...data, phone: e.target.value})} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="+971 XX XXX XXXX" /></div>
              <div><label className="block text-xs font-medium text-slate-600 mb-1">LinkedIn</label><input value={data.linkedin_url} onChange={e => setData({...data, linkedin_url: e.target.value})} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none" placeholder="linkedin.com/in/you" /></div>
            </div>
            <div><label className="block text-xs font-medium text-slate-600 mb-1">Cover Letter / Resume Summary</label><textarea rows={5} value={data.cover_letter} onChange={e => setData({...data, cover_letter: e.target.value})} className="w-full px-3 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none resize-none" placeholder="Tell us about your experience and why you are a great fit..." /></div>
            <div><label className="block text-xs font-medium text-slate-600 mb-1">Resume / CV (PDF, DOCX, TXT)</label>
              <input type="file" accept=".pdf,.docx,.doc,.txt" onChange={e => setResume(e.target.files?.[0] || null)} className="w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100" />
              {resume && <p className="text-xs text-slate-500 mt-1">Selected: {resume.name}</p>}
            </div>
            <button type="submit" disabled={submitting} className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white font-medium py-3 rounded-lg transition">{submitting ? "Submitting..." : "Submit Application"}</button>
            {error && <div className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</div>}
          </form>
        </div>
        <div className="text-center text-xs text-slate-400 mt-4">Powered by Talent Pool Management System</div>
      </div>
    </div>
  );
}
