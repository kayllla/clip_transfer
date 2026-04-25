import json
import anthropic
from transitions import TRANSITIONS

client = anthropic.Anthropic()

TRANSITION_LIST = "\n".join(f"  - {k}: {v}" for k, v in TRANSITIONS.items())


def design_transitions(prompt_a: str, prompt_b: str, style: str, feedback: str = "") -> list[dict]:
    """Ask Claude to suggest 3 transition options between two clips."""

    feedback_line = f"\nUser feedback on previous options: {feedback}" if feedback else ""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": f"""You are a creative video editor designing transitions.

Clip A prompt: {prompt_a}
Clip B prompt: {prompt_b}
Overall style: {style}{feedback_line}

Available transitions:
{TRANSITION_LIST}

Suggest exactly 3 different transitions that fit the visual and emotional shift.
Vary your choices — don't suggest the same transition type twice.

Respond ONLY with a JSON array, no markdown:
[
  {{"transition": "fade", "duration": 1.0, "why": "一句话说明为什么适合这个切换"}},
  {{"transition": "zoom_in", "duration": 0.8, "why": "..."}},
  {{"transition": "wipe_left", "duration": 0.6, "why": "..."}}
]""",
            }
        ],
    )

    text = response.content[0].text.strip()
    return json.loads(text)
