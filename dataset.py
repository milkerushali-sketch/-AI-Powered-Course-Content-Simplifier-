"""
dataset.py — Kaggle CommonLit dataset processing
Handles CSV loading, column inspection, passage retrieval, and comparison.

Fixes applied:
- load_from_kagglehub() walks subdirectories to find the CSV files regardless of
  where kagglehub places them.
- load_csv_from_upload() accepts a fresh UploadedFile each call (no session-state
  caching here — that lives in app.py).
- get_student_summaries() uses 'text' column for summaries (not 'prompt_id').
"""

import os
import pandas as pd
from typing import Optional, Tuple, List, Dict


# ---------------------------------------------------------------------------
# kagglehub auto-download
# ---------------------------------------------------------------------------
KAGGLE_COMPETITION  = "commonlit-evaluate-student-summaries"
_PROMPTS_FILENAME   = "prompts_train.csv"
_SUMMARIES_FILENAME = "summaries_train.csv"


def _find_file(root: str, filename: str) -> Optional[str]:
    """Walk a directory tree and return the first path matching filename."""
    for dirpath, _dirs, files in os.walk(root):
        if filename in files:
            return os.path.join(dirpath, filename)
    return None


def load_from_kagglehub() -> Tuple[
    Optional[pd.DataFrame],  # prompts_df
    Optional[pd.DataFrame],  # summaries_df
    str,                     # error message (empty string on success)
]:
    """
    Download the CommonLit competition files via kagglehub and return
    (prompts_df, summaries_df, "").  Returns (None, None, error_message) on failure.

    Requirements:
    - kagglehub installed: pip install kagglehub
    - Kaggle credentials in ~/.kaggle/kaggle.json  OR  env vars
      KAGGLE_USERNAME and KAGGLE_KEY.
    - Competition rules accepted at:
      https://www.kaggle.com/c/commonlit-evaluate-student-summaries
    """
    try:
        import kagglehub
    except ImportError:
        return None, None, (
            "kagglehub is not installed.\n"
            "Run:  pip install kagglehub"
        )

    try:
        path = kagglehub.competition_download(KAGGLE_COMPETITION)
    except Exception as exc:
        return None, None, (
            f"kagglehub download failed: {exc}\n\n"
            "Checklist:\n"
            "1. Kaggle credentials exist at ~/.kaggle/kaggle.json  "
            "(or env vars KAGGLE_USERNAME / KAGGLE_KEY are set).\n"
            "2. You have accepted the competition rules at "
            "https://www.kaggle.com/c/commonlit-evaluate-student-summaries\n"
            "3. You are connected to the internet."
        )

    # kagglehub may return a path to a directory or to a zip extraction.
    # Walk the tree to find the CSV files.
    prompts_path   = _find_file(path, _PROMPTS_FILENAME)
    summaries_path = _find_file(path, _SUMMARIES_FILENAME)

    if prompts_path is None:
        return None, None, (
            f"Downloaded competition files but could not find '{_PROMPTS_FILENAME}' "
            f"inside '{path}'.\n"
            "The competition data may be structured differently. "
            "Try the manual CSV upload instead."
        )
    if summaries_path is None:
        return None, None, (
            f"Downloaded competition files but could not find '{_SUMMARIES_FILENAME}' "
            f"inside '{path}'.\n"
            "The competition data may be structured differently. "
            "Try the manual CSV upload instead."
        )

    prompts_df, err1 = load_csv(prompts_path)
    if err1:
        return None, None, f"Could not read {_PROMPTS_FILENAME}: {err1}"

    summaries_df, err2 = load_csv(summaries_path)
    if err2:
        return None, None, f"Could not read {_SUMMARIES_FILENAME}: {err2}"

    return prompts_df, summaries_df, ""


# ---------------------------------------------------------------------------
# CSV loading helpers
# ---------------------------------------------------------------------------
def load_csv(filepath: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load a CSV from a file path.
    Returns (DataFrame, "") on success or (None, error_message) on failure.
    """
    if not filepath or not os.path.exists(filepath):
        return None, f"File not found: {filepath}"
    try:
        df = pd.read_csv(filepath)
        if df.empty:
            return None, "The CSV file is empty."
        return df, ""
    except Exception as exc:
        return None, f"Could not read CSV: {exc}"


def load_csv_from_upload(uploaded_file) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load a CSV from a Streamlit UploadedFile object.
    Returns (DataFrame, "") on success or (None, error_message) on failure.
    """
    if uploaded_file is None:
        return None, "No file provided."
    try:
        uploaded_file.seek(0)          # reset pointer in case it was read before
        df = pd.read_csv(uploaded_file)
        if df.empty:
            return None, "The uploaded CSV file is empty."
        return df, ""
    except Exception as exc:
        return None, f"Could not read uploaded CSV: {exc}"


# ---------------------------------------------------------------------------
# Column inspection helpers
# ---------------------------------------------------------------------------
def inspect_columns(df: pd.DataFrame) -> Dict:
    """Return column names, dtypes, null counts, and sample values."""
    info = {}
    for col in df.columns:
        non_null = df[col].dropna()
        info[col] = {
            "dtype":      str(df[col].dtype),
            "null_count": int(df[col].isna().sum()),
            "sample":     str(non_null.iloc[0])[:120] if len(non_null) > 0 else "N/A",
        }
    return info


def find_text_column(df: pd.DataFrame) -> Optional[str]:
    """
    Heuristically find the column most likely to contain long passage text.
    Checks known column names first, then picks the column with the longest
    average string length.
    """
    preferred = ["prompt_text", "text", "passage", "content", "summary"]
    for col in preferred:
        if col in df.columns:
            return col
    str_cols = df.select_dtypes(include="object").columns.tolist()
    if not str_cols:
        return None
    avg_len = {c: df[c].dropna().str.len().mean() for c in str_cols}
    return max(avg_len, key=avg_len.get)


def find_id_column(df: pd.DataFrame) -> Optional[str]:
    preferred = ["prompt_id", "student_id", "id"]
    for col in preferred:
        if col in df.columns:
            return col
    return df.columns[0] if len(df.columns) > 0 else None


def find_title_column(df: pd.DataFrame) -> Optional[str]:
    preferred = ["prompt_title", "title", "prompt_question"]
    for col in preferred:
        if col in df.columns:
            return col
    return None


# ---------------------------------------------------------------------------
# Passage and summary retrieval
# ---------------------------------------------------------------------------
def get_passages(prompts_df: pd.DataFrame, max_passages: int = 20) -> List[Dict]:
    """
    Extract a list of passages from the prompts CSV.
    Returns a list of dicts: {id, title, text}.
    """
    text_col  = find_text_column(prompts_df)
    id_col    = find_id_column(prompts_df)
    title_col = find_title_column(prompts_df)

    if text_col is None:
        return []

    passages = []
    for _, row in prompts_df.dropna(subset=[text_col]).head(max_passages).iterrows():
        passages.append({
            "id":    str(row[id_col])    if id_col    else "unknown",
            "title": str(row[title_col]) if title_col else "Untitled",
            "text":  str(row[text_col]),
        })
    return passages


def get_student_summaries(
    summaries_df: pd.DataFrame,
    prompt_id: str,
    max_summaries: int = 5,
) -> List[str]:
    """
    Return up to max_summaries student-written summaries for a given prompt_id.
    The summaries_train.csv has columns: student_id, prompt_id, text, content, wording.
    We filter on prompt_id and return the 'text' column values.
    """
    if summaries_df is None or summaries_df.empty:
        return []

    # Find the student summary text column (should be 'text' for CommonLit dataset)
    text_col = None
    for candidate in ["text", "summary", "content"]:
        if candidate in summaries_df.columns:
            text_col = candidate
            break
    if text_col is None:
        text_col = find_text_column(summaries_df)
    if text_col is None:
        return []

    # Filter by prompt_id if the column exists
    if "prompt_id" in summaries_df.columns:
        mask   = summaries_df["prompt_id"].astype(str) == str(prompt_id)
        subset = summaries_df[mask].dropna(subset=[text_col])
    else:
        subset = summaries_df.dropna(subset=[text_col])

    return subset[text_col].head(max_summaries).tolist()


# ---------------------------------------------------------------------------
# Sample built-in passages (used when Kaggle files are not yet loaded)
# ---------------------------------------------------------------------------
SAMPLE_PASSAGES = [
    {
        "id": "sample_01",
        "title": "Photosynthesis",
        "text": (
            "Photosynthesis is the process by which green plants, algae, and some bacteria "
            "convert light energy, usually from the sun, into chemical energy stored in glucose. "
            "This process occurs primarily in the chloroplasts of plant cells, using chlorophyll "
            "to absorb light. The overall equation is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2. "
            "Photosynthesis is fundamental to life on Earth because it produces oxygen and forms "
            "the base of the food chain."
        ),
    },
    {
        "id": "sample_02",
        "title": "Newton's Laws of Motion",
        "text": (
            "Newton's three laws of motion describe the relationship between a body and the forces "
            "acting upon it. The First Law states that an object at rest stays at rest and an object "
            "in motion stays in motion unless acted upon by an external force (inertia). "
            "The Second Law states that Force equals mass times acceleration (F = ma). "
            "The Third Law states that for every action there is an equal and opposite reaction. "
            "These laws form the foundation of classical mechanics."
        ),
    },
    {
        "id": "sample_03",
        "title": "The Water Cycle",
        "text": (
            "The water cycle, also known as the hydrological cycle, describes the continuous movement "
            "of water on, above, and below the surface of the Earth. Key stages include evaporation "
            "(water turns to vapor from oceans and lakes), condensation (vapor cools to form clouds), "
            "precipitation (water falls as rain or snow), and collection (water gathers in rivers, "
            "lakes, and groundwater). The water cycle is driven by solar energy and gravity, and it "
            "is essential for distributing freshwater around the planet."
        ),
    },
    {
        "id": "sample_04",
        "title": "DNA and Genetics",
        "text": (
            "Deoxyribonucleic acid (DNA) is a molecule that carries the genetic instructions for "
            "the development, functioning, growth, and reproduction of all known living organisms. "
            "DNA is structured as a double helix — two strands coiled around each other — made up "
            "of nucleotide base pairs: adenine (A) pairs with thymine (T), and cytosine (C) pairs "
            "with guanine (G). Genes are specific sequences of DNA that encode instructions for "
            "building proteins, which carry out most of the work in cells."
        ),
    },
    {
        "id": "sample_05",
        "title": "Supply and Demand in Economics",
        "text": (
            "Supply and demand is one of the most fundamental concepts in economics. "
            "Demand refers to how much of a product consumers are willing and able to buy at "
            "various prices, while supply refers to how much producers are willing and able to "
            "sell at various prices. When demand rises and supply remains constant, prices tend "
            "to increase. When supply exceeds demand, prices tend to fall. The equilibrium price "
            "is the point where quantity supplied equals quantity demanded, resulting in a stable "
            "market price."
        ),
    },
]
