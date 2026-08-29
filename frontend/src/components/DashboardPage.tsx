"use client";
import { useState, useEffect } from "react";
import { analyticsAPI, requisitionsAPI } from "@/lib/api";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Users, FileCheck, RefreshCw, Target, CheckCircle, Clock } from "lucide-react";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16"];

export default function DashboardPage() {
  const [dash, setDash] = useState<any>(null);
  const [analytics, setAnalytics] = useState<any>(null);
  const [reqs, setReqs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analyticsAPI.dashboard().then(r => setDash(r.data)),
      analyticsAPI.full().then(r => setAnalytics(r.data)),
      requisitionsAPI.list().then(r => setReqs(r.data)),
    ]).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="grid grid-cols-4 gap-4 animate-pulse">{[...Array(8)].map((_, i) => <div key={i} className="bg-white rounded-xl border h-32" />)}</div>;

  const sourceData = Object.entries(analytics?.candidates_by_source || {}).map(([name, value]) => ({ name, value }));
  const deptData = Object.entries(analytics?.candidates_by_department || {}).map(([name, value]) => ({ name, value }));
  const scoreDist = Object.entries(analytics?.score_distribution || {}).map(([name, value]) => ({ name, value }));
  const confData = Object.entries(analytics?.confidence_distribution || {}).map(([name, value]) => ({ name, value }));
  const locData = Object.entries(analytics?.candidates_by_location || {}).map(([name, value]) => ({ name, value }));
  const levelData = Object.entries(analytics?.candidates_by_career_level || {}).map(([name, value]) => ({ name, value }));

  const cards = [
    { label: "Total Candidates", value: dash?.total_candidates || 0, icon: Users, color: "bg-blue-50 text-blue-600" },
    { label: "Requisitions", value: dash?.total_requisitions || 0, icon: FileCheck, color: "bg-violet-50 text-violet-600" },
    { label: "Synced to ERP", value: dash?.synced_candidates || 0, icon: RefreshCw, color: "bg-green-50 text-green-600" },
    { label: "Pending Sync", value: dash?.pending_sync || 0, icon: Clock, color: "bg-amber-50 text-amber-600" },
    { label: "Avg Score", value: dash?.average_score || "N/A", icon: Target, color: "bg-cyan-50 text-cyan-600" },
    { label: "High Confidence", value: dash?.high_confidence_count || 0, icon: CheckCircle, color: "bg-emerald-50 text-emerald-600" },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {cards.map(c => (
          <div key={c.label} className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-sm transition">
            <div className="flex items-center gap-2 mb-2"><div className={"p-1.5 rounded-lg " + c.color}><c.icon className="w-4 h-4" /></div><span className="text-[10px] font-medium text-slate-500 uppercase">{c.label}</span></div>
            <div className="text-2xl font-bold text-slate-800">{c.value}</div>
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CC title="Candidates by Source"><ResponsiveContainer width="100%" height={250}><PieChart><Pie data={sourceData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>{sourceData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></CC>
        <CC title="Score Distribution"><ResponsiveContainer width="100%" height={250}><BarChart data={scoreDist}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" tick={{fontSize:11}} /><YAxis tick={{fontSize:11}} /><Tooltip /><Bar dataKey="value" fill="#3b82f6" radius={[4,4,0,0]} /></BarChart></ResponsiveContainer></CC>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CC title="By Department"><ResponsiveContainer width="100%" height={250}><BarChart data={deptData} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis type="number" tick={{fontSize:11}} /><YAxis dataKey="name" type="category" width={80} tick={{fontSize:11}} /><Tooltip /><Bar dataKey="value" fill="#10b981" radius={[0,4,4,0]} /></BarChart></ResponsiveContainer></CC>
        <CC title="By Location"><ResponsiveContainer width="100%" height={250}><BarChart data={locData}><CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" /><XAxis dataKey="name" tick={{fontSize:11}} /><YAxis tick={{fontSize:11}} /><Tooltip /><Bar dataKey="value" fill="#8b5cf6" radius={[4,4,0,0]} /></BarChart></ResponsiveContainer></CC>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <CC title="Career Level"><ResponsiveContainer width="100%" height={250}><PieChart><Pie data={levelData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>{levelData.map((_, i) => <Cell key={i} fill={COLORS[(i+2)%COLORS.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></CC>
        <CC title="AI Confidence"><ResponsiveContainer width="100%" height={250}><PieChart><Pie data={confData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>{confData.map((_, i) => <Cell key={i} fill={COLORS[(i+4)%COLORS.length]} />)}</Pie><Tooltip /></PieChart></ResponsiveContainer></CC>
      </div>
      {reqs.length > 0 && <div className="bg-white rounded-xl border p-6"><h3 className="text-sm font-semibold text-slate-700 mb-4">Open Requisitions</h3><div className="grid grid-cols-1 md:grid-cols-3 gap-3">{reqs.filter((r:any)=>r.status==="Open").slice(0,9).map((r:any)=>(<div key={r.requisition_id} className="p-3 bg-slate-50 rounded-lg border"><div className="font-medium text-sm">{r.designation}</div><div className="text-xs text-slate-500 mt-1">{r.department} | {r.location}</div>{r.required_skills?.length>0 && <div className="flex flex-wrap gap-1 mt-2">{r.required_skills.slice(0,3).map((s:string,i:number)=><span key={i} className="px-1.5 py-0.5 bg-blue-50 text-blue-700 rounded text-[10px]">{s}</span>)}</div>}</div>))}</div></div>}
    </div>
  );
}
function CC({title,children}:{title:string;children:React.ReactNode}){return <div className="bg-white rounded-xl border border-slate-200 p-5"><h3 className="text-sm font-semibold text-slate-700 mb-3">{title}</h3>{children}</div>;}
