import { Link } from 'react-router';
import { Button } from '@/components/ui';

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-aegis-500">404</h1>
        <p className="mt-4 text-xl text-gray-300">Page not found</p>
        <p className="mt-2 text-gray-500">The page you're looking for doesn't exist.</p>
        <div className="mt-6">
          <Link to="/login">
            <Button>Go to Login</Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
