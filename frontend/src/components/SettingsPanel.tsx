'use client';

import { useState, useEffect } from 'react';
import { settingsAPI, authAPI } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import toast from 'react-hot-toast';
import {
  Server, Cpu, Users, FileText, Database, RefreshCw,
  CheckCircle, XCircle, Save, Eye, EyeOff, Plus, Trash2, Edit, Webhook, Copy
} from 'lucide-react';

type SettingsTab = 'erpnext' | 'ai' | 'users' | 'logs' | 'webhook';

export default function SettingsPanel() {
  const [activeTab, setActiveTab] = useState<SettingsTab>('erpnext');

  const tabs = [
    { id: 'erpnext' as const, label: 'ERPNext', icon: Server },
    { id: 'ai' as const, label: 'AI / LLM', icon: Cpu },
    { id: 'webhook' as const, label: 'Webhook', icon: Webhook },
    { id: 'users' as const, label: 'Users', icon: Users },
    { id: 'logs' as const, label: 'Audit Logs', icon: FileText },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-slate-200 p-1 inline-flex gap-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
              activeTab === tab.id
                ? 'bg-blue-50 text-blue-700'
                : 'text-slate-500 hover:bg-slate-50'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'erpnext' && <ERPNextSettings />}
      {activeTab === 'ai' && <AISettings />}
      {activeTab === 'webhook' && <WebhookSettings />}
      {activeTab === 'users' && <UserManagement />}
      {activeTab === 'logs' && <AuditLogs />}
    </div>
  );
}

// ─── ERPNext Settings ─────────────────────────────────────────────────────────

function ERPNextSettings() {
  const [form, setForm] = useState({
    url: '', api_key: '', api_secret: '', default_company: '',
    default_job_applicant_doctype: 'Job Applicant', sync_threshold: 60,
  });
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const res = await settingsAPI.getERPNext();
      setForm(res.data);
    } catch {} finally { setLoading(false); }
  };

  const save = async () => {
    try {
      await settingsAPI.updateERPNext(form);
      toast.success('ERPNext settings saved');
    } catch { toast.error('Failed to save'); }
  };

  const testConnection = async () => {
    setTesting(true); setTestResult(null);
    try {
      const res = await settingsAPI.testERPNext();
      setTestResult(res.data);
      toast.success(res.data.message);
    } catch { toast.error('Connection test failed'); }
    finally { setTesting(false); }
  };

  if (loading) return <div className="bg-white rounded-xl border p-6 animate-pulse h-64" />;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 max-w-2xl">
      <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <Server className="w-5 h-5 text-blue-600" />
        ERPNext Integration
      </h3>
      <div className="space-y-4">
        <Field label="ERPNext URL" value={form.url} onChange={(v) => setForm({ ...form, url: v })} placeholder="https://your-erpnext.com" />
        <Field label="API Key" value={form.api_key} onChange={(v) => setForm({ ...form, api_key: v })} placeholder="ERPNext API Key" />
        <Field label="API Secret" value={form.api_secret} onChange={(v) => setForm({ ...form, api_secret: v })} placeholder="ERPNext API Secret" type="password" />
        <Field label="Default Company" value={form.default_company} onChange={(v) => setForm({ ...form, default_company: v })} />
        <Field label="Job Applicant Doctype" value={form.default_job_applicant_doctype} onChange={(v) => setForm({ ...form, default_job_applicant_doctype: v })} />
        <Field label="Sync Threshold (score >=)" value={String(form.sync_threshold)} onChange={(v) => setForm({ ...form, sync_threshold: Number(v) })} type="number" />
        <div className="flex items-center gap-3 pt-2">
          <button onClick={save} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
            <Save className="w-4 h-4" /> Save Settings
          </button>
          <button onClick={testConnection} disabled={testing} className="flex items-center gap-2 px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-50">
            {testing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <CheckCircle className="w-4 h-4" />}
            Test Connection
          </button>
        </div>
        {testResult && (
          <div className={`p-3 rounded-lg text-sm ${testResult.success ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
            {testResult.message}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── AI / LLM Settings ───────────────────────────────────────────────────────

function AISettings() {
  const [settings, setSettings] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [apiKey, setApiKey] = useState('');

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const res = await settingsAPI.getLLM();
      setSettings(res.data);
    } catch {} finally { setLoading(false); }
  };

  const save = async () => {
    try {
      const update: any = {};
      if (apiKey) update.api_key = apiKey;
      await settingsAPI.updateLLM(update);
      toast.success('AI settings saved');
      load();
    } catch { toast.error('Failed to save'); }
  };

  const updateSetting = async (key: string, value: any) => {
    try {
      await settingsAPI.updateLLM({ [key]: value });
      setSettings({ ...settings, [key]: value });
    } catch {}
  };

  if (loading || !settings) return <div className="bg-white rounded-xl border p-6 animate-pulse h-64" />;

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Cpu className="w-5 h-5 text-violet-600" />
          OpenRouter AI Configuration
        </h3>
        <div className="space-y-4">
          <Field label="OpenRouter API Key" value={apiKey} onChange={setApiKey} placeholder={settings.api_key_set ? '(key is set)' : 'Enter your OpenRouter API key'} type="password" />
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
            <div>
              <span className="text-sm font-medium text-slate-700">Auto Model Discovery</span>
              <p className="text-xs text-slate-500">Automatically fetch free models from OpenRouter</p>
            </div>
            <button onClick={() => updateSetting('auto_discovery', !settings.auto_discovery)} className={`relative w-11 h-6 rounded-full transition ${settings.auto_discovery ? 'bg-blue-600' : 'bg-slate-300'}`}>
              <div className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${settings.auto_discovery ? 'left-[22px]' : 'left-0.5'}`} />
            </button>
          </div>
          <Field label="Primary Model" value={settings.primary_model || ''} onChange={(v) => updateSetting('primary_model', v)} placeholder="e.g. mistralai/mistral-7b-instruct:free" />
          <Field label="Fallback Model" value={settings.fallback_model || ''} onChange={(v) => updateSetting('fallback_model', v)} placeholder="e.g. google/gemma-7b-it:free" />
          <Field label="Max Tokens" value={String(settings.max_tokens)} onChange={(v) => updateSetting('max_tokens', Number(v))} type="number" />
          <Field label="Temperature" value={String(settings.temperature)} onChange={(v) => updateSetting('temperature', Number(v))} type="number" />
          <button onClick={save} className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
            <Save className="w-4 h-4" /> Save Settings
          </button>
        </div>
      </div>
      {settings.available_models?.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Available Free Models ({settings.available_models.length})</h3>
          <div className="max-h-80 overflow-y-auto space-y-1">
            {settings.available_models.filter((m: any) => m.is_free).map((model: any) => (
              <div key={model.id} className="flex items-center justify-between p-2 rounded-lg hover:bg-slate-50 text-sm">
                <div>
                  <span className="font-medium text-slate-800">{model.name}</span>
                  <span className="text-xs text-slate-400 ml-2">({model.provider})</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-400">{model.context_length?.toLocaleString()} ctx</span>
                  <button onClick={() => updateSetting('primary_model', model.id)} className="px-2 py-0.5 text-[10px] bg-blue-50 text-blue-700 rounded hover:bg-blue-100">Set Primary</button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Webhook Settings ─────────────────────────────────────────────────────────

function WebhookSettings() {
  const [webhookKey, setWebhookKey] = useState('');
  const [saved, setSaved] = useState(false);
  const { user } = useAuthStore();

  const baseUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:8000';
  const apiBase = process.env.NEXT_PUBLIC_API_URL || baseUrl;

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const saveKey = async () => {
    if (!webhookKey.trim()) { toast.error('Enter a webhook key'); return; }
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${apiBase}/api/webhook/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-API-Key': token || '' },
        body: JSON.stringify({ api_key: webhookKey }),
      });
      if (res.ok) {
        toast.success('Webhook key saved');
        setSaved(true);
      } else {
        toast.error('Failed to save');
      }
    } catch { toast.error('Failed to save'); }
  };

  const curlFileExample = `curl -X POST ${apiBase}/api/webhook/cv \\
  -H "X-API-Key: YOUR_KEY" \\
  -F "file=@candidate.pdf" \\
  -F "source=linkedin" \\
  -F "department=Engineering"`;

  const curlJsonExample = `curl -X POST ${apiBase}/api/webhook/cv \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "Full CV text here...",
    "filename": "cv.pdf",
    "source": "linkedin",
    "department": "Engineering",
    "format": "text"
  }'`;

  const curlBase64Example = `curl -X POST ${apiBase}/api/webhook/cv \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "content": "<base64-encoded-file>",
    "filename": "cv.pdf",
    "source": "email",
    "format": "base64"
  }'`;

  const curlBatchExample = `curl -X POST ${apiBase}/api/webhook/cv/batch \\
  -H "X-API-Key: YOUR_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "cvs": [
      {"content": "CV 1 text...", "filename": "cv1.pdf", "source": "linkedin"},
      {"content": "CV 2 text...", "filename": "cv2.pdf", "source": "referral"}
    ]
  }'`;

  return (
    <div className="space-y-6 max-w-4xl">
      {/* API Key Config */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
          <Webhook className="w-5 h-5 text-emerald-600" />
          Webhook Configuration
        </h3>
        <p className="text-sm text-slate-500 mb-4">
          Set a secret API key to authenticate webhook requests. External systems will use this key to push CVs into your talent pool.
        </p>
        <div className="flex items-end gap-3">
          <div className="flex-1 max-w-md">
            <Field label="Webhook API Key" value={webhookKey} onChange={setWebhookKey} placeholder="Enter a secret key (e.g. tpms-webhook-abc123)" type="password" />
          </div>
          <button onClick={saveKey} className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700">
            <Save className="w-4 h-4" /> Save Key
          </button>
        </div>
        {saved && (
          <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700">
            Webhook key saved. Use it in the X-API-Key header.
          </div>
        )}
      </div>

      {/* Endpoints */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Webhook Endpoints</h3>
        <div className="space-y-3">
          <EndpointRow method="POST" path="/api/webhook/cv" desc="Push a single CV (file or JSON)" />
          <EndpointRow method="POST" path="/api/webhook/cv/batch" desc="Push multiple CVs at once (max 50)" />
          <EndpointRow method="GET" path="/api/webhook/status" desc="Health check (requires API key)" />
          <EndpointRow method="POST" path="/api/webhook/config" desc="Update webhook API key (admin only)" />
        </div>
      </div>

      {/* Code Examples */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Integration Examples</h3>

        <CodeBlock title="File Upload (multipart)" code={curlFileExample} />
        <CodeBlock title="JSON with raw text" code={curlJsonExample} />
        <CodeBlock title="JSON with base64" code={curlBase64Example} />
        <CodeBlock title="Batch upload" code={curlBatchExample} />
      </div>

      {/* Python Example */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Python Integration Example</h3>
        <CodeBlock title="Using requests library" code={`import requests

API_URL = "${apiBase}/api/webhook/cv"
API_KEY = "your-webhook-key"

# Push a CV file
with open("candidate.pdf", "rb") as f:
    response = requests.post(
        API_URL,
        headers={"X-API-Key": API_KEY},
        files={"file": f},
        data={"source": "linkedin", "department": "Engineering"}
    )

print(response.json())
# {"status": "ok", "candidate_id": "...", "full_name": "...", ...}`} />
      </div>
    </div>
  );
}

function EndpointRow({ method, path, desc }: { method: string; path: string; desc: string }) {
  const methodColor: Record<string, string> = {
    GET: 'bg-blue-100 text-blue-700',
    POST: 'bg-green-100 text-green-700',
    PUT: 'bg-amber-100 text-amber-700',
    DELETE: 'bg-red-100 text-red-700',
  };
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className={`px-2 py-0.5 rounded text-xs font-bold ${methodColor[method] || 'bg-slate-100 text-slate-700'}`}>{method}</span>
      <code className="text-slate-700 font-mono text-xs">{path}</code>
      <span className="text-slate-400">-</span>
      <span className="text-slate-500 text-xs">{desc}</span>
    </div>
  );
}

function CodeBlock({ title, code }: { title: string; code: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mb-3 border border-slate-100 rounded-lg overflow-hidden">
      <button onClick={() => setOpen(!open)} className="w-full flex items-center justify-between px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-50">
        <span>{title}</span>
        <span className="text-slate-400">{open ? 'Hide' : 'Show'}</span>
      </button>
      {open && (
        <div className="relative bg-slate-900 text-slate-200 p-4 text-xs font-mono overflow-x-auto">
          <pre>{code}</pre>
          <button onClick={() => { navigator.clipboard.writeText(code); toast.success('Copied'); }} className="absolute top-2 right-2 p-1.5 bg-slate-700 rounded hover:bg-slate-600">
            <Copy className="w-3 h-3" />
          </button>
        </div>
      )}
    </div>
  );
}

// ─── User Management ──────────────────────────────────────────────────────────

function UserManagement() {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ email: '', full_name: '', password: '', role: 'Viewer', team: '' });

  useEffect(() => { load(); }, []);

  const load = async () => {
    try {
      const res = await authAPI.getUsers();
      setUsers(res.data);
    } catch {} finally { setLoading(false); }
  };

  const createUser = async () => {
    try {
      await authAPI.createUser(form);
      toast.success('User created');
      setShowCreate(false);
      setForm({ email: '', full_name: '', password: '', role: 'Viewer', team: '' });
      load();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed');
    }
  };

  const toggleActive = async (userId: string, isActive: boolean) => {
    try {
      await authAPI.updateUser(userId, { is_active: !isActive });
      load();
    } catch { toast.error('Failed'); }
  };

  if (loading) return <div className="bg-white rounded-xl border p-6 animate-pulse h-64" />;

  const roles = ['Super Admin', 'HR Admin', 'Recruiter', 'Technical Team', 'Requester', 'Viewer'];

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 max-w-3xl">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Users className="w-5 h-5 text-green-600" /> User Management
        </h3>
        <button onClick={() => setShowCreate(!showCreate)} className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700">
          <Plus className="w-4 h-4" /> Add User
        </button>
      </div>
      {showCreate && (
        <div className="bg-slate-50 rounded-lg p-4 mb-4 space-y-3 border border-slate-200">
          <div className="grid grid-cols-2 gap-3">
            <Field label="Email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} placeholder="user@example.com" />
            <Field label="Full Name" value={form.full_name} onChange={(v) => setForm({ ...form, full_name: v })} placeholder="John Doe" />
            <Field label="Password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} type="password" />
            <div>
              <label className="block text-xs font-medium text-slate-600 mb-1">Role</label>
              <select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm">
                {roles.map((r) => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
            <Field label="Team" value={form.team} onChange={(v) => setForm({ ...form, team: v })} placeholder="Optional team name" />
          </div>
          <div className="flex gap-2">
            <button onClick={createUser} className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700">Create User</button>
            <button onClick={() => setShowCreate(false)} className="px-4 py-2 border border-slate-200 rounded-lg text-sm hover:bg-slate-50">Cancel</button>
          </div>
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-2 text-xs font-semibold text-slate-500 uppercase">User</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500 uppercase">Role</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500 uppercase">Team</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500 uppercase">Status</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.user_id} className="border-b border-slate-100">
                <td className="py-3">
                  <div className="font-medium text-slate-800">{u.full_name}</div>
                  <div className="text-xs text-slate-500">{u.email}</div>
                </td>
                <td className="py-3"><span className="px-2 py-0.5 bg-blue-50 text-blue-700 rounded text-xs font-medium">{u.role}</span></td>
                <td className="py-3 text-slate-600">{u.team || '---'}</td>
                <td className="py-3">
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {u.is_active ? 'Active' : 'Disabled'}
                  </span>
                </td>
                <td className="py-3">
                  <button onClick={() => toggleActive(u.user_id, u.is_active)} className="text-xs text-slate-500 hover:text-slate-700">
                    {u.is_active ? 'Disable' : 'Enable'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ─── Audit Logs ───────────────────────────────────────────────────────────────

function AuditLogs() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => { load(); }, [page]);

  const load = async () => {
    try {
      const res = await settingsAPI.getAuditLogs({ page, page_size: 30 });
      setLogs(res.data.items);
      setTotal(res.data.total);
    } catch {} finally { setLoading(false); }
  };

  if (loading) return <div className="bg-white rounded-xl border p-6 animate-pulse h-64" />;

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 max-w-4xl">
      <h3 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
        <FileText className="w-5 h-5 text-amber-600" /> Audit Logs
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-200">
              <th className="text-left py-2 text-xs font-semibold text-slate-500">Action</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500">Entity</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500">Details</th>
              <th className="text-left py-2 text-xs font-semibold text-slate-500">Time</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log) => (
              <tr key={log.log_id} className="border-b border-slate-50">
                <td className="py-2">
                  <span className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded text-xs font-medium">{log.action}</span>
                </td>
                <td className="py-2 text-slate-600">{log.entity_type} -- {log.entity_id?.slice(0, 8)}</td>
                <td className="py-2 text-xs text-slate-500 max-w-xs truncate">
                  {JSON.stringify(log.details || {}).slice(0, 80)}
                </td>
                <td className="py-2 text-xs text-slate-400">
                  {new Date(log.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100 text-sm">
        <span className="text-slate-500">Total: {total} entries</span>
        <div className="flex gap-2">
          <button disabled={page <= 1} onClick={() => setPage(page - 1)} className="px-3 py-1 border rounded text-xs disabled:opacity-30">Prev</button>
          <button disabled={logs.length < 30} onClick={() => setPage(page + 1)} className="px-3 py-1 border rounded text-xs disabled:opacity-30">Next</button>
        </div>
      </div>
    </div>
  );
}

// ─── Shared Field Component ───────────────────────────────────────────────────

function Field({ label, value, onChange, placeholder, type = 'text' }: {
  label: string; value: string; onChange: (v: string) => void; placeholder?: string; type?: string;
}) {
  const [showPw, setShowPw] = useState(false);
  const isPassword = type === 'password';
  return (
    <div>
      <label className="block text-xs font-medium text-slate-600 mb-1">{label}</label>
      <div className="relative">
        <input
          type={isPassword && !showPw ? 'password' : type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className="w-full px-3 py-2 rounded-lg border border-slate-200 text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
        />
        {isPassword && (
          <button onClick={() => setShowPw(!showPw)} className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-slate-400 hover:text-slate-600">
            {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        )}
      </div>
    </div>
  );
}
