import type { LearningLevel, StudyPack } from "../types";

interface ApiError {
  error?: string;
}

export async function generateStudyPack(
  content: string,
  level: LearningLevel,
): Promise<StudyPack> {
  const response = await fetch("/api/study-pack", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content, level }),
  });
  let result: StudyPack | ApiError;
  try {
    result = (await response.json()) as StudyPack | ApiError;
  } catch {
    throw new Error("The server returned an unreadable response. Please try again.");
  }

  if (!response.ok) {
    const errorMessage =
      result &&
      typeof result === "object" &&
      "error" in result &&
      typeof result.error === "string"
        ? result.error
        : "The study pack could not be generated. Please try again.";
    throw new Error(
      errorMessage,
    );
  }

  return result as StudyPack;
}
