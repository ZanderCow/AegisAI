import { useEffect, useState } from 'react';
import type { AlarmEvent, AlarmFilterType } from '@/types';
import { securityService } from '@/services';
import { Badge, Button, Card, DataTable, SearchBar, Select, Spinner } from '@/components/ui';

function filterBadgeVariant(filterType: AlarmFilterType): 'warning' | 'danger' {
  return filterType === 'keyword' ? 'warning' : 'danger';
}

function providerBadgeVariant(provider: string): 'info' | 'default' {
  return provider === 'deepseek' ? 'info' : 'default';
}

export function FlaggingDashboardPage() {
  const [alarms, setAlarms] = useState<AlarmEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState<'all' | AlarmFilterType>('all');
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isCancelled = false;

    async function loadAlarms() {
      setIsLoading(true);
      setError('');
      try {
        const data = await securityService.getAlarmEvents();
        if (!isCancelled) {
          setAlarms(data);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load alarm events');
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadAlarms();

    return () => {
      isCancelled = true;
    };
  }, [reloadToken]);

  const normalizedQuery = search.trim().toLowerCase();
  const filteredAlarms = alarms.filter(alarm => {
    const matchesFilter = filterType === 'all' || alarm.filterType === filterType;
    if (!matchesFilter) {
      return false;
    }
    if (!normalizedQuery) {
      return true;
    }
    return (
      alarm.userEmail.toLowerCase().includes(normalizedQuery) ||
      alarm.provider.toLowerCase().includes(normalizedQuery) ||
      alarm.filterType.toLowerCase().includes(normalizedQuery) ||
      alarm.messageContent.toLowerCase().includes(normalizedQuery)
    );
  });

  const statCards = [
    { label: 'Total Alarms', value: alarms.length, color: 'text-red-400' },
    { label: 'Keyword Flags', value: alarms.filter(alarm => alarm.filterType === 'keyword').length, color: 'text-yellow-400' },
    { label: 'Provider Flags', value: alarms.filter(alarm => alarm.filterType === 'provider').length, color: 'text-blue-400' },
    { label: 'Unique Users', value: new Set(alarms.map(alarm => alarm.userId)).size, color: 'text-aegis-400' },
  ];

  const filterOptions = [
    { value: 'all', label: 'All alarms' },
    { value: 'keyword', label: 'Keyword' },
    { value: 'provider', label: 'Provider' },
  ];

  const columns = [
    {
      key: 'time',
      header: 'Time',
      render: (alarm: AlarmEvent) => (
        <div>
          <p className="text-sm font-medium text-gray-200">{new Date(alarm.createdAt).toLocaleString()}</p>
          <p className="text-xs text-gray-500">{alarm.conversationId}</p>
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-48',
    },
    {
      key: 'user',
      header: 'User',
      render: (alarm: AlarmEvent) => (
        <div>
          <p className="font-medium text-gray-200">{alarm.userEmail}</p>
          <p className="text-xs text-gray-500">{alarm.userId}</p>
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-56',
    },
    {
      key: 'meta',
      header: 'Classification',
      render: (alarm: AlarmEvent) => (
        <div className="flex flex-wrap gap-2">
          <Badge variant={filterBadgeVariant(alarm.filterType)}>
            {alarm.filterType}
          </Badge>
          <Badge variant={providerBadgeVariant(alarm.provider)}>
            {alarm.provider}
          </Badge>
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-44',
    },
    {
      key: 'message',
      header: 'Flagged User Input',
      render: (alarm: AlarmEvent) => (
        <div className="space-y-2">
          <p className="whitespace-pre-wrap break-words text-sm text-gray-300">{alarm.messageContent}</p>
          {alarm.reason ? (
            <p className="text-xs text-gray-500">{alarm.reason}</p>
          ) : null}
        </div>
      ),
      className: 'px-4 py-4 text-sm text-gray-300 align-top min-w-[32rem]',
    },
  ];

  if (isLoading && alarms.length === 0 && !error) {
    return <Spinner className="mt-20" />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Flagging Dashboard</h1>
        <p className="mt-1 text-sm text-gray-400">
          Persisted moderation alarms across all conversations, ordered by newest first.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map(stat => (
          <Card key={stat.label}>
            <p className="text-sm text-gray-400">{stat.label}</p>
            <p className={`mt-1 text-3xl font-bold ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      {error && (
        <div className="flex flex-col gap-3 rounded-xl border border-red-800 bg-red-900/30 px-4 py-4 text-sm text-red-200 sm:flex-row sm:items-center sm:justify-between">
          <span>{error}</span>
          <Button
            variant="secondary"
            onClick={() => {
              setAlarms([]);
              setReloadToken(current => current + 1);
            }}
          >
            Retry
          </Button>
        </div>
      )}

      <Card padding={false}>
        <div className="flex flex-col gap-4 border-b border-gray-800 p-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="lg:w-96">
            <SearchBar value={search} onChange={setSearch} placeholder="Search flagged content..." />
          </div>
          <div className="w-full lg:w-48">
            <Select
              aria-label="Alarm filter"
              options={filterOptions}
              value={filterType}
              onChange={event => setFilterType(event.target.value as 'all' | AlarmFilterType)}
            />
          </div>
        </div>

        {isLoading ? (
          <Spinner className="my-12" />
        ) : (
          <DataTable
            columns={columns}
            data={filteredAlarms}
            keyExtractor={alarm => alarm.id}
            emptyMessage="No flagged content events found"
          />
        )}
      </Card>
    </div>
  );
}
