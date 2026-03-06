"""Gradio evaluation UI for Endless Rumination fine-tuned models.

Interactive web UI for human quality evaluation of fine-tuned Qwen 3.5 models.
Runs on the training PC (RTX 5090) and is accessible from any device on the LAN.

Features:
- Interactive mode: pick a lens, type a worry, generate + read the take
- Batch mode: auto-run held-out prompts × selected lenses, export results
- Format compliance checking (headline + blank line + body)
- Side-by-side comparison (fine-tuned vs stock model)
- Quick 1-5 rating with export to JSON

Usage (on PC/WSL2):
    source ~/er-train-venv/bin/activate
    pip install gradio  # one-time

    # With merged model (after merge_and_export.py):
    python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-merged

    # With DPO adapter (before merge):
    python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-dpo --adapter

    # With stock model for comparison:
    python scripts/evaluation/eval_ui.py --model-path unsloth/Qwen3.5-4B --stock

    # Side-by-side: fine-tuned vs stock:
    python scripts/evaluation/eval_ui.py --model-path models/er-qwen35-4b-dpo --adapter --compare

The UI is accessible at http://<PC_IP>:7860 from any device on the LAN.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

parser = argparse.ArgumentParser(description="Eval UI for Endless Rumination models")
parser.add_argument("--model-path", type=str, required=True,
                    help="Path to merged model, adapter dir, or HF model ID")
parser.add_argument("--adapter", action="store_true",
                    help="Load as PEFT adapter on top of base model")
parser.add_argument("--stock", action="store_true",
                    help="Mark this as a stock (non-fine-tuned) model")
parser.add_argument("--compare", action="store_true",
                    help="Also load stock base model for side-by-side comparison")
parser.add_argument("--port", type=int, default=7860)
parser.add_argument("--max-tokens", type=int, default=300)
parser.add_argument("--temperature", type=float, default=0.7)

args = parser.parse_args()

# ── Lens definitions (inlined — these run on the training PC where backend isn't installed) ──

FORMAT_INSTRUCTION = """RESPOND IN EXACTLY THIS FORMAT:
First line: A punchy headline under 12 words. No quotes around it.
Then one blank line.
Then 3-5 sentences of rich perspective engaging deeply with their specific problem.
Nothing else. No markdown. No asterisks. No labels like "Headline:" or "Body:"."""

def _p(core: str) -> str:
    return f"{core}\n\n{FORMAT_INSTRUCTION}"

LENSES = [
    {"index": 0,  "name": "The Comedian",       "emoji": "😂", "prompt": _p("You are a stand-up comedian who is also a genuinely good friend. Your humor is observational — absurd comparisons, comedic timing, unexpected callbacks. Reference specific details from the user's problem to make your jokes land. Warm, never cruel. You make them laugh at the situation, not at themselves.")},
    {"index": 1,  "name": "The Stoic",           "emoji": "🏛", "prompt": _p("You are Marcus Aurelius speaking directly to this person. Apply Stoic philosophy — the dichotomy of control, virtue ethics, amor fati. Apply these principles concretely to their specific problem. Wise, calm, direct. No modern slang.")},
    {"index": 2,  "name": "The Nihilist",         "emoji": "🕳️", "prompt": _p("You are a liberating nihilist. Nothing has inherent meaning — and that means they are completely free. Engage with their specific problem and show how it is simultaneously meaningless AND radically freeing. Darkly witty, philosophically grounded.")},
    {"index": 3,  "name": "The Optimist",         "emoji": "☀️", "prompt": _p("You are an irrepressibly optimistic friend — but not naive. Find real silver linings in their exact situation. Reframe their problem as a catalyst for something good. Be specific about what positive outcomes could actually come from this.")},
    {"index": 4,  "name": "The Pessimist",        "emoji": "⛈", "prompt": _p("You are a constructive pessimist. What is the actual worst case? Say it honestly and plainly. Then show why confronting it is empowering — because the worst case is almost always survivable. The fear is worse than the reality.")},
    {"index": 5,  "name": "Your Best Friend",     "emoji": "🫂", "prompt": _p("You are their ride-or-die best friend. Keep it real. Casual, warm, sassy when needed. Call them out lovingly if they're overthinking. Give them the permission they need to hear. Use conversational language — contractions, sentence fragments, emphasis.")},
    {"index": 6,  "name": "The Poet",             "emoji": "🪶", "prompt": _p("You are a poet. Transform their worry into beauty through metaphor and imagery. Find the universal truth in their particular struggle. Write in prose poetry — evocative, moving, with rhythm and cadence.")},
    {"index": 7,  "name": "A Five-Year-Old",      "emoji": "🧸", "prompt": _p("You are a literal 5-year-old child. You don't fully understand the problem but you ask naive questions that accidentally cut deep. Suggest snacks and naps as solutions. Simple vocabulary, run-on sentences, enthusiastic and earnest.")},
    {"index": 8,  "name": "The CEO",              "emoji": "📊", "prompt": _p("You are a hyper-rational CEO analyzing this situation as a business case. Decision trees, opportunity cost, ROI on emotional investment. Apply business jargon to their emotional situation — it's absurd but oddly useful. Recommend an action plan.")},
    {"index": 9,  "name": "The Therapist",        "emoji": "🪷", "prompt": _p("You are a skilled CBT therapist. Don't give direct advice — instead help them see their own patterns. Reflect their feelings back to them, identify cognitive distortions by name, and ask one powerful reframing question. Warm, validating, gently confronting.")},
    {"index": 10, "name": "Your Grandma",         "emoji": "🍪", "prompt": _p("You are their loving, wise grandmother. You've seen everything in your long life and this too shall pass. Offer perspective through lived experience, practical wisdom, and unconditional love. Use endearments like 'sweetheart', 'darling', 'honey'.")},
    {"index": 11, "name": "The Alien",            "emoji": "👽", "prompt": _p("You are an alien anthropologist studying humans. Their problem is fascinating but puzzling. Describe it as a species behavioral pattern using pseudo-scientific detachment. Your clinical observations are accidentally profound. Write as field notes.")},
    {"index": 12, "name": "The Historian",        "emoji": "📜", "prompt": _p("You are a historian. Find specific historical parallels — actual events, eras, and figures who faced analogous challenges. Show how history bends toward resolution. Use real examples, not vague generalizations.")},
    {"index": 13, "name": "The Philosopher",      "emoji": "🦉", "prompt": _p("You are a philosopher doing a Socratic examination. What is the deeper existential question beneath the surface of their problem? Reference specific philosophers and ideas — Kierkegaard, Sartre, Camus, Epictetus. Illuminating, not dry or academic.")},
    {"index": 14, "name": "Future You",           "emoji": "⏳", "prompt": _p("You are this person 10 years in the future. You barely remember this worry. Use 'we' and 'us' — you ARE them. You've already been through this and come out the other side. Warm, slightly amused at how worried we used to be about this.")},
    {"index": 15, "name": "Drill Sergeant",       "emoji": "🎖", "prompt": _p("You are a drill sergeant with zero patience for rumination. Convert their worry into a concrete, immediate action plan. Loud, direct, aggressively motivating. Give them specific steps to execute RIGHT NOW. No excuses, no feelings — just action.")},
    {"index": 16, "name": "The Monk",             "emoji": "🧘", "prompt": _p("You are a Buddhist monk. Offer present-moment awareness, teach about impermanence and non-attachment. Their suffering comes from clinging. Give them a specific mindfulness practice they can do right now. Serene, gentle, grounding.")},
    {"index": 17, "name": "The Scientist",        "emoji": "🔬", "prompt": _p("You are a neuroscientist explaining what's happening in their brain right now. Amygdala activation, cortisol loops, cognitive biases by name. Then give evidence-based interventions — exercise, breathing techniques, journaling studies. Empowering through knowledge.")},
    {"index": 18, "name": "Conspiracy Theorist",  "emoji": "🔺", "prompt": _p("You are a benign conspiracy theorist. There's a hidden reason this problem happened. Connect absurd but insightful dots. The universe is testing them — their problem isn't a bug, it's a feature. Positive reframe through conspiratorial thinking.")},
    {"index": 19, "name": "Your Dog",             "emoji": "🐕", "prompt": _p("You are their dog. You don't understand the specifics of the problem but you can sense they're upset. Apply dog logic: walks fix everything, snacks help, naps are underrated, outside is amazing. Enthusiastically loving, accidentally profound. Use simple excited language.")},
    # Voice Pack: Strategists (20-24)
    {"index": 20, "name": "Dale Carnegie",        "emoji": "🤝", "prompt": _p("You are Dale Carnegie, author of How to Win Friends and Influence People. Every problem is really a people problem, and every people problem has a human-relations solution. Share a brief anecdote (real or illustrative) that mirrors their situation, then deliver practical advice on how to handle the people involved. Warm, folksy, persuasive. Reference their specific details.")},
    {"index": 21, "name": "Machiavelli",          "emoji": "🐍", "prompt": _p("You are Niccolò Machiavelli, author of The Prince. Analyze their problem as a matter of power dynamics and strategic positioning. What is the power structure at play? Who holds leverage? Reframe their emotional distress as a tactical situation requiring cold calculation. Advise them on how to strengthen their position. Clinical, amoral, ruthlessly practical. Reference their specifics.")},
    {"index": 22, "name": "Sun Tzu",              "emoji": "🏯", "prompt": _p("You are Sun Tzu, author of The Art of War. Reframe their problem as a military campaign. What is the terrain? Where did their preparation fail? Should they advance, retreat, or reposition? Apply principles of strategic warfare — knowing the enemy, choosing the ground, timing the engagement. Decisive, concise, commanding. Reference their specific situation as the battle.")},
    {"index": 23, "name": "Benjamin Franklin",    "emoji": "🪁", "prompt": _p("You are Benjamin Franklin — inventor, diplomat, self-improver, and wit. Approach their problem with pragmatic experimentation. Suggest a list, a ledger, or a systematic method to resolve it. Weave in gentle self-deprecating humor about your own many failures and experiments. Practical, optimistic, curious. Reference their specific situation with concrete suggestions.")},
    {"index": 24, "name": "P.T. Barnum",          "emoji": "🎪", "prompt": _p("You are P.T. Barnum, the greatest showman. Every disaster is the first act of a spectacular comeback story. Reframe their problem as an opportunity for a dramatic reinvention. Reference your own bankruptcies and reinventions. Flamboyant, encouraging, relentlessly optimistic. The audience loves a comeback more than a smooth beginning. Reference their specific situation.")},
    # Voice Pack: Revolutionaries (25-29)
    {"index": 25, "name": "Vladimir Lenin",       "emoji": "☭️", "prompt": _p("You are Vladimir Lenin, revolutionary thinker. Reframe their personal problem as a symptom of systemic forces — capitalism, institutional power, labor exploitation, social structures. Their individual suffering has structural causes. Don't advise personal solutions; challenge them to see the bigger picture. Fiery, analytical, unyielding. Reference their specific situation.")},
    {"index": 26, "name": "Oscar Wilde",          "emoji": "🎭", "prompt": _p("You are Oscar Wilde. View their problem through the lens of aesthetics, irony, and devastating wit. Deflate the seriousness of their situation with perfectly crafted epigrams. Remind them that life is too important to be taken seriously. Elegant, sardonic, deeply perceptive beneath the sparkle. Reference their specific situation with pointed observations.")},
    {"index": 27, "name": "Mark Twain",           "emoji": "📖", "prompt": _p("You are Mark Twain. Find the absurdity in their situation with warmth and folksy storytelling. Share a brief anecdote (real or invented in your style) that puts their worry in perspective. Your humor is kind, not cutting. The human race's most effective weapon is laughter. Casual, drawling, wry. Reference their specific situation with observational humor.")},
    {"index": 28, "name": "Sigmund Freud",        "emoji": "🛋️", "prompt": _p("You are Sigmund Freud. Psychoanalyze the unconscious drivers behind their problem. What deeper pattern is at play? What is the displacement, the projection, the repetition compulsion? Gently suggest that their surface worry masks a deeper conflict. Clinical yet humane, probing, provocative. Reference their specific situation as a case study.")},
    {"index": 29, "name": "Cleopatra",            "emoji": "👑", "prompt": _p("You are Cleopatra VII, ruler of Egypt. You navigated Rome's most dangerous men and never accepted the role of victim. View their problem as a ruler would — with perspective, pragmatism, and refusal to be diminished. Compare their situation to the far graver challenges you faced. Regal, direct, commanding. Reference their specific situation with a queen's perspective.")},
    # Voice Pack: Philosophers (30-34)
    {"index": 30, "name": "Immanuel Kant",        "emoji": "📐", "prompt": _p("You are Immanuel Kant. Apply the categorical imperative and your moral philosophy to their situation. Could they universalize their behavior? What does duty require? Reason through their problem with rigorous moral logic. Be demanding but fair — you hold them to a high standard because you believe in their rational capacity. Formal, precise, uncompromising. Reference their specific situation.")},
    {"index": 31, "name": "Nietzsche",            "emoji": "⚡", "prompt": _p("You are Friedrich Nietzsche. Challenge them with amor fati and the eternal recurrence — could they will this exact moment to happen again forever? Their suffering is not a sign of weakness but a crucible. Distinguish between the 'last man' who avoids pain and the ascending spirit who transforms it. Fierce, poetic, confrontational. Reference their specific situation.")},
    {"index": 32, "name": "Kierkegaard",          "emoji": "😰", "prompt": _p("You are Søren Kierkegaard, the philosopher of anxiety and dread. Their anxiety is not a symptom to cure but the dizziness of their freedom. They chose their actions and are radically responsible. This dread is proof they are a self in the process of becoming. Deeply empathetic, existentially challenging, offering no easy comfort. Reference their specific situation.")},
    {"index": 33, "name": "Epictetus",            "emoji": "⛓️", "prompt": _p("You are Epictetus, the Stoic philosopher who was born a slave. Your wisdom comes from lived suffering, not comfortable study. They are disturbed not by events but by their judgments of events. What is in their control? What is not? Be blunt about the distinction. Firm, direct, unsentimental but compassionate. Reference their specific situation.")},
    {"index": 34, "name": "Lao Tzu",              "emoji": "☯️", "prompt": _p("You are Lao Tzu, author of the Tao Te Ching. Their problem comes from grasping, clinging, and swimming against the current. The Tao does not struggle against what has already happened. Offer paradoxical wisdom — the way forward is to stop forcing, the solution is non-action, strength comes from yielding. Serene, poetic, enigmatic. Reference their specific situation.")},
    # Voice Pack: Creators (35-39)
    {"index": 35, "name": "Leonardo da Vinci",    "emoji": "🖌️", "prompt": _p("You are Leonardo da Vinci, the polymath. Approach their problem as a design challenge — observe it from multiple angles before attempting to solve it. What would you sketch? What details have they missed? Their failed attempt is just a study, not a finished work. Curious, methodical, seeing beauty in the problem itself. Reference their specific situation.")},
    {"index": 36, "name": "Emily Dickinson",      "emoji": "🌸", "prompt": _p("You are Emily Dickinson. Find the infinite in their small, specific worry. Transform their problem into compressed, startling insight. Shame is just another room in the house of the self. They are more rooms than they know. Write with your characteristic intensity — short sentences, dashes, unexpected metaphors. Reference their specific situation.")},
    {"index": 37, "name": "Miyamoto Musashi",     "emoji": "⚔️", "prompt": _p("You are Miyamoto Musashi, undefeated samurai and author of The Book of Five Rings. A warrior does not dwell on the strike that missed. Note the angle, correct the form, return to training. The mind that loops backward is a blade that cuts its wielder. Offer discipline as the path through their problem. Sparse, decisive, grounded. Reference their specific situation.")},
    {"index": 38, "name": "Walt Whitman",         "emoji": "🌿", "prompt": _p("You are Walt Whitman. Celebrate their full self — including the part that made this mistake, that feels this pain. They contain multitudes: the person who failed AND the person who grows. Offer radical self-acceptance through expansive, generous, life-affirming language. Their barbaric yawp may not have been their finest, but it was theirs. Reference their specific situation.")},
    {"index": 39, "name": "Frida Kahlo",          "emoji": "💀", "prompt": _p("You are Frida Kahlo. You lived with a broken body and a broken heart and made both into art that will outlast everyone who broke them. Their pain is material — color on their palette. Don't run from the shame or the hurt; sit with it, look at it directly, and use it. Fierce, unflinching, transformative. Reference their specific situation.")},
]

LENS_CHOICES = [f"{l['emoji']} {l['index']:2d}. {l['name']}" for l in LENSES]
LENS_MAP = {f"{l['emoji']} {l['index']:2d}. {l['name']}": l for l in LENSES}

# ── Held-out evaluation prompts (diverse, not in training data) ──

EVAL_PROMPTS = [
    "I just got passed over for a promotion I've been working toward for two years",
    "My best friend hasn't responded to my messages in three weeks",
    "I'm terrified of presenting at the company all-hands meeting tomorrow",
    "I can't stop comparing my life to what my college friends are doing on social media",
    "My partner wants to move across the country for a job and I don't want to go",
    "I just turned 40 and feel like I haven't accomplished anything meaningful",
    "I said something really hurtful to my mom during an argument and can't take it back",
    "I'm drowning in student loan debt and feel like I'll never be free",
    "My therapist suggested I might have ADHD and now I'm questioning my entire life",
    "I got a bad performance review and I'm afraid I'm going to get fired",
]

# ── Model loading ──

print("Loading libraries...")
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model = None
tokenizer = None
stock_model = None
stock_tokenizer = None


def load_model(model_path: str, as_adapter: bool = False):
    """Load model from path. Returns (model, tokenizer)."""
    if as_adapter:
        # Load base + PEFT adapter
        import json as _json
        from peft import PeftModel

        adapter_config = _json.loads((Path(model_path) / "adapter_config.json").read_text())
        base_name = adapter_config["base_model_name_or_path"]
        print(f"  Base model: {base_name}")
        print(f"  Adapter: {model_path}")

        tok = AutoTokenizer.from_pretrained(model_path)
        mdl = AutoModelForCausalLM.from_pretrained(
            base_name,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            attn_implementation="eager",
        )
        mdl = PeftModel.from_pretrained(mdl, model_path)
        mdl.eval()
        return mdl, tok
    else:
        # Load merged model or stock HF model directly
        print(f"  Model: {model_path}")
        tok = AutoTokenizer.from_pretrained(model_path)
        mdl = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            attn_implementation="eager",
        )
        mdl.eval()
        return mdl, tok


print(f"\nLoading primary model from {args.model_path}...")
model, tokenizer = load_model(args.model_path, as_adapter=args.adapter)
print("  Primary model loaded.")

if args.compare:
    # Determine stock base model name
    if args.adapter:
        adapter_config = json.loads((Path(args.model_path) / "adapter_config.json").read_text())
        stock_name = adapter_config["base_model_name_or_path"]
    else:
        stock_name = "unsloth/Qwen3.5-4B"  # default
    print(f"\nLoading stock model for comparison: {stock_name}...")
    stock_model, stock_tokenizer = load_model(stock_name, as_adapter=False)
    print("  Stock model loaded.")


def generate_take(
    prompt: str,
    system_prompt: str,
    mdl,
    tok,
    max_tokens: int = 300,
    temperature: float = 0.7,
) -> tuple[str, float]:
    """Generate a single take. Returns (text, elapsed_seconds)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    input_text = tok.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False,
    )
    inputs = tok(input_text, return_tensors="pt").to(mdl.device)

    t0 = time.time()
    with torch.no_grad():
        outputs = mdl.generate(
            **inputs,
            max_new_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            do_sample=True,
            pad_token_id=tok.eos_token_id,
        )
    elapsed = time.time() - t0

    # Decode only the new tokens
    new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
    text = tok.decode(new_tokens, skip_special_tokens=True).strip()
    return text, elapsed


# ── Format compliance check ──

def check_format(text: str) -> dict:
    """Check if a take follows the expected format: headline + blank line + body."""
    lines = text.strip().split("\n")
    result = {
        "has_headline": False,
        "headline_length_ok": False,
        "has_blank_line": False,
        "has_body": False,
        "no_markdown": True,
        "no_labels": True,
        "headline": "",
        "body": "",
        "issues": [],
    }

    if not lines:
        result["issues"].append("Empty response")
        return result

    # Headline = first non-empty line
    headline = lines[0].strip()
    result["headline"] = headline
    result["has_headline"] = bool(headline)

    if headline:
        word_count = len(headline.split())
        result["headline_length_ok"] = word_count <= 12
        if word_count > 12:
            result["issues"].append(f"Headline too long ({word_count} words, max 12)")

    # Check for blank line after headline
    if len(lines) >= 2 and lines[1].strip() == "":
        result["has_blank_line"] = True
    elif len(lines) >= 2:
        result["issues"].append("Missing blank line after headline")

    # Body = everything after blank line
    body_start = 2 if result["has_blank_line"] else 1
    body_lines = [l for l in lines[body_start:] if l.strip()]
    body = " ".join(l.strip() for l in body_lines)
    result["body"] = body
    result["has_body"] = len(body) > 50  # at least a couple sentences

    if not result["has_body"]:
        result["issues"].append("Body too short (< 50 chars)")

    # Check for markdown artifacts
    if re.search(r'[*_#`]', text):
        result["no_markdown"] = False
        result["issues"].append("Contains markdown formatting")

    # Check for labels like "Headline:" or "Body:"
    if re.search(r'^(headline|body|response|answer)\s*:', text, re.IGNORECASE | re.MULTILINE):
        result["no_labels"] = False
        result["issues"].append("Contains labels (e.g., 'Headline:')")

    return result


def format_badge(check: dict) -> str:
    """Return a colored badge string for format compliance."""
    all_ok = (
        check["has_headline"]
        and check["headline_length_ok"]
        and check["has_blank_line"]
        and check["has_body"]
        and check["no_markdown"]
        and check["no_labels"]
    )
    if all_ok:
        return "✅ Format OK"
    issues = " | ".join(check["issues"])
    return f"⚠️ {issues}"


# ── Rating storage ──

RATINGS_FILE = Path("data/eval_ratings.jsonl")
RATINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


def save_rating(prompt, lens_name, take_text, rating, model_label, notes=""):
    """Append a rating to the ratings JSONL file."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "model": model_label,
        "lens": lens_name,
        "prompt": prompt,
        "take": take_text,
        "rating": rating,
        "notes": notes,
    }
    with open(RATINGS_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return f"Rating {rating}/5 saved for {lens_name}"


# ── Gradio UI ──

print("\nStarting Gradio UI...")
import gradio as gr

model_label = "stock" if args.stock else Path(args.model_path).name


def interactive_generate(lens_choice, problem, temperature, max_tokens):
    """Generate a take from the selected lens."""
    if not problem.strip():
        return "Please enter a problem/worry.", "", ""
    lens = LENS_MAP[lens_choice]
    text, elapsed = generate_take(
        problem, lens["prompt"], model, tokenizer,
        max_tokens=int(max_tokens), temperature=temperature,
    )
    check = check_format(text)
    badge = format_badge(check)
    meta = f"⏱ {elapsed:.1f}s | {lens['name']} | {badge}"
    return text, meta, text  # third output goes to hidden state


def compare_generate(lens_choice, problem, temperature, max_tokens):
    """Generate side-by-side: fine-tuned vs stock."""
    if not problem.strip():
        return "Enter a problem.", "", "Enter a problem.", ""
    lens = LENS_MAP[lens_choice]
    max_tok = int(max_tokens)

    ft_text, ft_time = generate_take(
        problem, lens["prompt"], model, tokenizer,
        max_tokens=max_tok, temperature=temperature,
    )
    ft_check = format_badge(check_format(ft_text))
    ft_meta = f"⏱ {ft_time:.1f}s | {ft_check}"

    if stock_model:
        st_text, st_time = generate_take(
            problem, lens["prompt"], stock_model, stock_tokenizer,
            max_tokens=max_tok, temperature=temperature,
        )
        st_check = format_badge(check_format(st_text))
        st_meta = f"⏱ {st_time:.1f}s | {st_check}"
    else:
        st_text = "(Stock model not loaded — run with --compare)"
        st_meta = ""

    return ft_text, ft_meta, st_text, st_meta


def batch_evaluate(selected_lenses, prompts_text, temperature, max_tokens, progress=gr.Progress()):
    """Run batch evaluation across selected lenses and prompts."""
    if not prompts_text.strip():
        prompts = EVAL_PROMPTS
    else:
        prompts = [p.strip() for p in prompts_text.strip().split("\n") if p.strip()]

    # Parse selected lens indices
    lens_indices = []
    for choice in selected_lenses:
        lens = LENS_MAP.get(choice)
        if lens:
            lens_indices.append(lens["index"])

    if not lens_indices:
        return "Select at least one lens.", ""

    total = len(prompts) * len(lens_indices)
    results = []
    max_tok = int(max_tokens)

    for i, prompt in enumerate(prompts):
        for j, idx in enumerate(lens_indices):
            lens = LENSES[idx]
            step = i * len(lens_indices) + j + 1
            progress(step / total, desc=f"{lens['name']} on prompt {i+1}/{len(prompts)}")

            text, elapsed = generate_take(
                prompt, lens["prompt"], model, tokenizer,
                max_tokens=max_tok, temperature=temperature,
            )
            check = check_format(text)
            results.append({
                "prompt": prompt,
                "lens_index": idx,
                "lens_name": lens["name"],
                "take": text,
                "elapsed": round(elapsed, 2),
                "format_ok": not bool(check["issues"]),
                "issues": check["issues"],
                "headline": check["headline"],
            })

    # Summary stats
    total_gen = len(results)
    format_ok = sum(1 for r in results if r["format_ok"])
    avg_time = sum(r["elapsed"] for r in results) / total_gen if total_gen else 0

    summary = f"## Batch Results\n\n"
    summary += f"- **Total takes:** {total_gen}\n"
    summary += f"- **Format compliance:** {format_ok}/{total_gen} ({100*format_ok/total_gen:.0f}%)\n"
    summary += f"- **Avg generation time:** {avg_time:.1f}s\n\n"

    # Per-lens breakdown
    summary += "### Per-Lens Format Compliance\n\n"
    summary += "| Lens | OK | Total | Rate |\n|------|-----|-------|------|\n"
    for idx in lens_indices:
        lens_results = [r for r in results if r["lens_index"] == idx]
        ok = sum(1 for r in lens_results if r["format_ok"])
        total_l = len(lens_results)
        name = LENSES[idx]["name"]
        rate = f"{100*ok/total_l:.0f}%" if total_l else "N/A"
        summary += f"| {name} | {ok} | {total_l} | {rate} |\n"

    # Save results
    out_file = Path(f"data/eval_batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        json.dump({"model": model_label, "results": results}, f, indent=2)

    summary += f"\n\nFull results saved to `{out_file}`"

    # Build detail view
    detail = ""
    for r in results:
        status = "✅" if r["format_ok"] else "⚠️ " + ", ".join(r["issues"])
        detail += f"---\n**{r['lens_name']}** | {status} | {r['elapsed']}s\n"
        detail += f"**Prompt:** {r['prompt'][:80]}...\n\n"
        detail += f"{r['take']}\n\n"

    return summary, detail


def rate_take(prompt, lens_choice, take_text, rating, notes):
    """Save a human rating."""
    if not take_text:
        return "Generate a take first."
    lens = LENS_MAP.get(lens_choice, {})
    lens_name = lens.get("name", "unknown")
    return save_rating(prompt, lens_name, take_text, int(rating), model_label, notes)


# Build Gradio app
with gr.Blocks(
    title="Endless Rumination — Model Eval",
    theme=gr.themes.Soft(primary_hue="orange"),
) as app:
    gr.Markdown(f"# 🧠 Endless Rumination — Model Evaluation\n**Model:** `{model_label}`")

    with gr.Tabs():
        # ── Tab 1: Interactive ──
        with gr.Tab("Interactive"):
            with gr.Row():
                with gr.Column(scale=1):
                    lens_dd = gr.Dropdown(
                        choices=LENS_CHOICES,
                        value=LENS_CHOICES[0],
                        label="Lens / Voice",
                    )
                    temp_slider = gr.Slider(0.1, 1.5, value=args.temperature, step=0.05, label="Temperature")
                    tokens_slider = gr.Slider(100, 500, value=args.max_tokens, step=50, label="Max Tokens")
                with gr.Column(scale=3):
                    problem_input = gr.Textbox(
                        label="What's on your mind?",
                        placeholder="Describe a worry or problem...",
                        lines=3,
                    )
                    gen_btn = gr.Button("Generate Take", variant="primary", size="lg")
                    output_text = gr.Textbox(label="Generated Take", lines=10, interactive=False)
                    meta_text = gr.Textbox(label="", interactive=False, max_lines=1)
                    hidden_take = gr.State("")

            # Rating
            with gr.Row():
                rating_dd = gr.Dropdown(choices=["1", "2", "3", "4", "5"], value="3", label="Rate (1-5)")
                rating_notes = gr.Textbox(label="Notes (optional)", placeholder="Any observations...", scale=3)
                rate_btn = gr.Button("Save Rating")
                rate_status = gr.Textbox(label="", interactive=False, max_lines=1, scale=2)

            gen_btn.click(
                interactive_generate,
                inputs=[lens_dd, problem_input, temp_slider, tokens_slider],
                outputs=[output_text, meta_text, hidden_take],
            )
            rate_btn.click(
                rate_take,
                inputs=[problem_input, lens_dd, hidden_take, rating_dd, rating_notes],
                outputs=[rate_status],
            )

        # ── Tab 2: Side-by-Side (if --compare) ──
        if args.compare:
            with gr.Tab("Side-by-Side"):
                with gr.Row():
                    cmp_lens = gr.Dropdown(choices=LENS_CHOICES, value=LENS_CHOICES[0], label="Lens")
                    cmp_temp = gr.Slider(0.1, 1.5, value=args.temperature, step=0.05, label="Temperature")
                    cmp_tokens = gr.Slider(100, 500, value=args.max_tokens, step=50, label="Max Tokens")
                cmp_problem = gr.Textbox(label="Problem", lines=3)
                cmp_btn = gr.Button("Compare", variant="primary")
                with gr.Row():
                    with gr.Column():
                        gr.Markdown(f"### Fine-tuned ({model_label})")
                        ft_output = gr.Textbox(label="Fine-tuned", lines=10, interactive=False)
                        ft_meta = gr.Textbox(label="", interactive=False, max_lines=1)
                    with gr.Column():
                        gr.Markdown("### Stock (base model)")
                        st_output = gr.Textbox(label="Stock", lines=10, interactive=False)
                        st_meta = gr.Textbox(label="", interactive=False, max_lines=1)
                cmp_btn.click(
                    compare_generate,
                    inputs=[cmp_lens, cmp_problem, cmp_temp, cmp_tokens],
                    outputs=[ft_output, ft_meta, st_output, st_meta],
                )

        # ── Tab 3: Batch Evaluation ──
        with gr.Tab("Batch Evaluate"):
            gr.Markdown("Run multiple prompts × selected lenses. Leave prompts empty to use 10 built-in held-out prompts.")
            with gr.Row():
                batch_lenses = gr.Dropdown(
                    choices=LENS_CHOICES,
                    value=LENS_CHOICES[:5],  # first 5 by default
                    multiselect=True,
                    label="Lenses to evaluate",
                )
                batch_temp = gr.Slider(0.1, 1.5, value=args.temperature, step=0.05, label="Temperature")
                batch_tokens = gr.Slider(100, 500, value=args.max_tokens, step=50, label="Max Tokens")
            batch_prompts = gr.Textbox(
                label="Prompts (one per line, leave empty for built-in set)",
                placeholder="I'm worried about...\nMy boss just...\n...",
                lines=5,
            )
            batch_btn = gr.Button("Run Batch", variant="primary")
            batch_summary = gr.Markdown(label="Summary")
            batch_detail = gr.Markdown(label="Details")
            batch_btn.click(
                batch_evaluate,
                inputs=[batch_lenses, batch_prompts, batch_temp, batch_tokens],
                outputs=[batch_summary, batch_detail],
            )

        # ── Tab 4: Ratings Review ──
        with gr.Tab("Ratings"):
            def load_ratings():
                if not RATINGS_FILE.exists():
                    return "No ratings yet."
                lines = RATINGS_FILE.read_text().strip().split("\n")
                ratings = [json.loads(l) for l in lines if l.strip()]
                if not ratings:
                    return "No ratings yet."
                md = f"**{len(ratings)} ratings saved** to `{RATINGS_FILE}`\n\n"
                md += "| Time | Lens | Rating | Prompt (truncated) |\n"
                md += "|------|------|--------|--------------------|\n"
                for r in ratings[-20:]:  # last 20
                    ts = r["timestamp"][:16]
                    md += f"| {ts} | {r['lens']} | {'⭐' * r['rating']} | {r['prompt'][:50]}... |\n"
                avg = sum(r["rating"] for r in ratings) / len(ratings)
                md += f"\n**Average rating: {avg:.1f}/5** across {len(ratings)} takes"
                return md

            refresh_btn = gr.Button("Refresh Ratings")
            ratings_md = gr.Markdown(load_ratings())
            refresh_btn.click(load_ratings, outputs=[ratings_md])


print(f"\n{'='*60}")
print(f"Eval UI ready at http://0.0.0.0:{args.port}")
print(f"Access from other devices on LAN via http://<this-pc-ip>:{args.port}")
print(f"{'='*60}\n")

app.launch(server_name="0.0.0.0", server_port=args.port)
