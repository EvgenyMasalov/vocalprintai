import React, { useState } from 'react';
import { authService } from '../services/authService';
import { X } from 'lucide-react';

interface AuthModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSuccess: (username: string) => void;
}

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [adminSecret, setAdminSecret] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                await authService.login(username, password);
                onSuccess(username);
            } else {
                await authService.register(username, email, password, adminSecret);
                // Automatically login after registration
                await authService.login(username, password);
                onSuccess(username);
            }
            onClose();
        } catch (err: any) {
            setError(err.message || 'Authentication failed');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <div className="baroque-panel max-w-md w-full p-8 md:p-12 relative animate-in fade-in zoom-in duration-300">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-pink-500/50 hover:text-pink-500 transition-colors"
                >
                    <X size={24} />
                </button>

                <h2 className="text-3xl font-baroque text-pink-500 text-center uppercase tracking-widest mb-8 pink-glow">
                    {isLogin ? 'Вход в Систему' : 'Регистрация'}
                </h2>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-500/60">Логин</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            className="w-full bg-black/50 border border-pink-500/20 p-3 text-white focus:outline-none focus:border-pink-500 transition-colors font-serif italic"
                        />
                    </div>

                    {!isLogin && (
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-500/60">Email</label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                required
                                className="w-full bg-black/50 border border-pink-500/20 p-3 text-white focus:outline-none focus:border-pink-500 transition-colors font-serif italic"
                            />
                        </div>
                    )}

                    <div className="space-y-1">
                        <label className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-500/60">Пароль</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            className="w-full bg-black/50 border border-pink-500/20 p-3 text-white focus:outline-none focus:border-pink-500 transition-colors font-serif italic"
                        />
                    </div>

                    {!isLogin && (
                        <div className="space-y-1">
                            <label className="text-[10px] font-black uppercase tracking-[0.2em] text-pink-500/60">Admin Secret (Необязательно)</label>
                            <input
                                type="password"
                                value={adminSecret}
                                onChange={(e) => setAdminSecret(e.target.value)}
                                className="w-full bg-black/50 border border-pink-500/20 p-3 text-white focus:outline-none focus:border-pink-500 transition-colors font-serif italic"
                            />
                        </div>
                    )}

                    {error && (
                        <div className="text-red-500 text-[10px] uppercase font-bold tracking-wider text-center bg-red-500/10 p-2 border border-red-500/20">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full py-4 bg-[#ff2d75] text-black font-baroque font-black text-xs uppercase tracking-[0.3em] hover:bg-white transition-all shadow-[0_0_20px_rgba(255,45,117,0.3)] disabled:opacity-50"
                    >
                        {loading ? 'Обработка...' : (isLogin ? 'Войти' : 'Создать Аккаунт')}
                    </button>
                </form>

                <div className="mt-8 text-center">
                    <button
                        onClick={() => setIsLogin(!isLogin)}
                        className="text-pink-500/60 hover:text-pink-500 text-[10px] uppercase tracking-widest transition-colors font-bold"
                    >
                        {isLogin ? 'У вас нет аккаунта? Зарегистрироваться' : 'Уже есть аккаунт? Войти'}
                    </button>
                </div>

                <div className="mt-8 flex items-center gap-4">
                    <div className="h-px flex-1 bg-pink-500/10"></div>
                    <span className="text-[9px] font-black text-pink-500/30 uppercase tracking-[0.3em]">OR LOGIN WITH</span>
                    <div className="h-px flex-1 bg-pink-500/10"></div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-4">
                    <button
                        onClick={async () => {
                            setLoading(true);
                            try {
                                const res = await authService.mockSocialLogin('Google');
                                onSuccess(res.username);
                                onClose();
                            } catch (err: any) {
                                setError(err.message);
                            } finally {
                                setLoading(false);
                            }
                        }}
                        disabled={loading}
                        className="flex items-center justify-center gap-3 py-3 border border-pink-500/20 hover:border-pink-500/50 hover:bg-pink-500/5 transition-all group"
                    >
                        <svg className="w-4 h-4 text-pink-500/40 group-hover:text-pink-500 transition-colors" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12.48 10.92v3.28h7.84c-.24 1.84-.94 3.16-1.92 4.16-1.12 1.12-2.88 2.32-5.92 2.32-4.72 0-8.52-3.84-8.52-8.56S7.76 3.56 12.48 3.56c2.56 0 4.48.96 5.8 2.24l2.32-2.32C18.6 1.64 15.96 0 12.48 0 5.56 0 0 5.6 0 12.52s5.56 12.52 12.48 12.52c3.76 0 6.6-1.24 8.84-3.56 2.32-2.32 3.12-5.56 3.12-8.24 0-.48-.04-1-.12-1.44H12.48z" />
                        </svg>
                        <span className="text-[10px] font-black uppercase tracking-widest text-pink-500/60 group-hover:text-pink-500">Google</span>
                    </button>
                    <button
                        onClick={async () => {
                            setLoading(true);
                            try {
                                const res = await authService.mockSocialLogin('GitHub');
                                onSuccess(res.username);
                                onClose();
                            } catch (err: any) {
                                setError(err.message);
                            } finally {
                                setLoading(false);
                            }
                        }}
                        disabled={loading}
                        className="flex items-center justify-center gap-3 py-3 border border-pink-500/20 hover:border-pink-500/50 hover:bg-pink-500/5 transition-all group"
                    >
                        <svg className="w-4 h-4 text-pink-500/40 group-hover:text-pink-500 transition-colors" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                        </svg>
                        <span className="text-[10px] font-black uppercase tracking-widest text-pink-500/60 group-hover:text-pink-500">GitHub</span>
                    </button>
                </div>
            </div>
        </div>
    );
};

export default AuthModal;
