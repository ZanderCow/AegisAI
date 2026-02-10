import { useEffect, useState } from 'react';
import type { SecurityLog, FlagType } from '@/types';
import { securityService } from '@/services';
import { Card, DataTable, Spinner, SearchBar, Select } from '@/components/ui';
import { FlagIndicator } from '@/components/ui';

export function SecurityPage() {
  const [logs, setLogs] = useState<SecurityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [flagFilter, setFlagFilter] = useState<string>('all');

  useEffect(() => {
    securityService.getAll().then(data => {
      setLogs(data);
      setIsLoading(false);
    });
  }, []);

  const filtered = logs.filter(l => {
    const matchesSearch =
      l.userName.toLowerCase().includes(search.toLowerCase()) ||
      l.action.toLowerCase().includes(search.toLowerCase()) ||
      l.resource.toLowerCase().includes(search.toLowerCase());
    const matchesFlag = flagFilter === 'all' || l.flagType === flagFilter;
    return matchesSearch && matchesFlag;
  });

  const flagOptions = [
    { value: 'all', label: 'All Events' },
    { value: 'none', label: 'Clean Only' },
    { value: 'unauthorized_access', label: 'Unauthorized Access' },
    { value: 'suspicious_query', label: 'Suspicious Query' },
    { value: 'data_exfiltration', label: 'Data Exfiltration' },
  ];

  const columns = [
    { key: 'time', header: 'Time', render: (l: SecurityLog) => (
      <span className="text-xs text-gray-400">{new Date(l.timestamp).toLocaleString()}</span>
    )},
    { key: 'user', header: 'User', render: (l: SecurityLog) => <span className="font-medium text-gray-200">{l.userName}</span> },
    { key: 'action', header: 'Action', render: (l: SecurityLog) => <span className="text-gray-300">{l.action}</span> },
    { key: 'resource', header: 'Resource', render: (l: SecurityLog) => <span className="text-gray-300">{l.resource}</span> },
    { key: 'ip', header: 'IP', render: (l: SecurityLog) => <span className="font-mono text-xs text-gray-400">{l.ipAddress}</span> },
    { key: 'flag', header: 'Flag', render: (l: SecurityLog) => <FlagIndicator flagType={l.flagType as FlagType} /> },
    { key: 'details', header: 'Details', render: (l: SecurityLog) => (
      <span className="text-xs text-gray-500 max-w-xs truncate block">{l.details}</span>
    ), className: 'px-4 py-3 text-sm max-w-xs' },
  ];

  if (isLoading) return <Spinner className="mt-20" />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-100">Security Logs</h1>

      <Card padding={false}>
        <div className="p-4 border-b border-gray-800 flex flex-col sm:flex-row gap-3">
          <div className="flex-1">
            <SearchBar value={search} onChange={setSearch} placeholder="Search logs..." />
          </div>
          <div className="w-full sm:w-48">
            <Select options={flagOptions} value={flagFilter} onChange={e => setFlagFilter(e.target.value)} />
          </div>
        </div>
        <DataTable columns={columns} data={filtered} keyExtractor={l => l.id} emptyMessage="No security logs found" />
      </Card>
    </div>
  );
}
