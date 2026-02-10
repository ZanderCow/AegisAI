import { Routes, Route, Navigate } from 'react-router';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { RoleGuard } from '@/components/auth/RoleGuard';
import { AppLayout } from '@/components/layout/AppLayout';
import { LoginPage } from '@/pages/LoginPage';
import { NotFoundPage } from '@/pages/NotFoundPage';
import { ForbiddenPage } from '@/pages/ForbiddenPage';
import { ChatPage } from '@/pages/chat/ChatPage';
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage';
import { RoleManagementPage } from '@/pages/admin/RoleManagementPage';
import { UserManagementPage } from '@/pages/admin/UserManagementPage';
import { DocumentManagementPage } from '@/pages/admin/DocumentManagementPage';
import { SecurityPage } from '@/pages/admin/SecurityPage';
import { SecurityDashboardPage } from '@/pages/security/SecurityDashboardPage';
import { SecurityDocumentsPage } from '@/pages/security/SecurityDocumentsPage';

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forbidden" element={<ForbiddenPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          {/* Chat - accessible to admin, it, hr, finance */}
          <Route element={<RoleGuard allowedRoles={['admin', 'it', 'hr', 'finance']} />}>
            <Route path="/chat" element={<ChatPage />} />
          </Route>

          {/* Admin routes */}
          <Route element={<RoleGuard allowedRoles={['admin']} />}>
            <Route path="/admin/dashboard" element={<AdminDashboardPage />} />
            <Route path="/admin/roles" element={<RoleManagementPage />} />
            <Route path="/admin/users" element={<UserManagementPage />} />
            <Route path="/admin/documents" element={<DocumentManagementPage />} />
            <Route path="/admin/security" element={<SecurityPage />} />
          </Route>

          {/* Security routes */}
          <Route element={<RoleGuard allowedRoles={['security']} />}>
            <Route path="/security/dashboard" element={<SecurityDashboardPage />} />
            <Route path="/security/documents" element={<SecurityDocumentsPage />} />
          </Route>
        </Route>
      </Route>

      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
