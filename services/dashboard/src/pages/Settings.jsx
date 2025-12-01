import React from 'react';
import { useStore } from '../store';
import { useTheme } from '../hooks/useTheme';
import toast from 'react-hot-toast';

const Settings = () => {
  const { demoMode, setDemoMode, refreshData } = useStore();
  const { theme, setTheme } = useTheme();

  const handleDemoModeToggle = () => {
    setDemoMode(!demoMode);
    refreshData();
    toast.success(`Demo mode ${!demoMode ? 'enabled' : 'disabled'}`);
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>
      <div className="card space-y-6">
        <div>
          <h3 className="text-lg font-semibold mb-4">Appearance</h3>
          <div className="space-y-3">
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="radio" name="theme" checked={theme === 'light'} onChange={() => setTheme('light')} className="w-4 h-4" />
              <span>Light Mode</span>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input type="radio" name="theme" checked={theme === 'dark'} onChange={() => setTheme('dark')} className="w-4 h-4" />
              <span>Dark Mode</span>
            </label>
          </div>
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-4">Data Source</h3>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" checked={demoMode} onChange={handleDemoModeToggle} className="w-4 h-4" />
            <span>Use Demo Data</span>
          </label>
          <p className="text-sm text-gray-500 mt-2">When enabled, the dashboard displays sample data instead of connecting to the API.</p>
        </div>
        <div>
          <h3 className="text-lg font-semibold mb-4">API Configuration</h3>
          <div className="space-y-3">
            <div>
              <label className="block text-sm font-medium mb-1">API URL</label>
              <input type="text" defaultValue="http://localhost:8000" className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800" />
            </div>
            <button className="btn-primary">Save Changes</button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
