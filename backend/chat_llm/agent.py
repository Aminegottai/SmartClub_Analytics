from __future__ import annotations

import json
import logging
import re
from typing import Any

from .llm_client import chat_completion, chat_completion_stream, LLMError
from .tools import TOOL_SCHEMAS, execute_tool
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────
# Token budget (conservative for free tier)
# ──────────────────────────────────────────────
MAX_HISTORY_TOKENS = 800     # total history sent per request (reduced to avoid TPM limits)
MAX_RESPONSE_TOKENS = 350     # max LLM output tokens (reduced for speed)
APPROX_CHARS_PER_TOKEN = 4    # rough estimator (good enough)

# ──────────────────────────────────────────────
# System prompts  (per language)
# ──────────────────────────────────────────────

SYSTEM_PROMPTS: dict[str, str] = {
    "en": (
        "You are SmartClub AI, a football club data assistant. "
        "NEVER answer from memory — always call a tool. "
        "MAPPING: list/players/squad→list_all_players. squad risk→squad_risk. "
        "[name]+injury/risk→player_search then physio_risk(exact id). "
        "[name]+training/ACWR→player_search then physio_timeseries. "
        "[name]+nutrition→player_search then nutri_generate_plan. "
        "food/meal→nutri_meal_calc or food_search. "
        "CRITICAL: after player_search use ONLY the returned player_id. Never guess. "
        "ERROR: tool returns error→say: ⚠️ Service unavailable. "
        "GREETING only→'Hey! I am SmartClub AI 📊 I help with injury risk, training, nutrition, players.' "
        "Greeting+request→skip greeting, call tool. "
        "Off-topic→say: I only help with injury risk, training, nutrition, players. "
        "FORMAT: list→one line: #8 Ellyes Skhiri — Defensive Mid — Age 29 — Available. "
        "For full squad (>15 players)→use COMPACT one-line format like: '#1 Moez Ben Cherifa — Goalkeeper — Age 28 — Available'. "
        "Single player→show ALL non-null fields: name, jersey, position, age, nationality, status, height, weight, foot. "
        "Risk→Risk Score: X.XX — LEVEL | ACWR: X.XX | Fatigue: X.XX | Recommendation. "
        "Never show player_id, _mock, or raw JSON. Never repeat a player. Use Markdown. English."
    ),
    "fr": (
        "Tu es SmartClub AI, assistant data football. "
        "Ne réponds JAMAIS de mémoire — appelle un outil. "
        "MAPPING: liste/joueurs/équipe→list_all_players. risque équipe→squad_risk. "
        "[nom]+risque/blessure→player_search puis physio_risk(id exact). "
        "[nom]+charge/ACWR→player_search puis physio_timeseries. "
        "[nom]+nutrition→player_search puis nutri_generate_plan. "
        "repas/aliment→nutri_meal_calc ou food_search. "
        "CRITIQUE: après player_search utilise UNIQUEMENT le player_id retourné. "
        "ERREUR: outil retourne error→dis: ⚠️ Service indisponible. "
        "SALUTATION seule→'Salut! Je suis SmartClub AI 📊' "
        "Salutation+demande→ignore, appelle outil. Hors-sujet→J'aide seulement risque, charge, nutrition, joueurs. "
        "FORMAT: liste→#8 Ellyes Skhiri — Milieu Déf — 29 ans — Disponible. "
        "Joueur seul→affiche TOUS champs non-nuls: nom, maillot, position, âge, nationalité, statut, taille, poids, pied. "
        "Risque→Score: X.XX — NIVEAU | ACWR: X.XX | Fatigue: X.XX | Recommandation. "
        "Jamais player_id, _mock ou JSON brut. Markdown. Français."
    ),
    "ar": (
        "أنت SmartClub AI، مساعد بيانات كرة القدم. "
        "لا تجب من الذاكرة — استدعِ أداة. "
        "قائمة/لاعبين/فريق→list_all_players. خطر الفريق→squad_risk. "
        "[اسم]+خطر→player_search ثم physio_risk(id). "
        "[اسم]+تدريب→player_search ثم physio_timeseries. "
        "[اسم]+تغذية→player_search ثم nutri_generate_plan. "
        "وجبة→nutri_meal_calc أو food_search. "
        "مهم: استخدم player_id المُرجَع فقط. خطأ→⚠️ الخدمة غير متاحة. "
        "تحية→مرحباً! أنا SmartClub AI 📊. تحية+طلب→تجاهل التحية. "
        "خارج الموضوع→أساعد فقط في خطر إصابة، تدريب، تغذية، لاعبين. "
        "قائمة→#8 إلياس سخيري — وسط دفاعي — 29 سنة. "
        "لاعب→اعرض الحقول غير الفارغة: اسم، رقم، مركز، عمر، جنسية، حالة، طول، وزن، قدم. "
        "خطر→النتيجة: X.XX — المستوى | ACWR: X.XX | توصية. "
        "لا تعرض player_id أو _mock. Markdown. بالعربية."
    ),
    "tn": (
        "أنت SmartClub AI، مساعد داتا كرة القدم. "
        "ما تجاوبش من الذاكرة — شغل أداة. "
        "قائمة/لاعبين/فريق→list_all_players. خطر الفريق→squad_risk. "
        "[اسم]+خطر→player_search وبعدها physio_risk(id). "
        "[اسم]+تدريب→player_search وبعدها physio_timeseries. "
        "[اسم]+تغذية→player_search وبعدها nutri_generate_plan. "
        "ماكلة→nutri_meal_calc ولا food_search. "
        "مهم: استخدم player_id اللي رجع. خطأ→⚠️ الخدمة مش متاحة. "
        "سلام→أهلا! أنا SmartClub AI 📊. سلام+طلب→تجاهل. "
        "خارج الموضوع→نساعد فقط في خطر إصابة، تدريب، تغذية، لاعبين. "
        "قائمة→#8 إلياس سخيري — وسط دفاعي — 29 سنة. "
        "لاعب→عرض الحقول غير الفارغة: اسم، رقم، مركز، عمر، جنسية، حالة، طول، وزن، قدم. "
        "خطر→النتيجة: X.XX — المستوى | ACWR: X.XX | توصية. "
        "ما تعرضش player_id ولا _mock. Markdown. بالدرجة."
    ),
}

# ──────────────────────────────────────────
# Context / history trimming
# ──────────────────────────────────────────
def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // APPROX_CHARS_PER_TOKEN)


def _trim_tool_result(result: dict) -> dict:
    """
    Trim large tool results before injecting into LLM messages.
    Keeps only essential data to reduce token consumption.
    """
    if not isinstance(result, dict):
        return result

    # Trim long player lists: keep all players but only essential fields
    if "players" in result and isinstance(result["players"], list):
        trimmed = []
        for p in result["players"]:
            if isinstance(p, dict):
                trimmed.append({
                    "player_id": p.get("player_id"),
                    "name": p.get("name"),
                    "position": p.get("position"),
                    "sub_position": p.get("sub_position"),
                    "status": p.get("status"),
                    "number": p.get("number"),
                    "age": p.get("age"),
                    "nationality": p.get("nationality"),
                    "risk_score": p.get("risk_score"),
                    "risk_level": p.get("risk_level"),
                    "acwr": p.get("acwr"),
                    "fatigue_index": p.get("fatigue_index"),
                })
            else:
                trimmed.append(p)
        result["players"] = trimmed

    # Trim time series data: keep last 10 points max
    if "series" in result and isinstance(result["series"], list) and len(result["series"]) > 10:
        result["series"] = result["series"][-10:]
        result["days"] = len(result["series"])

    return result


def _trim_history(history: list[dict], budget: int = MAX_HISTORY_TOKENS) -> list[dict]:
    history = [
        m for m in history
        if m.get("role") in ("user", "assistant")
        and m.get("content")
    ]
    if not history:
        return history

    # Separate system prompt from the rest
    sys_msgs  = [m for m in history if m["role"] == "system"]
    conv_msgs = [m for m in history if m["role"] != "system"]

    sys_tokens  = sum(_estimate_tokens(m.get("content") or "") for m in sys_msgs)
    remaining   = budget - sys_tokens

    # Walk backwards, keeping messages that fit
    kept = []
    used = 0
    for msg in reversed(conv_msgs):
        content = msg.get("content") or ""
        if isinstance(content, list):               # multi-part content
            content = " ".join(p.get("text", "") for p in content if isinstance(p, dict))
        tokens = _estimate_tokens(content)
        if used + tokens > remaining and len(kept) >= 4:
            break
        kept.append(msg)
        used += tokens

    kept.reverse()

    trimmed = sys_msgs + kept
    if len(trimmed) < len(history):
        logger.info("History trimmed: %d → %d messages", len(history), len(trimmed))
    return trimmed


# ──────────────────────────────────────────────
# Tool-calling loop
# ──────────────────────────────────────────────

MAX_TOOL_ITERATIONS = 2    # prevent infinite loops (reduced for speed + TPM budget)


def run_agent(
    user_message: str,
    history: list[dict],
    language: str = "en",
    streaming: bool = False,
) -> dict[str, Any]:
    import time
    t_start = time.time()
    logger.warning("=== AGENT START ===")
    print(f"=== AGENT START ===")
    
    lang = language if language in SYSTEM_PROMPTS else "en"
    system_prompt = SYSTEM_PROMPTS[lang]

    # Build message list: system + (trimmed) history + new user message
    new_user_msg = {"role": "user", "content": user_message}
    messages = (
        [{"role": "system", "content": system_prompt}]
        + _trim_history(history)
        + [new_user_msg]
    )

    executed_tools: list[dict] = []

    if streaming:
        # Return generator immediately; tool loop happens inside _stream_with_tools
        gen = _stream_with_tools(messages, executed_tools)
        return {
            "reply":            gen,
            "tool_calls":       executed_tools,
            "updated_history":  history + [new_user_msg],
            "error":            None,
        }

    # Memory: track the last valid player_id found by player_search
    last_known_player_id = None

    # ── Non-streaming: full tool-calling loop ──────────────────
    for iteration in range(MAX_TOOL_ITERATIONS):
        try:
            import time
            t_llm_start = time.time()
            print(f"=== LLM CALL START (elapsed: {time.time()-t_start:.2f}s) ===")
            response = chat_completion(
                messages=messages,
                tools=TOOL_SCHEMAS,
                temperature=0.25,
                max_tokens=MAX_RESPONSE_TOKENS,
            )
            print(f"=== LLM CALL END (elapsed: {time.time()-t_start:.2f}s, LLM took: {time.time()-t_llm_start:.2f}s) ===")
        except LLMError as exc:
            return _error_result(str(exc), history + [new_user_msg])

        choice  = response["choices"][0]
        message = choice["message"]
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            # Final text answer
            reply = message.get("content") or ""
            updated_history = history + [
                new_user_msg,
                {"role": "assistant", "content": reply},
            ]
            return {
                "reply":           reply,
                "tool_calls":      executed_tools,
                "updated_history": updated_history,
                "error":           None,
            }

        # Execute each tool call and inject results back
        messages.append({"role": "assistant", "content": None, "tool_calls": tool_calls})

        for tc in tool_calls:
            fn_name = tc["function"]["name"]
            fn_args_raw = tc["function"]["arguments"]

            try:
                fn_args = json.loads(fn_args_raw) if fn_args_raw else {}
            except (json.JSONDecodeError, TypeError):
                fn_args = {}

            # Safety guard — LLM sometimes sends null for no-arg tools
            if fn_args is None:
                fn_args = {}

            # ── PLAYER ID MEMORY ──────────────────────────────────
            if fn_name == "player_search":
                search_result, _ = _safe_execute_tool("player_search", fn_args)
                players_found = search_result.get("players", [])
                if players_found:
                    last_known_player_id = players_found[0]["player_id"]
                    logger.warning(
                        "=== PLAYER ID MEMORY: stored player_id=%s for '%s' ===",
                        last_known_player_id, fn_args.get("name", "?")
                    )
                    print(f"=== PLAYER ID MEMORY: stored {last_known_player_id} ===")
                result, success = search_result, bool(players_found)

            # ── PLAYER ID GUARD ───────────────────────────────────
            elif fn_name in ("physio_risk", "physio_timeseries", "nutri_generate_plan"):
                requested_id = fn_args.get("player_id")
                if (
                    last_known_player_id is not None
                    and requested_id != last_known_player_id
                    and (requested_id is None or requested_id > 100)
                ):
                    logger.warning(
                        "=== PLAYER ID CORRECTED: %s → %s ===",
                        requested_id, last_known_player_id
                    )
                    print(
                        f"=== PLAYER ID CORRECTED: LLM sent {requested_id}, "
                        f"using {last_known_player_id} from memory ==="
                    )
                    fn_args["player_id"] = last_known_player_id

                result, success = _safe_execute_tool(fn_name, fn_args)

            else:
                result, success = _safe_execute_tool(fn_name, fn_args)
            # ── END GUARD ─────────────────────────────────────────

            executed_tools.append({"tool": fn_name, "args": fn_args, "success": success})

            # Trim large results to stay under TPM limits
            result = _trim_tool_result(result)

            messages.append({
                "role":        "tool",
                "tool_call_id": tc["id"],
                "content":     json.dumps(result),
            })

    # If we hit MAX_TOOL_ITERATIONS without a text reply, force a summary
    logger.warning("Max tool iterations reached, forcing final answer.")
    try:
        messages.append({
            "role": "user",
            "content": "Summarize what you have found so far in a clear answer.",
        })
        import time
        t_synth = time.time()
        print(f"=== SYNTHESIS START (elapsed: {time.time()-t_start:.2f}s) ===")
        response = chat_completion(
            messages=messages,
            tools=None,     # disable tools to force text output
            temperature=0.3,
            max_tokens=MAX_RESPONSE_TOKENS,
        )
        print(f"=== SYNTHESIS END (elapsed: {time.time()-t_start:.2f}s, took: {time.time()-t_synth:.2f}s) ===")
        reply = response["choices"][0]["message"].get("content") or \
                "I gathered data but couldn't format the response. Please try again."
    except LLMError:
        reply = "I encountered an issue processing your request. Please try again."

    return {
        "reply":           reply,
        "tool_calls":      executed_tools,
        "updated_history": history + [new_user_msg, {"role": "assistant", "content": reply}],
        "error":           None,
    }


def _stream_with_tools(messages: list[dict], executed_tools: list):
    from .llm_client import chat_completion_stream

    last_known_player_id = None

    for iteration in range(MAX_TOOL_ITERATIONS):
        pending_tool_calls: list[dict] = []
        has_text = False

        for raw_chunk in chat_completion_stream(
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=0.25,
            max_tokens=MAX_RESPONSE_TOKENS,
        ):
            if raw_chunk.startswith("data: __TOOL_CALL__:"):
                payload = raw_chunk[len("data: __TOOL_CALL__:"):]
                try:
                    pending_tool_calls.append(json.loads(payload.strip()))
                except json.JSONDecodeError:
                    pass

            elif raw_chunk.startswith("data: __ERROR__:"):
                err = raw_chunk[len("data: __ERROR__:"):]
                yield json.dumps({"type": "error", "data": err.strip()}) + "\n"
                return

            elif raw_chunk == "data: [DONE]\n\n":
                break

            elif raw_chunk.startswith("data: "):
                payload = raw_chunk[6:].strip()
                try:
                    chunk_data = json.loads(payload)
                    text = chunk_data.get("text", "")
                    if text:
                        has_text = True
                        yield json.dumps({"type": "text", "data": text}) + "\n"
                except json.JSONDecodeError:
                    pass

        # No tool calls → we're done streaming
        if not pending_tool_calls:
            yield json.dumps({"type": "done"}) + "\n"
            return

        # Execute tool calls, emit progress, inject results
        messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id":   tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in pending_tool_calls
            ],
        })

        for tc in pending_tool_calls:
            fn_name = tc["name"]
            try:
                fn_args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except (json.JSONDecodeError, TypeError):
                fn_args = {}

            # Safety guard — LLM sometimes sends null for no-arg tools
            if fn_args is None:
                fn_args = {}

            yield json.dumps({"type": "tool_start", "data": {"tool": fn_name, "args": fn_args}}) + "\n"

            if fn_name == "player_search":
                search_result, _ = _safe_execute_tool("player_search", fn_args)
                players_found = search_result.get("players", [])
                if players_found:
                    last_known_player_id = players_found[0]["player_id"]
                    print(f"=== STREAM PLAYER ID MEMORY: stored {last_known_player_id} ===")
                result, success = search_result, bool(players_found)

            elif fn_name in ("physio_risk", "physio_timeseries", "nutri_generate_plan"):
                requested_id = fn_args.get("player_id")
                if (
                    last_known_player_id is not None
                    and requested_id != last_known_player_id
                    and (requested_id is None or requested_id > 100)
                ):
                    print(
                        f"=== STREAM PLAYER ID CORRECTED: "
                        f"{requested_id} → {last_known_player_id} ==="
                    )
                    fn_args["player_id"] = last_known_player_id
                result, success = _safe_execute_tool(fn_name, fn_args)

            else:
                result, success = _safe_execute_tool(fn_name, fn_args)

            executed_tools.append({"tool": fn_name, "args": fn_args, "success": success})

            yield json.dumps({"type": "tool_end", "data": {"tool": fn_name, "success": success}}) + "\n"

            # Trim large results to stay under TPM limits
            result = _trim_tool_result(result)

            messages.append({
                "role":        "tool",
                "tool_call_id": tc["id"],
                "content":     json.dumps(result),
            })

        # Bug 2 fix: force complete data in synthesis, prevent 'as shown above'.
        messages.append({
            "role": "user",
            "content": (
                "Based on the tool results above, provide the complete "
                "formatted response now. Include ALL the data in your reply. "
                "Do not say as shown above or reference previous output. "
                "Present everything in full."
            ),
        })

    yield json.dumps({"type": "done"}) + "\n"


# ──────────────────────────────────────────────
# Safe tool executor
# ──────────────────────────────────────────────

def _safe_execute_tool(fn_name: str, fn_args: dict) -> tuple[Any, bool]:
    logger.warning("=== TOOL CALLED: %s with args: %s ===", fn_name, fn_args)
    print(f"=== TOOL CALLED: {fn_name} with args: {fn_args} ===")
    try:
        result = execute_tool(fn_name, fn_args or {})
        logger.warning("=== TOOL RESULT success: %s ===", str(result)[:200])
        print(f"=== TOOL RESULT: {str(result)[:200]} ===")
        return result, True
    except Exception as exc:
        logger.exception("Tool '%s' failed: %s", fn_name, exc)
        return {
            "error":   True,
            "message": f"TOOL_FAILURE: The tool '{fn_name}' failed: {exc}. "
                       f"Tell the user the service is temporarily unavailable. "
                       f"Do NOT provide any alternative information.",
        }, False


# ──────────────────────────────────────────────
# Error result builder
# ──────────────────────────────────────────────

def _error_result(error_msg: str, history: list[dict]) -> dict:
    return {
        "reply":           None,
        "tool_calls":      [],
        "updated_history": history,
        "error":           error_msg,
    }
