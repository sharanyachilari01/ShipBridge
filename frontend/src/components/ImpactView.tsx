import React, { useEffect, useState } from 'react';
import { fetchImpactMetrics, fetchEvaluations, fetchExceptions } from '../api';
import { ImpactMetrics, FinalEvaluation, ShipmentException } from '../types';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';
import { Leaf, DollarSign, ShieldCheck, Award, Download, TrendingUp, AlertTriangle, ClipboardCheck } from 'lucide-react';

export const ImpactView: React.FC = () => {
  const [metrics, setMetrics] = useState<ImpactMetrics | null>(null);
  const [evaluations, setEvaluations] = useState<FinalEvaluation[]>([]);
  const [exceptions, setExceptions] = useState<ShipmentException[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    Promise.all([
      fetchImpactMetrics(),
      fetchEvaluations(),
      fetchExceptions()
    ])
      .then(([metricsData, evalsData, excsData]) => {
        setMetrics(metricsData);
        setEvaluations(evalsData);
        setExceptions(excsData);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Error fetching analytics & evaluations:', err);
        setLoading(false);
      });
  }, []);

  if (loading || !metrics) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-12 text-center text-slate-500 font-medium">
        Loading MySQL-backed evaluation & sustainability analytics...
      </div>
    );
  }

  const COLORS = ['#059669', '#2563eb', '#f59e0b', '#e11d48'];

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 pb-24 space-y-6">
      {/* Header Banner */}
      <div className="bg-white rounded-2xl p-6 shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <span className="p-2.5 bg-emerald-100 text-emerald-600 rounded-xl">
              <Leaf className="h-6 w-6" />
            </span>
            <div>
              <h2 className="text-xl font-bold text-slate-900">Final Evaluations & Impact Analytics</h2>
              <p className="text-sm text-slate-500">
                Real-time metrics sourced from MySQL database tables <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-700">final_evaluation_table</code> and <code className="bg-slate-100 px-1 py-0.5 rounded font-mono text-slate-700">shipment_exception_table</code>.
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled
            className="flex items-center gap-1.5 bg-slate-100 text-slate-400 text-xs font-semibold px-3 py-2 rounded-xl border border-slate-200 cursor-not-allowed"
          >
            <Download className="h-3.5 w-3.5" />
            Export Impact Report (Coming soon)
          </button>
        </div>
      </div>

      {/* Metric Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Card 1: Cost Savings */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-emerald-100 text-emerald-700 rounded-2xl">
            <DollarSign className="h-7 w-7" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Total Cost Saved</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-0.5">
              ${metrics.total_cost_saved.toLocaleString()}
            </div>
            <div className="text-[11px] text-emerald-600 font-semibold flex items-center gap-0.5 mt-1">
              <TrendingUp className="h-3 w-3" /> Live MySQL aggregation
            </div>
          </div>
        </div>

        {/* Card 2: CO2 Saved */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-blue-100 text-blue-700 rounded-2xl">
            <Leaf className="h-7 w-7" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">CO2 Offset</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-0.5">
              {metrics.total_co2_saved_kg.toLocaleString()} <span className="text-sm font-semibold">kg</span>
            </div>
            <div className="text-[11px] text-blue-600 font-semibold flex items-center gap-0.5 mt-1">
              <TrendingUp className="h-3 w-3" /> Carbon avoided via piggybacking
            </div>
          </div>
        </div>

        {/* Card 3: Total Recoveries */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-purple-100 text-purple-700 rounded-2xl">
            <ShieldCheck className="h-7 w-7" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Evaluated Recoveries</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-0.5">
              {evaluations.length > 0 ? evaluations.length : metrics.total_recoveries_count}
            </div>
            <div className="text-[11px] text-purple-600 font-semibold flex items-center gap-0.5 mt-1">
              <Award className="h-3 w-3" /> Recorded evaluations
            </div>
          </div>
        </div>

        {/* Card 4: Active Exceptions */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex items-center gap-4">
          <div className="p-3 bg-amber-100 text-amber-700 rounded-2xl">
            <AlertTriangle className="h-7 w-7" />
          </div>
          <div>
            <div className="text-xs text-slate-500 font-medium">Shipment Exceptions</div>
            <div className="text-2xl font-extrabold text-slate-900 mt-0.5">
              {exceptions.length}
            </div>
            <div className="text-[11px] text-amber-600 font-semibold flex items-center gap-0.5 mt-1">
              From shipment_exception_table
            </div>
          </div>
        </div>
      </div>

      {/* Real MySQL Data Table 1: final_evaluation_table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <ClipboardCheck className="h-5 w-5 text-blue-600" />
              <h3 className="text-base font-bold text-slate-900">Final Evaluations Log</h3>
              <span className="font-mono text-xs bg-blue-50 text-blue-700 px-2.5 py-0.5 rounded-full border border-blue-200 font-semibold">
                final_evaluation_table
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Live evaluations recorded for recovered and rerouted shipments in MySQL.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {evaluations.length} evaluation record(s) loaded
          </span>
        </div>

        {evaluations.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm italic">
            No evaluation records present in final_evaluation_table yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-3">Shipment ID</th>
                  <th className="py-3 px-3">Original Cost</th>
                  <th className="py-3 px-3">Recovery Cost</th>
                  <th className="py-3 px-3">Cost Saved</th>
                  <th className="py-3 px-3">Time Saved</th>
                  <th className="py-3 px-3">Deadline Met</th>
                  <th className="py-3 px-3">Status</th>
                  <th className="py-3 px-3">Add. Dist</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {evaluations.map((ev) => (
                  <tr key={`eval-row-${ev.evaluation_id}`} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">
                      {ev.tracking_number || `SB-IND-SH${ev.shipment_id.toString().padStart(3, '0')}`}
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600">${ev.original_cost.toFixed(2)}</td>
                    <td className="py-3 px-3 font-mono text-slate-600">${ev.recovery_cost.toFixed(2)}</td>
                    <td className="py-3 px-3 font-mono font-bold text-emerald-600">${ev.cost_saved.toFixed(2)}</td>
                    <td className="py-3 px-3">{ev.time_saved_hours.toFixed(1)} hrs</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${ev.deadline_met ? 'bg-emerald-100 text-emerald-800' : 'bg-red-100 text-red-800'}`}>
                        {ev.deadline_met ? 'MET' : 'MISSED'}
                      </span>
                    </td>
                    <td className="py-3 px-3">
                      <span className="px-2 py-0.5 rounded font-semibold text-[10px] bg-blue-100 text-blue-800 border border-blue-200">
                        {ev.recovery_success_status}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-600">{ev.additional_distance_km.toFixed(1)} km</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Real MySQL Data Table 2: shipment_exception_table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
              <h3 className="text-base font-bold text-slate-900">Shipment Exceptions Log</h3>
              <span className="font-mono text-xs bg-amber-50 text-amber-700 px-2.5 py-0.5 rounded-full border border-amber-200 font-semibold">
                shipment_exception_table
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              Exceptions logged by Tier 1 Sentry and Misplacement Decision Engine in MySQL.
            </p>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {exceptions.length} exception record(s) logged
          </span>
        </div>

        {exceptions.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm italic">
            No exception records logged in shipment_exception_table.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-slate-700 border-collapse">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 font-semibold text-slate-600 uppercase tracking-wider">
                  <th className="py-3 px-3">ID</th>
                  <th className="py-3 px-3">Shipment</th>
                  <th className="py-3 px-3">Exception Type</th>
                  <th className="py-3 px-3">Severity</th>
                  <th className="py-3 px-3">Confidence</th>
                  <th className="py-3 px-3">Detected Timestamp</th>
                  <th className="py-3 px-3">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {exceptions.map((exc) => (
                  <tr key={`exc-row-${exc.exception_id}`} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3 px-3 font-mono font-bold text-slate-500">#{exc.exception_id}</td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-900">
                      {exc.tracking_number || `SB-IND-SH${exc.shipment_id.toString().padStart(3, '0')}`}
                    </td>
                    <td className="py-3 px-3 font-semibold text-slate-800">{exc.exception_type}</td>
                    <td className="py-3 px-3">
                      <span className={`px-2 py-0.5 rounded font-bold text-[10px] ${exc.severity === 'HIGH' ? 'bg-red-100 text-red-800' : 'bg-amber-100 text-amber-800'}`}>
                        {exc.severity}
                      </span>
                    </td>
                    <td className="py-3 px-3 font-mono font-bold text-slate-700">
                      {(exc.confidence_score * 100).toFixed(0)}%
                    </td>
                    <td className="py-3 px-3 font-mono text-slate-500">
                      {new Date(exc.detected_timestamp).toLocaleString()}
                    </td>
                    <td className="py-3 px-3 text-slate-600 max-w-xs truncate" title={exc.exception_details || ''}>
                      {exc.exception_details || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Chart 1: Monthly Cost Comparison Bar Chart */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="mb-4">
            <h3 className="font-bold text-slate-900 text-base">Monthly Logistics Recovery Expenses</h3>
            <p className="text-xs text-slate-500">
              Comparison between estimated dedicated recovery cost vs actual piggyback cost ($)
            </p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metrics.monthly_comparison} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip
                  formatter={(value: any) => [`$${value}`, 'Cost']}
                  contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}
                />
                <Bar dataKey="dedicated_cost" name="Dedicated Truck Cost ($)" fill="#94a3b8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="piggyback_cost" name="Piggyback Cost ($)" fill="#059669" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Chart 2: CO2 Emissions Offset Trend */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="mb-4">
            <h3 className="font-bold text-slate-900 text-base">Cumulative Carbon Offset (kg CO2)</h3>
            <p className="text-xs text-slate-500">CO2 emissions avoided month-over-month via piggybacking</p>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={metrics.co2_trend} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorCo2" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563eb" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#2563eb" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 12, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 12, fill: '#64748b' }} />
                <Tooltip
                  formatter={(value: any) => [`${value} kg CO2`, 'Saved']}
                  contentStyle={{ borderRadius: '0.5rem', border: '1px solid #e2e8f0' }}
                />
                <Area type="monotone" dataKey="co2_saved_kg" stroke="#2563eb" strokeWidth={3} fillOpacity={1} fill="url(#colorCo2)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
