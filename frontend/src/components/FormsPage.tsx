"use client";
import { useState, useEffect } from "react";
import toast from "react-hot-toast";
import { ClipboardList, Copy, Clock, Users, Trash2 } from "lucide-react";

export default function FormsPage() {
  const [forms, setForms] = useState<any[]>([]);
  const [reqs, setReqs] = useState<any[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ requisition_id: "", title: "", description: "", expires_days: "7" });
  const [selectedForm, setSelectedForm] = useState<string | null>(null);
  const [subs, setSubs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadForms(); loadReqs(); }, []);
  const loadForms = async () => { try { const r = await fetch("/api/admin/forms", { headers: { Authorization: "Bearer " + localStorage.getItem("token") } }); setForms(await r.json()); } catch {} finally { setLoading(false); } };
  const loadReqs = async () => { try { const r = await fetch("/api/requisitions", { headers: { Authorization: "Bearer " + localStorage.getItem("token") } }); setReqs(await r.json()); } catch {} };
  const loadSubs = async (fid: string) => { setSelectedForm(fid); try { const r = await fetch("/api/admin/forms/" + fid + "/submissions", { headers: { Authorization: "Bearer " + localStorage.getItem("token") } }); setSubs(await r.json()); } catch {} };

  const createForm = async () => {
    const expires = new Date(Date.now() + parseInt(form.expires_days || "7") * 86400000).toISOString();
    try { const r = await fetch("/api/admin/forms", { method: "POST", headers: { "Content-Type": "application/json", Authorization: "Bearer " + localStorage.getItem("token") }, body: JSON.stringify({ requisition_id: form.requisition_id, title: form.title, description: form.description, expires_at: expires }) }); if (r.ok) { toast.success("Form created"); setShowCreate(false); loadForms(); } } catch { toast.error("Failed"); }
  };
  const deleteForm = async (fid: string) => { if (!confirm("Delete?")) return; await fetch("/api/admin/forms/" + fid, { method: "DELETE", headers: { Authorization: "Bearer " + localStorage.getItem("token") } }); toast.success("Deleted"); loadForms(); };
  const baseUrl = typeof window !== "undefined" ? window.location.origin : "";
  const copyLink = (fid: string) => { navigator.clipboard.writeText(baseUrl + "/apply/" + fid); toast.success("Link copied"); };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between"><h2 className="text-lg font-bold text-slate-800">Application Forms</h2>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700"><ClipboardList className="w-4 h-4" /> Create Form</button></div>

      {showCreate && (<div className="bg-white rounded-xl border p-6 space-y-4"><h3 className="font-semibold text-sm">New Application Form</h3>
        <select value={form.requisition_id} onChange={e => setForm({...form, requisition_id: e.target.value})} className="w-full px-3 py-2 border rounded-lg text-sm"><option value="">Select Requisition...</option>{reqs.map((r: any) => <option key={r.requisition_id} value={r.requisition_id}>{r.designation} - {r.department}</option>)}</select>
        <input placeholder="Form Title" value={form.title} onChange={e => setForm({...form, title: e.target.value})} className="w-full px-3 py-2 border rounded-lg text-sm" />
        <input placeholder="Description" value={form.description} onChange={e => setForm({...form, description: e.target.value})} className="w-full px-3 py-2 border rounded-lg text-sm" />
        <div className="flex items-center gap-3"><label className="text-sm text-slate-600">Available for:</label>
          <select value={form.expires_days} onChange={e => setForm({...form, expires_days: e.target.value})} className="px-3 py-2 border rounded-lg text-sm"><option value="1">1 Day</option><option value="3">3 Days</option><option value="7">7 Days</option><option value="14">14 Days</option><option value="30">30 Days</option><option value="90">90 Days</option></select></div>
        <div className="flex gap-2"><button onClick={createForm} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm">Create</button><button onClick={() => setShowCreate(false)} className="px-4 py-2 border rounded-lg text-sm">Cancel</button></div></div>)}

      <div className="bg-white rounded-xl border overflow-hidden"><table className="w-full text-sm"><thead><tr className="border-b bg-slate-50">
        <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500">Form</th>
        <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500">Requisition</th>
        <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500">Expires</th>
        <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500">Submissions</th>
        <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500">Actions</th></tr></thead>
        <tbody>{forms.map((f: any) => (<tr key={f.form_id} className="border-b hover:bg-slate-50">
          <td className="px-4 py-3 font-medium">{f.title}</td>
          <td className="px-4 py-3 text-slate-600">{f.requisition_title}</td>
          <td className="px-4 py-3"><span className="flex items-center gap-1 text-xs"><Clock className="w-3 h-3" />{f.expires_at ? new Date(f.expires_at).toLocaleDateString() : "Never"}</span></td>
          <td className="px-4 py-3"><button onClick={() => loadSubs(f.form_id)} className="flex items-center gap-1 text-xs text-blue-600 hover:underline"><Users className="w-3 h-3" />{f.submissions_count}</button></td>
          <td className="px-4 py-3"><div className="flex items-center gap-2"><button onClick={() => copyLink(f.form_id)} className="p-1 hover:bg-slate-100 rounded"><Copy className="w-4 h-4 text-slate-500" /></button><button onClick={() => deleteForm(f.form_id)} className="p-1 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4 text-red-400" /></button></div></td></tr>))}
          {forms.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-slate-400">No forms yet</td></tr>}</tbody></table></div>

      {selectedForm && (<div className="bg-white rounded-xl border p-6"><h3 className="font-semibold text-sm mb-3">Submissions</h3>
        <table className="w-full text-sm"><thead><tr className="border-b"><th className="text-left py-2 text-xs font-semibold text-slate-500">Name</th><th className="text-left py-2 text-xs font-semibold text-slate-500">Email</th><th className="text-left py-2 text-xs font-semibold text-slate-500">Phone</th><th className="text-left py-2 text-xs font-semibold text-slate-500">Date</th></tr></thead>
        <tbody>{subs.map((s: any) => (<tr key={s.submission_id} className="border-b"><td className="py-2 font-medium">{s.full_name}</td><td className="py-2 text-slate-600">{s.email}</td><td className="py-2 text-slate-600">{s.phone}</td><td className="py-2 text-xs text-slate-400">{new Date(s.submitted_at).toLocaleString()}</td></tr>))}
          {subs.length === 0 && <tr><td colSpan={4} className="py-4 text-center text-slate-400">No submissions</td></tr>}</tbody></table></div>)}
    </div>
  );
}
