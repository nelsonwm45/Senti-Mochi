'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { motion } from 'framer-motion';
import { Save, Bot, Target, AlertTriangle, DollarSign, Sparkles, User } from 'lucide-react';
import { toast } from 'react-hot-toast';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';

interface Profile {
  financial_goals: string;
  risk_tolerance: string;
  assets_value: number;
}

export default function Profile() {
  const [profile, setProfile] = useState<Profile>({
    financial_goals: '',
    risk_tolerance: 'Medium',
    assets_value: 0
  });
  const [advice, setAdvice] = useState('');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      axios.get('http://localhost:8000/users/profile', {
        headers: { Authorization: `Bearer ${token}` }
      }).then(res => {
        if (res.data) setProfile(res.data);
      }).catch(err => console.error(err));
    }
  }, []);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    const token = localStorage.getItem('token');
    try {
      await axios.post('http://localhost:8000/users/profile', profile, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Profile updated successfully');
    } catch (err) {
      toast.error('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const getAdvice = async () => {
    setLoading(true);
    const token = localStorage.getItem('token');
    try {
      const res = await axios.post('http://localhost:8000/users/advice', {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAdvice(res.data.advice);
    } catch (err) {
      toast.error('Could not generate advice. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { 
      y: 0, 
      opacity: 1,
      transition: { type: 'spring', stiffness: 100 }
    }
  };

  return (
    <ProtectedLayout>
      <div className="min-h-full bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 p-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center space-x-3 mb-2">
              <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl">
                <User className="w-8 h-8 text-white" />
              </div>
              <h1 className="text-4xl font-bold text-gray-900 dark:text-white">
                Your Profile
              </h1>
            </div>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Manage your financial preferences and get personalized AI advice
            </p>
          </div>

          <motion.div 
            className="grid grid-cols-1 md:grid-cols-2 gap-8"
            initial="hidden"
            animate="visible"
            variants={containerVariants}
          >
            {/* Profile Form Card */}
            <motion.div 
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
              variants={itemVariants}
            >
              <div className="flex items-center space-x-2 mb-6">
                <Target className="w-6 h-6 text-purple-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  Financial Profile
                </h2>
              </div>
              
              <form onSubmit={handleUpdate} className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Financial Goals
                  </label>
                  <textarea 
                    className="w-full h-32 bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all resize-none"
                    value={profile.financial_goals || ''}
                    onChange={(e) => setProfile({...profile, financial_goals: e.target.value})}
                    placeholder="e.g. Retire by 50, buy a house in 2 years..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Risk Tolerance
                  </label>
                  <div className="relative">
                    <AlertTriangle className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                    <select 
                      className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl py-3 pl-12 pr-4 text-gray-900 dark:text-white appearance-none focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all cursor-pointer"
                      value={profile.risk_tolerance || 'Medium'}
                      onChange={(e) => setProfile({...profile, risk_tolerance: e.target.value})}
                    >
                      <option value="Low">Low - Conservative</option>
                      <option value="Medium">Medium - Balanced</option>
                      <option value="High">High - Aggressive</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Total Assets Value ($)
                  </label>
                  <div className="relative">
                    <DollarSign className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
                    <input 
                      type="number" 
                      className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl py-3 pl-12 pr-4 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                      value={profile.assets_value || 0}
                      onChange={(e) => setProfile({...profile, assets_value: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>

                <button 
                  type="submit" 
                  disabled={saving}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl py-3 font-semibold hover:shadow-lg hover:shadow-purple-500/25 transition-all flex items-center justify-center space-x-2 disabled:opacity-70"
                >
                  {saving ? (
                    <span>Saving...</span>
                  ) : (
                    <>
                      <Save className="w-5 h-5" />
                      <span>Save Profile</span>
                    </>
                  )}
                </button>
              </form>
            </motion.div>

            {/* AI Advisor Card */}
            <motion.div 
              className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 flex flex-col h-full"
              variants={itemVariants}
            >
              <div className="flex items-center space-x-2 mb-6">
                <Bot className="w-6 h-6 text-cyan-500" />
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  AI Advisor
                </h2>
              </div>
              
              <div className="flex-1">
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  Based on your goals and risk profile, our AI generates personalized financial advice tailored specifically to your situation.
                </p>
                
                {advice && (
                  <motion.div 
                    className="bg-purple-50 dark:bg-purple-900/10 border border-purple-100 dark:border-purple-500/20 rounded-xl p-6 mb-6"
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                  >
                    <div className="flex items-center space-x-2 mb-3 text-purple-600 dark:text-purple-400 font-semibold">
                      <Sparkles className="w-5 h-5" />
                      <span>Strategic Insight</span>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                      {advice}
                    </p>
                  </motion.div>
                )}
              </div>

              <button 
                onClick={getAdvice} 
                disabled={loading}
                className={`w-full text-white rounded-xl py-3 font-semibold transition-all flex items-center justify-center space-x-2 ${
                  loading 
                    ? 'bg-gray-500 cursor-not-allowed' 
                    : 'bg-gradient-to-r from-cyan-500 to-blue-500 hover:shadow-lg hover:shadow-cyan-500/25'
                }`}
              >
                {loading ? (
                  <div className="flex items-center space-x-2">
                    <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Analyzing...</span>
                  </div>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5" />
                    <span>Generate AI Advice</span>
                  </>
                )}
              </button>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </ProtectedLayout>
  )
}
