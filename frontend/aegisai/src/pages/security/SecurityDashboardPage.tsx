import { useEffect, useState } from 'react';
import type { SecurityLog } from '@/types';
import { securityService } from '@/services';
import { Card, DataTable, Spinner, SearchBar } from '@/components/ui';
import { FlagIndicator } from '@/components/ui';

export function SecurityDashboardPage() {
  const [logs, setLogs] = useState<SecurityLog[]>([]);
  const [stats, setStats] = useState<{ totalLogs: number; flaggedCount: number; recentActivity: number; uniqueUsers: number } | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    Promise.all([securityService.getAll(), securityService.getStats()]).then(([logData, statsData]) => {
      setLogs(logData);
      setStats(statsData);
      setIsLoading(false);
    });
  }, []);

  if (isLoading) return <Spinner className="mt-20" />;

  const filtered = logs.filter(l =>
    l.userName.toLowerCase().includes(search.toLowerCase()) ||
    l.action.toLowerCase().includes(search.toLowerCase()) ||
    l.details.toLowerCase().includes(search.toLowerCase()),
  );

  const statCards = [
    { label: 'Total Events', value: stats?.totalLogs ?? 0, color: 'text-blue-400' },
    { label: 'Flagged Events', value: stats?.flaggedCount ?? 0, color: 'text-red-400' },
    { label: 'Last 24h Activity', value: stats?.recentActivity ?? 0, color: 'text-green-400' },
    { label: 'Unique Users', value: stats?.uniqueUsers ?? 0, color: 'text-aegis-400' },
  ];

  const columns = [
    { key: 'time', header: 'Time', render: (l: SecurityLog) => (
      <span className="text-xs text-gray-400">{new Date(l.timestamp).toLocaleString()}</span>
    )},
    { key: 'user', header: 'User', render: (l: SecurityLog) => <span className="font-medium text-gray-200">{l.userName}</span> },
    { key: 'action', header: 'Action', render: (l: SecurityLog) => <span className="text-gray-300">{l.action}</span> },
    { key: 'resource', header: 'Resource', render: (l: SecurityLog) => <span className="text-gray-300">{l.resource}</span> },
    { key: 'flag', header: 'Flag', render: (l: SecurityLog) => <FlagIndicator flagType={l.flagType} /> },
    { key: 'details', header: 'Details', render: (l: SecurityLog) => (
      <span className="text-xs text-gray-500 max-w-xs truncate block">{l.details}</span>
    ), className: 'px-4 py-3 text-sm max-w-xs' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-100">Security Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map(s => (
          <Card key={s.label}>
            <p className="text-sm text-gray-400">{s.label}</p>
            <p className={`text-3xl font-bold mt-1 ${s.color}`}>{s.value}</p>
          </Card>
        ))}
      </div>

      <Card padding={false}>
        <div className="p-4 border-b border-gray-800">
          <SearchBar value={search} onChange={setSearch} placeholder="Search security logs..." />
        </div>
        <DataTable columns={columns} data={filtered} keyExtractor={l => l.id} emptyMessage="No security logs found" />
      </Card>
    </div>
  );
}
