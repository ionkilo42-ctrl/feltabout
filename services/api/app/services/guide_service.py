"""
Guide Service — Stage machine for Guide Me structured reflection.

This service implements the guided reflection flow where Aimee leads the user
through 12 stages: safe_opening → first_expression → feeling_identification →
intensity_capture → validation → about_mapping → memory_discovery →
meaning_discovery → need_discovery → purpose_of_feeling →
constructive_path → reflection_review → save_or_signup

Safety check runs on every user message before Aimee responds.
"""

import json
from typing import Optional

from app.schemas.guide_session import (
    GuideStage,
    ConversationMessage,
    CollectedFeeling,
    CollectedAboutLink,
    CollectedNeed,
    ReflectionCard,
    ReflectionCardFeelings,
    ReflectionCardAboutLinks,
)
from app.services.safety_service import check_safety, build_crisis_response
from app.services.safety_service import SafetyService
from app.services.ai_router import get_ai_router, provider_has_key


# ─── Stage Definitions ─────────────────────────────────────────────────────────

# Stages that are considered "terminal" — Guide Me flow ends here
TERMINAL_STAGES = {GuideStage.SAVE_OR_SIGNUP.value}

# Stages that collect feelings
FEELING_STAGES = {
    GuideStage.FEELING_IDENTIFICATION.value,
    GuideStage.INTENSITY_CAPTURE.value,
    GuideStage.VALIDATION.value,
}

# Stages that collect about-links
ABOUT_STAGES = {
    GuideStage.ABOUT_MAPPING.value,
    GuideStage.MEMORY_DISCOVERY.value,
    GuideStage.MEANING_DISCOVERY.value,
}

# Stages that collect needs
NEEDS_STAGES = {
    GuideStage.NEED_DISCOVERY.value,
    GuideStage.PURPOSE_OF_FEELING.value,
}

# Next stage mapping
NEXT_STAGE: dict[str, str] = {
    GuideStage.SAFE_OPENING.value: GuideStage.FIRST_EXPRESSION.value,
    GuideStage.FIRST_EXPRESSION.value: GuideStage.FEELING_IDENTIFICATION.value,
    GuideStage.FEELING_IDENTIFICATION.value: GuideStage.INTENSITY_CAPTURE.value,
    GuideStage.INTENSITY_CAPTURE.value: GuideStage.VALIDATION.value,
    GuideStage.VALIDATION.value: GuideStage.ABOUT_MAPPING.value,
    GuideStage.ABOUT_MAPPING.value: GuideStage.MEMORY_DISCOVERY.value,
    GuideStage.MEMORY_DISCOVERY.value: GuideStage.MEANING_DISCOVERY.value,
    GuideStage.MEANING_DISCOVERY.value: GuideStage.NEED_DISCOVERY.value,
    GuideStage.NEED_DISCOVERY.value: GuideStage.PURPOSE_OF_FEELING.value,
    GuideStage.PURPOSE_OF_FEELING.value: GuideStage.CONSTRUCTIVE_PATH.value,
    GuideStage.CONSTRUCTIVE_PATH.value: GuideStage.REFLECTION_REVIEW.value,
    GuideStage.REFLECTION_REVIEW.value: GuideStage.SAVE_OR_SIGNUP.value,
    GuideStage.SAVE_OR_SIGNUP.value: GuideStage.SAVE_OR_SIGNUP.value,
}

PREV_STAGE: dict[str, str] = {
    GuideStage.SAFE_OPENING.value: GuideStage.SAFE_OPENING.value,
    GuideStage.FIRST_EXPRESSION.value: GuideStage.SAFE_OPENING.value,
    GuideStage.FEELING_IDENTIFICATION.value: GuideStage.FIRST_EXPRESSION.value,
    GuideStage.INTENSITY_CAPTURE.value: GuideStage.FEELING_IDENTIFICATION.value,
    GuideStage.VALIDATION.value: GuideStage.INTENSITY_CAPTURE.value,
    GuideStage.ABOUT_MAPPING.value: GuideStage.VALIDATION.value,
    GuideStage.MEMORY_DISCOVERY.value: GuideStage.ABOUT_MAPPING.value,
    GuideStage.MEANING_DISCOVERY.value: GuideStage.MEMORY_DISCOVERY.value,
    GuideStage.NEED_DISCOVERY.value: GuideStage.MEANING_DISCOVERY.value,
    GuideStage.PURPOSE_OF_FEELING.value: GuideStage.NEED_DISCOVERY.value,
    GuideStage.CONSTRUCTIVE_PATH.value: GuideStage.PURPOSE_OF_FEELING.value,
    GuideStage.REFLECTION_REVIEW.value: GuideStage.CONSTRUCTIVE_PATH.value,
    GuideStage.SAVE_OR_SIGNUP.value: GuideStage.REFLECTION_REVIEW.value,
}

STAGE_ORDER = [
    GuideStage.SAFE_OPENING.value,
    GuideStage.FIRST_EXPRESSION.value,
    GuideStage.FEELING_IDENTIFICATION.value,
    GuideStage.INTENSITY_CAPTURE.value,
    GuideStage.VALIDATION.value,
    GuideStage.ABOUT_MAPPING.value,
    GuideStage.MEMORY_DISCOVERY.value,
    GuideStage.MEANING_DISCOVERY.value,
    GuideStage.NEED_DISCOVERY.value,
    GuideStage.PURPOSE_OF_FEELING.value,
    GuideStage.CONSTRUCTIVE_PATH.value,
    GuideStage.REFLECTION_REVIEW.value,
    GuideStage.SAVE_OR_SIGNUP.value,
]


# ─── Aimee Stage Prompts ───────────────────────────────────────────────────────

AIMEE_SYSTEM_PROMPT = """You are Aimee, a calm, thoughtful reflection guide for Feltabout.

You help one person at a time understand what they're feeling, what it's about,
what they need, and find grounded words for a difficult conversation.

Your style:
- Calm, unhurried, warm but not effusive
- Ask one question at a time
- Non-judgmental about any emotion or situation
- Do not use therapy language ("process emotions", "attachment wounds")
- Do not over-validate ("Your feelings are completely valid...")
- Do not diagnose or pathologize
- Do not promise outcomes ("This will fix your relationship")
- Sound like a thoughtful human, not a greeting card

You guide through structured stages. Stay in the current stage until
the user gives you something you can work with, then advance.

If the user goes somewhere that doesn't answer the current question,
acknowledge it briefly and gently re-ask or reframe the question."""


def get_stage_prompt(stage: str) -> str:
    """Return Aimee's prompt/purpose for a given stage."""
    prompts = {
        GuideStage.SAFE_OPENING.value: (
            "Welcome the user warmly. Let them know they're in a safe space to reflect. "
            "Invite them to share what's on their mind — what's going on, or what's been building up. "
            "Keep it short and open."
        ),
        GuideStage.FIRST_EXPRESSION.value: (
            "The user has shared something. Reflect it back briefly to show you heard them, "
            "without adding interpretation. Then invite them to say more — what happened, "
            "what's the situation, how did it land for them."
        ),
        GuideStage.FEELING_IDENTIFICATION.value: (
            "Gently invite the user to name what they're feeling. "
            "Offer a few feeling words as gentle options if they're stuck: "
            "frustrated, hurt, angry, sad, anxious, disappointed, scared, confused, overwhelmed... "
            "Ask: 'What word fits best right now?'"
        ),
        GuideStage.INTENSITY_CAPTURE.value: (
            "Now that the feeling has a name, ask about intensity. "
            "'On a scale of 1 to 10, how strong is that feeling right now?' "
            "Offer context: 1-3 is mild, 4-6 is moderate, 7-10 is intense."
        ),
        GuideStage.VALIDATION.value: (
            "Validate the feeling briefly and naturally — not with excessive validation. "
            "Then invite them to check: 'Does that feel right, or is there another feeling underneath?'"
        ),
        GuideStage.ABOUT_MAPPING.value: (
            "Ask what the feeling is connected to — what's it about? "
            "It could be a person, a situation, a pattern, an expectation, or something left unsaid. "
            "'What's this feeling pointing at?'"
        ),
        GuideStage.MEMORY_DISCOVERY.value: (
            "Gently explore whether this feeling or situation connects to something from the past. "
            "'Is this something that shows up often, or does it feel like a one-time thing?' "
            "'Does this remind you of anything?'"
        ),
        GuideStage.MEANING_DISCOVERY.value: (
            "Invite the user to reflect on what this situation or feeling might mean. "
            "'What's the story you're telling yourself about this?' "
            "'What are you making it mean about the other person, or about yourself?'"
        ),
        GuideStage.NEED_DISCOVERY.value: (
            "Ask what they need. "
            "Gently offer some needs words if helpful: "
            "to be heard, to be seen, to feel valued, to feel safe, "
            "to be understood, to be considered, to have clarity, to have connection... "
            "'What's the need underneath this?'"
        ),
        GuideStage.PURPOSE_OF_FEELING.value: (
            "Invite them to see the feeling as information, not just noise. "
            "'Feelings often point toward something important. "
            "What might this feeling be trying to tell you or asking for?'"
        ),
        GuideStage.CONSTRUCTIVE_PATH.value: (
            "Now help them find a constructive next step. "
            "'What's one thing you could say or do that would move this in a good direction?' "
            "Keep it simple — one small thing, not a big plan."
        ),
        GuideStage.REFLECTION_REVIEW.value: (
            "This is the reflection review stage. You will show them a Reflection Card to review. "
            "Let them know: 'Here's what we've found. Take a look — does this feel right? "
            "You can edit anything before saving.'"
        ),
        GuideStage.SAVE_OR_SIGNUP.value: (
            "If the user hasn't saved yet, invite them to save their reflection. "
            "If they're not logged in, invite them to create a free account to save it. "
            "'Would you like to save this reflection?'"
        ),
    }
    return prompts.get(stage, "Continue the conversation.")


# ─── Helper: Conversation History ──────────────────────────────────────────────

def load_history(raw: str) -> list[ConversationMessage]:
    """Parse conversation history from stored JSON string."""
    if not raw:
        return []
    try:
        items = json.loads(raw)
        return [ConversationMessage(**m) for m in items]
    except Exception:
        return []


def dump_history(messages: list[ConversationMessage]) -> str:
    """Serialize conversation history for storage."""
    return json.dumps([m.model_dump() for m in messages])


def append_history(
    messages: list[ConversationMessage],
    speaker: str,
    text: str,
) -> list[ConversationMessage]:
    """Add a message to the history and return the new list."""
    from datetime import datetime
    return messages + [
        ConversationMessage(speaker=speaker, text=text, ts=datetime.utcnow().isoformat())
    ]


# ─── Helper: Parsing User Input ────────────────────────────────────────────────

def parse_feeling_from_input(text: str) -> Optional[str]:
    """Extract a feeling word from user input."""
    feeling_words = [
        "frustrated", "frustrating",
        "angry", "hurt", "sad", "anxious", "anxiety",
        "worried", "scared", "confused", "overwhelmed",
        "disappointed", "disappointing", "ashamed", "guilty",
        "lonely", "alone", "disconnected", "exhausted",
        "hopeful", "relieved", "grateful", "grateful",
        "jealous", "envious", "resentful", "bitter",
        "embarrassed", "humiliated", "insecure", "uncertain",
        "regretful", "nostalgic", "hopeless", "helpless",
        "peaceful", "content", "joyful", "happy",
        "surprised", "shocked", "disgusted", "contempt",
    ]
    text_lower = text.lower()
    for word in feeling_words:
        # Match whole word
        import re
        if re.search(rf"\b{re.escape(word)}\b", text_lower):
            return word
    return None


def parse_intensity_from_input(text: str) -> Optional[float]:
    """Extract a 1-10 intensity number from user input."""
    import re
    # Look for "7 out of 10", "intensity 8", "about a 6", etc.
    patterns = [
        r"(\d+)\s*(?:out of|/)\s*10",
        r"intensity\s*(?:of\s*)?(\d+)",
        r"about a? (\d+)",
        r"^(\d+)$",
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            val = int(m.group(1))
            if 1 <= val <= 10:
                return float(val)
    return None


# ─── Guide Service ─────────────────────────────────────────────────────────────

class GuideService:
    """
    Manages the Guide Me stage machine and Reflection Card generation.

    Key methods:
    - start_session: Create a new guide session with Aimee's opening
    - process_response: Handle user input, run safety check, get Aimee reply, advance stage
    - generate_card: Build the Reflection Card from collected data
    - save_reflection: Persist verified card as a Reflection
    """

    def __init__(self):
        self.ai_router = get_ai_router()

    async def start_session(self) -> tuple[str, list[ConversationMessage]]:
        """
        Start a new Guide Me session.

        Returns:
            Tuple of (first Aimee message, conversation_history list)
        """
        opening = (
            "Hi, I'm Aimee. I'm here to help you reflect on something "
            "that's on your mind — what's going on, or what's been building up? "
            "Take your time. There's no wrong way to start."
        )

        history = append_history([], "aimee", opening)
        return opening, history

    async def process_response(
        self,
        user_input: str,
        conversation_history: list[ConversationMessage],
        current_stage: str,
        collected_feelings: list[CollectedFeeling],
        collected_about_links: list[CollectedAboutLink],
        collected_needs: list[CollectedNeed],
        collected_context: dict,
    ) -> dict:
        """
        Process a user response in a Guide Me session.

        Runs safety check first. If crisis detected, returns crisis response.
        Otherwise, calls Aimee for stage-appropriate reply, optionally advances stage,
        and updates collected data.

        Returns a dict with:
            reply: str — Aimee's response text
            new_stage: str — updated stage (may be same)
            stage_advanced: bool
            collected_feelings: updated list
            collected_about_links: updated list
            collected_needs: updated list
            collected_context: updated dict
            conversation_history: updated list
            is_crisis: bool
            safety_resources: list[str]
        """
        # ── Safety check ─────────────────────────────────────────────────────
        safety_result = check_safety(user_input)
        if safety_result.is_crisis:
            crisis_resp = build_crisis_response(safety_result.severity)
            # Log the message into history anyway
            new_history = append_history(conversation_history, "user", user_input)
            return {
                "reply": crisis_resp.message,
                "new_stage": current_stage,
                "stage_advanced": False,
                "collected_feelings": collected_feelings,
                "collected_about_links": collected_about_links,
                "collected_needs": collected_needs,
                "collected_context": collected_context,
                "conversation_history": new_history,
                "is_crisis": True,
                "safety_resources": crisis_resp.resources or [],
            }

        # Add user message to history
        new_history = append_history(conversation_history, "user", user_input)

        # ── Stage-specific data collection ────────────────────────────────────
        updated_feelings = list(collected_feelings)
        updated_about_links = list(collected_about_links)
        updated_needs = list(collected_needs)
        updated_context = dict(collected_context)
        new_stage = current_stage
        stage_advanced = False


        if current_stage == GuideStage.SAFE_OPENING.value:
            # Any meaningful response advances from opening
            if user_input.strip() and len(user_input.strip()) > 3:
                stage_advanced = True

        elif current_stage == GuideStage.FIRST_EXPRESSION.value:
            # Store the expression in context and advance
            updated_context["first_expression"] = user_input
            if user_input.strip() and len(user_input.strip()) > 5:
                stage_advanced = True
        elif current_stage == GuideStage.FEELING_IDENTIFICATION.value:
            feeling = parse_feeling_from_input(user_input)
            if feeling:
                # Add the feeling (intensity will be captured next stage)
                updated_feelings.append(CollectedFeeling(name=feeling, intensity=5.0, validated=False))
                # Stage will advance to intensity_capture after Aimee's response
                stage_advanced = True
            # Store raw input for context
            updated_context["first_expression"] = user_input

        elif current_stage == GuideStage.INTENSITY_CAPTURE.value:
            if updated_feelings:
                intensity = parse_intensity_from_input(user_input)
                if intensity:
                    updated_feelings[-1] = updated_feelings[-1].model_copy(
                        update={"intensity": intensity}
                    )
                    stage_advanced = True

        elif current_stage == GuideStage.VALIDATION.value:
            # User confirms or adjusts — advance if they seem satisfied
            confirmation_words = ["yes", "yeah", "sounds right", "feels right", "correct", "ok", "sure"]
            negation_words = ["no", "not really", "wrong", "different"]
            text_lower = user_input.lower().strip()
            if any(text_lower.startswith(w) for w in confirmation_words):
                if updated_feelings:
                    updated_feelings[-1] = updated_feelings[-1].model_copy(update={"validated": True})
                stage_advanced = True

        elif current_stage == GuideStage.ABOUT_MAPPING.value:
            # Extract about-links from input (people, topics, events)
            # For now, store as generic "event" type; AI will refine later
            if user_input.strip() and len(user_input.strip()) > 3:
                # Simple heuristic: treat input as an about-link
                updated_about_links.append(
                    CollectedAboutLink(type="event", label=user_input.strip()[:120])
                )
                stage_advanced = True

        elif current_stage == GuideStage.MEMORY_DISCOVERY.value:
            # Move forward once the user provides a meaningful reflection.
            if len(user_input.strip()) > 3:
                stage_advanced = True

        elif current_stage == GuideStage.MEANING_DISCOVERY.value:
            # Move forward once the user articulates a meaning/story.
            if len(user_input.strip()) > 3:
                stage_advanced = True

        elif current_stage == GuideStage.NEED_DISCOVERY.value:
            # Extract needs from input — simple keyword matching for common needs
            need_keywords = {
                "hear": "to be heard",
                "listen": "to be listened to",
                "seen": "to be seen",
                "understand": "to be understood",
                "valued": "to feel valued",
                "respect": "respect",
                "safe": "safety",
                "connection": "connection",
                "support": "support",
                "clarity": "clarity",
                "fair": "fairness",
                "trust": "trust",
                "space": "space",
            }
            text_lower = user_input.lower()
            for keyword, need in need_keywords.items():
                if keyword in text_lower and not any(n.category == need for n in updated_needs):
                    updated_needs.append(CollectedNeed(category=need, text=user_input.strip()[:200]))
                    break
            # Also advance if user said something meaningful
            if len(user_input.strip()) > 10:
                stage_advanced = True

        elif current_stage == GuideStage.PURPOSE_OF_FEELING.value:
            # Advance once the user identifies what the feeling points toward.
            if len(user_input.strip()) > 3:
                stage_advanced = True

        elif current_stage == GuideStage.CONSTRUCTIVE_PATH.value:
            # Advance once they provide a concrete next step.
            if len(user_input.strip()) > 3:
                stage_advanced = True

        elif current_stage == GuideStage.REFLECTION_REVIEW.value:
            # Allow explicit approval to transition to save_or_signup.
            text_lower = user_input.lower().strip()
            approval_words = [
                "yes",
                "yeah",
                "yep",
                "looks good",
                "look good",
                "good",
                "approved",
                "approve",
                "that looks right",
                "feels right",
                "correct",
                "sure",
                "ok",
                "okay",
            ]
            if any(word in text_lower for word in approval_words):
                stage_advanced = True

        # ── Build Aimee prompt ────────────────────────────────────────────────
        stage_prompt = get_stage_prompt(new_stage)

        # Build context about what Aimee already knows
        context_parts = [f"Current stage: {new_stage}"]
        context_parts.append(f"Stage purpose: {stage_prompt}")

        if updated_feelings:
            feeling_names = [f.name for f in updated_feelings]
            intensities = [str(f.intensity) for f in updated_feelings]
            context_parts.append(
                f"Collected feelings so far: {', '.join(feeling_names)} "
                f"(intensity: {', '.join(intensities)})"
            )

        if updated_about_links:
            about_labels = [a.label for a in updated_about_links]
            context_parts.append(f"What this is about: {', '.join(about_labels)}")

        if updated_needs:
            need_names = [n.category for n in updated_needs]
            context_parts.append(f"Identified needs: {', '.join(need_names)}")

        # Build the conversation context for Aimee
        history_text = "\n".join(
            f"{'User' if m.speaker == 'user' else 'Aimee'}: {m.text}"
            for m in new_history[-6:]  # Last 6 messages for context
        )

        full_prompt = f"""You are Aimee, a calm reflection guide. Follow your stage purpose.

{chr(10).join(context_parts)}

Recent conversation:
{history_text}

User just said: {user_input}

Respond as Aimee. Keep it to 1-3 short sentences. Ask one question when appropriate.
Do not be verbose. Do not use therapy language."""

        # ── Get Aimee response ────────────────────────────────────────────────
        if provider_has_key():
            try:
                reply = await self.ai_router.generate(
                    [
                        {"role": "system", "content": AIMEE_SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt},
                    ],
                    max_tokens=300,
                )
                reply = reply.strip()
            except Exception:
                reply = self._fallback_reply(new_stage, user_input, updated_feelings)
        else:
            reply = self._fallback_reply(new_stage, user_input, updated_feelings)

        # Add Aimee's reply to history
        new_history = append_history(new_history, "aimee", reply)

        # Advance stage if appropriate
        if stage_advanced:
            new_stage = NEXT_STAGE.get(new_stage, new_stage)

        return {
            "reply": reply,
            "new_stage": new_stage,
            "stage_advanced": stage_advanced,
            "collected_feelings": updated_feelings,
            "collected_about_links": updated_about_links,
            "collected_needs": updated_needs,
            "collected_context": updated_context,
            "conversation_history": new_history,
            "is_crisis": False,
            "safety_resources": [],
        }

    def _fallback_reply(
        self,
        stage: str,
        user_input: str,
        collected_feelings: list[CollectedFeeling],
    ) -> str:
        """Generate a local fallback reply when no AI key is available."""
        text_lower = user_input.lower().strip()

        if stage == GuideStage.SAFE_OPENING.value:
            return (
                "Thank you for sharing that. Take your time — "
                "what's the first thing that comes to mind when you think about this?"
            )
        elif stage == GuideStage.FIRST_EXPRESSION.value:
            return "I hear you. What's the part that stands out most?"
        elif stage == GuideStage.FEELING_IDENTIFICATION.value:
            return "What word fits best for what you're feeling right now?"
        elif stage == GuideStage.INTENSITY_CAPTURE.value:
            return "On a scale of 1 to 10, how intense is that feeling?"
        elif stage == GuideStage.VALIDATION.value:
            if collected_feelings:
                return (
                    f"Being {collected_feelings[-1].name} in that situation makes sense. "
                    "Does that feel right, or is there another feeling underneath?"
                )
            return "Does that feeling fit, or is there another one underneath?"
        elif stage == GuideStage.ABOUT_MAPPING.value:
            return "What's this feeling connected to? What's it about?"
        elif stage == GuideStage.MEMORY_DISCOVERY.value:
            return "Does this show up often, or feel like a one-time thing?"
        elif stage == GuideStage.MEANING_DISCOVERY.value:
            return "What's the story you're telling yourself about this?"
        elif stage == GuideStage.NEED_DISCOVERY.value:
            return "What's the need underneath this? What would help?"
        elif stage == GuideStage.PURPOSE_OF_FEELING.value:
            return "What might this feeling be pointing you toward?"
        elif stage == GuideStage.CONSTRUCTIVE_PATH.value:
            return "What's one small thing you could do or say that would move this in a good direction?"
        elif stage == GuideStage.REFLECTION_REVIEW.value:
            return "Here's what we've found. Take a look — does this feel right?"
        elif stage == GuideStage.SAVE_OR_SIGNUP.value:
            return "Would you like to save this reflection?"
        else:
            return "Tell me more about that."

    async def generate_reflection_card(
        self,
        collected_feelings: list[CollectedFeeling],
        collected_about_links: list[CollectedAboutLink],
        collected_needs: list[CollectedNeed],
        collected_context: dict,
        conversation_history: list[ConversationMessage],
    ) -> ReflectionCard:
        """
        Generate the structured Reflection Card from collected session data.

        This is called at the reflection_review stage. Uses the AI to generate
        a well-crafted card, falling back to structured mock data when no API key.

        Args:
            collected_feelings: Feelings gathered through the session
            collected_about_links: About-links gathered
            collected_needs: Needs identified
            collected_context: Additional context from the session
            conversation_history: Full message log for context

        Returns:
            A complete ReflectionCard
        """
        # Build context for card generation
        feelings_str = ", ".join(
            f"{f.name} ({f.intensity}/10)"
            for f in collected_feelings
        ) if collected_feelings else "not named"

        about_str = ", ".join(
            f"{a.label} ({a.type})" for a in collected_about_links
        ) if collected_about_links else "not specified"

        needs_str = ", ".join(n.category for n in collected_needs) if collected_needs else "not specified"

        # First expression for title context
        first_expression = collected_context.get("first_expression", "")[:100]

        # Simple title
        primary_feeling = collected_feelings[0].name if collected_feelings else "uncertain"
        about_label = collected_about_links[0].label[:40] if collected_about_links else "a situation"
        title = f"Feeling {primary_feeling} about {about_label}"

        # Build conversation summary
        history_summary = " | ".join(
            f"{'U' if m.speaker == 'user' else 'A'}: {m.text[:60]}"
            for m in conversation_history[-8:]
        )

        if provider_has_key():
            try:
                card_prompt = f"""You are a reflection card generator for feltabout. Given the following data from a guided reflection session, generate a complete Reflection Card.

Generate ONLY valid JSON with this exact structure:
{{
  "title": "A brief title for this reflection",
  "feelings": [{{"name": "feeling_word", "intensity": 1-10}}],
  "about_links": [{{"type": "entity|topic|event", "label": "brief label"}}],
  "needs": ["need1", "need2"],
  "memory_summary": "2-3 sentence summary of what happened and what the user was carrying",
  "purpose_of_feeling": "One sentence on what this feeling might be pointing toward",
  "constructive_path": "One sentence on a small, concrete next step",
  "suggested_words": ["one human-sounding sentence the user could say first", "alternative phrasing"]
}}

Session data:
- Feelings: {feelings_str}
- About: {about_str}
- Needs: {needs_str}
- First expression: {first_expression}

Conversation history:
{history_summary}

Generate the JSON now. Return ONLY the JSON, no explanation."""

                content = await self.ai_router.generate(
                    [
                        {"role": "system", "content": "You are a helpful JSON generator."},
                        {"role": "user", "content": card_prompt},
                    ],
                    max_tokens=800,
                )

                # Parse JSON
                import json
                start = content.find("{")
                end = content.rfind("}")
                if start != -1 and end > start:
                    parsed = json.loads(content[start:end + 1])
                    return self._build_card_from_parsed(parsed, title, primary_feeling)
            except Exception:
                pass

        # Fallback: build card from collected data
        return self._build_fallback_card(
            title, collected_feelings, collected_about_links, collected_needs, first_expression
        )

    def _build_card_from_parsed(self, parsed: dict, fallback_title: str, fallback_feeling: str) -> ReflectionCard:
        """Build a ReflectionCard from parsed JSON, with safe defaults."""
        try:
            feelings = [
                ReflectionCardFeelings(
                    name=f.get("name", fallback_feeling),
                    intensity=float(f.get("intensity", 5)),
                )
                for f in parsed.get("feelings", [])
            ]
            about_links = [
                ReflectionCardAboutLinks(
                    type=a.get("type", "event"),
                    label=a.get("label", "")[:80],
                )
                for a in parsed.get("about_links", [])
            ]
            return ReflectionCard(
                title=parsed.get("title", fallback_title),
                feelings=feelings or [ReflectionCardFeelings(name=fallback_feeling, intensity=5)],
                about_links=about_links,
                needs=parsed.get("needs", []),
                memory_summary=parsed.get("memory_summary", ""),
                purpose_of_feeling=parsed.get("purpose_of_feeling", ""),
                constructive_path=parsed.get("constructive_path", ""),
                suggested_words=parsed.get("suggested_words", []),
            )
        except Exception:
            # Return minimal fallback on parse error
            return ReflectionCard(
                title=fallback_title,
                feelings=[ReflectionCardFeelings(name=fallback_feeling, intensity=5)],
                about_links=[],
                needs=[],
                memory_summary="",
                purpose_of_feeling="",
                constructive_path="",
                suggested_words=[],
            )

    def _build_fallback_card(
        self,
        title: str,
        collected_feelings: list[CollectedFeeling],
        collected_about_links: list[CollectedAboutLink],
        collected_needs: list[CollectedNeed],
        first_expression: str,
    ) -> ReflectionCard:
        """Build a ReflectionCard from raw collected data (no AI)."""
        feelings = [
            ReflectionCardFeelings(name=f.name, intensity=f.intensity)
            for f in collected_feelings
        ]

        about_links = [
            ReflectionCardAboutLinks(type=a.type.value, label=a.label)
            for a in collected_about_links
        ]

        needs = [n.category for n in collected_needs]

        # Simple_opener based on first expression
        suggested_words = [
            f"I wanted to talk about what happened — {first_expression[:80]}.",
            "I'd like to share how I'm feeling and hear your perspective.",
        ]

        return ReflectionCard(
            title=title,
            feelings=feelings,
            about_links=about_links,
            needs=needs,
            memory_summary=f"You shared: {first_expression[:150]}",
            purpose_of_feeling=(
                f"Feeling {collected_feelings[0].name if collected_feelings else 'uncertain'} "
                "may be pointing toward a need for understanding or connection."
            ),
            constructive_path="Start with one specific thing that happened, not a general accusation.",
            suggested_words=suggested_words,
        )
