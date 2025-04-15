export interface Rating {
  notebook: string;
  dandiset_id: string;
  subfolder: string;
  overall_score: number;
  scores: Score[];
  metadata?: RatingMetadata;
}

export interface RatingMetadata {
  dandi_notebook_gen_version: string;
  system_info: {
    platform: string;
    hostname: string;
    processor: string;
    python_version: string;
  };
  model: string;
  vision_model: string;
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_vision_prompt_tokens: number;
  total_vision_completion_tokens: number;
  timestamp: string;
  elapsed_time_seconds: number;
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

export interface PlotRating {
  notebook: string;
  dandiset_id: string;
  subfolder: string;
  plots: {
    plot_id: string;
    cell_index: number;
    output_index: number;
    scores: Score[];
  }[];
  metadata?: RatingMetadata;
}
