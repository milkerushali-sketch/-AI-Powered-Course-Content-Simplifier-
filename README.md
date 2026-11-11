# AI-Powered Course Content Simplifier

**Problem Statement #19 · Course Content Simplification Agent**

Turn difficult course content into learner-friendly explanations, examples, revision notes, and quizzes. The Netlify deployment uses a React + Vite frontend and a server-side Netlify Function that can call IBM watsonx.ai / Granite.

## Features

- Six structured study-note sections, five multiple-choice questions, and five revision questions
- Beginner, intermediate, and advanced learning levels
- Interactive quizzes with answer feedback and scores
- Five built-in sample passages, TXT/PDF upload, downloadable study packs, and browser history
- Dark and light appearance
- Preview mode works without IBM credentials or external API calls

## Deploy to Netlify

1. Push this repository to GitHub and select **Add new site → Import an existing project** in Netlify.
2. Select the repository. `netlify.toml` configures the build command (`npm run build`), publish directory (`dist`), and Netlify Function directory.
3. Use Node.js **22.12 or newer**. The repository includes `.nvmrc` and sets `NODE_VERSION` for Netlify.
4. Deploy. The site works immediately in Preview mode; no secrets are required to demonstrate the app.

### Enable live IBM Granite

In the Netlify site dashboard, open **Site configuration → Environment variables** and add these variables for the Functions runtime:

| Variable | Required | Description |
|---|---:|---|
| `WATSONX_API_KEY` | Yes | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | Yes | watsonx.ai project ID |
| `WATSONX_URL` | No | Regional endpoint; defaults to `https://us-south.ml.cloud.ibm.com` |
| `GRANITE_MODEL_ID` | No | Model ID; defaults to `ibm/granite-3-8b-instruct` |

After saving or changing variables, trigger a new deploy. In the app sidebar, switch off **Use live IBM Granite** to make live requests.

**Keep IBM credentials server-side.** Do not add them to source code, `netlify.toml`, or any `VITE_` variable. The browser calls `/api/study-pack`; the Netlify Function reads the secrets at runtime.

If IBM returns `BXNIM0415E` or says the key could not be found, create a fresh API key in [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys), replace `WATSONX_API_KEY` in Netlify, and redeploy. Check that the project ID and regional URL belong to the same watsonx.ai account and region.

> The live function is a public endpoint for this educational demo. Before promoting a high-traffic public site, add access control or rate limiting and set IBM usage/quota alerts.

## Local development

Requirements: Node.js 22.12+ and npm.

```powershell
npm ci
npm run dev
```

The Vite/Netlify plugin serves the frontend and local functions. Preview mode is enabled by default. To test live calls locally, configure the same IBM environment variables in the local Netlify environment; never commit a real `.env` file.

Run the checks and production build:

```powershell
npm test
npm run build
```

The original Python/Streamlit implementation is retained in `app.py` for reference and local use (`npm run dev:streamlit`). It is not the Netlify deployment entry point.

## Architecture

```text
React + Vite
  ├─ Preview study packs (local; no network request)
  └─ POST /api/study-pack
       └─ Netlify Function
            ├─ IBM IAM token (server-side)
            └─ watsonx.ai text generation (server-side)
```

The server validates request size and learning level, verifies the structured model response, and returns a fixed study-pack shape. The app keeps the latest 20 study packs in browser storage.

## Project files

| Path | Purpose |
|---|---|
| `src/App.tsx` | React app pages, forms, theme, history, and interactions |
| `src/lib/studyPack.ts` | Preview responses and study-pack export formatting |
| `netlify/functions/study-pack.ts` | Validated server-side IBM IAM and watsonx.ai integration |
| `netlify.toml` | Netlify build, function, routing, and response-header configuration |
| `app.py`, `granite.py`, `dataset.py` | Retained Streamlit implementation |

Built with React, Vite, Netlify Functions, and IBM watsonx.ai · Edunet Foundation
