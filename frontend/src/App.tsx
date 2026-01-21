import { AuthProvider, useAuth } from "./auth/AuthContext";
import LoginPage from "./pages/Login/LoginPage";
import CustomerHome from "./pages/Customer/CustomerHome";
import AdminDashboard from "./pages/Admin/AdminDashboard";
import AgentDashboard from "./pages/HumanAgent/AgentDashboard";

const AppInner: React.FC = () => {
  const { user } = useAuth();

  if (!user) {
    return <LoginPage />;
  }

  if (user.role === "customer") {
    return <CustomerHome />;
  }

  if (user.role === "admin") {
    return <AdminDashboard />;
  }

  if (user.role === "agent") {
    return <AgentDashboard />;
  }

  // Fallback
  return <LoginPage />;
};

const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppInner />
    </AuthProvider>
  );
};

export default App;