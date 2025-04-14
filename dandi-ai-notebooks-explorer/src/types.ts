export interface Rating {
  notebook: string;
  dandiset_id: string;
  subfolder: string;
  overall_score: number;
  scores: Score[];
}

export interface Score {
  name: string;
  version: number;
  score: number;
  reps: Rep[];
}

export interface Rep {
  score: number;
  thinking: string;
  repnum: number;
}
