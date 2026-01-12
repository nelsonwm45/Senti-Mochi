'use client';

import { motion } from 'framer-motion';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useEffect, useState } from 'react';

// Simulated data for now
const TICKERS = [
  { symbol: 'MAYBANK', price: 9.88, change: 0.5, type: 'up' },
  { symbol: 'CIMB', price: 6.54, change: -0.2, type: 'down' },
  { symbol: 'TENAGA', price: 11.20, change: 1.1, type: 'up' },
  { symbol: 'PCHEM', price: 6.88, change: 0.0, type: 'neutral' },
  { symbol: 'IHH', price: 6.05, change: -0.4, type: 'down' },
  { symbol: 'PBBANK', price: 4.25, change: 0.2, type: 'up' },
];

export function MarketTicker() {
  return (
    <div className="w-full bg-glass-surface/50 border-y border-glass-border overflow-hidden py-2">
      <div className="flex gap-8 animate-scroll whitespace-nowrap">
        {[...TICKERS, ...TICKERS, ...TICKERS].map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <span className="font-bold text-accent">{item.symbol}</span>
            <span className="text-foreground text-sm">{item.price.toFixed(2)}</span>
            <span className={`text-xs flex items-center ${
              item.type === 'up' ? 'text-green-500' : 
              item.type === 'down' ? 'text-red-500' : 'text-gray-400'
            }`}>
              {item.type === 'up' && <TrendingUp size={12} className="mr-0.5" />}
              {item.type === 'down' && <TrendingDown size={12} className="mr-0.5" />}
              {item.type === 'neutral' && <Minus size={12} className="mr-0.5" />}
              {item.change > 0 ? '+' : ''}{item.change}%
            </span>
          </div>
        ))}
      </div>
      <style jsx>{`
        .animate-scroll {
          animation: scroll 30s linear infinite;
        }
        @keyframes scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
      `}</style>
    </div>
  );
}
