'use client';

import { useState, useEffect } from 'react';
import { useAuthStore, useAppStore } from '@/lib/store';
import { useRouter } from 'next/navigation';
import {
  Database, Settings, Users, Search, LogOut, Menu, X,
  BarChart3, FileText, Upload, ChevronDown, Bell, ClipboardList
} from 'lucide-react';
import DashboardPage from "@/components/DashboardPage";
import FormsPage from "@/components/FormsPage";
import DatabaseView from './DatabaseView';
import SettingsPanel from './SettingsPanel';
import StatsCards from './StatsCards';

export default function Dashboard() {
  const { user, logout } = useAuthStore();
  const { activeView, setActiveView, sidebarOpen, toggleSidebar } = useAppStore();
  const router = useRouter();
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const navItems = [
    { id: 'dashboard' as const, label: 'Dashboard', icon: BarChart3 },
    { id: 'database' as const, label: 'Database', icon: Database },
    { id: 'forms' as const, label: 'Forms', icon: ClipboardList },
    { id: 'settings' as const, label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-16'
        } bg-white border-r border-slate-200 transition-all duration-300 flex flex-col fixed h-full z-30`}
      >
        {/* Logo */}
        <div className="p-4 border-b border-slate-100 flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <Users className="w-5 h-5 text-white" />
          </div>
          {sidebarOpen && (
            <div>
              <div className="font-bold text-sm text-slate-800">Talent Pool</div>
              <div className="text-[10px] text-slate-400">Management System</div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveView(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                activeView === item.id
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:bg-slate-50'
              }`}
            >
              <item.icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        {/* User section */}
        <div className="p-3 border-t border-slate-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-slate-500 hover:bg-red-50 hover:text-red-600 transition"
          >
            <LogOut className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className={`flex-1 ${sidebarOpen ? 'ml-64' : 'ml-16'} transition-all duration-300`}>
        {/* Top Bar */}
        <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between sticky top-0 z-20">
          <div className="flex items-center gap-4">
            <button
              onClick={toggleSidebar}
              className="p-2 rounded-lg hover:bg-slate-100 text-slate-500 transition"
            >
              {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <h1 className="text-lg font-semibold text-slate-800">
              {{ dashboard: 'Dashboard', database: 'Candidate Database', forms: 'Application Forms', settings: 'Settings' }[activeView as string] || 'Settings'}
            </h1>
          </div>

          <div className="flex items-center gap-4">
            <div className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded">
              {user?.role}
            </div>
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-50 transition"
              >
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-blue-700 font-medium text-sm">
                  {user?.full_name?.charAt(0) || 'U'}
                </div>
                <span className="text-sm font-medium text-slate-700">{user?.full_name}</span>
                <ChevronDown className="w-4 h-4 text-slate-400" />
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50">
                  <div className="px-4 py-2 text-xs text-slate-500 border-b border-slate-100">
                    {user?.email}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                  >
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Content */}
        <div className="p-6">
          {(() => { switch(activeView) {
            case 'dashboard': return <DashboardPage />;
            case 'database': return <DatabaseView />;
            case 'forms': return <FormsPage />;
            default: return <SettingsPanel />;
          } })()}
        </div>
      </main>
    </div>
  );
}
