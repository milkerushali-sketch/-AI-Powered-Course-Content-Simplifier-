# AI-Powered Course Content Simplifier

**Problem Statement #19 — Course Content Simplification Agent**

Course Content Simplifier turns difficult learning material into clear, level-appropriate study resources. Enter a topic or course text, upload a TXT or PDF file, or try a built-in sample to create notes, quizzes, and revision questions.

The main application uses React, Vite, and TypeScript. It can generate study packs locally in preview mode or use IBM watsonx.ai with the IBM Granite model for live generation.

## Features

- Generate six structured note sections, five multiple-choice questions, and five revision questions.
- Choose a beginner, intermediate, or advanced learning level.
- Take interactive quizzes with answer feedback and scores.
- Provide text, upload a TXT or PDF file, or select from five built-in samples.
- Download study packs and revisit the latest 20 packs saved in the browser.
- Switch between dark and light appearance.
- Use preview mode without IBM credentials or external AI requests.

## IBM Technologies Used

- **IBM watsonx.ai** — processes learner-provided course material and returns generated study packs.
- **IBM Granite 3-8B Instruct** — generates simplified notes, quiz questions, and revision questions.
- **IBM Cloud IAM** — securely authenticates server-side requests to watsonx.ai.

## Run locally

### 1. Install the prerequisites

- [Git](https://git-scm.com/downloads)
- [Node.js 22.12 or newer](https://nodejs.org/) (npm is included)

Check that Node.js and npm are available:

```powershell
node --version
npm --version
```

### 2. Clone the repository

Replace the example URL and folder name with the repository URL and name:

```powershell
git clone <repository-url>
Set-Location <repository-folder>
```

### 3. Install dependencies

```powershell
npm ci
```

### 4. Start the development server

```powershell
npm run dev
```

Open the local URL printed in the terminal (usually `http://127.0.0.1:5173`). Preview mode works without IBM credentials. Keep the terminal running while you use the app; press **Ctrl+C** to stop the server.

## Enable live IBM Granite generation (optional)

Live generation requires an IBM Cloud API key and a watsonx.ai project ID. The app works in preview mode without them.

1. Copy the example environment file:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Open `.env` and replace the example values:

   ```text
   WATSONX_API_KEY=your_ibm_cloud_api_key
   WATSONX_PROJECT_ID=your_watsonx_project_id
   WATSONX_URL=https://us-south.ml.cloud.ibm.com
   GRANITE_MODEL_ID=ibm/granite-3-8b-instruct
   ```

3. Restart the development server if it was already running, then enable live IBM Granite in the app.

Keep `.env` private. Do not commit credentials or expose them through client-side `VITE_` variables. The API key and project ID are used by the server-side function.

| Variable             | Required for live generation | Default or purpose                              |
| -------------------- | ---------------------------: | ----------------------------------------------- |
| `WATSONX_API_KEY`    |                          Yes | IBM Cloud API key                               |
| `WATSONX_PROJECT_ID` |                          Yes | watsonx.ai project ID                           |
| `WATSONX_URL`        |                           No | Defaults to `https://us-south.ml.cloud.ibm.com` |
| `GRANITE_MODEL_ID`   |                           No | Defaults to `ibm/granite-3-8b-instruct`         |

## Run checks

Run the test suite:

```powershell
npm test
```

Run type checks and create a production build:

```powershell
npm run build
```

The production build is written to `dist/`.

## Optional: run the retained Streamlit version

The repository also contains an earlier Python/Streamlit implementation. To run it locally, create and activate a virtual environment, install the Python requirements, and start Streamlit:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
npm run dev:streamlit
```

The Streamlit version is separate from the React application.

## How the application works

1. The learner provides course material and selects a learning level.
2. Preview mode creates a sample study pack locally, without an AI request.
3. Live mode sends the content to `/api/study-pack`.
4. The server-side function authenticates with IBM IAM and requests generation from watsonx.ai.
5. The response is validated and presented as notes, quiz questions, and revision questions.

The current implementation uses a prompt-driven IBM Granite model workflow. It does not currently use Langflow, RAG, or multiple collaborating agents.

## Project structure

| Path                                 | Purpose                                                    |
| ------------------------------------ | ---------------------------------------------------------- |
| `src/App.tsx`                        | React application, forms, theme, history, and interactions |
| `src/lib/studyPack.ts`               | Preview study packs and export formatting                  |
| `src/types.ts`                       | Shared study-pack types                                    |
| `netlify/functions/study-pack.ts`    | Server-side IBM IAM and watsonx.ai integration             |
| `server.mjs`                         | Node.js server for the frontend and study-pack API         |
| `netlify.toml`                       | Local Vite/Netlify plugin and function configuration       |
| `app.py`, `granite.py`, `dataset.py` | Retained Python/Streamlit implementation                   |

---

Made by **Vrushali Milke**, with a mission to make learning clearer and more joyful.

Built using React, Vite, TypeScript, and IBM watsonx.ai.
