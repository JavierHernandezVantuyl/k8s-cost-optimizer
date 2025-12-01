import React from 'react';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export const SavingsLineChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <LineChart data={data}>
      <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
      <XAxis dataKey="date" className="text-sm" />
      <YAxis className="text-sm" />
      <Tooltip contentStyle={{ backgroundColor: 'rgb(31 41 55)', border: 'none', borderRadius: '8px' }} />
      <Legend />
      <Line type="monotone" dataKey="savings" stroke="#3b82f6" strokeWidth={2} />
    </LineChart>
  </ResponsiveContainer>
);

export const SavingsAreaChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <AreaChart data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis />
      <Tooltip />
      <Area type="monotone" dataKey="current" stackId="1" stroke="#ef4444" fill="#ef4444" fillOpacity={0.6} />
      <Area type="monotone" dataKey="optimized" stackId="2" stroke="#22c55e" fill="#22c55e" fillOpacity={0.6} />
    </AreaChart>
  </ResponsiveContainer>
);

export const ClusterBarChart = ({ data }) => (
  <ResponsiveContainer width="100%" height={300}>
    <BarChart data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="cluster" />
      <YAxis />
      <Tooltip />
      <Legend />
      <Bar dataKey="current" fill="#ef4444" name="Current Cost" />
      <Bar dataKey="optimized" fill="#22c55e" name="Optimized Cost" />
    </BarChart>
  </ResponsiveContainer>
);

export const OptimizationPieChart = ({ data }) => {
  const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6'];

  return (
    <ResponsiveContainer width="100%" height={300}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" labelLine={false} label={(entry) => entry.name} outerRadius={80} fill="#8884d8" dataKey="value">
          {data.map((entry, index) => (
            <Cell key={index} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default { SavingsLineChart, SavingsAreaChart, ClusterBarChart, OptimizationPieChart };
