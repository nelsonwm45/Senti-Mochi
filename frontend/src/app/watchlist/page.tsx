'use client';

import { useEffect, useState } from 'react';
import ProtectedLayout from '@/components/layouts/ProtectedLayout';
import { watchlistApi, WatchlistItem } from '@/lib/api/watchlist';
import { GlassCard } from '@/components/ui/GlassCard';
import { GlassButton } from '@/components/ui/GlassButton';
import { Loader2, Star, Trash2 } from 'lucide-react';
import Link from 'next/link';

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchWatchlist();
  }, []);

  const fetchWatchlist = async () => {
    try {
        const data = await watchlistApi.getAll();
        setItems(data);
    } catch (err) {
        console.error(err);
    } finally {
        setLoading(false);
    }
  };

  const handleRemove = async (id: string) => {
      try {
          await watchlistApi.remove(id);
          setItems(prev => prev.filter(i => i.id !== id));
      } catch (err) {
          console.error(err);
      }
  };

  if (loading) {
    return (
      <ProtectedLayout>
        <div className="flex justify-center items-center h-full">
            <Loader2 className="animate-spin text-accent" size={32} />
        </div>
      </ProtectedLayout>
    );
  }

  return (
    <ProtectedLayout>
      <div className="space-y-6">
        <div className="flex items-center gap-3">
            <div className="p-3 bg-yellow-500/10 rounded-xl text-yellow-500">
                <Star size={24} />
            </div>
            <div>
                <h1 className="text-2xl font-bold text-foreground">My Watchlist</h1>
                <p className="text-foreground-muted">Track your favorite companies</p>
            </div>
        </div>

        {items.length === 0 ? (
            <div className="text-center py-12">
                <p className="text-foreground-muted mb-4">You are not watching any companies yet.</p>
                <Link href="/dashboard">
                    <GlassButton variant="primary">Browse Market</GlassButton>
                </Link>
            </div>
        ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {items.map((item) => (
                    <GlassCard key={item.id} className="p-6 relative group">
                        <Link href={`/companies/${item.company.id}`} className="block">
                            <div className="flex justify-between items-start mb-4">
                                <span className="font-mono bg-accent/10 text-accent px-2 py-1 rounded text-sm">
                                    {item.company.ticker}
                                </span>
                            </div>
                            <h3 className="text-lg font-bold text-foreground mb-1 group-hover:text-accent transition-colors">
                                {item.company.name}
                            </h3>
                            <p className="text-sm text-foreground-muted">{item.company.sector}</p>
                        </Link>
                        
                        <button 
                            onClick={(e) => {
                                e.preventDefault();
                                handleRemove(item.id);
                            }}
                            className="absolute top-6 right-6 p-2 text-foreground-muted hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors opacity-0 group-hover:opacity-100"
                        >
                            <Trash2 size={16} />
                        </button>
                    </GlassCard>
                ))}
            </div>
        )}
      </div>
    </ProtectedLayout>
  );
}
