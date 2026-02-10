import { useEffect, useState } from 'react';
import { Card, Spinner } from '@/components/ui';
import { userService, documentService, securityService } from '@/services';
import type { User, Document, SecurityLog } from '@/types';
import { FlagIndicator } from '@/components/ui';

export function AdminDashboardPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [securityStats, setSecurityStats] = useState<{ totalLogs: number; flaggedCount: number; recentActivity: number; uniqueUsers: number } | null>(null);
  const [recentLogs, setRecentLogs] = useState<SecurityLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      userService.getAll(),
      documentService.getAll(),
      securityService.getStats(),
      securityService.getAll(),
    ]).then(([u, d, stats, logs]) => {
      setUsers(u);
      setDocuments(d);
      setSecurityStats(stats);
      setRecentLogs(logs.slice(0, 5));
      setIsLoading(false);
    });
  }, []);

  if (isLoading) return <Spinner className="mt-20" />;

  const stats = [
    { label: 'Total Users', value: users.length, color: 'text-aegis-400' },
    { label: 'Documents', value: documents.length, color: 'text-blue-400' },
    { label: 'Security Events', value: securityStats?.totalLogs ?? 0, color: 'text-green-400' },
    { label: 'Flagged Events', value: securityStats?.flaggedCount ?? 0, color: 'text-red-400' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-100">Admin Dashboard</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(stat => (
          <Card key={stat.label}>
            <p className="text-sm text-gray-400">{stat.label}</p>
            <p className={`text-3xl font-bold mt-1 ${stat.color}`}>{stat.value}</p>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Recent Security Activity</h2>
          <div className="space-y-3">
            {recentLogs.map(log => (
              <div key={log.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-200">{log.userName}</p>
                  <p className="text-xs text-gray-500">{log.action} - {log.resource}</p>
                </div>
                <div className="flex items-center gap-2">
                  <FlagIndicator flagType={log.flagType} />
                  <span className="text-xs text-gray-500">
                    {new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold text-gray-100 mb-4">Document Overview</h2>
          <div className="space-y-3">
            {documents.slice(0, 5).map(doc => (
              <div key={doc.id} className="flex items-center justify-between py-2 border-b border-gray-800 last:border-0">
                <div>
                  <p className="text-sm font-medium text-gray-200">{doc.title}</p>
                  <p className="text-xs text-gray-500">{doc.allowedRoles.join(', ')}</p>
                </div>
                <span className={`text-xs px-2 py-1 rounded-full ${doc.status === 'active' ? 'bg-green-900/50 text-green-400' : doc.status === 'processing' ? 'bg-yellow-900/50 text-yellow-400' : 'bg-gray-700 text-gray-400'}`}>
                  {doc.status}
                </span>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </div>
  );
}
