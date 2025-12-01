import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { FiHome, FiServer, FiPackage, FiTrendingUp, FiDollarSign, FiSettings, FiMoon, FiSun } from 'react-icons/fi';
import { useTheme } from './hooks/useTheme';
import { useStore } from './store';
import Dashboard from './pages/Dashboard';
import Clusters from './pages/Clusters';
import Workloads from './pages/Workloads';
import Recommendations from './pages/Recommendations';
import Savings from './pages/Savings';
import Settings from './pages/Settings';

const Navigation = () => {
  const { theme, toggleTheme } = useTheme();
  const location = useLocation();

  const links = [
    { to: '/', icon: FiHome, label: 'Dashboard' },
    { to: '/clusters', icon: FiServer, label: 'Clusters' },
    { to: '/workloads', icon: FiPackage, label: 'Workloads' },
    { to: '/recommendations', icon: FiTrendingUp, label: 'Recommendations' },
    { to: '/savings', icon: FiDollarSign, label: 'Savings' },
    { to: '/settings', icon: FiSettings, label: 'Settings' },
  ];

  return (
    <nav className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex space-x-8">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-primary-600">K8s Cost Optimizer</h1>
            </div>
            {links.map(({ to, icon: Icon, label }) => {
              const isActive = location.pathname === to;
              return (
                <Link key={to} to={to} className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors ${isActive ? 'border-primary-600 text-gray-900 dark:text-white' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-300 dark:hover:text-gray-100'}`}>
                  <Icon className="w-4 h-4 mr-2" />
                  {label}
                </Link>
              );
            })}
          </div>
          <div className="flex items-center">
            <button onClick={toggleTheme} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
              {theme === 'dark' ? <FiSun className="w-5 h-5" /> : <FiMoon className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

function App() {
  const refreshData = useStore((state) => state.refreshData);

  useEffect(() => {
    refreshData();
  }, [refreshData]);

  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/clusters" element={<Clusters />} />
            <Route path="/workloads" element={<Workloads />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/savings" element={<Savings />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
        <Toaster position="top-right" />
      </div>
    </BrowserRouter>
  );
}

export default App;
