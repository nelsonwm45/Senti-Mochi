'use client';
import { useEffect, useState } from 'react';
import axios from 'axios';
import { useRouter } from 'next/navigation';
import { motion } from 'framer-motion';
import { Save, Bot, Target, AlertTriangle, DollarSign, Sparkles } from 'lucide-react';

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
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }
    
    // Fetch profile
    axios.get('http://localhost:8000/users/profile', {
      headers: { Authorization: `Bearer ${token}` }
    }).then(res => {
      if (res.data) setProfile(res.data);
    }).catch(err => console.error(err));
  }, [router]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem('token');
    try {
      await axios.post('http://localhost:8000/users/profile', profile, {
        headers: { Authorization: `Bearer ${token}` }
      });
      alert('Profile updated');
    } catch (err) {
      alert('Update failed');
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
      alert('Could not get advice');
    } finally {
      setLoading(false);
    }
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { 
        staggerChildren: 0.2
      }
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
    <motion.div 
      className="container" 
      style={{ marginTop: '2rem', paddingBottom: '3rem' }}
      initial="hidden"
      animate="visible"
      variants={containerVariants}
    >
      <div className="grid-layout">
        <motion.div className="glass-card" variants={itemVariants}>
          <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Target className="text-primary" size={24} style={{ color: '#8b5cf6' }} />
            Financial Profile
          </h2>
          <form onSubmit={handleUpdate}>
            <div className="form-group">
              <label className="label">Financial Goals</label>
              <textarea 
                className="input-field" 
                style={{ minHeight: '120px', resize: 'vertical' }}
                value={profile.financial_goals || ''}
                onChange={(e) => setProfile({...profile, financial_goals: e.target.value})}
                placeholder="e.g. Retire by 50, buy a house in 2 years..."
              />
            </div>
            <div className="form-group">
              <label className="label">Risk Tolerance</label>
              <div style={{ position: 'relative' }}>
                <AlertTriangle size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                <select 
                  className="input-field"
                  style={{ paddingLeft: '2.5rem' }}
                  value={profile.risk_tolerance || 'Medium'}
                  onChange={(e) => setProfile({...profile, risk_tolerance: e.target.value})}
                >
                  <option value="Low" style={{color: 'black'}}>Low</option>
                  <option value="Medium" style={{color: 'black'}}>Medium</option>
                  <option value="High" style={{color: 'black'}}>High</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label className="label">Total Assets Value ($)</label>
              <div style={{ position: 'relative' }}>
                <DollarSign size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#94a3b8' }} />
                <input 
                  type="number" 
                  className="input-field"
                  style={{ paddingLeft: '2.5rem' }}
                  value={profile.assets_value || 0}
                  onChange={(e) => setProfile({...profile, assets_value: parseFloat(e.target.value)})}
                />
              </div>
            </div>
            <button type="submit" className="btn-primary" style={{ width: '100%' }}>
              <Save size={18} /> Save Profile
            </button>
          </form>
        </motion.div>

        <motion.div className="glass-card" variants={itemVariants}>
          <h2 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <Bot size={24} style={{ color: '#06b6d4' }} />
            AI Advisor
          </h2>
          <p style={{ marginBottom: '1rem', color: '#94a3b8' }}>
            Based on your goals and risk profile, our AI generates personalized financial advice.
          </p>
          
          {advice && (
            <motion.div 
              style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '1rem', marginBottom: '1.5rem', whiteSpace: 'pre-wrap', border: '1px solid var(--glass-border)', lineHeight: 1.6 }}
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
            >
              <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem', color: '#8b5cf6', fontWeight: 600 }}>
                <Sparkles size={18} /> Insight
              </div>
              {advice}
            </motion.div>
          )}

          <button 
            onClick={getAdvice} 
            className="btn-primary" 
            disabled={loading}
            style={{ width: '100%', background: loading ? '#4b5563' : 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)' }}
          >
            {loading ? (
              <motion.span animate={{ opacity: [0.5, 1, 0.5] }} transition={{ duration: 1.5, repeat: Infinity }}>
                Analyzing...
              </motion.span>
            ) : (
              <>
                <Sparkles size={18} /> Get AI Advice
              </>
            )}
          </button>
        </motion.div>
      </div>
    </motion.div>
  )
}
