import { Routes, Route, Navigate } from 'react-router-dom';
import React from 'react';
import { LoginPage } from './pages/LoginPage';
import { SignupPage } from './pages/SignupPage';

/**
 * A wrapper component that protects routes requiring authentication.
 * Redirects unauthenticated users to the login page.
 *
 * @param props - The props containing child components to render if authenticated.
 * @returns The protected components or a Navigate redirect.
 */
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;
  return children;
}

/**
 * The main landing page for authenticated users.
 * Provides a simple welcome message and a logout action.
 *
 * @returns The rendered Home component.
 */
function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950 text-white">
      <div className="text-center">
        <h1 className="text-4xl font-bold mb-4">Welcome Home</h1>
        <button
          className="bg-red-500 text-white px-4 py-2 rounded"
          onClick={() => {
            localStorage.removeItem('token');
            window.location.href = '/login';
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
}

/**
 * The root application component that defines all primary routes.
 *
 * @returns The configured Router providing layout and page access.
 */
function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Home />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;
