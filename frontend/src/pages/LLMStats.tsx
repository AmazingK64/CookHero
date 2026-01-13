/**
 * LLM Statistics Dashboard Page
 * Displays usage statistics, trends, and distribution
 */

import { useCallback, useEffect, useState } from 'react';
import {
  Activity,
  BarChart3,
  Clock,
  Loader2,
  RefreshCcw,
  Zap,
  TrendingUp,
  PieChart as PieChartIcon,
  Layers,
  Cpu,
} from 'lucide-react';
import {
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { useAuth } from '../contexts';
import {
  getLLMStatsSummary,
  getLLMStatsTimeSeries,
  getLLMStatsDistributionByModule,
  getLLMStatsDistributionByModel,
} from '../services/api/llmStats';
import type {
  LLMStatsSummary,
  TimeSeriesResponse,
  ModuleDistributionResponse,
  ModelDistributionResponse,
} from '../types/llmStats';

// Chart colors
const COLORS = [
  '#f97316', // orange-500
  '#3b82f6', // blue-500
  '#10b981', // emerald-500
  '#8b5cf6', // violet-500
  '#ec4899', // pink-500
  '#eab308', // yellow-500
  '#6366f1', // indigo-500
  '#14b8a6', // teal-500
];

/**
 * Stat card component
 */
interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  color?: 'orange' | 'blue' | 'green' | 'red' | 'gray' | 'violet';
}

function StatCard({ title, value, subtitle, icon, color = 'orange' }: StatCardProps) {
  const colorClasses = {
    orange: 'from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 border-orange-200 dark:border-orange-800',
    blue: 'from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200 dark:border-blue-800',
    green: 'from-emerald-50 to-emerald-100 dark:from-emerald-900/20 dark:to-emerald-800/20 border-emerald-200 dark:border-emerald-800',
    red: 'from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200 dark:border-red-800',
    gray: 'from-gray-50 to-gray-100 dark:from-gray-900/20 dark:to-gray-800/20 border-gray-200 dark:border-gray-800',
    violet: 'from-violet-50 to-violet-100 dark:from-violet-900/20 dark:to-violet-800/20 border-violet-200 dark:border-violet-800',
  };

  const iconColorClasses = {
    orange: 'text-orange-500',
    blue: 'text-blue-500',
    green: 'text-emerald-500',
    red: 'text-red-500',
    gray: 'text-gray-500',
    violet: 'text-violet-500',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} border rounded-2xl p-4 shadow-sm`}>
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-gray-500 dark:text-gray-400 font-medium uppercase tracking-wider mb-1">
            {title}
          </p>
          <p className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white">
            {value}
          </p>
          {subtitle && (
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
          )}
        </div>
        <div className={`p-2 rounded-xl bg-white/50 dark:bg-gray-800/50 ${iconColorClasses[color]}`}>
          {icon}
        </div>
      </div>
    </div>
  );
}

/**
 * Period selector for time series
 */
interface PeriodSelectorProps {
  days: number;
  granularity: 'day' | 'hour';
  onDaysChange: (days: number) => void;
  onGranularityChange: (g: 'day' | 'hour') => void;
}

function PeriodSelector({ days, granularity, onDaysChange, onGranularityChange }: PeriodSelectorProps) {
  const periodOptions = granularity === 'hour' ? [1, 3, 7] : [7, 14, 30];

  const formatLabel = (d: number) => {
    if (granularity === 'hour') {
      return `${d * 24}小时`;
    }
    return `${d}天`;
  };

  const handleGranularityChange = (g: 'day' | 'hour') => {
    onGranularityChange(g);
    const nextOptions = g === 'hour' ? [1, 3, 7] : [7, 14, 30];
    if (!nextOptions.includes(days)) {
      onDaysChange(nextOptions[0]);
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2">
      <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {periodOptions.map((d) => (
          <button
            key={d}
            onClick={() => onDaysChange(d)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              days === d
                ? 'bg-orange-500 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            {formatLabel(d)}
          </button>
        ))}
      </div>
      <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
        {(['day', 'hour'] as const).map((g) => (
          <button
            key={g}
            onClick={() => handleGranularityChange(g)}
            className={`px-3 py-1.5 text-xs font-medium transition-colors ${
              granularity === g
                ? 'bg-orange-500 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            {g === 'day' ? '按天' : '按小时'}
          </button>
        ))}
      </div>
    </div>
  );
}

/**
 * Usage chart component
 */
interface UsageChartProps {
  data: TimeSeriesResponse | null;
  loading: boolean;
}

function UsageChart({ data, loading }: UsageChartProps) {
  if (loading) {
    return (
      <div className="h-72 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!data || data.time_series.length === 0) {
    return (
      <div className="h-72 flex flex-col items-center justify-center text-gray-500">
        <BarChart3 className="w-8 h-8 mb-2 opacity-50" />
        <p>暂无使用数据</p>
      </div>
    );
  }

  // Transform data for chart
  const chartData = data.time_series.map((point) => ({
    period: new Date(point.period).toLocaleDateString('zh-CN', {
      month: 'short',
      day: 'numeric',
      ...(data.granularity === 'hour' ? { hour: '2-digit' } : {}),
    }),
    calls: point.call_count,
    tokens: point.total_tokens,
  }));

  return (
    <ResponsiveContainer width="100%" height={288}>
      <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
        <defs>
          <linearGradient id="colorCalls" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
          </linearGradient>
          <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" opacity={0.5} />
        <XAxis
          dataKey="period"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={{ stroke: '#e5e7eb' }}
        />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          label={{ value: '调用次数', angle: -90, position: 'insideLeft', fontSize: 10, fill: '#9ca3af' }}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}
          label={{ value: 'Tokens', angle: 90, position: 'insideRight', fontSize: 10, fill: '#9ca3af' }}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'rgba(255,255,255,0.95)',
            borderRadius: '8px',
            border: '1px solid #e5e7eb',
            boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
          }}
        />
        <Legend verticalAlign="bottom" height={36} />
        <Area
          yAxisId="left"
          type="monotone"
          dataKey="calls"
          name="调用次数"
          stroke="#f97316"
          strokeWidth={2}
          fill="url(#colorCalls)"
        />
        <Area
          yAxisId="right"
          type="monotone"
          dataKey="tokens"
          name="Tokens"
          stroke="#3b82f6"
          strokeWidth={2}
          fill="url(#colorTokens)"
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}

/**
 * Distribution pie chart component
 */
interface DistributionChartProps {
  data: Array<{ name: string; value: number }>;
  loading: boolean;
  type: 'module' | 'model';
}

function DistributionChart({ data, loading, type }: DistributionChartProps) {
  if (loading) {
    return (
      <div className="h-64 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-gray-500">
        <PieChartIcon className="w-8 h-8 mb-2 opacity-50" />
        <p>暂无分布数据</p>
      </div>
    );
  }

  return (
    <div className="h-64 relative">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number | undefined) => [value?.toLocaleString() ?? '0', 'Tokens']}
          />
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center pointer-events-none">
        <p className="text-xs text-gray-500 font-medium uppercase">Total</p>
        <p className="text-lg font-bold text-gray-900 dark:text-white">
          {(data.reduce((acc, curr) => acc + curr.value, 0) / 1000).toFixed(1)}k
        </p>
      </div>
    </div>
  );
}

/**
 * Main LLM Stats page component
 */
export default function LLMStatsPage() {
  const { token } = useAuth();

  // State
  const [summary, setSummary] = useState<LLMStatsSummary | null>(null);
  const [timeSeries, setTimeSeries] = useState<TimeSeriesResponse | null>(null);
  const [moduleDist, setModuleDist] = useState<ModuleDistributionResponse | null>(null);
  const [modelDist, setModelDist] = useState<ModelDistributionResponse | null>(null);
  
  const [loading, setLoading] = useState(true);
  const [tsLoading, setTsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

   // Filters
   const [days, setDays] = useState(7);
   const [granularity, setGranularity] = useState<'day' | 'hour'>('day');
   const [distTab, setDistTab] = useState<'module' | 'model'>('module');
   const [tableTab, setTableTab] = useState<'module' | 'model'>('module');

  // Load initial data
  const loadData = useCallback(async () => {
    if (!token) return;

    setLoading(true);
    setError(null);

    try {
      const [summaryData, tsData, modDistData, modelDistData] = await Promise.all([
        getLLMStatsSummary(token),
        getLLMStatsTimeSeries(token, days, granularity),
        getLLMStatsDistributionByModule(token),
        getLLMStatsDistributionByModel(token),
      ]);

      setSummary(summaryData);
      setTimeSeries(tsData);
      setModuleDist(modDistData);
      setModelDist(modelDistData);
    } catch (err) {
      console.error('Failed to load LLM stats:', err);
      setError(err instanceof Error ? err.message : '加载数据失败');
    } finally {
      setLoading(false);
    }
  }, [token, days, granularity]);

  // Load time series when filters change
  const loadTimeSeries = useCallback(async () => {
    if (!token) return;

    setTsLoading(true);
    try {
      const tsData = await getLLMStatsTimeSeries(token, days, granularity);
      setTimeSeries(tsData);
    } catch (err) {
      console.error('Failed to load time series:', err);
    } finally {
      setTsLoading(false);
    }
  }, [token, days, granularity]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (!loading) {
      loadTimeSeries();
    }
  }, [days, granularity]);

  // Process distribution data for charts
  const distChartData = distTab === 'module' 
    ? moduleDist?.distribution.map(d => ({ name: d.module_name, value: d.total_tokens })) || []
    : modelDist?.distribution.map(d => ({ name: d.model_name, value: d.total_tokens })) || [];

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-orange-500" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-4">
        <Activity className="w-12 h-12 text-red-500 mb-4" />
        <p className="text-gray-600 dark:text-gray-300 mb-4">{error}</p>
        <button
          onClick={loadData}
          className="px-4 py-2 rounded-lg bg-orange-500 text-white text-sm font-medium hover:bg-orange-600 transition-colors"
        >
          重试
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-4 md:p-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <p className="text-xs uppercase tracking-[0.2em] text-orange-500 font-semibold">
              Analytics
            </p>
            <h1 className="text-xl md:text-2xl font-bold flex items-center gap-2">
              <Activity className="w-5 h-5 md:w-6 md:h-6 text-orange-500" />
              LLM 使用统计
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              追踪 Token 消耗、模型调用和性能指标
            </p>
          </div>
          <button
            onClick={loadData}
            className="p-2 rounded-lg text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 dark:hover:text-gray-300 transition-colors self-start md:self-auto"
            title="刷新数据"
          >
            <RefreshCcw className="w-4 h-4" />
          </button>
        </div>

        {/* Top Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-4 mb-6">
          <StatCard
            title="总调用次数"
            value={summary?.total_calls.toLocaleString() ?? 0}
            icon={<Zap className="w-5 h-5" />}
            color="orange"
          />
          <StatCard
            title="总 Token 消耗"
            value={(summary?.total_tokens ?? 0).toLocaleString()}
            subtitle={`平均 ${summary?.avg_tokens_per_call.toFixed(0) ?? 0} / 次`}
            icon={<Layers className="w-5 h-5" />}
            color="blue"
          />
          <StatCard
            title="平均耗时"
            value={summary?.avg_duration_ms ? `${(summary.avg_duration_ms / 1000).toFixed(2)}s` : '-'}
            icon={<Clock className="w-5 h-5" />}
            color="violet"
          />
          <StatCard
            title="模型数量"
            value={modelDist?.count ?? 0}
            subtitle={`${moduleDist?.count ?? 0} 个模块`}
            icon={<Cpu className="w-5 h-5" />}
            color="green"
          />
        </div>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          {/* Trends Chart */}
          <section className="lg:col-span-2 bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm p-4 md:p-5">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 md:w-9 md:h-9 rounded-xl bg-orange-100 dark:bg-orange-500/10 flex items-center justify-center">
                  <TrendingUp className="w-4 h-4 md:w-5 md:h-5 text-orange-500" />
                </div>
                <div>
                  <h2 className="font-semibold text-base md:text-lg">使用趋势</h2>
                  <p className="text-xs text-gray-500">
                    调用量与 Token 消耗
                  </p>
                </div>
              </div>
              <PeriodSelector
                days={days}
                granularity={granularity}
                onDaysChange={setDays}
                onGranularityChange={setGranularity}
              />
            </div>
            <UsageChart data={timeSeries} loading={tsLoading} />
          </section>

          {/* Distribution Chart */}
          <section className="bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm p-4 md:p-5">
            <div className="flex flex-col gap-4 h-full">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-blue-100 dark:bg-blue-500/10 flex items-center justify-center">
                    <PieChartIcon className="w-4 h-4 text-blue-500" />
                  </div>
                  <h2 className="font-semibold text-base md:text-lg">Token 分布</h2>
                </div>
                
                <div className="flex bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
                  <button
                    onClick={() => setDistTab('module')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      distTab === 'module'
                        ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    按模块
                  </button>
                  <button
                    onClick={() => setDistTab('model')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                      distTab === 'model'
                        ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                        : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                    }`}
                  >
                    按模型
                  </button>
                </div>
              </div>

              <div className="flex-1 flex flex-col justify-center">
                 <DistributionChart data={distChartData} loading={loading} type={distTab} />
                 
                 <div className="mt-4 space-y-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                    {distChartData.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-2 h-2 rounded-full" 
                            style={{ backgroundColor: COLORS[idx % COLORS.length] }}
                          />
                          <span className="text-gray-600 dark:text-gray-300 truncate max-w-[120px]" title={item.name}>
                            {item.name}
                          </span>
                        </div>
                        <span className="font-mono text-gray-500">
                          {(item.value / 1000).toFixed(1)}k
                        </span>
                      </div>
                    ))}
                 </div>
              </div>
            </div>
          </section>
        </div>

        {/* Detailed Table */}
        <div className="bg-white dark:bg-gray-900/60 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-sm overflow-hidden">
           <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex items-center justify-between">
             <h3 className="font-semibold text-gray-900 dark:text-white">{tableTab === 'module' ? '模块详情' : '模型详情'}</h3>
             <div className="flex bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
               <button
                 onClick={() => setTableTab('module')}
                 className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                   tableTab === 'module'
                     ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                     : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                 }`}
               >
                 模块详情
               </button>
               <button
                 onClick={() => setTableTab('model')}
                 className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${
                   tableTab === 'model'
                     ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm'
                     : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
                 }`}
               >
                 模型详情
               </button>
             </div>
           </div>
           <div className="overflow-x-auto">
             <table className="w-full text-sm text-left">
               <thead className="bg-gray-50 dark:bg-gray-800/50 text-gray-500 dark:text-gray-400">
                 <tr>
                   <th className="px-6 py-3 font-medium">{tableTab === 'module' ? '模块名称' : '模型名称'}</th>
                   <th className="px-6 py-3 font-medium text-right">调用次数</th>
                   <th className="px-6 py-3 font-medium text-right">总 Tokens</th>
                   <th className="px-6 py-3 font-medium text-right">平均 Tokens</th>
                   <th className="px-6 py-3 font-medium text-right">平均耗时</th>
                 </tr>
               </thead>
               <tbody className="divide-y divide-gray-200 dark:divide-gray-800">
                 {(tableTab === 'module' ? moduleDist?.distribution : modelDist?.distribution)?.map((item) => (
                   <tr key={tableTab === 'module' ? item.module_name : item.model_name} className="hover:bg-gray-50 dark:hover:bg-gray-800/30">
                     <td className="px-6 py-4 font-medium text-gray-900 dark:text-white">
                       {tableTab === 'module' ? item.module_name : item.model_name}
                     </td>
                     <td className="px-6 py-4 text-right text-gray-600 dark:text-gray-300">
                       {item.call_count.toLocaleString()}
                     </td>
                     <td className="px-6 py-4 text-right text-gray-600 dark:text-gray-300">
                       {item.total_tokens.toLocaleString()}
                     </td>
                     <td className="px-6 py-4 text-right text-gray-600 dark:text-gray-300">
                       {Math.round(item.avg_tokens).toLocaleString()}
                     </td>
                     <td className="px-6 py-4 text-right text-gray-600 dark:text-gray-300">
                       {Math.round(item.avg_duration_ms)}ms
                     </td>
                   </tr>
                 ))}
                 {((tableTab === 'module' && (!moduleDist || moduleDist.distribution.length === 0)) ||
                   (tableTab === 'model' && (!modelDist || modelDist.distribution.length === 0))) && (
                    <tr>
                      <td colSpan={5} className="px-6 py-8 text-center text-gray-500">
                        暂无数据
                      </td>
                    </tr>
                 )}
               </tbody>
             </table>
           </div>
        </div>
      </div>
    </div>
  );
}
