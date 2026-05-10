// Shared types mirrored for mobile app
// These should match packages/shared/src/types.ts

export type ReflectionStatus = "draft" | "completed" | "archived";

export interface User {
  id: string;
  email: string;
  name?: string;
  display_name?: string;
  created_at?: string;
}

export interface AuthSession {
  token: string;
  user: User;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  display_name: string;
}

export interface Reflection {
  id: string;
  user_id: string;
  title: string;
  situation: string;
  feelings: string;
  interpretation: string;
  needs: string;
  fears: string;
  desired_outcome: string;
  message_draft: string;
  status: ReflectionStatus;
  created_at: string;
  updated_at: string;
  output?: ReflectionOutput | null;
}

export interface ReflectionOutput {
  id: string;
  reflection_id: string;
  emotional_summary: string;
  needs_summary: string;
  assumptions: string;
  reframe: string;
  avoid_saying: string;
  conversation_opener: string;
  followup_questions: string;
  repair_statement: string;
  created_at: string;
}

export interface CreateReflectionRequest {
  title: string;
  situation: string;
  feelings: string;
  interpretation: string;
  needs: string;
  fears: string;
  desired_outcome: string;
  message_draft: string;
}

export interface UpdateReflectionRequest {
  title?: string;
  situation?: string;
  feelings?: string;
  interpretation?: string;
  needs?: string;
  fears?: string;
  desired_outcome?: string;
  message_draft?: string;
  status?: ReflectionStatus;
}

export interface GenerateResponse {
  is_crisis: boolean;
  severity: string;
  message: string;
  resources: string[];
  output: ReflectionOutput | null;
}

// ─── Feedback Types ───────────────────────────────────────────────────────────

export interface ReflectionFeedback {
  id: string;
  reflection_id: string;
  user_id: string;
  prepared_score: number;  // 1=No, 2=Somewhat, 3=Yes
  less_reactive_score: number;  // 1=No, 2=Somewhat, 3=Yes
  helpful_text: string;
  conversation_went_better: number;  // 0=not answered, 1=No, 2=Somewhat, 3=Yes
  created_at: string;
}

export interface CreateFeedbackRequest {
  prepared_score: number;
  less_reactive_score: number;
  helpful_text?: string;
}

// Wizard step types
export interface WizardStep {
  key: string;
  question: string;
  hint: string;
}

export const WIZARD_STEPS: WizardStep[] = [
  {
    key: "situation",
    question: "What happened?",
    hint: "Describe the situation as factually as you can.",
  },
  {
    key: "feelings",
    question: "What are you feeling?",
    hint: "Name your emotions — frustration, sadness, worry, hurt, etc.",
  },
  {
    key: "interpretation",
    question: "What story are you telling yourself about it?",
    hint: "What meaning are you giving to what happened?",
  },
  {
    key: "needs",
    question: "What do you need?",
    hint: "What would help you feel better or move forward?",
  },
  {
    key: "fears",
    question: "What are you afraid of?",
    hint: "What's the worst outcome you're worried about?",
  },
  {
    key: "desired_outcome",
    question: "What outcome do you want?",
    hint: "Ideally, what would a good resolution look like?",
  },
  {
    key: "message_draft",
    question: "What do you want to say?",
    hint: "Draft how you'd like to open the conversation.",
  },
];
