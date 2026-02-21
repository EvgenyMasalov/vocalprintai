import React, { useState, useEffect, useRef } from 'react';
import { Heart, Server, Zap, Sparkles, CheckCircle, Shield } from 'lucide-react';

const SupportModule: React.FC = () => {
  const GOAL = 1000;
  const [projectFund, setProjectFund] = useState(0);
  const [selectedAmount, setSelectedAmount] = useState<number | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusText, setStatusText] = useState<string | null>(null);
  const [milestone, setMilestone] = useState<string | null>(null);
  const balanceDisplayRef = useRef<HTMLSpanElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem('projectFund');
    if (saved) {
      setProjectFund(parseFloat(saved));
    }
  }, []);

  const launchConfetti = () => {
    const colors = ['#7c3aed', '#818cf8', '#34d399', '#fbbf24', '#f472b6', '#60a5fa'];
    const count = 60;
    for (let i = 0; i < count; i++) {
      setTimeout(() => {
        const p = document.createElement('div');
        // We'll style the particle dynamically
        p.className = 'confetti-particle absolute pointer-events-none z-[9999]';
        const x = Math.random() * window.innerWidth;
        const fallY = (200 + Math.random() * 400) + 'px';
        const fallX = (Math.random() * 200 - 100) + 'px';
        const rot = (Math.random() * 720 - 360) + 'deg';
        const dur = (0.8 + Math.random() * 0.8) + 's';

        p.style.cssText = `
          left: ${x}px; 
          top: ${Math.random() * window.innerHeight * 0.4}px;
          background: ${colors[Math.floor(Math.random() * colors.length)]};
          --fall-y: ${fallY}; 
          --fall-x: ${fallX};
          --rotation: ${rot};
          width: 8px;
          height: 8px;
          border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
          animation: confetti-fall ${dur} cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
        `;
        document.body.appendChild(p);
        setTimeout(() => p.remove(), 1600);
      }, i * 18);
    }
  };

  const animateValue = (start: number, end: number, duration: number) => {
    if (!balanceDisplayRef.current) return;
    const el = balanceDisplayRef.current;
    let startTimestamp: number | null = null;

    el.classList.add('scale-110', 'text-purple-400');
    setTimeout(() => el.classList.remove('scale-110', 'text-purple-400'), 300);

    const step = (timestamp: number) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(start + (end - start) * ease);
      el.innerHTML = current.toString();
      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        el.innerHTML = end.toString();
      }
    };
    window.requestAnimationFrame(step);
  };

  const checkMilestone = (newFund: number) => {
    const pct = (newFund / GOAL) * 100;
    const milestones = [
      { pct: 10, msg: '10% — Первый шаг сделан!' },
      { pct: 25, msg: '25% — Уже четверть пути 🎯' },
      { pct: 50, msg: '50% — Половина! Отлично 🔥' },
      { pct: 75, msg: '75% — Почти у цели 💎' },
      { pct: 100, msg: '🎉 Цель достигнута!' },
    ];
    const hit = [...milestones].reverse().find(m => pct >= m.pct);
    if (hit) {
      setMilestone(hit.msg);
    }
  };

  const handleDonate = () => {
    if (!selectedAmount || isProcessing) return;
    setIsProcessing(true);
    setStatusText('processing');

    setTimeout(() => {
      const newFund = Math.min(projectFund + selectedAmount, GOAL);
      setProjectFund(newFund);
      localStorage.setItem('projectFund', newFund.toString());

      setStatusText('success');
      animateValue(projectFund, newFund, 800);
      launchConfetti();
      checkMilestone(newFund);

      setTimeout(() => {
        setStatusText(null);
        setSelectedAmount(null);
        setIsProcessing(false);
      }, 2000);

    }, 1500);
  };

  const progressPct = Math.min((projectFund / GOAL) * 100, 100).toFixed(1);

  return (
    <>
      <style>{`
        .glass-card {
          background: rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(24px);
          -webkit-backdrop-filter: blur(24px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }
        @keyframes pulse-glow {
          0%, 100% { box-shadow: 0 0 20px rgba(124,58,237,0.4); }
          50% { box-shadow: 0 0 40px rgba(124,58,237,0.8); }
        }
        @keyframes confetti-fall {
          0% { transform: translateY(0) translateX(0) rotate(0deg); opacity: 1; }
          100% { transform: translateY(var(--fall-y)) translateX(var(--fall-x)) rotate(var(--rotation)); opacity: 0; }
        }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
        .progress-bar-inner {
          background: linear-gradient(90deg, #7c3aed, #818cf8, #7c3aed);
          background-size: 200% 100%;
          animation: shimmer 2s linear infinite;
          transition: width 1s cubic-bezier(0.4, 0, 0.2, 1);
        }
        @keyframes dot-blink { 0%,100%{opacity:0.2} 50%{opacity:1} }
        .dot-pulse {
          width: 6px; height: 6px; border-radius: 50%;
          background: currentColor;
          animation: dot-blink 1s ease-in-out infinite;
        }
      `}</style>

      <div className="w-full max-w-md mx-auto mt-16 font-sans">
        <div className="glass-card rounded-3xl p-8 relative overflow-hidden">
          {/* Header */}
          <div className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-2xl flex items-center justify-center bg-gradient-to-br from-purple-600 to-indigo-600">
              <Heart className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-white font-semibold text-lg leading-tight">Поддержать проект</h2>
              <p className="text-white/40 text-xs">VocalPrint AI</p>
            </div>
            <div className="ml-auto">
              <span className="text-white/20 text-xs">MVP</span>
            </div>
          </div>

          {/* Balance */}
          <div className="mb-6 text-center">
            <p className="text-white/40 text-xs uppercase tracking-widest mb-1">Собрано</p>
            <div className="flex items-baseline justify-center gap-1">
              <span className="text-white/60 text-2xl font-light">$</span>
              <span
                ref={balanceDisplayRef}
                className="text-white text-5xl font-bold transition-all duration-300 transform"
              >
                {projectFund}
              </span>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-white/50 text-xs flex items-center gap-1">
                <Server className="w-3 h-3" /> На серверы
              </span>
              <span className="text-white/50 text-xs">${projectFund} / ${GOAL}</span>
            </div>
            <div className="h-2 rounded-full overflow-hidden bg-white/10">
              <div
                className="h-full rounded-full progress-bar-inner"
                style={{ width: `${progressPct}%` }}
              ></div>
            </div>
            {milestone && (
              <div className="mt-3 animate-in slide-in-from-bottom-2 fade-in duration-500">
                <div className="flex items-center gap-2 w-fit px-3 py-1.5 rounded-full text-[11px] font-medium bg-emerald-500/15 border border-emerald-500/30 text-emerald-400">
                  <Zap className="w-3 h-3" />
                  <span>{milestone}</span>
                </div>
              </div>
            )}
          </div>

          <div className="border-t border-white/5 mb-6"></div>

          {/* Chips */}
          <p className="text-white/40 text-xs uppercase tracking-widest mb-3">Выбери сумму</p>
          <div className="flex gap-3 mb-6">
            {[
              { amount: 5, icon: '☕' },
              { amount: 15, icon: '🍕' },
              { amount: 50, icon: '🚀' },
            ].map(({ amount, icon }) => (
              <button
                key={amount}
                onClick={() => !isProcessing && setSelectedAmount(amount)}
                className={`flex-1 py-3 rounded-2xl text-sm font-medium flex flex-col items-center gap-1 transition-all duration-300
                  ${selectedAmount === amount
                    ? 'bg-gradient-to-br from-purple-600 to-indigo-600 text-white shadow-[0_0_20px_rgba(124,58,237,0.5)] scale-105 border-transparent'
                    : 'bg-white/5 text-white border border-white/10 hover:bg-white/10 hover:-translate-y-1'
                  }`}
              >
                <span className="text-lg">{icon}</span>
                <span>${amount}</span>
              </button>
            ))}
          </div>

          {/* Status Area */}
          <div className="mb-4 h-8 flex items-center justify-center">
            {statusText === 'processing' && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-amber-500/15 border border-amber-500/30 text-amber-500">
                <div className="dot-pulse"></div>
                Processing...
              </div>
            )}
            {statusText === 'success' && (
              <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 animate-in zoom-in duration-300">
                <CheckCircle className="w-3 h-3" />
                Донат засчитан! Спасибо ❤️
              </div>
            )}
          </div>

          {/* Donate Button */}
          <button
            onClick={handleDonate}
            disabled={!selectedAmount || isProcessing}
            className={`w-full py-4 rounded-2xl text-white font-semibold text-sm transition-all duration-300 relative overflow-hidden
              ${isProcessing ? 'animate-[pulse-glow_1s_ease-in-out_infinite]' : ''}
              ${!selectedAmount || isProcessing
                ? 'bg-white/10 opacity-50 cursor-not-allowed'
                : 'bg-gradient-to-br from-purple-600 to-indigo-600 hover:scale-[1.02] hover:shadow-[0_8px_30px_rgba(124,58,237,0.6)] active:scale-95'
              }`}
          >
            <span className="flex items-center justify-center gap-2 relative z-10">
              <Sparkles className="w-4 h-4" />
              Поддержать
            </span>
          </button>

          {/* Footer note */}
          <p className="text-center text-white/20 text-xs mt-5 flex items-center justify-center gap-1">
            <Shield className="w-3 h-3" />
            Тестовый режим · Данные хранятся локально
          </p>
        </div>
      </div>
    </>
  );
};

export default SupportModule;
