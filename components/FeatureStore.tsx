import React, { useState, useEffect } from 'react';
import { Lock, Unlock, CheckSquare, Square, Info } from 'lucide-react';

export interface PremiumFeature {
  id: string;
  title: string;
  description: string;
  price: number;
}

export const AVAILABLE_FEATURES: PremiumFeature[] = [
  {
    id: 'deep-research',
    title: 'Deep Research',
    description: 'Приложение VocalPrint AI предлагает платную функцию дополнительного поиска, который делает Ваш запрос более качественным. ИИ-агент найдет наиболее значимую информацию о вокальной технике исполнителя и самых распротраненных техник обработки вокала. Стоимость 1$',
    price: 1,
  },
];

interface FeatureStoreProps {
  onFeaturesChange?: (activeFeatures: string[]) => void;
  isAdmin?: boolean;
}

const FeatureStore: React.FC<FeatureStoreProps> = ({ onFeaturesChange, isAdmin = false }) => {
  const [unlockedFeatures, setUnlockedFeatures] = useState<string[]>([]);
  const [activeFeatures, setActiveFeatures] = useState<string[]>([]);
  const [balance, setBalance] = useState<number>(0);
  const [shakeId, setShakeId] = useState<string | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [unlockingId, setUnlockingId] = useState<string | null>(null);

  // Sync with localStorage
  useEffect(() => {
    const savedFunds = parseFloat(localStorage.getItem('projectFund') || '0');
    setBalance(savedFunds);

    const savedUnlocked = JSON.parse(localStorage.getItem('unlockedFeatures') || '[]');
    setUnlockedFeatures(savedUnlocked);

    // Sync active features with unlocked ones (auto-enable recently unlocked or let user toggle)
    // For now, let's just make unlocked features inactive by default until toggled
  }, []);

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const syncBalance = (newBalance: number) => {
    setBalance(newBalance);
    localStorage.setItem('projectFund', newBalance.toString());
    // Dispatch event so other components (like SupportModule) can update
    window.dispatchEvent(new Event('storage'));
  };

  const handleToggle = (feature: PremiumFeature) => {
    // If not unlocked, try to buy
    if (!unlockedFeatures.includes(feature.id)) {
      if (isAdmin || balance >= feature.price) {
        // Buy animation
        setUnlockingId(feature.id);

        setTimeout(() => {
          if (!isAdmin) {
            const newBalance = Math.max(0, balance - feature.price);
            syncBalance(newBalance);
          }

          const newUnlocked = [...unlockedFeatures, feature.id];
          setUnlockedFeatures(newUnlocked);
          localStorage.setItem('unlockedFeatures', JSON.stringify(newUnlocked));

          // Auto-activate upon purchase
          const newActive = [...activeFeatures, feature.id];
          setActiveFeatures(newActive);
          onFeaturesChange?.(newActive);

          showToast(`Функция "${feature.title}" разблокирована!`, 'success');
          setUnlockingId(null);
        }, 800); // 800ms unlock animation delay
      } else {
        // Cannot afford
        setShakeId(feature.id);
        showToast('Недостаточно средств на балансе', 'error');
        setTimeout(() => setShakeId(null), 500);
      }
    } else {
      // Already unlocked, just toggle active state
      const isCurrentlyActive = activeFeatures.includes(feature.id);
      const newActive = isCurrentlyActive
        ? activeFeatures.filter(id => id !== feature.id)
        : [...activeFeatures, feature.id];

      setActiveFeatures(newActive);
      onFeaturesChange?.(newActive);
    }
  };

  return (
    <div className="w-full mt-2 font-sans relative">
      <style>{`
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-4px) rotate(-1deg); }
          50% { transform: translateX(4px) rotate(1deg); }
          75% { transform: translateX(-4px) rotate(-1deg); }
        }
        .shake-animation {
          animation: shake 0.4s cubic-bezier(.36, .07, .19, .97) both;
        }
        @keyframes unlock-glow {
          0% { box-shadow: 0 0 0 rgba(255, 255, 255, 0); }
          50% { box-shadow: 0 0 20px rgba(124, 58, 237, 0.6); }
          100% { box-shadow: 0 0 0 rgba(255, 255, 255, 0); }
        }
        .unlocking {
          animation: unlock-glow 0.8s ease-out forwards;
        }
        .toast-enter {
          animation: slideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
        @keyframes slideUp {
          from { transform: translateY(100%) translateX(-50%); opacity: 0; }
          to { transform: translateY(0) translateX(-50%); opacity: 1; }
        }
`}</style>

      {/* Wallet Balance Indicator */}
      <div className="flex justify-between items-center mb-4 px-2">
        <span className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-500/60">Магазин Функций</span>
        <div className={`flex items-center gap-2 text-xs font-medium px-3 py-1 rounded-full border transition-colors duration-300 ${shakeId ? 'bg-red-500/20 border-red-500/50 text-red-400' : 'bg-white/5 border-white/10 text-white/70'}`}>
          <span>Баланс:</span>
          <span className={`font-mono font-bold ${shakeId ? 'text-red-400' : 'text-purple-400'}`}>${balance.toFixed(2)}</span>
        </div>
      </div>

      {/* Feature List */}
      <div className="space-y-3">
        {AVAILABLE_FEATURES.map((feature) => {
          const isUnlocked = unlockedFeatures.includes(feature.id);
          const isActive = activeFeatures.includes(feature.id);
          const isUnlocking = unlockingId === feature.id;
          const isShaking = shakeId === feature.id;

          return (
            <div
              key={feature.id}
              className={`group relative flex items-center p-4 rounded-xl border transition-all duration-300 cursor-pointer overflow-hidden
                ${isShaking ? 'shake-animation border-red-500/50 bg-red-500/5' : ''}
                ${isUnlocking ? 'unlocking bg-purple-500/10 border-purple-500/50' : ''}
                ${!isUnlocked && !isShaking && !isUnlocking ? 'bg-black/40 border-white/5 hover:bg-white/5 hover:border-white/10' : ''}
                ${isUnlocked && isActive ? 'bg-gradient-to-r from-pink-500/10 to-purple-500/10 border-pink-500/30' : ''}
                ${isUnlocked && !isActive ? 'bg-white/5 border-white/10 opacity-70 hover:opacity-100' : ''}
              `}
              onClick={() => handleToggle(feature)}
            >
              {/* Checkbox / Lock Icon */}
              <div className="mr-4 flex-shrink-0 transition-transform group-active:scale-95">
                {!isUnlocked ? (
                  <div className="w-6 h-6 rounded-md bg-white/5 border border-white/10 flex items-center justify-center text-white/40 group-hover:text-purple-400 group-hover:border-purple-500/50 transition-colors">
                    <Lock className="w-3.5 h-3.5" />
                  </div>
                ) : isActive ? (
                  <CheckSquare className="w-6 h-6 text-pink-500" />
                ) : (
                  <Square className="w-6 h-6 text-white/30 group-hover:text-white/60" />
                )}
              </div>

              {/* Title, Description & Price */}
              <div className="flex-grow flex items-start justify-between gap-4">
                <div className="flex flex-col gap-1 w-full max-w-[500px]">
                  <span className={`font-semibold text-sm transition-colors ${isUnlocked ? (isActive ? 'text-pink-100' : 'text-white/80') : 'text-white/60'}`}>
                    {feature.title}
                  </span>

                  {/* Show description if NOT active */}
                  {(!isUnlocked || !isActive) && (
                    <p className="text-[10px] text-white/50 leading-relaxed font-serif mt-1">
                      {feature.description}
                    </p>
                  )}
                </div>

                {/* Status Badge */}
                <div className="flex-shrink-0">
                  {!isUnlocked ? (
                    <span className="flex items-center gap-1.5 px-2.5 py-1 rounded border border-purple-500/30 bg-purple-500/10 text-purple-300 text-[10px] font-bold uppercase tracking-wider group-hover:bg-purple-500 group-hover:text-white transition-colors">
                      {isUnlocking ? 'Открываем...' : `$${feature.price}`}
                    </span>
                  ) : (
                    <span className={`flex items-center gap-1 px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-widest transition-colors ${isActive ? 'text-pink-400 bg-pink-400/10' : 'text-white/30'}`}>
                      {isActive ? 'Active' : 'Unlocked'}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Toast Notification Container */}
      {toast && (
        <div className="fixed bottom-8 left-1/2 z-[100] toast-enter">
          <div className={`flex items-center gap-3 px-5 py-3 rounded-2xl shadow-2xl border backdrop-blur-xl ${toast.type === 'success'
            ? 'bg-emerald-950/80 border-emerald-500/30 text-emerald-400'
            : 'bg-red-950/80 border-red-500/30 text-red-400'
            }`}>
            {toast.type === 'success' ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
            <span className="font-semibold text-sm tracking-wide">{toast.message}</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default FeatureStore;
