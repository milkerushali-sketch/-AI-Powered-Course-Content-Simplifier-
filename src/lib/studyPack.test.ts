import assert from "node:assert/strict";
import test from "node:test";
import { createPreviewStudyPack, formatStudyPack } from "./studyPack.ts";
import studyPack, { parseStudyPack } from "../../netlify/functions/study-pack.ts";

test("preview study packs contain all sections, five quiz questions, and revision questions", () => {
  const pack = createPreviewStudyPack("Photosynthesis uses sunlight.", "Beginner");

  assert.equal(Object.keys(pack.sections).length, 6);
  assert.equal(pack.mcqs.length, 5);
  assert.equal(pack.revision_questions.length, 5);
  assert.match(pack.sections["Simple Definition"], /Photosynthesis/);
});

test("study packs can be exported as readable text", () => {
  const pack = createPreviewStudyPack("Water cycle", "Intermediate");
  const output = formatStudyPack(pack, "Water cycle notes", "Intermediate");

  assert.match(output, /MULTIPLE-CHOICE QUESTIONS/);
  assert.match(output, /REVISION QUESTIONS/);
  assert.match(output, /Water cycle notes/);
});

test("the function validates the generated study-pack response", () => {
  const sections = Object.fromEntries([
    "Simple Definition",
    "Easy Explanation",
    "Real-Life Example",
    "Important Exam Points",
    "Short Summary",
    "Difficult Words",
  ].map((key) => [key, `Explanation for ${key}`]));
  const questions = Array.from({ length: 5 }, (_, index) => ({
    question: `Question ${index + 1}`,
    options: { A: "First", B: "Second", C: "Third", D: "Fourth" },
    answer: "A",
  }));
  const raw = JSON.stringify({
    sections,
    mcqs: questions,
    revision_questions: ["First?", "Second?", "Third?", "Fourth?", "Fifth?"],
  });

  assert.equal(parseStudyPack(raw)?.mcqs.length, 5);
  assert.equal(parseStudyPack(JSON.stringify({ sections, mcqs: questions.slice(1), revision_questions: [] })), undefined);
  assert.equal(parseStudyPack("not JSON"), undefined);
});

test("the function rejects methods and malformed user input before using credentials", async () => {
  const methodResponse = await studyPack(new Request("https://example.test/api/study-pack"), {} as never);
  assert.equal(methodResponse.status, 405);

  const inputResponse = await studyPack(
    new Request("https://example.test/api/study-pack", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: " ", level: "Beginner" }),
    }),
    {} as never,
  );
  assert.equal(inputResponse.status, 400);
});
