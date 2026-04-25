import json
from openai import OpenAI
from transitions import TRANSITIONS
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

TRANSITION_LIST = "\n".join(f"  - {k}: {v}" for k, v in TRANSITIONS.items())


def design_transitions(prompt_a: str, prompt_b: str, style: str, feedback: str = "") -> list[dict]:
    """Ask GPT to suggest 3 transition options between two clips."""

    feedback_line = f"\nUser feedback on previous options: {feedback}" if feedback else ""

    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=1024,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a creative video editor. Always respond with valid JSON only.",
            },
            {
                "role": "user",
                "content": f"""Design transitions between two video clips.

Clip A prompt: {prompt_a}
Clip B prompt: {prompt_b}
Overall style: {style}{feedback_line}

Available transitions:
{TRANSITION_LIST}

Suggest exactly 3 different transitions that fit the visual and emotional shift.
Vary your choices — don't suggest the same transition type twice.

Respond with this JSON structure:
{{
  "transitions": [
    {{"transition": "fade", "duration": 1.0, "why": "一句话说明为什么适合这个切换"}},
    {{"transition": "zoom_in", "duration": 0.8, "why": "..."}},
    {{"transition": "wipe_left", "duration": 0.6, "why": "..."}}
  ]
}}""",
            },
        ],
    )

    data = json.loads(response.choices[0].message.content)
    return data["transitions"]
