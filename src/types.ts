export const STUDY_SECTIONS = [
  "Simple Definition",
  "Easy Explanation",
  "Real-Life Example",
  "Important Exam Points",
  "Short Summary",
  "Difficult Words",
] as const;

export type StudySection = (typeof STUDY_SECTIONS)[number];
export type LearningLevel = "Beginner" | "Intermediate" | "Advanced";
export type PageName =
  | "Home"
  | "Simplify Content"
  | "Study Materials"
  | "Quiz Generator"
  | "History"
  | "About";

export interface MultipleChoiceQuestion {
  question: string;
  options: Record<"A" | "B" | "C" | "D", string>;
  answer: "A" | "B" | "C" | "D";
}

export interface StudyPack {
  sections: Record<StudySection, string>;
  mcqs: MultipleChoiceQuestion[];
  revision_questions: string[];
}

export interface StudyRecord {
  id: string;
  title: string;
  level: LearningLevel;
  source: string;
  createdAt: string;
  pack: StudyPack;
}

export interface Passage {
  id: string;
  title: string;
  text: string;
}
