import { useAuth } from "../../auth/AuthContext";
// import "./AgentDashboard.css"; // Assuming you have styles here

const AgentDashboard = () => {
  // 1. Destructure the logout function from your context
  const { logout } = useAuth();

  return (
    <div className="agent-dashboard">
      <nav className="agent-nav">
        <span>Agent Workspace</span>

        {/* 2. Add the Logout Button */}
        <button
          onClick={logout}
          className="logout-button"
        >
          Log Out
        </button>
      </nav>

      <div className="dashboard-content">
        <p>Coming soon...</p>
      </div>
    </div>
  );
};

export default AgentDashboard;