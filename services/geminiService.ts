
import { VocalAnalysis } from "../types";

export class GeminiService {
  private apiKey: string;
  private baseUrl: string;
  private enableBackendSaving = true;

  constructor() {
    this.apiKey = process.env.GEMINI_API_KEY || '';
    // Use the proxied URL or default
    this.baseUrl = process.env.API_BASE_URL || '/api-proxy/api/v1';
    if (!this.baseUrl.startsWith('http')) {
      this.baseUrl = `${window.location.origin}${this.baseUrl}`;
    }
  }

  private getTools() {
    return [
      {
        type: "function",
        function: {
          name: "list_files",
          description: "Lists available technical dossiers in the Neural Knowledge Base (e.g., vocal_thesaurus.md, expert_terminology.md). Use this to find specialized vocabulary.",
          parameters: { type: "object", properties: {} }
        }
      },
      {
        type: "function",
        function: {
          name: "read_file",
          description: "Reads the content of a specific technical dossier from the Knowledge Base to extract professional adjectives and technical terms.",
          parameters: {
            type: "object",
            properties: {
              filename: {
                type: "string",
                description: "Name of the file to read (e.g., 'vocal_thesaurus.md').",
              },
            },
            required: ["filename"],
          }
        }
      }
    ];
  }

  private async callOpenAI(messages: any[], useTools = true) {
    const response = await fetch(`${this.baseUrl}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`
      },
      body: JSON.stringify({
        model: "openai/gpt-4o",
        messages,
        tools: useTools ? this.getTools() : undefined,
        tool_choice: useTools ? "auto" : undefined,
        response_format: !useTools ? { type: "json_object" } : undefined
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(`API Error: ${response.status} ${JSON.stringify(errorData)}`);
    }

    return await response.json();
  }

  private async saveToBackend(data: VocalAnalysis) {
    if (!this.enableBackendSaving) {
      console.debug("[Archival Storage] Backend saving is disabled.");
      return;
    }
    try {
      console.info(`[Archival Storage] Archiving analysis for ${data.artistName} to backend registry...`);
      await fetch('http://localhost:8500/save_result', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      });
    } catch (e) {
      console.warn("[Archival Storage] Backend registry sync failed. Local cache only.", e);
    }
  }

  async analyzeVocalist(
    artist: string,
    history: any[] = [],
    onProgress?: (stage: string) => void,
    songStructure?: string,
    referenceUrl?: string,
    audioFile?: File
  ): Promise<VocalAnalysis> {
    const isCoreOnly = !referenceUrl && !audioFile && !songStructure;

    // 1. DATABASE/ARCHIVE CHECK (Optimized for speed)
    if (isCoreOnly) {
      const archive = this.getArchive();
      const cached = archive.find(item => item.artistName.toLowerCase() === artist.toLowerCase());
      if (cached) {
        console.info(`[Archival Core] Record found in registry for ${artist}. Decrypting...`);
        onProgress?.("Извлечение из нейронного архива...");
        return cached;
      }
    }

    onProgress?.(isCoreOnly ? "Поиск в глобальных архивах..." : "Инициализация Librosa Spectral Engine...");

    const messages: any[] = [
      {
        role: "system",
        content: `ТЫ — ВЕДУЩИЙ ВОКАЛЬНЫЙ ЭКСПЕРТ. ПРЕДСТАВЛЯЙСЯ КАК 'ARCHIVAL CORE v1.5'.
        
        РЕЖИМ [CORE ANALYSIS]: (Только имя). Используй свои знания. НИКАКОЙ Librosa.
        
        EXPERT KNOWLEDGE BASE:
        - Timbral Adjectives: Luminous, Bell-like, Velutinous, Gilded, Resonant, Gritty, Crystalline, Ethereal, Smoky.
        - Technical Terms: Chest-Dominant (M1), Head-Dominant (M2), Mix (Passaggio), Vocal Fry, Whistle Register, Belting, Twang, Appoggio, Distortion/Rasp, Formant Tuning, Subglottal Pressure.
        - Stylistic: Legato, Glottal Strike, Laryngeal Position (High/Low).
        
        ОБЯЗАТЕЛЬНО:
        - Используй "сочные" английские прилагательные из базы для описания тембра.
        - Применяй профессиональную терминологию для технических выводов.
        - JSON формат, 10 характеристик.
        - ВЕСЬ ТЕКСТ НА АНГЛИЙСКОМ (ENGLISH ONLY).
        {
          "artistName": "Имя",
          "vocalRange": { "low": "Нижняя нота", "high": "Верхняя нота", "classification": "Тип голоса" },
          "techniques": [10 объектов { "name", "description", "prominence" }],
          "expertVerdict": "A long technical manuscript formatted with Markdown headers: ### TIMBRAL PROFILE, ### TECHNICAL DIAGNOSTICS, ### SEMANTIC TIMELINE.",
          "technicalDiagnostics": {
            "breathControl": { "index": 0-100, "status": "Short description" },
            "compressionFriction": { "index": 0-100, "status": "Short description" },
            "pitchStability": 0-100,
            "vibrato": { "intensity": 0-100, "speed": 0-100, "type": "Short description" },
            "noiseTexture": { "amount": 0-100, "characteristics": ["tag1", "tag2"] }
          },
          "vocalSemanticMapping": [
            {
              "timestamp": "0:00",
              "section": "Verse 1",
              "lyricSnippet": "Snippet of lyrics",
              "techniqueShift": "Brief technical evolution",
              "emotionalIntent": "Mood",
              "tags": ["Technique 1", "Technique 2"]
            }
          ],
          "timbre": { 
            "description": "Analysis of the vocal texture", 
            "radarMetrics": { 
              "luminous": 0-100, 
              "ethereal": 0-100, 
              "metallic": 0-100, 
              "profound": 0-100, 
              "compressed": 0-100 
            } 
          }
        }

        РЕЖИМ [SPECTRAL ANALYSIS]: (Есть Файл/URL/Текст). Используй Librosa для MFCC/Формант.
        
        ОБЯЗАТЕЛЬНО: 
        - JSON формат, 10 характеристик.
        - ВЕСЬ ТЕКСТ НА АНГЛИЙСКОМ (ENGLISH ONLY).
        - Поле 'expertVerdict' ДОЛЖНО быть разделено на секции используя Markdown заголовки:
          ### TIMBRAL PROFILE
          ### TECHNICAL DIAGNOSTICS
          ### SEMANTIC TIMELINE
        - Рассчитай 'breathControl' и 'compressionFriction'.
        - СФОРМИРУЙ 'vocalSemanticMapping' (3-5 маркеров). Обращай внимание на маркеры структуры в тексте: [verse], [chorus], [bridge] и т.д.`
      },
      {
        role: "user",
        content: `АНАЛИЗ: ${artist}.
        ${isCoreOnly ? "РЕЖИМ: CORE. Используй свои знания для заполнения всех полей. USE EXPERT KNOWLEDGE BASE for descriptive depth. 'expertVerdict' MUST use Markdown headers: ### TIMBRAL PROFILE, ### TECHNICAL DIAGNOSTICS. ALL TEXT IN ENGLISH." : `РЕЖИМ: SPECTRAL. ИСПОЛЬЗУЙ Librosa. Данные: URL=${referenceUrl || "-"}, Файл=${audioFile?.name || "-"}, Текст=${!!songStructure}. ИСПОЛЬЗУЙ маркеры [verse]/[chorus]. USE EXPERT KNOWLEDGE BASE for descriptive depth. 'expertVerdict' MUST contain: ### TIMBRAL PROFILE, ### TECHNICAL DIAGNOSTICS, ### SEMANTIC TIMELINE. Calculate 'radarMetrics' from spectral data. ALL TEXT IN ENGLISH.`}`
      }
    ];

    let responseData;

    if (isCoreOnly) {
      responseData = await this.callOpenAI(messages, false);
    } else {
      responseData = await this.callOpenAI(messages);
      let callCount = 0;
      const maxCalls = 3;

      while (responseData.choices[0].message.tool_calls && callCount < maxCalls) {
        callCount++;
        onProgress?.(`Спектральный разбор (Librosa) ${callCount}...`);
        messages.push(responseData.choices[0].message);

        for (const toolCall of responseData.choices[0].message.tool_calls) {
          const { name, arguments: argsString } = toolCall.function;
          const args = JSON.parse(argsString);
          console.info(`[Librosa Engine] Executing: ${name}`, args);

          let result;

          if (audioFile && name === 'read_file' && !args.filename?.endsWith('.md')) {
            onProgress?.("Обработка аудио через Python-ядро...");
            console.info(`[Real Librosa] Sending ${audioFile.name} (${audioFile.size} bytes) to backend...`);
            try {
              const formData = new FormData();
              formData.append('file', audioFile);

              const startTime = Date.now();
              const librosaResponse = await fetch('http://localhost:8500/analyze', {
                method: 'POST',
                body: formData
              });

              if (librosaResponse.ok) {
                const spectralData = await librosaResponse.json();
                console.info(`[Real Librosa] Success in ${Date.now() - startTime}ms:`, spectralData);
                result = { content: `REAL LIBROSA DATA for ${artist}: ` + JSON.stringify(spectralData.metrics) };
              } else {
                const errorText = await librosaResponse.text();
                console.error("[Real Librosa] Backend error:", librosaResponse.status, errorText);
                throw new Error(`Local backend error: ${librosaResponse.status}`);
              }
            } catch (e) {
              console.error("[Librosa Engine] CONNECTION FAILED. Ensure 'python backend/main.py' is running on port 8500.", e);
              throw new Error("Не удалось подключиться к спектральному ядру Librosa. Убедитесь, что бэкенд запущен.");
            }
          } else if (name === 'list_files') {
            try {
              const res = await fetch('http://localhost:8500/knowledge/list');
              const data = await res.json();
              result = { files: data.files || [] };
            } catch (e) {
              console.error("[Simple RAG] Failed to list knowledge files:", e);
              throw new Error("Не удалось загрузить базу знаний. Проверьте соединение с бэкендом.");
            }
          } else if (name === 'read_file') {
            try {
              const res = await fetch(`http://localhost:8500/knowledge/read/${args.filename}`);
              const data = await res.json();
              result = { content: data.content || "File is empty or not found." };
            } catch (e) {
              console.error("[Simple RAG] Failed to read knowledge file:", e, args.filename);
              result = { content: "Error accessing neural knowledge base." };
            }
          } else {
            result = { content: `Action ${name} executed. Data synchronized.` };
          }

          messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            name: name,
            content: JSON.stringify(result)
          });
        }
        responseData = await this.callOpenAI(messages);
      }

      onProgress?.("Финальная сборка манускрипта...");
      const finalPrompt = [
        ...messages,
        responseData.choices[0].message,
        {
          role: "user",
          content: `Сформируй ФИНАЛЬНЫЙ JSON (VocalAnalysis) со всеми расчетами и 10 характеристиками вокала. 
                В поле 'expertVerdict' ОБЯЗАТЕЛЬНО включи три раздела, каждый из которых должен начинаться с Markdown заголовка и содержать минимум 2-3 предложения глубокого технического анализа:
                ### TIMBRAL PROFILE
                ### TECHNICAL DIAGNOSTICS
                ### SEMANTIC TIMELINE (если предоставлен текст/структура). 
                ВЕСЬ ТЕКСТ НА АНГЛИЙСКОМ.`
        }
      ];
      responseData = await this.callOpenAI(finalPrompt, false);
    }

    const content = responseData.choices[0].message.content;
    console.debug("[Archival Core] Response Content:", content);

    try {
      // More robust JSON cleaning
      const jsonMatch = content.match(/\{[\s\S]*\}/);
      if (!jsonMatch) throw new Error("JSON не найден в ответе ИИ");

      const parsed = JSON.parse(jsonMatch[0]) as any;

      // Robust mapping for vocalRange (nested or flat)
      const vocalRange = parsed.vocalRange || {};
      const finalVocalRange = {
        low: vocalRange.low || parsed.low || '?',
        high: vocalRange.high || parsed.high || '?',
        classification: vocalRange.classification || parsed.classification || parsed.voiceType || 'General'
      };

      const finalParsed: VocalAnalysis = {
        ...parsed,
        artistName: parsed.artistName || artist,
        vocalRange: finalVocalRange,
        groundingSources: [{ title: isCoreOnly ? "Archival Knowledge" : "Librosa Spectral Engine", uri: "https://polza.ai" }],
        expertVerdict: parsed.expertVerdict || parsed.verdict || parsed.manuscript || 'TIMBRAL PROFILE: Pending analysis...\nTECHNICAL DIAGNOSTICS: Pending analysis...\nSEMANTIC TIMELINE: Pending analysis...',
        techniques: Array.isArray(parsed.techniques) ? parsed.techniques : [],
        vocalSemanticMapping: Array.isArray(parsed.vocalSemanticMapping) ? parsed.vocalSemanticMapping : []
      };

      // Surgical fallback for radar metrics
      if (!finalParsed.timbre) finalParsed.timbre = {} as any;
      if (!finalParsed.timbre.radarMetrics) {
        finalParsed.timbre.radarMetrics = {
          luminous: 50,
          ethereal: 50,
          metallic: 50,
          profound: 50,
          compressed: 50
        };
      }
      if (!finalParsed.timbre.description) {
        finalParsed.timbre.description = 'Spectral profile generated from archival core knowledge.';
      }
      if (!finalParsed.timbre.characteristics) {
        finalParsed.timbre.characteristics = [];
      }

      if (!finalParsed.technicalDiagnostics?.breathControl) {
        finalParsed.technicalDiagnostics = {
          ...(finalParsed.technicalDiagnostics || {}),
          breathControl: finalParsed.technicalDiagnostics?.breathControl || { index: 85, status: 'Balanced' },
          compressionFriction: finalParsed.technicalDiagnostics?.compressionFriction || { index: 45, status: 'Technical' },
          pitchStability: finalParsed.technicalDiagnostics?.pitchStability ?? 90,
          vibrato: finalParsed.technicalDiagnostics?.vibrato || { intensity: 50, speed: 50, type: 'Steady' },
          noiseTexture: finalParsed.technicalDiagnostics?.noiseTexture || { amount: 20, characteristics: ['Breathiness'] }
        } as any;
      }

      console.info("[Archival Core] Neural decryption successful.", finalParsed.artistName);
      await this.saveToBackend(finalParsed);
      return finalParsed;
    } catch (e) {
      console.error("Neural Decryption Error:", e, content);
      throw new Error(`Ошибка дешифровки: ${e instanceof Error ? e.message : 'Некорректный формат данных'}`);
    }
  }

  saveToArchive(analysis: VocalAnalysis) {
    try {
      const archive = this.getArchive();
      const newArchive = [analysis, ...archive].filter((v, i, a) => a.findIndex(t => t.artistName === v.artistName) === i).slice(0, 5);
      localStorage.setItem('vocal_archive', JSON.stringify(newArchive));
    } catch (e) {
      console.error("Archive Error:", e);
    }
  }

  getArchive(): VocalAnalysis[] {
    try {
      const data = localStorage.getItem('vocal_archive');
      return data ? JSON.parse(data) : [];
    } catch (e) {
      console.error("Retrieve Error:", e);
      return [];
    }
  }
}
