import { useEffect, useRef, useState } from "react";
import { HOME_EXAMPLES, SAMPLE_PASSAGES } from "./data";
import { generateStudyPack } from "./lib/api";
import { createPreviewStudyPack, formatStudyPack } from "./lib/studyPack";
import {
  STUDY_SECTIONS,
  type LearningLevel,
  type MultipleChoiceQuestion,
  type PageName,
  type StudyPack,
  type StudyRecord,
} from "./types";

const NAV_ITEMS: { name: PageName; icon: string }[] = [
  { name: "Home", icon: "⌂" },
  { name: "Simplify Content", icon: "✎" },
  { name: "Study Materials", icon: "▤" },
  { name: "Quiz Generator", icon: "◉" },
  { name: "History", icon: "◷" },
  { name: "About", icon: "ⓘ" },
];
const STORAGE_KEYS = {
  records: "course-simplifier.history.v1",
  theme: "course-simplifier.theme.v1",
  preview: "course-simplifier.preview.v1",
  level: "course-simplifier.level.v1",
};
const MAX_INPUT_LENGTH = 16_000;

function readStorage<T>(key: string, fallback: T, isValid: (value: unknown) => value is T): T {
  try {
    const saved = localStorage.getItem(key);
    if (saved === null) return fallback;
    const parsed: unknown = JSON.parse(saved);
    return isValid(parsed) ? parsed : fallback;
  } catch {
    return fallback;
  }
}

function isRecords(value: unknown): value is StudyRecord[] {
  if (!Array.isArray(value)) return false;
  return value.every(
    (record) =>
      record &&
      typeof record.id === "string" &&
      typeof record.title === "string" &&
      typeof record.createdAt === "string" &&
      record.pack &&
      typeof record.pack === "object",
  );
}

function fileName(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 60) || "study-pack";
}

function downloadPack(record: StudyRecord): void {
  const blob = new Blob(
    [formatStudyPack(record.pack, record.source, record.level)],
    { type: "text/plain;charset=utf-8" },
  );
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${fileName(record.title)}-study-pack.txt`;
  link.click();
  URL.revokeObjectURL(url);
}

function App() {
  const [page, setPage] = useState<PageName>("Home");
  const [theme, setTheme] = useState<"dark" | "light">(() =>
    readStorage(
      STORAGE_KEYS.theme,
      "dark",
      (value): value is "dark" | "light" => value === "dark" || value === "light",
    ),
  );
  const [preview, setPreview] = useState(() =>
    readStorage(STORAGE_KEYS.preview, true, (value): value is boolean => typeof value === "boolean"),
  );
  const [level, setLevel] = useState<LearningLevel>(() =>
    readStorage(
      STORAGE_KEYS.level,
      "Beginner",
      (value): value is LearningLevel =>
        value === "Beginner" || value === "Intermediate" || value === "Advanced",
    ),
  );
  const [records, setRecords] = useState<StudyRecord[]>(() =>
    readStorage(STORAGE_KEYS.records, [], isRecords),
  );
  const [homeText, setHomeText] = useState("");
  const [contentText, setContentText] = useState("");
  const [quizText, setQuizText] = useState("");
  const [result, setResult] = useState<StudyRecord | null>(null);
  const [quizQuestions, setQuizQuestions] = useState<MultipleChoiceQuestion[]>([]);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(STORAGE_KEYS.theme, JSON.stringify(theme));
  }, [theme]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.preview, JSON.stringify(preview));
  }, [preview]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.level, JSON.stringify(level));
  }, [level]);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.records, JSON.stringify(records.slice(0, 20)));
  }, [records]);

  async function createPack(content: string, title?: string): Promise<StudyRecord | null> {
    const trimmed = content.trim();
    if (!trimmed) {
      setError("Add a topic or some notes before generating a study pack.");
      return null;
    }
    if (trimmed.length > MAX_INPUT_LENGTH) {
      setError(`Keep your notes under ${MAX_INPUT_LENGTH.toLocaleString()} characters.`);
      return null;
    }

    setLoading(true);
    setError("");
    setNotice("");
    try {
      const pack = preview
        ? createPreviewStudyPack(trimmed, level)
        : await generateStudyPack(trimmed, level);
      const record: StudyRecord = {
        id: crypto.randomUUID(),
        title: title?.trim() || trimmed.split(/[.!?\n]/, 1)[0]?.slice(0, 70) || "Study pack",
        level,
        source: trimmed,
        createdAt: new Date().toISOString(),
        pack,
      };
      setResult(record);
      setRecords((current) => [record, ...current.filter((item) => item.title !== record.title)].slice(0, 20));
      setNotice(preview ? "Preview pack ready — it uses a local demo response." : "Your AI study pack is ready.");
      return record;
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "The study pack could not be generated. Please try again.",
      );
      return null;
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(file: File): Promise<void> {
    setUploading(true);
    setError("");
    try {
      if (file.size > 20 * 1024 * 1024) {
        setError("Files must be smaller than 20 MB.");
        return;
      }
      if (!/\.(pdf|txt)$/i.test(file.name)) {
        setError("Choose a PDF or TXT file.");
        return;
      }
      let text: string;
      if (file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf")) {
        const pdfjs = await import("pdfjs-dist");
        pdfjs.GlobalWorkerOptions.workerSrc = new URL(
          "pdfjs-dist/build/pdf.worker.min.mjs",
          import.meta.url,
        ).toString();
        const document = await pdfjs.getDocument({ data: await file.arrayBuffer() }).promise;
        const pages: string[] = [];
        for (let pageNumber = 1; pageNumber <= document.numPages; pageNumber += 1) {
          const page = await document.getPage(pageNumber);
          const content = await page.getTextContent();
          pages.push(content.items.map((item) => ("str" in item ? item.str : "")).join(" "));
        }
        text = pages.join("\n").trim();
      } else {
        text = await file.text();
      }

      if (!text.trim()) {
        setError("No readable text was found in that file. Try a text-based PDF or TXT file.");
        return;
      }
      if (text.length > MAX_INPUT_LENGTH) {
        setError(`The file is over ${MAX_INPUT_LENGTH.toLocaleString()} characters. Shorten it and try again.`);
        return;
      }
      setContentText(text);
      setNotice(`${file.name} is ready to simplify.`);
    } catch (fileError) {
      setError(fileError instanceof Error ? `Could not read the file: ${fileError.message}` : "Could not read the selected file.");
    } finally {
      setUploading(false);
      if (fileInput.current) fileInput.current.value = "";
    }
  }

  async function generateQuiz(): Promise<void> {
    const record = await createPack(quizText, "Practice quiz");
    if (record) {
      setQuizQuestions(record.pack.mcqs);
      setAnswers({});
    }
  }

  function showRecord(record: StudyRecord): void {
    setResult(record);
    setPage("Home");
    setError("");
    setNotice(`Opened “${record.title}” from your history.`);
  }

  const answeredCount = Object.keys(answers).length;
  const quizComplete = quizQuestions.length > 0 && answeredCount === quizQuestions.length;
  const correctCount = quizQuestions.reduce(
    (total, question, index) => total + (answers[index] === question.answer ? 1 : 0),
    0,
  );

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand" onClick={() => setPage("Home")} aria-label="Course Simplifier home">
          <span className="brand-mark">CS</span>
          <span className="brand-copy">
            <strong>Course Simplifier</strong>
            <small>AI Study Assistant</small>
          </span>
        </button>

        <p className="sidebar-label">Workspace</p>
        <nav className="navigation" aria-label="Main navigation">
          {NAV_ITEMS.map((item) => (
            <button
              className={`nav-item ${page === item.name ? "active" : ""}`}
              key={item.name}
              onClick={() => {
                setPage(item.name);
                setError("");
                setNotice("");
              }}
            >
              <span className="nav-icon" aria-hidden="true">{item.icon}</span>
              {item.name}
            </button>
          ))}
        </nav>

        <div className="sidebar-spacer" />
        <div className="sidebar-controls">
          <div className="mode-row">
            <span className="mode-indicator" />
            <span>{preview ? "Preview mode" : "Live IBM mode"}</span>
          </div>
          <label className="toggle-row">
            <span>Use live IBM Granite</span>
            <input
              type="checkbox"
              checked={!preview}
              onChange={(event) => {
                setPreview(!event.target.checked);
                setNotice(event.target.checked ? "Live mode selected." : "Preview mode selected.");
              }}
              aria-label="Use live IBM Granite"
            />
            <span className="toggle-ui" />
          </label>
          <button
            className="appearance-button"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          >
            <span aria-hidden="true">{theme === "dark" ? "☼" : "◐"}</span>
            {theme === "dark" ? "Light appearance" : "Dark appearance"}
          </button>
          <p className="sidebar-footnote">
            {preview
              ? "Try every feature without an API key."
              : "IBM credentials stay on the Netlify server."}
          </p>
        </div>
      </aside>

      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-title">
            <span className="mobile-brand-mark">CS</span>
            <span>{page}</span>
          </div>
          <div className="topbar-user">
            <span className="status-dot" />
            <span>Welcome, Student!</span>
          </div>
          <div className="mobile-controls">
            <button
              className="mobile-control-button"
              onClick={() => setPreview(!preview)}
              aria-label={preview ? "Switch to live IBM mode" : "Switch to Preview mode"}
              title={preview ? "Switch to live IBM mode" : "Switch to Preview mode"}
            >
              {preview ? "Preview" : "Live"}
            </button>
            <button
              className="mobile-control-button theme-control"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
              aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} appearance`}
              title={`Switch to ${theme === "dark" ? "light" : "dark"} appearance`}
            >
              {theme === "dark" ? "☼" : "◐"}
            </button>
          </div>
        </header>

        <div className="page-content">
          {error && (
            <div className="alert alert-error" role="alert">
              <span aria-hidden="true">!</span>
              <p>{error}</p>
              <button onClick={() => setError("")} aria-label="Dismiss error">×</button>
            </div>
          )}
          {notice && !error && (
            <div className="alert alert-success" role="status">
              <span aria-hidden="true">✓</span>
              <p>{notice}</p>
              <button onClick={() => setNotice("")} aria-label="Dismiss message">×</button>
            </div>
          )}

          {page === "Home" && (
            <HomePage
              text={homeText}
              setText={setHomeText}
              level={level}
              setLevel={setLevel}
              loading={loading}
              result={result}
              preview={preview}
              onGenerate={() => void createPack(homeText)}
              onExample={(example) => {
                setHomeText(example.text);
                void createPack(example.text, example.title);
              }}
              onDownload={downloadPack}
            />
          )}
          {page === "Simplify Content" && (
            <SimplifyPage
              text={contentText}
              setText={setContentText}
              level={level}
              setLevel={setLevel}
              loading={loading}
              uploading={uploading}
              preview={preview}
              result={result}
              fileInput={fileInput}
              onUpload={(file) => void handleUpload(file)}
              onGenerate={() => void createPack(contentText)}
              onSample={(text) => setContentText(text)}
              onDownload={downloadPack}
            />
          )}
          {page === "Study Materials" && (
            <MaterialsPage
              onUse={(passage) => {
                setContentText(passage.text);
                setPage("Simplify Content");
              }}
            />
          )}
          {page === "Quiz Generator" && (
            <QuizPage
              text={quizText}
              setText={setQuizText}
              level={level}
              setLevel={setLevel}
              loading={loading}
              questions={quizQuestions}
              answers={answers}
              setAnswers={setAnswers}
              completed={quizComplete}
              correctCount={correctCount}
              onGenerate={() => void generateQuiz()}
            />
          )}
          {page === "History" && (
            <HistoryPage records={records} onOpen={showRecord} onDownload={downloadPack} />
          )}
          {page === "About" && <AboutPage />}
        </div>
      </main>
    </div>
  );
}

interface LevelSelectProps {
  level: LearningLevel;
  setLevel: (level: LearningLevel) => void;
  id: string;
}

function LevelSelect({ level, setLevel, id }: LevelSelectProps) {
  return (
    <label className="level-select" htmlFor={id}>
      <span>Learning level</span>
      <select id={id} value={level} onChange={(event) => setLevel(event.target.value as LearningLevel)}>
        <option>Beginner</option>
        <option>Intermediate</option>
        <option>Advanced</option>
      </select>
    </label>
  );
}

interface BusyButtonProps {
  loading: boolean;
  onClick: () => void;
  label: string;
  className?: string;
  disabled?: boolean;
}

function BusyButton({ loading, onClick, label, className = "", disabled = false }: BusyButtonProps) {
  return (
    <button className={`primary-button ${className}`} onClick={onClick} disabled={loading || disabled}>
      {loading ? <><span className="spinner" /> Working…</> : <>{label}<span aria-hidden="true">→</span></>}
    </button>
  );
}

interface HomePageProps {
  text: string;
  setText: (text: string) => void;
  level: LearningLevel;
  setLevel: (level: LearningLevel) => void;
  loading: boolean;
  result: StudyRecord | null;
  preview: boolean;
  onGenerate: () => void;
  onExample: (example: (typeof HOME_EXAMPLES)[number]) => void;
  onDownload: (record: StudyRecord) => void;
}

function HomePage({
  text,
  setText,
  level,
  setLevel,
  loading,
  result,
  preview,
  onGenerate,
  onExample,
  onDownload,
}: HomePageProps) {
  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow"><span className="sparkle">✦</span> YOUR PERSONAL STUDY PARTNER</span>
          <h1>Make learning<br /><span>feel simpler.</span></h1>
          <p>Turn complex notes into friendly explanations, useful examples, and revision materials made for you.</p>
          <div className="hero-badges">
            <span>✦ Six clear note sections</span>
            <span>◉ Interactive quizzes</span>
            <span>↗ Made for your level</span>
          </div>
        </div>
        <div className="hero-art" aria-hidden="true">
          <div className="art-glow" />
          <div className="art-orbit orbit-one" />
          <div className="art-orbit orbit-two" />
          <div className="art-book">
            <span className="book-spark">✦</span>
            <span className="book-line line-one" />
            <span className="book-line line-two" />
            <span className="book-line line-three" />
            <span className="book-dot" />
          </div>
          <span className="float-star star-one">✦</span>
          <span className="float-star star-two">✧</span>
        </div>
      </section>

      <section className="home-compose panel">
        <div className="section-heading">
          <div>
            <span className="eyebrow">START HERE</span>
            <h2>Tell me what to simplify</h2>
          </div>
          <span className="privacy-chip">{preview ? "Local preview" : "Secure server request"}</span>
        </div>
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Paste your notes or ask a question…"
          rows={4}
          maxLength={MAX_INPUT_LENGTH}
        />
        <div className="compose-footer">
          <span className="input-hint">{text.length.toLocaleString()} / {MAX_INPUT_LENGTH.toLocaleString()} characters</span>
          <div className="compose-actions">
            <LevelSelect level={level} setLevel={setLevel} id="home-level" />
            <BusyButton loading={loading} onClick={onGenerate} label="Create study pack" />
          </div>
        </div>
      </section>

      <section className="examples-section">
        <div className="section-heading compact-heading">
          <div>
            <span className="eyebrow">QUICK START</span>
            <h2>What would you like to learn today?</h2>
          </div>
          <span className="muted-count">Four ways to get started</span>
        </div>
        <div className="example-grid">
          {HOME_EXAMPLES.map((example, index) => (
            <button
              className="example-card"
              key={example.key}
              onClick={() => onExample(example)}
              disabled={loading}
            >
              <span className={`example-icon icon-${index + 1}`}>{["✎", "✧", "◉", "▤"][index]}</span>
              <span className="example-title">{example.title}</span>
              <span className="example-description">{example.description}</span>
              <span className="card-arrow">↗</span>
            </button>
          ))}
        </div>
      </section>

      {result && (
        <StudyPackView
          record={result}
          preview={preview}
          onDownload={() => onDownload(result)}
        />
      )}
    </>
  );
}

interface SimplifyPageProps {
  text: string;
  setText: (text: string) => void;
  level: LearningLevel;
  setLevel: (level: LearningLevel) => void;
  loading: boolean;
  uploading: boolean;
  preview: boolean;
  result: StudyRecord | null;
  fileInput: React.RefObject<HTMLInputElement | null>;
  onUpload: (file: File) => void;
  onGenerate: () => void;
  onSample: (text: string) => void;
  onDownload: (record: StudyRecord) => void;
}

function SimplifyPage(props: SimplifyPageProps) {
  const sample = SAMPLE_PASSAGES.find((item) => item.text === props.text);
  return (
    <section className="work-page">
      <div className="page-intro">
        <span className="eyebrow">YOUR STUDY DESK</span>
        <h1>Let's simplify it.</h1>
        <p>Paste your course notes, choose a sample topic, or upload a text-based PDF.</p>
      </div>
      <div className="panel editor-panel">
        <div className="editor-toolbar">
          <span className="toolbar-label">YOUR CONTENT</span>
          <div className="editor-tools">
            <select
              aria-label="Choose sample passage"
              value={sample?.id ?? ""}
              onChange={(event) => {
                const passage = SAMPLE_PASSAGES.find((item) => item.id === event.target.value);
                if (passage) props.onSample(passage.text);
              }}
            >
              <option value="">Choose a sample topic</option>
              {SAMPLE_PASSAGES.map((passage) => <option value={passage.id} key={passage.id}>{passage.title}</option>)}
            </select>
            <button className="secondary-button" onClick={() => props.fileInput.current?.click()} disabled={props.uploading}>
              {props.uploading ? "Reading…" : "↑ Upload TXT / PDF"}
            </button>
          </div>
        </div>
        <input
          ref={props.fileInput}
          className="visually-hidden"
          type="file"
          accept=".txt,.pdf,text/plain,application/pdf"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) props.onUpload(file);
          }}
        />
        <textarea
          value={props.text}
          onChange={(event) => props.setText(event.target.value)}
          placeholder="Paste course notes or enter a topic to explain…"
          rows={12}
          maxLength={MAX_INPUT_LENGTH}
        />
        <div className="compose-footer">
          <span className="input-hint">{props.text.length.toLocaleString()} / {MAX_INPUT_LENGTH.toLocaleString()} characters</span>
          <div className="compose-actions">
            <LevelSelect level={props.level} setLevel={props.setLevel} id="simplify-level" />
            <BusyButton loading={props.loading} onClick={props.onGenerate} label="Simplify content" />
          </div>
        </div>
      </div>
      {props.result && (
        <StudyPackView
          record={props.result}
          preview={props.preview}
          onDownload={() => props.onDownload(props.result!)}
        />
      )}
    </section>
  );
}

function MaterialsPage({ onUse }: { onUse: (passage: (typeof SAMPLE_PASSAGES)[number]) => void }) {
  return (
    <section className="work-page">
      <div className="page-intro">
        <span className="eyebrow">START WITH A SAMPLE</span>
        <h1>Study materials</h1>
        <p>Explore a topic, then send it straight to the simplifier.</p>
      </div>
      <div className="materials-grid">
        {SAMPLE_PASSAGES.map((passage, index) => (
          <article className="panel material-card" key={passage.id}>
            <span className={`material-number material-${index + 1}`}>0{index + 1}</span>
            <h2>{passage.title}</h2>
            <p>{passage.text}</p>
            <button className="text-button" onClick={() => onUse(passage)}>
              Use these notes <span aria-hidden="true">→</span>
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}

interface QuizPageProps {
  text: string;
  setText: (text: string) => void;
  level: LearningLevel;
  setLevel: (level: LearningLevel) => void;
  loading: boolean;
  questions: MultipleChoiceQuestion[];
  answers: Record<number, string>;
  setAnswers: (answers: Record<number, string>) => void;
  completed: boolean;
  correctCount: number;
  onGenerate: () => void;
}

function QuizPage(props: QuizPageProps) {
  return (
    <section className="work-page">
      <div className="page-intro">
        <span className="eyebrow">PRACTICE MAKES PROGRESS</span>
        <h1>Quiz generator</h1>
        <p>Build a five-question quiz from your notes and check your understanding.</p>
      </div>
      <div className="panel quiz-input">
        <textarea
          value={props.text}
          onChange={(event) => props.setText(event.target.value)}
          placeholder="Paste notes or type a topic for your quiz…"
          rows={5}
          maxLength={MAX_INPUT_LENGTH}
        />
        <div className="compose-footer">
          <span className="input-hint">{props.text.length.toLocaleString()} / {MAX_INPUT_LENGTH.toLocaleString()} characters</span>
          <div className="compose-actions">
            <LevelSelect level={props.level} setLevel={props.setLevel} id="quiz-level" />
            <BusyButton loading={props.loading} onClick={props.onGenerate} label="Generate quiz" />
          </div>
        </div>
      </div>
      {props.questions.length > 0 && (
        <div className="quiz-results">
          {props.completed && (
            <div className="score-banner">
              <span className="score-icon">✦</span>
              <div><strong>You scored {props.correctCount} out of {props.questions.length}</strong><span>Review each answer below and try again when you're ready.</span></div>
            </div>
          )}
          {props.questions.map((question, index) => (
            <QuestionCard
              key={`${index}-${question.question}`}
              index={index}
              question={question}
              selected={props.answers[index]}
              onSelect={(answer) => props.setAnswers({ ...props.answers, [index]: answer })}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function QuestionCard({
  index,
  question,
  selected,
  onSelect,
}: {
  index: number;
  question: MultipleChoiceQuestion;
  selected?: string | undefined;
  onSelect: (answer: string) => void;
}) {
  return (
    <article className="panel question-card">
      <span className="question-count">QUESTION {String(index + 1).padStart(2, "0")}</span>
      <h3>{question.question}</h3>
      <div className="option-list">
        {Object.entries(question.options).map(([key, text]) => {
          const isCorrect = selected && key === question.answer;
          const isWrong = selected === key && key !== question.answer;
          return (
            <button
              key={key}
              className={`quiz-option ${isCorrect ? "correct" : ""} ${isWrong ? "incorrect" : ""}`}
              onClick={() => onSelect(key)}
              disabled={Boolean(selected)}
            >
              <span className="option-key">{key}</span>
              <span>{text}</span>
              {isCorrect && <span className="option-check">✓</span>}
              {isWrong && <span className="option-check">×</span>}
            </button>
          );
        })}
      </div>
      {selected && (
        <p className={`answer-feedback ${selected === question.answer ? "feedback-correct" : "feedback-wrong"}`}>
          {selected === question.answer ? "That's right!" : `Not quite. The correct answer is ${question.answer}.`}
        </p>
      )}
    </article>
  );
}

function HistoryPage({
  records,
  onOpen,
  onDownload,
}: {
  records: StudyRecord[];
  onOpen: (record: StudyRecord) => void;
  onDownload: (record: StudyRecord) => void;
}) {
  return (
    <section className="work-page">
      <div className="page-intro">
        <span className="eyebrow">YOUR RECENT WORK</span>
        <h1>Study history</h1>
        <p>Your last 20 study packs are saved in this browser.</p>
      </div>
      {records.length === 0 ? (
        <div className="panel empty-state">
          <span className="empty-icon">◷</span>
          <h2>Nothing here just yet</h2>
          <p>Your study packs will show up here after you create one.</p>
        </div>
      ) : (
        <div className="history-list">
          {records.map((record) => (
            <article className="panel history-card" key={record.id}>
              <div className="history-icon">▤</div>
              <div className="history-copy">
                <h2>{record.title}</h2>
                <p>{new Date(record.createdAt).toLocaleString()} · {record.level}</p>
                <span>{record.source.slice(0, 150)}{record.source.length > 150 ? "…" : ""}</span>
              </div>
              <div className="history-actions">
                <button className="secondary-button" onClick={() => onOpen(record)}>Open</button>
                <button className="icon-button" onClick={() => onDownload(record)} aria-label={`Download ${record.title}`}>↓</button>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}

function AboutPage() {
  return (
    <section className="work-page">
      <div className="page-intro">
        <span className="eyebrow">ABOUT THIS PROJECT</span>
        <h1>Learning, made clearer.</h1>
        <p>Course Simplifier helps learners turn challenging academic material into a study format they can use.</p>
      </div>
      <div className="about-grid">
        <article className="panel about-card">
          <span className="about-symbol">✦</span>
          <h2>A complete study pack</h2>
          <p>Each response contains six clear note sections, five multiple-choice questions, and five revision prompts.</p>
        </article>
        <article className="panel about-card">
          <span className="about-symbol">◉</span>
          <h2>Learn at your level</h2>
          <p>Choose beginner, intermediate, or advanced explanations to match your learning needs.</p>
        </article>
        <article className="panel about-card">
          <span className="about-symbol">⌘</span>
          <h2>Private credentials</h2>
          <p>Live IBM credentials are read by a Netlify Function and are never included in the browser bundle.</p>
        </article>
      </div>
      <div className="panel setup-card">
        <span className="eyebrow">DEPLOYMENT NOTES</span>
        <h2>Preview works right away</h2>
        <p>Preview mode uses local sample responses and needs no API key. To use live IBM Granite, add <code>WATSONX_API_KEY</code> and <code>WATSONX_PROJECT_ID</code> as Netlify function environment variables, then redeploy.</p>
        <p>Optional settings: <code>WATSONX_URL</code> defaults to the US South endpoint; <code>GRANITE_MODEL_ID</code> defaults to IBM Granite 3 8B Instruct. Never use a <code>VITE_</code> prefix for secrets.</p>
      </div>
    </section>
  );
}

function StudyPackView({
  record,
  preview,
  onDownload,
}: {
  record: StudyRecord;
  preview: boolean;
  onDownload: () => void;
}) {
  return (
    <section className="study-output">
      <div className="output-heading">
        <div>
          <span className="eyebrow">{preview ? "PREVIEW STUDY PACK" : "YOUR STUDY PACK"}</span>
          <h2>{record.title}</h2>
          <p>{record.level} level · {new Date(record.createdAt).toLocaleString()}</p>
        </div>
        <button className="secondary-button" onClick={onDownload}>↓ Download notes</button>
      </div>
      <div className="study-section-grid">
        {STUDY_SECTIONS.map((section, index) => (
          <article className="panel study-section-card" key={section}>
            <span className={`section-index section-${index + 1}`}>0{index + 1}</span>
            <h3>{section}</h3>
            <p>{record.pack.sections[section]}</p>
          </article>
        ))}
      </div>
      <div className="panel revision-card knowledge-check">
        <div className="revision-header"><span className="about-symbol">◉</span><div><h3>Knowledge check</h3><p>Review the questions and answers, or use Quiz Generator to try them interactively.</p></div></div>
        <ol>
          {record.pack.mcqs.map((question, index) => (
            <li className="knowledge-question" key={`${question.question}-${index}`}>
              <strong>{question.question}</strong>
              <div className="knowledge-options">
                {Object.entries(question.options).map(([key, text]) => (
                  <span className={key === question.answer ? "knowledge-answer" : ""} key={key}>
                    {key}) {text}{key === question.answer ? " ✓" : ""}
                  </span>
                ))}
              </div>
            </li>
          ))}
        </ol>
      </div>
      <div className="panel revision-card">
        <div className="revision-header"><span className="about-symbol">↗</span><div><h3>Revision questions</h3><p>Pause and answer these in your own words.</p></div></div>
        <ol>{record.pack.revision_questions.map((question, index) => <li key={`${question}-${index}`}>{question}</li>)}</ol>
      </div>
    </section>
  );
}

export default App;
