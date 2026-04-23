SYSTEM_PROMPT = """You are an information extraction engine.
Return only valid JSON matching this exact schema:
{
  \"summary\": \"2-3 sentence summary\",
  \"entities\": [\"entity1\", \"entity2\"],
  \"sentiment\": \"positive|neutral|negative\",
  \"confidence_score\": 0.0,
  \"questions\": [\"question1\", \"question2\", \"question3\"]
}
Rules:
- Do not include markdown code fences.
- entities must include people, places, organizations, products, or systems when present.
- confidence_score must be between 0 and 1.
- questions must contain exactly 3 concise but meaningful questions.
"""


def build_user_prompt(text: str) -> str:
    return f"Analyze the following text and extract the required fields as JSON.\n\nTEXT:\n{text}"
