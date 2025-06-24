import os
import io
import json
import fitz  # PyMuPDF for PDFs
from docx import Document
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AzureOpenAI

# ---------------- Configuration ----------------
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "")

# ---------------- Azure OpenAI Client Setup ----------------
client = AzureOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_KEY,
    api_version="2024-05-01-preview"
)

# ---------------- FastAPI Setup ----------------
app = FastAPI(title="Resume")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to hold Job Description text
jd_text: str = None

# ---------------- Utility Functions ----------------
def extract_text_from_file(file: UploadFile) -> str:
    contents = file.file.read()
    filename = file.filename.lower()

    if filename.endswith(".pdf"):
        with fitz.open(stream=contents, filetype="pdf") as doc:
            return "\n".join(page.get_text() for page in doc)
    elif filename.endswith(".docx"):
        doc = Document(io.BytesIO(contents))
        return "\n".join(para.text for para in doc.paragraphs)
    elif filename.endswith(".txt"):
        return contents.decode("utf-8")
    else:
        raise HTTPException(status_code=400, detail="Unsupported file format. Use PDF, DOCX, or TXT.")

def build_prompt(jd_text: str, resume_text: str):
    return [
        {
            "role": "system",
            "content": "You are an AI assistant that screens resumes against job descriptions."
        },
        {
            "role": "user",
            "content": f"""
Analyze the following:

--- JOB DESCRIPTION ---
{jd_text}

--- CANDIDATE RESUME ---
{resume_text}

Perform these tasks:
1. Extract required skills from the job description.
2. Extract skills from the resume.
3. Identify:
   - matched_skills
   - missing_skills
   - additional_skills
4. Extract location and email from JD or resume.
5. Calculate skill match percentage.

Provide results in the following format:
{{
  "required_skills": ["skill1", "skill2"],
  "matched_skills": ["skill1", "skill3"],
  "missing_skills": ["skill2"],
  "additional_skills": ["skill5"],
  "match_percentage": 80,
  "location": "City, Country",
  "email": "email@example.com"
}}
"""
        }
    ]

# ---------------- API Endpoints ----------------

@app.post("/upload-jd")
async def upload_job_description(file: UploadFile = File(...)):
    global jd_text
    try:
        jd_text = extract_text_from_file(file)
        print("Job Description Text Extracted:", jd_text[:500])  # Log first 500 chars for debugging
        if not jd_text.strip():
            raise HTTPException(status_code=400, detail="Job description is empty.")
        return {"message": "Job description uploaded successfully."}
    except Exception as e:
        print(f"Error extracting job description: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload-resumes")
async def upload_resumes(files: List[UploadFile] = File(...)):
    global jd_text

    if not jd_text:
        raise HTTPException(status_code=400, detail="Upload job description first using /upload-jd")

    results = []

    for file in files:
        try:
            resume_text = extract_text_from_file(file)
            print(f"Resume Text for {file.filename}: {resume_text[:200]}...")  # Log first 200 chars

            if not resume_text.strip():
                results.append({
                    "resume_filename": file.filename,
                    "error": "Resume text extraction failed or is empty"
                })
                continue

            messages = build_prompt(jd_text, resume_text)

            response = client.chat.completions.create(
                model=AZURE_DEPLOYMENT_NAME,
                messages=messages,
                max_tokens=1500,
                temperature=0.3
            )

            # Print the full response for debugging
            print(f"Full OpenAI API response for {file.filename}: {response}")

            result_str = response.choices[0].message.content.strip()
            print(f"OpenAI Response for {file.filename}: {result_str}")

            if not result_str:
                results.append({
                    "resume_filename": file.filename,
                    "error": "Empty response from OpenAI."
                })
                continue

            try:
                result_json = json.loads(result_str)
            except json.JSONDecodeError as jde:
                print(f"JSON decode error for {file.filename}: {jde}")
                results.append({
                    "resume_filename": file.filename,
                    "error": f"Invalid JSON from OpenAI: {jde}",
                    "raw_response": result_str
                })
                continue

            results.append({
                "resume_filename": file.filename,
                **result_json
            })

        except Exception as e:
            print(f"Error processing resume {file.filename}: {e}")
            results.append({
                "resume_filename": file.filename,
                "error": str(e)
            })

    valid_results = [
        r for r in results if "match_percentage" in r and isinstance(r["match_percentage"], (int, float))
    ]
    sorted_results = sorted(valid_results, key=lambda x: x["match_percentage"], reverse=True)

    return {
        "results": sorted_results,
        "all_results": results  # Include all results for debugging
    }

