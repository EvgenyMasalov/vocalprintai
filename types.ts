
export interface VocalAnalysis {
  artistName: string;
  expertVerdict: string; // Grand summary of the analysis
  timbre: {
    description: string;
    characteristics: string[];
    spectralBalance: string;
    brightness: number;
    density: number;
    radarMetrics: {
      luminous: number;   // Brightness
      ethereal: number;   // Breathiness/Air
      metallic: number;   // Sharpness/Edge
      profound: number;   // Depth/Bass
      compressed: number; // Density/Power
    };
  };
  technicalDiagnostics: {
    pitchStability: number;
    vibrato: {
      intensity: number;
      speed: number;
      type: string;
    };
    noiseTexture: {
      amount: number;
      characteristics: string[];
    };
    breathControl: {
      index: number;
      status: string;
    };
    compressionFriction: {
      index: number;
      status: string;
    };
    pitchMovement: Array<{
      time: string;
      stability: number;
      note?: string;
    }>;
  };
  vocalSemanticMapping: Array<{
    timestamp: string;
    section: string;
    lyricSnippet: string;
    techniqueShift: string;
    emotionalIntent: string;
    brightnessDelta: number;
    densityDelta: number;
    tags: string[]; // e.g., ["Fry", "Belting", "Yodel"]
  }>;
  vocalRange: {
    low: string;
    high: string;
    classification: string;
  };
  techniques: Array<{
    name: string;
    description: string;
    prominence: number;
  }>;
  trackStructureAnalysis: Array<{
    songName: string;
    sections: Array<{
      type: string;
      vocalApproach: string;
      dynamicLevel: string;
      timestamp?: string;
    }>;
  }>;
  comparison?: {
    referenceName: string;
    referenceUrl?: string;
    similarities: string[];
    differences: string[];
    overallMatch: number;
    comparativeTimbreAnalysis?: string;
  };
  groundingSources: Array<{
    title: string;
    uri: string;
  }>;
  tempo?: number;
  key?: string;
  // Vocal separation & gender classification (feat-треки)
  collaboration?: {
    is_collaboration: boolean;
    vocal_separation_used: boolean;
    analyzed_vocal: 'female' | 'male' | 'mixed' | 'vocal_stem';
    primary_artist: string | null;
    featured_artists: string[];
    clean_title: string;
    trigger: string | null;
    gender_stats?: {
      total_segments: number;
      female_segments: number;
      male_segments: number;
      unknown_segments: number;
      female_duration_sec: number;
      male_duration_sec: number;
      dominant_gender: 'female' | 'male' | 'mixed';
      avg_female_f0: number;
      avg_male_f0: number;
    };
  };
}

export interface AnalysisState {
  loading: boolean;
  error: string | null;
  data: VocalAnalysis | null;
}
