import { useEffect, useState } from 'react';
import type { HistoricChatDashboard } from '@/types';
import { securityService } from '@/services';
import { Button, Card, SearchBar, Spinner } from '@/components/ui';
import { HistoricChatTable } from '@/components/security/HistoricChatTable';

const PAGE_SIZE = 10;

export function SecurityDashboardPage() {
  const [dashboard, setDashboard] = useState<HistoricChatDashboard | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    let isCancelled = false;

    async function loadDashboard() {
      setIsLoading(true);
      setError('');
      try {
        const data = await securityService.getHistoricChatDashboard(PAGE_SIZE, offset);
        if (!isCancelled) {
          setDashboard(data);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load historic chats');
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadDashboard();

    return () => {
      isCancelled = true;
    };
  }, [offset, reloadToken]);

  const filteredHistories = dashboard?.items.filter(history => {
    const query = search.trim().toLowerCase();
    if (!query) return true;

    return (
      history.userEmail.toLowerCase().includes(query) ||
      history.userId.toLowerCase().includes(query) ||
      history.title.toLowerCase().includes(query) ||
      history.provider.toLowerCase().includes(query) ||
      history.model.toLowerCase().includes(query) ||
      history.messages.some(message => message.content.toLowerCase().includes(query))
    );
  }) ?? [];

  const summary = dashboard?.summary;
  const total = dashboard?.total ?? 0;
  const showingFrom = total === 0 ? 0 : offset + 1;
  const showingTo = Math.min(offset + (dashboard?.items.length ?? 0), total);
  const hasPreviousPage = offset > 0;
  const hasNextPage = dashboard ? offset + dashboard.items.length < dashboard.total : false;

  const statCards = [
    { label: 'Total Histories', value: summary?.totalHistories ?? 0, color: 'text-blue-400' },
    { label: 'Total Messages', value: summary?.totalMessages ?? 0, color: 'text-aegis-400' },
    { label: 'Last 24h Activity', value: summary?.recentActivity ?? 0, color: 'text-green-400' },
    { label: 'Unique Users', value: summary?.uniqueUsers ?? 0, color: 'text-yellow-400' },
  ];

  if (isLoading && !dashboard) {
    return <Spinner className="mt-20" />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">Security Dashboard</h1>
        <p className="mt-1 text-sm text-gray-400">
          Historic chat transcripts across all users, ordered by most recent activity.
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
              setDashboard(null);
              setOffset(0);
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
            <SearchBar value={search} onChange={setSearch} placeholder="Search chat histories..." />
          </div>
          <div className="text-sm text-gray-400">
            Showing {showingFrom}-{showingTo} of {total} histories
          </div>
        </div>

        {isLoading ? (
          <Spinner className="my-12" />
        ) : (
          <HistoricChatTable histories={filteredHistories} />
        )}

        <div className="flex flex-col gap-3 border-t border-gray-800 p-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs text-gray-500">
            Search filters the currently loaded page. Pagination remains ordered by recent backend activity.
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              onClick={() => setOffset(current => Math.max(0, current - PAGE_SIZE))}
              disabled={!hasPreviousPage || isLoading}
            >
              Previous
            </Button>
            <Button
              variant="secondary"
              onClick={() => setOffset(current => current + PAGE_SIZE)}
              disabled={!hasNextPage || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
