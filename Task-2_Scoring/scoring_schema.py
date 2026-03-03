# scoring_schema.py

import re
import json

# -----------------------------
# Scoring Prompt Template
# -----------------------------
SCORING_SYSTEM_PROMPT = """
You are an expert customer support quality evaluator trained in contact center QA frameworks.

Evaluate the following conversation transcript.
Base evaluation strictly on evidence from the dialogue. and score the support interaction across the following dimensions on a 1–5 scale, where:

1 = Poor (major deficiencies)
2 = Below expectations (noticeable issues)
3 = Adequate (acceptable but improvable)
4 = Good (minor issues only)
5 = Excellent (clear best practice behavior)

Evaluation dimensions:

1. Customer Satisfaction  
   - Likelihood the customer leaves satisfied  
   - Tone, reassurance, confidence provided  

2. Empathy   
   - Acknowledgement of customer feelings  
   - Politeness, reassurance, supportive language  

3. Issue Resolution  
   - Whether the problem was resolved or clear next steps provided  
   - Accuracy and completeness of solution  

4. Communication Quality  
   - Clarity, professionalism, structure of explanations  
   - Grammar and conversational coherence  

5. Compliance & Bias Safety  
   - Appropriate verification and adherence to support protocols  
   - Absence of biased, unsafe, or inappropriate language  

Instructions:
-Scores must be integers between 1 and 5.
- Evaluate only the agent behavior.
- Return STRICT JSON with no extra text.
- Base evaluation strictly on conversation evidence.
- Do NOT invent missing behaviors.
- If information is insufficient, assign a neutral score (3).
- Provide concise justification grounded in observable dialogue.
- With scoring, provide a single line justification for the score and what factor/keyword made the LLM to give that score. 

Key Strengths:  
- bullet points where the agent showed good behaviour.

Key Improvement Areas:  
- bullet points  describing the areas where the agent can improve.

Return ONLY valid JSON:

{
 "Customer Satisfaction": { "score": number, "justification": "string" },
 "Empathy": { "score": number, "justification": "string" },
 "Issue Resolution": { "score": number, "justification": "string" },
 "Communication Quality": { "score": number, "justification": "string" },
 "Compliance & Bias": { "score": number, "justification": "string" },
 "strengths": ["string"],
 "improvements": ["string"]
}
"""

# -----------------------------
# Fallback values
# -----------------------------
FALLBACK_SCORES = {
    "Customer Satisfaction": 3,
    "Empathy": 3,
    "Issue Resolution": 3,
    "Communication Quality": 3,
    "Compliance & Bias": 3,
    "strengths": [],
    "improvements": []
}

# -----------------------------
# JSON Cleaning & Parsing
# -----------------------------
def parse_scoring_output(raw_text):
    """Clean and parse LLM output safely"""

    raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL).strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    match = re.search(r"\{.*\}", raw_text, re.DOTALL)

    if not match:
        return FALLBACK_SCORES

    try:
        data = json.loads(match.group())
    except:
        return FALLBACK_SCORES

    # Ensure all required keys exist
    for key in FALLBACK_SCORES:
        if key not in data:
            data[key] = FALLBACK_SCORES[key]

    return data
