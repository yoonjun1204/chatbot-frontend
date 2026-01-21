import HumanAgentPermissions from '../../components/Admin/HumanAgentPermissions';

const AdminDashboard = () => {
    return (
        <div className="admin-container">
            <h1>Admin Control Panel</h1>
            {/* You can nest specific functionality here */}
            <HumanAgentPermissions />
        </div>
    );
};

export default AdminDashboard;