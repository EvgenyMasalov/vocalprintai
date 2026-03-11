import React, { useState, useEffect } from 'react';
import { adminService, AdminClient, AdminGeneration } from '../services/adminService';
import { Users, FileText, Upload, ChevronLeft, Calendar, User as UserIcon } from 'lucide-react';

interface AdminCMSProps {
    onBack: () => void;
}

const AdminCMS: React.FC<AdminCMSProps> = ({ onBack }) => {
    const [activeTab, setActiveTab] = useState<'clients' | 'generations' | 'rag'>('clients');
    const [clients, setClients] = useState<AdminClient[]>([]);
    const [generations, setGenerations] = useState<AdminGeneration[]>([]);
    const [loading, setLoading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState<string>('');

    useEffect(() => {
        if (activeTab === 'clients') fetchClients();
        if (activeTab === 'generations') fetchGenerations();
    }, [activeTab]);

    const fetchClients = async () => {
        setLoading(true);
        try {
            const data = await adminService.getClients();
            setClients(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const fetchGenerations = async () => {
        setLoading(true);
        try {
            const data = await adminService.getGenerations();
            setGenerations(data);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setUploadStatus('Загрузка...');
            try {
                await adminService.uploadRagFile(e.target.files[0]);
                setUploadStatus('Файл успешно загружен в систему RAG');
            } catch (error) {
                setUploadStatus('Ошибка загрузки');
            }
        }
    };

    return (
        <div className="flex min-h-screen bg-[#050505] text-[#fce7f3] font-serif">
            {/* Sidebar */}
            <div className="w-64 border-r border-pink-500/10 p-6 flex flex-col gap-8 bg-black/50 backdrop-blur-xl">
                <button onClick={onBack} className="flex items-center gap-2 text-[10px] font-black uppercase tracking-widest text-pink-500/60 hover:text-pink-500 transition-colors">
                    <ChevronLeft size={14} /> Назад
                </button>

                <h2 className="text-2xl font-baroque pink-glow mb-4">Admin Core</h2>

                <nav className="flex flex-col gap-2">
                    <button
                        onClick={() => setActiveTab('clients')}
                        className={`flex items-center gap-3 p-3 text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'clients' ? 'bg-pink-500 text-black shadow-[0_0_20px_rgba(255,45,117,0.3)]' : 'border border-pink-500/20 text-pink-500 hover:bg-pink-500/5'}`}
                    >
                        <Users size={16} /> Пользователи
                    </button>
                    <button
                        onClick={() => setActiveTab('generations')}
                        className={`flex items-center gap-3 p-3 text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'generations' ? 'bg-pink-500 text-black shadow-[0_0_20px_rgba(255,45,117,0.3)]' : 'border border-pink-500/20 text-pink-500 hover:bg-pink-500/5'}`}
                    >
                        <FileText size={16} /> Генерации
                    </button>
                    <button
                        onClick={() => setActiveTab('rag')}
                        className={`flex items-center gap-3 p-3 text-[10px] font-black uppercase tracking-widest transition-all ${activeTab === 'rag' ? 'bg-pink-500 text-black shadow-[0_0_20px_rgba(255,45,117,0.3)]' : 'border border-pink-500/20 text-pink-500 hover:bg-pink-500/5'}`}
                    >
                        <Upload size={16} /> Система RAG
                    </button>
                </nav>
            </div>

            {/* Main Content */}
            <div className="flex-1 p-12 overflow-y-auto">
                {activeTab === 'clients' && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <div className="flex justify-between items-center">
                            <h3 className="text-[10px] font-black uppercase tracking-[0.5em] text-pink-500/40">Зарегистрированные Клиенты</h3>
                            <button
                                onClick={async () => {
                                    if (window.confirm('Вы уверены, что хотите удалить ВСЕХ пользователей с нулевым балансом?')) {
                                        setLoading(true);
                                        try {
                                            const result = await adminService.deleteZeroBalanceUsers();
                                            alert(`Успешно удалено пользователей: ${result.deleted_count}`);
                                            await fetchClients();
                                        } catch (error) {
                                            console.error(error);
                                            alert('Ошибка при удалении: ' + (error instanceof Error ? error.message : 'Неизвестная ошибка'));
                                        } finally {
                                            setLoading(false);
                                        }
                                    }
                                }}
                                className="px-4 py-2 border border-red-500/30 text-red-500 text-[10px] font-black uppercase tracking-widest hover:bg-red-500 hover:text-white transition-all"
                            >
                                Удалить нулевые балансы
                            </button>
                        </div>
                        {loading ? <p className="italic text-pink-500/60">Загрузка данных...</p> : (
                            <div className="grid gap-4">
                                {clients.map(client => (
                                    <div key={client.id} className="p-6 border border-pink-500/10 bg-pink-500/5 flex items-center justify-between group hover:border-pink-500/40 transition-all">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 border border-pink-500/20 flex items-center justify-center bg-black">
                                                <UserIcon size={16} className="text-pink-500/60" />
                                            </div>
                                            <div>
                                                <div className="text-lg italic font-serif text-white">{client.username}</div>
                                                <div className="text-[10px] uppercase text-pink-500/40">{client.email}</div>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-8">
                                            <div className="text-right">
                                                <div className="text-[9px] uppercase tracking-widest text-pink-500/30">Баланс</div>
                                                <div className={`text-sm font-mono font-bold ${client.is_admin ? 'text-pink-500 animate-pulse' : (client.balance > 0 ? 'text-emerald-400' : 'text-pink-500/60')}`}>
                                                    {client.is_admin ? 'Unlimited' : `$${client.balance || 0}`}
                                                </div>
                                            </div>

                                            <div className="text-right">
                                                <div className="text-[9px] uppercase tracking-widest text-pink-500/30">Зарегистрирован</div>
                                                <div className="text-[11px] font-mono text-pink-500/60">{new Date(client.created_at).toLocaleDateString()}</div>
                                            </div>

                                            {!client.is_admin && (
                                                <button
                                                    onClick={async () => {
                                                        if (window.confirm(`Удалить пользователя ${client.username}?`)) {
                                                            try {
                                                                await adminService.deleteUser(client.id);
                                                                await fetchClients();
                                                            } catch (error) {
                                                                console.error(error);
                                                                alert('Ошибка при удалении');
                                                            }
                                                        }
                                                    }}
                                                    className="p-2 opacity-0 group-hover:opacity-100 text-red-500/50 hover:text-red-500 transition-all"
                                                    title="Удалить пользователя"
                                                >
                                                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'generations' && (
                    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <h3 className="text-[10px] font-black uppercase tracking-[0.5em] text-pink-500/40">Последние 5 Анализов</h3>
                        {loading ? <p className="italic text-pink-500/60">Загрузка данных...</p> : (
                            <div className="grid gap-4">
                                {generations.map((gen, idx) => (
                                    <div key={idx} className="p-6 border border-pink-500/10 bg-pink-500/5 flex items-center justify-between group hover:border-pink-500/40 transition-all">
                                        <div className="flex items-center gap-4">
                                            <div className="w-10 h-10 border border-pink-500/20 flex items-center justify-center bg-black">
                                                <FileText size={16} className="text-pink-500/60" />
                                            </div>
                                            <div>
                                                <div className="text-lg italic font-serif text-white">{gen.artist}</div>
                                                <div className="text-[10px] uppercase text-pink-500/40">{gen.filename}</div>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <div className="text-[9px] uppercase tracking-widest text-pink-500/30">Дата анализа</div>
                                            <div className="text-[11px] font-mono text-pink-500/60">{new Date(gen.timestamp * 1000).toLocaleString()}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'rag' && (
                    <div className="max-w-xl space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-500">
                        <h3 className="text-[10px] font-black uppercase tracking-[0.5em] text-pink-500/40">Управление Базой Знаний (RAG)</h3>
                        <div className="baroque-panel p-10 space-y-6">
                            <p className="text-sm italic text-pink-100/60 leading-relaxed">
                                Загрузите новые материалы для обучения системы. Файлы будут проиндексированы и использованы при генерации вокальных манускриптов.
                            </p>
                            <div className="space-y-4">
                                <label className="flex flex-col items-center justify-center w-full h-32 px-4 transition bg-black/40 border-2 border-pink-500/10 border-dashed rounded-md appearance-none cursor-pointer hover:border-pink-500/40 focus:outline-none">
                                    <Upload className="w-8 h-8 text-pink-500/40 mb-2" />
                                    <span className="font-serif italic text-pink-100/40">Нажмите для выбора файла</span>
                                    <input type="file" className="hidden" onChange={handleFileUpload} />
                                </label>
                                {uploadStatus && (
                                    <div className="text-[10px] uppercase font-black tracking-widest text-center text-pink-500 animate-pulse">
                                        {uploadStatus}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default AdminCMS;
