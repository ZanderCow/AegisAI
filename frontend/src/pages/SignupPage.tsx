import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';
import { Button } from '../components/ui/Button';

/**
 * Renders the signup page where new users can register.
 * Captures email, password, and password confirmation, sending them to the backend API.
 * Handles automatic login upon successful registration.
 *
 * @returns The rendered SignupPage component.
 */
export function SignupPage() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        setLoading(true);

        try {
            const backendUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
            const response = await axios.post(`${backendUrl}/api/v1/auth/signup`, {
                email,
                password,
            });
            const token = response.data.access_token;
            if (token) {
                localStorage.setItem('token', token);
                navigate('/');
            } else {
                navigate('/login');
            }
        } catch (err: unknown) {
            const error = err as any;
            setError(error.response?.data?.detail || 'Failed to create account');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 to-aegis-950 py-12 px-4 sm:px-6 lg:px-8 text-white">
            <Card className="w-full max-w-md bg-gray-900 ">
                <div className="text-center mb-8">
                    <img src="/aegis_logo.png" alt="Aegis AI Logo" className="w-24 h-24 mx-auto mb-4 rounded-xl shadow-lg border border-purple-500/30" />
                    <h2 className="text-3xl font-extrabold text-white">
                        Create an account
                    </h2>
                </div>
                <form onSubmit={handleSignup} className="space-y-6">
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
                    <Input
                        label="Confirm Password"
                        type="password"
                        required
                        value={confirmPassword}
                        onChange={(e) => setConfirmPassword(e.target.value)}
                        placeholder="Confirm Password"
                    />
                    <Button type="submit" className="w-full" disabled={loading}>
                        {loading ? 'Creating account...' : 'Sign up'}
                    </Button>
                </form>
                <div className="mt-6 text-center">
                    <p className="text-sm text-gray-400">
                        Already have an account?{' '}
                        <Link to="/login" className="font-medium text-aegis-400 hover:text-aegis-300">
                            Sign in
                        </Link>
                    </p>
                </div>
            </Card>
        </div>
    );
}
