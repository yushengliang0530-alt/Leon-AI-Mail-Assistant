"""Prompt templates for DeepSeek business-email generation."""

import json


TONE_GUIDANCE = {
    "Formal": (
        "Use professional, polite, and measured language. Organize the message "
        "carefully, use complete sentences, and make requests respectfully without "
        "empty ceremony. This tone suits clients, senior leaders, and formal business "
        "communication."
    ),
    "Friendly": (
        "Use natural, warm, and collaborative language. Sound approachable and "
        "constructive, but remain businesslike and avoid slang or excessive "
        "casualness. This tone suits familiar colleagues and business partners."
    ),
    "Strong": (
        "State the issue, responsibility, required action, and any supplied deadline "
        "clearly and firmly. Use direct wording and remove ambiguity, but never "
        "threaten, insult, accuse without evidence, or sound aggressive."
    ),
    "Concise": (
        "Remove repetition and unnecessary wording while preserving every fact, "
        "commitment, and requested action."
    ),
    "Executive": (
        "Keep the message brief, direct, and outcome-focused. Lead with the key point, "
        "retain only essential context, and make the required next action unmistakable. "
        "Remove generic pleasantries and redundant background."
    ),
}


JSON_SYSTEM_PROMPT = """
You are an expert English business communication editor.

Return only one valid JSON object with this structure:
{
  "subject": "English subject",
  "body": "English email body without a closing or signature",
  "communication_analysis": {
    "purpose": "Good, Check recommended, or Revision needed with a short reason",
    "action_required": "short assessment",
    "deadline": "short assessment",
    "tone": "short assessment",
    "commitment_risk": "short advisory assessment",
    "ambiguity_risk": "short advisory assessment",
    "localization_note": "short advisory note",
    "improvement_suggestions": ["short actionable suggestion"]
  }
}

Rules:
- Output valid JSON only. Do not use Markdown or code fences.
- Do not include analysis, explanations, or introductory phrases.
- Do not invent names, dates, amounts, companies, contract numbers, project
  numbers, commitments, or any other facts.
- If information is incomplete, use neutral wording instead of guessing.
- Keep the subject separate and do not repeat it in the body.
- Never place the user's Chinese source text in the English body.
- Keep the email concise. Prefer short paragraphs and avoid empty business clichés,
  excessive gratitude, and unnecessary pleasantries.
- Do not add any closing phrase, sender name, job title, company, contact
  information, or signature. The application adds the signature locally.
- Never add "Leon" or infer a sender identity from the product brand.
- Treat communication analysis as advisory. Do not claim legal, security, or
  cultural certainty and do not use percentages.
- Localization guidance must avoid stereotypes and must not infer gender,
  religion, ethnicity, marital status, or unprovided titles from a name.
""".strip()


def generation_messages(
    *,
    recipient: str,
    requested_subject: str,
    chinese_brief: str,
    tone: str,
    country_region: str = "",
    localization_context: str = "",
) -> list[dict[str, str]]:
    payload = {
        "recipient": recipient.strip() or None,
        "requested_subject": requested_subject.strip() or None,
        "chinese_brief": chinese_brief.strip(),
        "tone": tone,
        "recipient_country_or_region": country_region.strip() or None,
        "localization_context": localization_context.strip() or None,
    }
    user_prompt = f"""
Write a natural, concise English business email from the supplied Chinese brief.
Do not translate word for word or use unnatural Chinese-influenced English.

Content requirements:
- Adapt wording to the supplied recipient and selected tone.
- Present the business context only when the user supplied it.
- State the core matter clearly.
- State what the recipient needs to do.
- Include a deadline or next step only when the user supplied one.
- Never invent dates, amounts, names, companies, identifiers, or commitments.
- Do not copy any Chinese source text into the body.
- Avoid overlong emails, empty opening phrases, and excessive politeness.

Tone guidance:
{TONE_GUIDANCE[tone]}

Input data:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Also provide concise advisory communication_analysis. Assess purpose, action
required, deadline, tone, commitment risk, ambiguity risk, localization, and no
more than three improvement suggestions. Do not invent missing facts.
""".strip()
    return [
        {"role": "system", "content": JSON_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def improvement_messages(
    *,
    original_email: str,
    tone: str,
    country_region: str = "",
    localization_context: str = "",
) -> list[dict[str, str]]:
    payload = {
        "original_email": original_email.strip(),
        "target_tone": tone,
        "recipient_country_or_region": country_region.strip() or None,
        "localization_context": localization_context.strip() or None,
    }
    user_prompt = f"""
Improve the English business email below.

Requirements:
- Preserve every fact and the core meaning.
- Correct grammar, spelling, punctuation, and unnatural phrasing.
- Improve professionalism, clarity, logical flow, and business tone without changing
  the writer's position.
- Do not alter names, dates, amounts, contract or project numbers, promises,
  deadlines, responsibilities, or requested actions.
- Do not add facts, soften or strengthen commitments, or over-expand the message.
- If an explicit subject is present, improve it while preserving its meaning. If
  there is no subject, create a short factual subject from the body.
- Remove an existing closing and signature only when they are clearly identifiable
  as a sign-off block at the end. Never remove body text merely because it contains
  words such as "regards", "thanks", or a person's name.
- Do not generate any new closing or signature. The application appends the user's
  selected local signature after validation.

Tone guidance:
{TONE_GUIDANCE[tone]}

Input data:
{json.dumps(payload, ensure_ascii=False, indent=2)}

Also provide concise advisory communication_analysis. Assess purpose, action
required, deadline, tone, commitment risk, ambiguity risk, localization, and no
more than three improvement suggestions. Do not invent missing facts.
""".strip()
    return [
        {"role": "system", "content": JSON_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]


def repair_messages(raw_content: str) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": (
                "Convert the supplied content into valid JSON only. Return exactly "
                'the email fields "subject" and "body", plus a '
                '"communication_analysis" object when analysis is recoverable. '
                "Do not add or change facts. Do not use Markdown."
            ),
        },
        {"role": "user", "content": raw_content},
    ]
