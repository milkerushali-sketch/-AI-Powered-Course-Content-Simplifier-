import {
  STUDY_SECTIONS,
  type LearningLevel,
  type MultipleChoiceQuestion,
  type StudyPack,
} from "../types.ts";

function extractTopic(content: string): string {
  const firstLine = content
    .trim()
    .split(/[.!?\n]/, 1)[0]
    ?.replace(/^(explain|describe|what is|define)\s+/i, "")
    .trim();

  return firstLine ? firstLine.slice(0, 100) : "your topic";
}

export function createPreviewStudyPack(
  content: string,
  level: LearningLevel,
): StudyPack {
  const topic = extractTopic(content);
  const levelGuidance = {
    Beginner: "Use familiar language and explain one idea at a time.",
    Intermediate: "Connect the main idea to its important details.",
    Advanced: "Focus on precise terminology and how the ideas relate.",
  }[level];
  const sections: StudyPack["sections"] = {
    "Simple Definition": `${topic} is the main idea in your notes. This preview shows the structure of the study pack; enable live IBM Granite for a content-specific explanation.`,
    "Easy Explanation": `${levelGuidance}\n1. Identify the main idea in the notes.\n2. Break it into smaller facts or steps.\n3. Connect each fact to the topic.\n4. Review the key terms and examples.`,
    "Real-Life Example":
      "Connect the topic to something familiar in everyday life. For example, describe where you might notice this idea at home, at school, or in your community.",
    "Important Exam Points":
      "- Identify the main idea.\n- Learn the key terms.\n- Remember the important steps or facts.\n- Explain how the ideas connect.\n- Give an example in your own words.",
    "Short Summary": `These notes introduce ${topic}. Focus on the main idea, its important details, and how the parts connect. Use the key terms and an example to check your understanding.`,
    "Difficult Words":
      "- concept — a main idea\n- process — a sequence of steps\n- evidence — information that supports an idea\n- example — a case that makes an idea clearer",
  };
  const prompts = [
    "Which choice best describes the main idea?",
    "What should you identify first when reviewing this topic?",
    "Which is the best way to explain the key concept?",
    "Why is it useful to connect the details to the main idea?",
    "How can you check your understanding of the topic?",
  ];
  const mcqs: MultipleChoiceQuestion[] = prompts.map((question) => ({
    question,
    options: {
      A: `The central idea of ${topic}`,
      B: "An unrelated detail",
      C: "A different subject",
      D: "None of the choices",
    },
    answer: "A",
  }));

  return {
    sections,
    mcqs,
    revision_questions: [
      `What is the main idea of ${topic}?`,
      "Describe an important detail or step in your own words.",
      "Which key terms should you remember?",
      "Give an everyday example that connects to the topic.",
      "Summarize the topic in two sentences.",
    ],
  };
}

export function formatStudyPack(
  pack: StudyPack,
  source: string,
  level: LearningLevel,
): string {
  return [
    "AI-POWERED COURSE CONTENT SIMPLIFIER",
    `Learning level: ${level}`,
    "",
    ...STUDY_SECTIONS.flatMap((section) => [
      section.toUpperCase(),
      pack.sections[section],
      "",
    ]),
    "MULTIPLE-CHOICE QUESTIONS",
    ...pack.mcqs.flatMap((question, index) => [
      `${index + 1}. ${question.question}`,
      ...Object.entries(question.options).map(([key, text]) => `${key}) ${text}`),
      `Answer: ${question.answer}`,
      "",
    ]),
    "REVISION QUESTIONS",
    ...pack.revision_questions.map((question, index) => `${index + 1}. ${question}`),
    "",
    "SOURCE NOTES",
    source,
  ].join("\n");
}
