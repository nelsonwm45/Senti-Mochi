'use client';

import { useEffect, useState } from 'react';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { adminApi, User } from '@/lib/api/admin';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassBadge } from '@/components/ui/GlassBadge';
import { Loader2, ShieldAlert } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';

export default function AdminPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (user && user.role !== 'ADMIN') {
        router.push('/dashboard');
        return;
    }

    async function fetchUsers() {
      try {
        const data = await adminApi.getUsers();
        setUsers(data);
      } catch (err) {
        setError('Failed to load users');
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    
    if (user?.role === 'ADMIN') {
        fetchUsers();
    }
  }, [user, router]);

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex justify-center items-center h-full">
            <Loader2 className="animate-spin text-accent" size={32} />
        </div>
      </ProtectedLayout>
    );
  }

  if (error) {
      return (
          <ProtectedLayout>
              <div className="text-red-500 text-center mt-10">{error}</div>
          </ProtectedLayout>
      )
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
            <div className="p-3 bg-red-500/10 rounded-xl text-red-500">
                <ShieldAlert size={24} />
            </div>
            <div>
                <h1 className="text-2xl font-bold text-foreground">Admin Panel</h1>
                <p className="text-foreground-muted">User Management & System Overview</p>
            </div>
        </div>

        <GlassCard className="overflow-hidden">
            <div className="overflow-x-auto">
                <table className="w-full text-left">
                    <thead className="bg-white/5 text-foreground-muted text-sm uppercase font-medium">
                        <tr>
                            <th className="p-4">User</th>
                            <th className="p-4">Role</th>
                            <th className="p-4">Status</th>
                            <th className="p-4">Joined</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {users.map((u) => (
                            <tr key={u.id} className="hover:bg-white/5 transition-colors">
                                <td className="p-4">
                                    <div className="flex flex-col">
                                        <span className="font-medium text-foreground">{u.full_name || 'No Name'}</span>
                                        <span className="text-xs text-foreground-muted">{u.email}</span>
                                    </div>
                                </td>
                                <td className="p-4">
                                    <GlassBadge variant={
                                        u.role === 'ADMIN' ? 'error' :
                                        u.role === 'RM' ? 'accent' :
                                        u.role === 'ANALYST' ? 'success' : 'default'
                                    }>
                                        {u.role}
                                    </GlassBadge>
                                </td>
                                <td className="p-4">
                                    <span className={`flex items-center gap-2 text-sm ${u.is_active ? 'text-green-400' : 'text-red-400'}`}>
                                        <span className={`w-1.5 h-1.5 rounded-full ${u.is_active ? 'bg-green-400' : 'bg-red-400'}`} />
                                        {u.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td className="p-4 text-sm text-foreground-muted">
                                    {new Date(u.created_at).toLocaleDateString()}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </GlassCard>
      </div>
    </ProtectedLayout>
  );
}
