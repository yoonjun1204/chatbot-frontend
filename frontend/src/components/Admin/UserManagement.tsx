import React, { useEffect, useState } from "react";
import axios from "axios";
import { useAuth } from "../../auth/AuthContext";
import { type User, ACCESS_KEYS, type AccessKey } from "./types";
import {
  Search, UserPlus, Edit2, Trash2,
  Shield, Mail, User as UserIcon, CheckCircle, XCircle
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

const UserManagement: React.FC = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState<User[]>([]);
  const [search, setSearch] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [newUser, setNewUser] = useState<Omit<User, "id" | "status"> & { password: string }>({
    name: "",
    email: "",
    password: "",
    role: "agent",
    access: {
      can_view_chats: true,
      can_reply: true,
      can_close_chat: false,
    },
  });

  // Redirect or block if current user is not admin
  useEffect(() => {
    if (!currentUser || currentUser.role !== "admin") {
      alert("Access denied: Admins only");
      window.location.href = "/"; // optional redirect
    }
  }, [currentUser]);

  // Fetch users from backend
  const fetchUsers = async () => {
    if (!currentUser) return;
    try {
      const res = await axios.get(`${API_BASE}/api/admin/users`, {
        headers: { user_id: currentUser.id },
        params: search ? { search } : {},
      });
      setUsers(res.data);
    } catch (err) {
      console.error(err);
      alert("Failed to fetch users. Are you an admin?");
    }
  };

  useEffect(() => {
    const delay = setTimeout(() => {
      fetchUsers();
    }, 300); // debounce

    return () => clearTimeout(delay);
  }, [search]);


  // Add new user
  const handleAddUser = async () => {
    if (!currentUser) return;
    try {
      await axios.post(`${API_BASE}/api/admin/users`, newUser, {
        headers: { user_id: currentUser.id },
      });
      setShowAddModal(false);
      setNewUser({
        name: "",
        email: "",
        password: "",
        role: "agent",
        access: { can_view_chats: false, can_reply: false, can_close_chat: false },
      });
      fetchUsers();
    } catch (err) {
      console.error(err);
      alert("Failed to add user, please check your inputs.");
    }
  };

  // Corrected Toggle Access
  const handleToggleAccess = async (userId: number, key: AccessKey) => {
    if (!currentUser) return;

    // 1. Find the user and calculate the NEW access object immediately
    const userToUpdate = users.find((u) => u.id === userId);
    if (!userToUpdate) return;

    const newAccess = {
      ...userToUpdate.access,
      [key]: !userToUpdate.access[key],
    };

    // 2. Optimistically update UI
    setUsers((prev) =>
      prev.map((u) =>
        u.id === userId ? { ...u, access: newAccess } : u
      )
    );

    try {
      // 3. Send the NEW access object to the API
      await axios.put(
        `${API_BASE}/api/admin/users/${userId}`,
        { access: newAccess }, // <--- Send the variable, not state
        { headers: { user_id: currentUser.id } }
      );
    } catch (err) {
      alert("Failed to update permissions");
      fetchUsers(); // rollback on error
    }
  };

  // Corrected Toggle Status
  const handleToggleStatus = async (userId: number) => {
    if (!currentUser) return;

    // 1. Find user and calculate NEW status
    const userToUpdate = users.find((u) => u.id === userId);
    if (!userToUpdate) return;

    const newStatus = userToUpdate.status === "active" ? "inactive" : "active";

    // 2. Optimistically update UI
    setUsers((prev) =>
      prev.map((u) =>
        u.id === userId ? { ...u, status: newStatus } : u
      )
    );

    try {
      // 3. Send the NEW status to the API
      await axios.put(
        `${API_BASE}/api/admin/users/${userId}`,
        { status: newStatus }, // <--- Send the variable, not state
        { headers: { user_id: currentUser.id } }
      );
    } catch {
      alert("Failed to update status");
      fetchUsers(); // rollback
    }
  };

  // Delete user
  const handleDeleteUser = async (userId: number) => {
    if (!currentUser) return;
    if (!confirm("Are you sure you want to delete this user?")) return;
    try {
      await axios.delete(`${API_BASE}/api/admin/users/${userId}`, {
        headers: { user_id: currentUser.id },
      });
      fetchUsers();
    } catch (err) {
      console.error(err);
      alert("Failed to delete user");
    }
  };

  const handleSaveEdit = async () => {
    if (!currentUser || !editingUser) return;
    try {
      await axios.put(
        `${API_BASE}/api/admin/users/${editingUser.id}`,
        {
          name: editingUser.name,
          email: editingUser.email
        },
        { headers: { user_id: currentUser.id } }
      );
      setEditingUser(null);
      fetchUsers(); // Refresh list
    } catch (err) {
      alert("Failed to update user. Email might be already in use.");
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6 font-sans text-gray-900">
      {/* HEADER SECTION */}
      <header className="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">User Management</h1>
          <p className="text-gray-500">Manage human agents, permissions, and system access.</p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-5 py-2.5 rounded-lg font-semibold transition-all shadow-md active:scale-95"
          >
            <UserPlus size={18} />
            Add Agent
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto">
        {/* SEARCH BAR */}
        <div className="relative mb-6 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search agents by email..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-white border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none shadow-sm transition-all"
          />
        </div>

        {/* TABLE CARD */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-gray-50/50 border-b border-gray-100">
                <th className="p-4 font-semibold text-gray-600 uppercase text-xs tracking-wider">User Info</th>
                <th className="p-4 font-semibold text-gray-600 uppercase text-xs tracking-wider">Role</th>
                <th className="p-4 font-semibold text-gray-600 uppercase text-xs tracking-wider">Permissions</th>
                <th className="p-4 font-semibold text-gray-600 uppercase text-xs tracking-wider">Status</th>
                <th className="p-4 font-semibold text-gray-600 uppercase text-xs tracking-wider text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50/80 transition-colors group">
                  <td className="p-4">
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 bg-indigo-100 text-indigo-700 rounded-full flex items-center justify-center font-bold">
                        {u.name.charAt(0)}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">{u.name}</div>
                        <div className="text-sm text-gray-500">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="p-4">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-widest ${u.role === 'admin' ? 'bg-purple-100 text-purple-700' : 'bg-blue-100 text-blue-700'
                      }`}>
                      {u.role}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="flex flex-wrap gap-2">
                      {ACCESS_KEYS.map((k) => (
                        <label key={k} className={`flex items-center gap-1.5 px-2 py-1 rounded-md text-[11px] font-medium border transition-all cursor-pointer ${u.access[k]
                          ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                          : 'bg-gray-50 border-gray-200 text-gray-400'
                          } ${u.role === 'admin' ? 'opacity-70 cursor-not-allowed' : 'hover:border-indigo-300'}`}>
                          <input
                            type="checkbox"
                            checked={u.access[k]}
                            disabled={u.role === "admin"}
                            onChange={() => handleToggleAccess(u.id, k)}
                            className="hidden"
                          />
                          {u.access[k] ? <CheckCircle size={12} /> : <XCircle size={12} />}
                          {k.replace('can_', '').replace('_', ' ')}
                        </label>
                      ))}
                    </div>
                  </td>
                  <td className="p-4">
                    <button
                      onClick={() => handleToggleStatus(u.id)}
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none ${u.status === "active" ? "bg-emerald-500" : "bg-gray-300"
                        }`}
                    >
                      <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${u.status === "active" ? "translate-x-6" : "translate-x-1"
                        }`} />
                    </button>
                  </td>
                  <td className="p-4 text-right">
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => setEditingUser(u)}
                        className="p-2 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-all"
                        title="Edit User"
                      >
                        <Edit2 size={18} />
                      </button>
                      <button
                        onClick={() => handleDeleteUser(u.id)}
                        className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-all"
                        title="Delete User"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {users.length === 0 && (
            <div className="p-12 text-center text-gray-500">
              No agents found matching your search.
            </div>
          )}
        </div>
      </main>

      {/* MODAL OVERLAY WRAPPER */}
      {(showAddModal || editingUser) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/60 backdrop-blur-sm p-4">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-1">
                {showAddModal ? "Create New Agent" : "Edit User Profile"}
              </h2>
              <p className="text-gray-500 text-sm mb-6">
                {showAddModal ? "Fill in the details to add a new human support agent." : "Update the agent's account information."}
              </p>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Full Name</label>
                  <div className="relative">
                    <UserIcon className="absolute left-3 top-3 text-gray-400" size={18} />
                    <input
                      type="text"
                      placeholder="e.g. John Doe"
                      value={showAddModal ? newUser.name : editingUser?.name}
                      onChange={(e) => showAddModal
                        ? setNewUser({ ...newUser, name: e.target.value })
                        : setEditingUser({ ...editingUser!, name: e.target.value })}
                      className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Email Address</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 text-gray-400" size={18} />
                    <input
                      type="email"
                      placeholder="agent@company.com"
                      value={showAddModal ? newUser.email : editingUser?.email}
                      onChange={(e) => showAddModal
                        ? setNewUser({ ...newUser, email: e.target.value })
                        : setEditingUser({ ...editingUser!, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
                    />
                  </div>
                </div>

                {showAddModal && (
                  <div>
                    <label className="block text-xs font-bold text-gray-500 uppercase mb-1 ml-1">Initial Password</label>
                    <div className="relative">
                      <Shield className="absolute left-3 top-3 text-gray-400" size={18} />
                      <input
                        type="password"
                        placeholder="••••••••"
                        value={newUser.password}
                        onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                        className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-gray-50 p-4 flex justify-end gap-3">
              <button
                onClick={() => { setShowAddModal(false); setEditingUser(null); }}
                className="px-4 py-2 text-gray-600 font-semibold hover:bg-gray-200 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={showAddModal ? handleAddUser : handleSaveEdit}
                className={`px-6 py-2 rounded-lg font-bold text-white shadow-md transition-all active:scale-95 ${showAddModal ? "bg-indigo-600 hover:bg-indigo-700" : "bg-indigo-600 hover:bg-indigo-700"
                  }`}
              >
                {showAddModal ? "Create Agent" : "Save Changes"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
