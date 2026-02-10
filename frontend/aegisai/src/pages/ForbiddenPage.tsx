import { useNavigate } from 'react-router';
import { Button } from '@/components/ui';

export function ForbiddenPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-red-500">403</h1>
        <p className="mt-4 text-xl text-gray-300">Access Denied</p>
        <p className="mt-2 text-gray-500">You don't have permission to view this page.</p>
        <div className="mt-6">
          <Button onClick={() => navigate(-1)}>Go Back</Button>
        </div>
      </div>
    </div>
  );
}
