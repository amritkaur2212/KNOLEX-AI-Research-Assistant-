import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI


# =========================================================
# 1. LOAD ENVIRONMENT VARIABLES
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise RuntimeError(
        "GOOGLE_API_KEY is missing. "
        "Please add it to backend/.env before starting the backend."
    )


# =========================================================
# 2. INITIALIZE GEMINI MODEL
# =========================================================

llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3,
)


# =========================================================
# 3. CLEAN AND EXTRACT AI RESPONSE
# =========================================================

def clean_response_content(content) -> str:
    """
    Extract readable text from Gemini's response.

    Handles:
    - Plain text responses
    - Lists of text content blocks
    - Structured response content
    - Escaped newline characters
    """

    # Case 1: Response is already plain text.
    if isinstance(content, str):
        answer = content

    # Case 2: Response contains multiple content blocks.
    elif isinstance(content, list):
        text_parts = []

        for block in content:

            # A content block may be a string.
            if isinstance(block, str):
                text_parts.append(block)

            # A content block may be a dictionary.
            elif isinstance(block, dict):
                if (
                    block.get("type") == "text"
                    and isinstance(block.get("text"), str)
                ):
                    text_parts.append(block["text"])

            # Some integrations return structured block objects.
            elif getattr(block, "type", None) == "text":
                block_text = getattr(block, "text", None)

                if isinstance(block_text, str):
                    text_parts.append(block_text)

        answer = "\n".join(text_parts)

    else:
        answer = ""

    # Normalize escaped line breaks if they are present literally.
    answer = (
        answer
        .replace("\\r\\n", "\n")
        .replace("\\n", "\n")
        .replace("\\t", "\t")
        .strip()
    )

    return answer


# =========================================================
# 4. GENERATE AI ANSWER
# =========================================================

def generate_answer(prompt: str) -> str:
    """
    Send a prompt to Gemini and return readable text.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("The prompt cannot be empty.")

    response = llm.invoke(prompt)

    answer = clean_response_content(response.content)

    if not answer:
        raise ValueError(
            "Gemini returned no readable text. "
            "Please try again."
        )

    return answer


# =========================================================
# 5. GENERATE SUMMARY
# =========================================================

def generate_summary(text: str) -> str:
    """
    Generate a structured academic summary of research text.
    """

    if not isinstance(text, str) or not text.strip():
        raise ValueError("No readable document text was provided.")

    prompt = f"""
You are KNOLEX, an AI research assistant.

Create a clear, accurate, well-organized academic summary
of the research text provided below.

FORMATTING RULES:
- Use Markdown headings.
- Use short, readable paragraphs.
- Use bullet points where appropriate.
- Use bold text for important terms.
- Do not include Python dictionaries or response metadata.
- Do not include encoded data or random character strings.
- Do not write literal escape sequences such as \\n.
- Do not invent information that is absent from the source.
- Clearly state when information is not provided.
- Include these sections when supported by the source:

1. Research Problem and Objective
2. Main Methodology
3. Important Findings and Applications
4. Key Contributions
5. Limitations
6. Conclusion

RESEARCH TEXT:
{text}
"""

    return generate_answer(prompt)


# =========================================================
# 6. GENERATE ANSWERS TO RESEARCH QUESTIONS
# =========================================================

def answer_research_question(
    question: str,
    research_text: str,
) -> str:
    """
    Answer a question using the provided research text.
    """

    if not question or not question.strip():
        raise ValueError("Please enter a research question.")

    if not research_text or not research_text.strip():
        raise ValueError("No readable research text was provided.")

    prompt = f"""
You are KNOLEX, an AI research assistant.

Answer the user's question using the research text provided below.

INSTRUCTIONS:
- Give a direct and clear answer.
- Use Markdown headings when useful.
- Use bullet points for multiple items.
- Explain technical terms in simple language when appropriate.
- Do not invent facts or citations.
- If the research text does not contain the answer, say so.
- Return readable text only.
- Do not include Python dictionaries, metadata, encoded data,
  or random character strings.

USER QUESTION:
{question}

RESEARCH TEXT:
{research_text}
"""

    return generate_answer(prompt)