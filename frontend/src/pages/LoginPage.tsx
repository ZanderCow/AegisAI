import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

/**
 * Renders the login page where existing users can authenticate.
 * Captures email and password, sending them to the backend API, and manages
 * local token storage.
 *
 * @returns The rendered LoginPage component.
 */
export function LoginPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await axios.post(`${backendUrl}/api/v1/auth/login`, {
                email,
                password,
            });
            const token = response.data.access_token;
            localStorage.setItem('token', token);
            navigate('/');
        } catch (err: unknown) {
            const error = err as any;
            setError(error.response?.data?.detail || 'Failed to login');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-aegis-950 py-12 px-4 sm:px-6 lg:px-8 text-white">
            <Card className="w-full max-w-md bg-gray-900 text-white">
                <div className="text-center mb-8">
                    <img src="/aegis_logo.png" alt="Aegis AI Logo" className="w-24 h-24 mx-auto mb-4 rounded-xl shadow-lg border border-purple-500/30" />
                    <h2 className="text-3xl font-extrabold text-white">
                        Sign in to your account
                    </h2>
                </div>
                <form onSubmit={handleLogin} className="space-y-6">
                    {error && (
                        <div className="bg-red-50 text-red-500 p-3 rounded-md text-sm">
                            {error}
                        </div>
                    )}
                    <Input
                        label="Email address"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        placeholder="Email address"
                    />
                    <Input
                        label="Password"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Password"
                    />
                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? 'Signing in...' : 'Sign in'}
                    </Button>
                </form>
                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-400">
                        Don't have an account?{' '}
                        <Link to="/signup" className="font-medium text-aegis-400 hover:text-aegis-300">
                            Sign up
                        </Link>
                    </p>
                </div>
            </Card>
        </div>
    );
}
