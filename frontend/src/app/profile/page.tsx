'use client';
import { useEffect, useState, useRef } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Camera, User as UserIcon, Mail, Shield, Calendar, Save, Upload } from 'lucide-react';
import { toast } from 'react-hot-toast';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassInput } from '@/components/ui/GlassInput';
import { GlassButton } from '@/components/ui/GlassButton';

interface User {
  id: string;
  email: string;
  full_name: string | null;
  avatar_url: string | null;
  role: string;
  created_at: string;
}

export default function Profile() {
  const [user, setUser] = useState<User | null>(null);
  const [fullName, setFullName] = useState('');
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchUserData();
  }, []);

  const fetchUserData = async () => {
    const token = localStorage.getItem('token');
    if (token) {
      try {
        const res = await axios.get('/api/v1/users/me', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(res.data);
        setFullName(res.data.full_name || '');
        setAvatarPreview(res.data.avatar_url);
      } catch (err) {
        console.error('Failed to fetch user data:', err);
        toast.error('Failed to load profile');
      }
    }
  };

  const handleUpdateName = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const token = localStorage.getItem('token');
    
    try {
      const res = await axios.patch(
        '/api/v1/users/me',
        { full_name: fullName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setUser(res.data);
      toast.success('Display name updated successfully');
    } catch (err) {
      toast.error('Failed to update display name');
    } finally {
      setSaving(false);
    }
  };

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file size (5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('File size must be less than 5MB');
      return;
    }

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('File must be an image');
      return;
    }

    setUploading(true);
    const token = localStorage.getItem('token');

    // Create temporary preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setAvatarPreview(reader.result as string);
    };
    reader.readAsDataURL(file);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await axios.post(
        '/api/v1/users/me/avatar',
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        }
      );
      
      // Update user state and preview with server URL
      setUser(res.data);
      setAvatarPreview(res.data.avatar_url); // ← Use server URL instead of local preview
      toast.success('Avatar updated successfully');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Failed to upload avatar');
      // Revert preview on error
      setAvatarPreview(user?.avatar_url || null);
    } finally {
      setUploading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  if (!user) {
    return (
      <ProtectedLayout>
        <div className="min-h-full flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent"></div>
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="min-h-full p-4 md:p-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <h1 className="text-4xl font-bold bg-gradient-brand bg-clip-text text-transparent mb-2">
              Account Settings
            </h1>
            <p className="text-foreground-muted">
              Manage your profile information and preferences
            </p>
          </motion.div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Avatar Section */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="lg:col-span-1"
            >
              <GlassCard className="p-6 sticky top-8 flex flex-col items-center text-center">
                {/* Avatar */}
                <div className="relative group mb-6">
                  <div className="w-40 h-40 rounded-full overflow-hidden ring-4 ring-glass-border shadow-lg relative bg-glass-bg">
                    {avatarPreview ? (
                      <img
                        src={avatarPreview}
                        alt="Avatar"
                        className="w-full h-full object-cover"
                      />
                    ) : (
                      <div className="w-full h-full bg-gradient-brand flex items-center justify-center">
                        <UserIcon className="w-20 h-20 text-white" />
                      </div>
                    )}
                    
                    {uploading && (
                      <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                      </div>
                    )}
                  </div>

                  {/* Edit Button Overlay */}
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={uploading}
                    className="absolute bottom-2 right-2 bg-gradient-brand text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all transform hover:scale-110 disabled:opacity-50"
                  >
                    <Camera className="w-5 h-5" />
                  </button>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                    className="hidden"
                  />
                </div>

                {/* User Details */}
                <div className="mb-6">
                  <h3 className="font-semibold text-lg text-foreground mb-1">
                    {user.full_name || 'Set your name'}
                  </h3>
                  <p className="text-sm text-foreground-muted">
                    {user.email}
                  </p>
                </div>

                <div className="w-full p-4 rounded-xl bg-accent/5 border border-accent/10 mb-6">
                  <div className="flex items-start gap-3 text-sm">
                    <Upload className="w-4 h-4 mt-0.5 flex-shrink-0 text-accent" />
                    <div className="text-left">
                      <p className="font-medium text-foreground mb-1">
                        Upload new avatar
                      </p>
                      <p className="text-xs text-foreground-muted">
                        Max size: 5MB<br/>Formats: JPG, PNG, GIF
                      </p>
                    </div>
                  </div>
                </div>

                {/* Account Stats */}
                <div className="w-full pt-6 border-t border-glass-border space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-foreground-muted">
                      <Shield className="w-4 h-4" />
                      <span>Role</span>
                    </div>
                    <span className="font-medium text-foreground capitalize bg-glass-border px-2 py-0.5 rounded-lg">
                      {user.role.toLowerCase()}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2 text-foreground-muted">
                      <Calendar className="w-4 h-4" />
                      <span>Joined</span>
                    </div>
                    <span className="font-medium text-foreground">
                      {formatDate(user.created_at)}
                    </span>
                  </div>
                </div>
              </GlassCard>
            </motion.div>

            {/* Profile Form Section */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              className="lg:col-span-2 space-y-6"
            >
              <GlassCard className="p-8">
                <div className="flex items-center gap-4 mb-8 pb-6 border-b border-glass-border">
                  <div className="p-3 bg-gradient-brand rounded-xl shadow-lg shadow-accent/20">
                    <UserIcon className="w-6 h-6 text-white" />
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-foreground">
                      Profile Information
                    </h2>
                    <p className="text-sm text-foreground-muted">
                      Update your personal details and display preferences
                    </p>
                  </div>
                </div>

                <form onSubmit={handleUpdateName} className="space-y-6">
                  {/* Email Field (Read-only) */}
                  <div>
                    <GlassInput
                      label="Email Address"
                      type="email"
                      value={user.email}
                      disabled
                      leftIcon={<Mail size={18} />}
                    />
                    <p className="mt-2 text-xs text-foreground-muted ml-1">
                      Email address is managed by identity provider
                    </p>
                  </div>

                  {/* Display Name Field */}
                  <div>
                    <GlassInput
                      label="Display Name"
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Enter your full name"
                      leftIcon={<UserIcon size={18} />}
                    />
                    <p className="mt-2 text-xs text-foreground-muted ml-1">
                      This is how others will see your name
                    </p>
                  </div>

                  {/* Save Button */}
                  <div className="pt-4 flex justify-end">
                    <GlassButton
                      type="submit"
                      disabled={saving || fullName === user.full_name}
                      isLoading={saving}
                      size="lg"
                      className="w-full md:w-auto min-w-[160px]"
                      leftIcon={<Save size={18} />}
                    >
                      Save Changes
                    </GlassButton>
                  </div>
                </form>
              </GlassCard>

              {/* Tips Card */}
              <GlassCard variant="interactive" className="p-6 border-blue-500/20 bg-blue-500/5">
                <div className="flex gap-4">
                  <div className="p-2 bg-blue-500/20 rounded-lg h-fit text-blue-500">
                    <UserIcon size={20} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-foreground mb-2">
                      Profile Tips
                    </h3>
                    <ul className="text-sm text-foreground-muted space-y-2">
                      <li className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        Use a clear photo for better team recognition
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        Keep your display name professional
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                        Update your profile regularly to keep it fresh
                      </li>
                    </ul>
                  </div>
                </div>
              </GlassCard>
            </motion.div>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  );
}
