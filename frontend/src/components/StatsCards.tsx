'use client';

import { useState, useEffect } from 'react';
import { analyticsAPI } from '@/lib/api';
import { Users, FileCheck, RefreshCw, Target, TrendingUp, CheckCircle } from 'lucide-react';

export default function StatsCards() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const res = await analyticsAPI.dashboard();
      setStats(res.data);
    } catch (err) {
      console.error('Failed to load stats');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-white rounded-xl border border-slate-200 p-5 animate-pulse">
            <div className="h-4 bg-slate-100 rounded w-24 mb-3"></div>
            <div className="h-8 bg-slate-100 rounded w-16"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      label: 'Total Candidates',
      value: stats?.total_candidates || 0,
      icon: Users,
      color: 'blue',
    },
    {
      label: 'Open Requisitions',
      value: stats?.total_requisitions || 0,
      icon: FileCheck,
      color: 'violet',
    },
    {
      label: 'Synced to ERP',
      value: stats?.synced_candidates || 0,
      icon: RefreshCw,
      color: 'green',
    },
    {
      label: 'Avg. Score',
      value: stats?.average_score ? `${stats.average_score}` : 'N/A',
      icon: Target,
      color: 'amber',
    },
    {
      label: 'High Confidence',
      value: stats?.high_confidence_count || 0,
      icon: CheckCircle,
      color: 'emerald',
    },
  ];

  const colorMap: Record<string, { bg: string; icon: string; text: string }> = {
    blue: { bg: 'bg-blue-50', icon: 'text-blue-600', text: 'text-blue-600' },
    violet: { bg: 'bg-violet-50', icon: 'text-violet-600', text: 'text-violet-600' },
    green: { bg: 'bg-green-50', icon: 'text-green-600', text: 'text-green-600' },
    amber: { bg: 'bg-amber-50', icon: 'text-amber-600', text: 'text-amber-600' },
    emerald: { bg: 'bg-emerald-50', icon: 'text-emerald-600', text: 'text-emerald-600' },
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {cards.map((card) => {
        const colors = colorMap[card.color];
        return (
          <div
            key={card.label}
            className="bg-white rounded-xl border border-slate-200 p-5 hover:shadow-sm transition"
          >
            <div className="flex items-center gap-3 mb-3">
              <div className={`p-2 rounded-lg ${colors.bg}`}>
                <card.icon className={`w-5 h-5 ${colors.icon}`} />
              </div>
              <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">{card.label}</span>
            </div>
            <div className="text-2xl font-bold text-slate-800">{card.value}</div>
          </div>
        );
      })}
    </div>
  );
}
