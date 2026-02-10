import { AuthProvider } from '@/context/AuthContext';
import { SidebarProvider } from '@/context/SidebarContext';
import { ChatProvider } from '@/context/ChatContext';
import { AppRouter } from '@/router';

function App() {
  return (
    <AuthProvider>
      <SidebarProvider>
        <ChatProvider>
          <AppRouter />
        </ChatProvider>
      </SidebarProvider>
    </AuthProvider>
  );
}

export default App;
