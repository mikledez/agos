export type FolderKind = "folder" | "athlete";

export type Folder = {
  id: number;
  user_id: number;
  parent_id: number | null;
  name: string;
  kind: FolderKind;
  created_at: string;
  updated_at: string;
};

export type SprintImage = {
  id: number;
  session_id: number | null;
  original_filename: string;
  phase: string;
  direction: string;
  swing_hip: number | null;
  swing_knee: number | null;
  swing_ankle: number | null;
  stance_hip: number | null;
  stance_knee: number | null;
  stance_ankle: number | null;
  thigh_thigh: number | null;
  feedback: string | null;
  swing_feedback: string | null;
  stance_feedback: string | null;
  created_at: string;
  updated_at: string;
  original_url: string;
  thumbnail_url: string;
  annotated_url: string | null;
  /** False once an athlete image's full photo was cleared after 48 idle hours. */
  has_photo: boolean;
};

export type ProgressAngles = {
  hip: number | null;
  knee: number | null;
  ankle: number | null;
};

export type ProgressPoint = {
  image_id: number;
  original_filename: string;
  phase: string;
  created_at: string;
  score: number | null;
  in_range: number;
  measured: number;
  swing: ProgressAngles;
  stance: ProgressAngles;
  thigh_thigh: number | null;
};

type Range = [number, number];

export type PhaseRanges = {
  swing: Record<"hip" | "knee" | "ankle", Range>;
  stance: Record<"hip" | "knee" | "ankle", Range>;
  thigh_thigh?: Range;
};

export type AthleteProgress = {
  points: ProgressPoint[];
  ranges: Record<string, PhaseRanges>;
};

export type Humanization = {
  id: number;
  image_id: number;
  model: string;
  prompt: string | null;
  humanized_text: string;
  created_at: string;
  updated_at: string;
};

export type ImageDetail = {
  image: SprintImage;
  humanization: Humanization | null;
};

export type ChatMessage = {
  id: number;
  image_id: number;
  role: "user" | "assistant";
  content: string;
  model: string | null;
  created_at: string;
};

export type ChatExchange = {
  user_message: ChatMessage;
  assistant_message: ChatMessage;
};
