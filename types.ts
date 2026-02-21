
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
}

export interface AnalysisState {
  loading: boolean;
  error: string | null;
  data: VocalAnalysis | null;
}
