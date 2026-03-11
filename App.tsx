import React, { useState, useEffect } from 'react';
import AnalysisDashboard from './components/AnalysisDashboard';
import { VocalAnalysis } from './types';
import { GeminiService } from './services/geminiService';
import SupportModule from './components/SupportModule';
import FeatureStore from './components/FeatureStore';
import AuthModal from './components/AuthModal';
import { authService } from './services/authService';
import { LogOut, User as UserIcon, Shield } from 'lucide-react';
import AdminCMS from './components/AdminCMS';

const App: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<VocalAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [showForm, setShowForm] = useState(false);
  const [archive, setArchive] = useState<VocalAnalysis[]>([]);

  // Form inputs
  const [artist, setArtist] = useState('');
  const [songStructure, setSongStructure] = useState('');
  const [referenceUrl, setReferenceUrl] = useState('');
  const [audioFile, setAudioFile] = useState<File | null>(null);
  const [isDeepResearchActive, setIsDeepResearchActive] = useState(false);

  // Auth state
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<string | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [showAdminCMS, setShowAdminCMS] = useState(false);

  useEffect(() => {
    setCurrentUser(authService.getCurrentUser());
    setIsAdmin(authService.isAdmin());
  }, []);

  useEffect(() => {
    const gemini = new GeminiService();
    setArchive(gemini.getArchive());
  }, [analysisData]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setAudioFile(e.target.files[0]);
      if (!artist) {
        // Try to guess artist name from filename
        const name = e.target.files[0].name.split(/[-_]/)[0];
        setArtist(name.replace(/\.[^/.]+$/, ""));
      }
    }
  };

  const startAnalysis = async () => {
    if (!artist.trim()) {
      setStatus('Ошибка: Имя исполнителя обязательно');
      return;
    }

    setShowForm(false);
    setLoading(true);
    setStatus('Синхронизация с нейронным ядром...');
    try {
      const gemini = new GeminiService();
      const result = await gemini.analyzeVocalist(
        artist,
        [],
        (stage) => setStatus(stage),
        songStructure,
        referenceUrl,
        audioFile || undefined,
        isDeepResearchActive
      );
      console.log("Analysis Result Received:", result);
      gemini.saveToArchive(result);
      setAnalysisData(result);
    } catch (error) {
      console.error("Analysis Error Details:", error);
      setStatus('Ошибка: ' + (error instanceof Error ? error.message : 'Неизвестная ошибка'));
    } finally {
      setLoading(false);
    }
  };

  if (showAdminCMS) {
    return <AdminCMS onBack={() => setShowAdminCMS(false)} />;
  }

  if (analysisData) {
    return (
      <div className="min-h-screen bg-[#050505] p-8 md:p-24 overflow-x-hidden">
        <button
          onClick={() => {
            setAnalysisData(null);
            setArtist('');
            setSongStructure('');
            setReferenceUrl('');
            setAudioFile(null);
            setStatus('');
          }}
          className="mb-12 px-6 py-3 border border-pink-500/30 text-pink-500 text-[10px] font-black uppercase tracking-widest hover:bg-pink-500 hover:text-black transition-all"
        >
          ← Вернуться в архив
        </button>
        <AnalysisDashboard data={analysisData} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-[#fce7f3] flex flex-col items-center justify-center p-8 font-serif">
      <h1 className="text-6xl md:text-8xl font-baroque mb-4 pink-glow text-center">VocalPrint AI</h1>
      <p className="text-pink-500/60 uppercase tracking-[0.5em] text-[10px] mb-12 text-center">Neural Vocal Manuscript Analysis</p>

      {/* Auth Bar */}
      <div className="fixed top-8 right-8 z-50 flex items-center gap-4">
        {currentUser ? (
          <div className="flex items-center gap-4 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex items-center gap-2 px-4 py-2 border border-pink-500/20 bg-pink-500/5 backdrop-blur-md">
              <UserIcon size={14} className="text-pink-500" />
              <span className="text-[10px] font-black uppercase tracking-widest text-pink-100">{currentUser}</span>
            </div>
            {isAdmin && (
              <button
                onClick={() => setShowAdminCMS(true)}
                className="flex items-center gap-2 px-4 py-2 border border-pink-500/50 bg-[#ff2d75]/10 text-pink-500 hover:bg-[#ff2d75] hover:text-black transition-all"
                title="Admin Control Panel"
              >
                <Shield size={14} />
                <span className="text-[10px] font-black uppercase tracking-widest">CMS</span>
              </button>
            )}
            <button
              onClick={() => {
                authService.logout();
                setCurrentUser(null);
                setIsAdmin(false);
                setShowAdminCMS(false);
              }}
              className="p-2 border border-pink-500/20 hover:border-pink-500/50 text-pink-500/50 hover:text-pink-500 transition-all hover:bg-pink-500/10"
              title="Выйти"
            >
              <LogOut size={16} />
            </button>
          </div>
        ) : (
          <button
            onClick={() => setIsAuthModalOpen(true)}
            className="px-6 py-2 border border-pink-500/30 text-pink-500 text-[10px] font-black uppercase tracking-widest hover:bg-pink-500 hover:text-black transition-all animate-in fade-in slide-in-from-right-4 duration-500"
          >
            Sign In / Sign Up
          </button>
        )}
      </div>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={(user) => {
          setCurrentUser(user);
          setIsAdmin(authService.isAdmin());
          setIsAuthModalOpen(false);
        }}
      />

      <div className="baroque-panel p-10 md:p-16 max-w-2xl w-full text-center space-y-10 relative">
        <div className="absolute -top-2 -left-2 w-8 h-8 border-t-2 border-l-2 border-pink-500/50"></div>
        <div className="absolute -bottom-2 -right-2 w-8 h-8 border-b-2 border-r-2 border-pink-500/50"></div>

        {loading ? (
          <div className="space-y-8 py-10">
            <div className="flex flex-col items-center">
              <div className="w-20 h-20 border-2 border-pink-500/20 border-t-pink-500 rounded-full animate-spin mb-6 shadow-[0_0_20px_rgba(255,45,117,0.2)]"></div>
              <p className="text-2xl italic animate-pulse text-pink-100">{status}</p>
            </div>
          </div>
        ) : showForm ? (
          <div className="space-y-10 text-left animate-in fade-in zoom-in-95 duration-500">
            <h2 className="text-2xl font-baroque text-pink-500 text-center uppercase tracking-widest">Параметры Анализа</h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="space-y-4">
                <label className="text-[10px] font-black uppercase tracking-[0.3em] text-pink-500/60">Имя исполнителя</label>
                <input
                  type="text"
                  value={artist}
                  onChange={(e) => setArtist(e.target.value)}
                  placeholder="Freddie Mercury"
                  className="w-full bg-black/50 border border-pink-500/20 p-4 text-white focus:outline-none focus:border-pink-500 transition-colors font-serif italic"
                />
              </div>
            </div>

            {/* Premium Features Store under Artist & Reference */}
            <div className="w-full">
              <FeatureStore
                isAdmin={isAdmin}
                onFeaturesChange={(features) => {
                  setIsDeepResearchActive(features.includes('deep-research'));
                }}
              />
            </div>

            <div className="space-y-4">
              <label className="text-[10px] font-black uppercase tracking-[0.3em] text-pink-500/60">Загрузить аудиофайл (.mp3, .wav)</label>
              <label className="flex items-center justify-center w-full h-24 px-4 transition bg-black/40 border-2 border-pink-500/10 border-dashed rounded-md appearance-none cursor-pointer hover:border-pink-500/40 focus:outline-none">
                <span className="flex items-center space-x-4">
                  <svg className="w-6 h-6 text-pink-500/40" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" /></svg>
                  <span className="font-serif italic text-pink-100/40">
                    {audioFile ? audioFile.name : "Выберите файл или перетащите сюда"}
                  </span>
                </span>
                <input type="file" name="file_upload" className="hidden" onChange={handleFileChange} accept="audio/*" />
              </label>
            </div>

            <div className="space-y-4">
              <label className="text-[10px] font-black uppercase tracking-[0.3em] text-pink-500/60">Структура песни / Текст</label>
              <textarea
                value={songStructure}
                onChange={(e) => setSongStructure(e.target.value)}
                placeholder="[verse] Текст куплета... [chorus] Текст припева..."
                className="w-full bg-black/50 border border-pink-500/20 p-4 text-white focus:outline-none focus:border-pink-500 transition-colors font-serif italic h-24 resize-none"
              />
            </div>

            <div className="flex gap-4 pt-6">
              <button
                onClick={() => setShowForm(false)}
                className="flex-1 py-4 border border-pink-500/30 text-pink-500/60 text-[10px] font-black uppercase tracking-widest hover:text-white hover:border-white transition-all"
              >
                Отмена
              </button>
              <button
                onClick={startAnalysis}
                className="flex-[2] py-4 bg-[#ff2d75] text-black font-baroque font-black text-xs uppercase tracking-[0.3em] hover:bg-white transition-all shadow-[0_0_30px_rgba(255,45,117,0.4)]"
              >
                Подтвердить Анализ
              </button>
            </div>
          </div>
        ) : (
          <>
            <p className="text-xl italic opacity-80 leading-relaxed font-serif">
              «Голос есть зеркало души, а спектрограмма — её чертеж».
              <br />
              <span className="text-sm opacity-50 not-italic block mt-4 text-pink-300">Готовы ли вы начать технический разбор?</span>
            </p>
            <div className="pt-6">
              <button
                onClick={() => {
                  if (currentUser) {
                    setShowForm(true);
                  } else {
                    setIsAuthModalOpen(true);
                  }
                }}
                className="px-12 py-6 bg-[#ff2d75] text-black font-baroque font-black text-xs uppercase tracking-[0.3em] hover:bg-white transition-all shadow-[0_0_40px_rgba(255,45,117,0.4)] group active:scale-95"
              >
                <span className="group-hover:scale-105 inline-block transition-transform">Начать Анализ</span>
              </button>
            </div>

            {archive.length > 0 && (
              <div className="mt-16 text-left border-t border-pink-500/10 pt-10">
                <h3 className="text-[10px] font-black uppercase tracking-[0.5em] text-pink-500/40 mb-6">Archival Registry (History)</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {archive.slice(0, 5).map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => setAnalysisData(item)}
                      className="p-4 border border-pink-500/10 hover:border-pink-500/40 bg-pink-500/5 flex items-center justify-between group transition-all"
                    >
                      <div className="text-left">
                        <div className="text-white text-sm font-serif italic">{item.artistName}</div>
                        <div className="text-[9px] text-pink-500/60 uppercase">{item.vocalRange?.classification}</div>
                      </div>
                      <svg className="w-4 h-4 text-pink-500 opacity-20 group-hover:opacity-100 transition-opacity" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" /></svg>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {status.startsWith('Ошибка') && (
              <div className="p-4 bg-red-950/30 border border-red-500/30 text-red-400 text-sm mt-8 animate-in fade-in slide-in-from-top-2">
                {status}
              </div>
            )}
          </>
        )}

        {!showForm && !analysisData && currentUser && (
          <div className="mt-16 w-full">
            <SupportModule isAdmin={isAdmin} />
          </div>
        )}
      </div>

      <p className="mt-20 text-pink-900 text-[9px] font-black uppercase tracking-[1em] opacity-40">Archival Core v1.5 // Polza AI</p>
    </div>
  );
};

export default App;
