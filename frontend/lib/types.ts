export type Folder = {
  id: number;
  user_id: number;
  parent_id: number | null;
  name: string;
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
  annotated_url: string | null;
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
