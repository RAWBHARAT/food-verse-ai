"""
Food Verse AI — Multimodal Food Intelligence Agent
Skill Wallet Capstone Project 3

Run locally:
    pip install -r requirements.txt
    streamlit run app.py

Safety note:
AI image assessments are estimates, not laboratory tests or certified inspections.
Never use an image-only assessment to decide whether high-risk food is safe.
"""
from __future__ import annotations

import json
import math
import os
import re
from typing import Any

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

APP_NAME = "Food Verse AI"
MODEL_OPTIONS = {
    "Gemini (vision + text)": "gemini",
    "Groq (text; image support depends on model/account)": "groq",
}

st.set_page_config(
    page_title="Food Verse AI",
    page_icon="🍋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#17221d; --muted:#617068; --lime:#d8ff63; --mint:#e9f8ef; --orange:#ff875c; }
html, body, [class*="css"] { font-family:'DM Sans',sans-serif; }
.stApp { background:linear-gradient(135deg,#f7faf4 0%,#f1f7ef 55%,#fff8ed 100%); color:var(--ink); }
h1,h2,h3 { font-family:'Space Grotesk',sans-serif !important; letter-spacing:-.035em; }
.hero { padding:1.6rem 1.8rem; border-radius:24px; background:#172b22; color:#fff; margin-bottom:1rem; border:1px solid #294c39; }
.hero h1 { color:#d8ff63; font-size:2.65rem; margin:0; }
.hero p { color:#d8e8dc; margin:.45rem 0 0; font-size:1.05rem; }
.eyebrow { text-transform:uppercase; letter-spacing:.16em; font-size:.72rem; font-weight:700; color:#9ec5a9; }
.pill { display:inline-block; padding:.35rem .75rem; border-radius:999px; background:#e3f6d4; color:#234a2e; font-weight:700; font-size:.8rem; }
.card { background:rgba(255,255,255,.82); border:1px solid #e2eae0; padding:1rem 1.1rem; border-radius:18px; box-shadow:0 5px 18px rgba(28,55,35,.04); }
.small-muted { color:#617068; font-size:.9rem; }
div[data-testid="stMetric"] { background:#fff; padding:1rem; border-radius:16px; border:1px solid #e2eae0; }
.stButton>button { border-radius:12px; font-weight:700; }
section[data-testid="stSidebar"] { background:#eef6e9; }
div[data-testid="stTabs"] button { font-weight:700; }
.warning-box { padding:.9rem 1rem; background:#fff3dd; border-left:4px solid #ffae44; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

# ---------- Helpers ----------
def get_secret(name: str, default: str = "") -> str:
    try:
        return str(st.secrets.get(name, default) or default)
    except Exception:
        return os.getenv(name, default)

def normalize_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {"result": data}
    except Exception:
        return {"summary": text}

def gemini_generate(prompt: str, image: Image.Image | None = None, api_key: str = "") -> str:
    """Gemini multimodal call. Imports SDK lazily so demo mode has no API dependency."""
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
    contents: list[Any] = [prompt]
    if image is not None:
        contents.append(image)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=types.GenerateContentConfig(temperature=0.35),
    )
    return response.text or ""

def groq_generate(prompt: str, api_key: str) -> str:
    """Text-only Groq call; image tasks deliberately use safe demo fallback."""
    from groq import Groq
    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are Food Verse AI, a careful food-science assistant. Return valid JSON only. Be transparent about uncertainty."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.35,
    )
    return response.choices[0].message.content or ""

def run_ai(prompt: str, image: Image.Image | None = None, task: str = "text") -> tuple[str, str]:
    """Return (text, mode). API errors fall back gracefully."""
    provider = st.session_state.get("provider", "demo")
    key = st.session_state.get("api_key", "")
    if provider == "gemini" and key:
        try:
            return gemini_generate(prompt, image=image, api_key=key), "Gemini"
        except Exception as exc:
            st.warning(f"Gemini request failed; switched to demonstration output. ({type(exc).__name__})")
    elif provider == "groq" and key and image is None:
        try:
            return groq_generate(prompt, api_key=key), "Groq"
        except Exception as exc:
            st.warning(f"Groq request failed; switched to demonstration output. ({type(exc).__name__})")
    elif provider == "groq" and image is not None:
        st.info("Groq is configured as text-only in this starter. Image analysis uses demonstration output; select Gemini for vision.")
    return "", "Demonstration mode"

def parse_image(uploaded) -> Image.Image:
    img = Image.open(uploaded).convert("RGB")
    img.thumbnail((1280, 1280))
    return img

def display_json_or_text(raw: str, fallback: dict) -> dict:
    if raw:
        parsed = normalize_json(raw)
        if "summary" in parsed and len(parsed) == 1:
            st.write(parsed["summary"])
        return parsed
    return fallback

def safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)

def nutrition_demo() -> dict:
    return {
        "dish_name": "Vegetable grain bowl (demo estimate)",
        "cuisine": "Contemporary fusion",
        "ingredients": ["cooked brown rice", "chickpeas", "roasted vegetables", "olive oil", "lemon"],
        "portion_size": "1 medium bowl, approximately 400 g",
        "nutrition": {"Calories (kcal)": 520, "Protein (g)": 18, "Carbohydrates (g)": 74, "Fats (g)": 16, "Fiber (g)": 13},
        "allergens": ["Possible cross-contact; confirm ingredients and preparation"],
        "health_score": 82,
        "score_reason": "Fiber-rich ingredients and a plant-protein source; sodium and oil are unknown.",
        "confidence_note": "Illustrative demo only. Photo-based portion and nutrient estimates can be substantially wrong."
    }

def freshness_demo() -> dict:
    return {
        "item": "Produce item (demo)",
        "observations": ["Visual condition cannot reveal all microbial or chemical hazards."],
        "stage": "Moderately Fresh",
        "advice": "Consume within 24h",
        "storage": ["Keep perishable items refrigerated promptly.", "Separate raw animal products from ready-to-eat food."],
        "confidence_note": "Demonstration output, not an actual assessment. Do not taste food to test safety."
    }

def hygiene_demo() -> dict:
    return {
        "score": 78,
        "observations": [
            {"indicator": "Hair restraint", "status": "Not verifiable from this sample", "severity": "Review"},
            {"indicator": "Glove / hand hygiene", "status": "Not reliably inferable", "severity": "Review"},
            {"indicator": "Sanitization", "status": "Surface cleanliness alone cannot verify sanitizing", "severity": "Review"},
            {"indicator": "Raw-to-ready-to-eat separation", "status": "Check for separation and dedicated tools", "severity": "High"}
        ],
        "actions": ["Verify local food code and documented procedures.", "Separate raw poultry and ready-to-eat produce.", "Record sanitizer concentration and contact time."]
    }

def recipe_demo(ingredients: list[str], diet: str) -> dict:
    pantry = ingredients or ["lentils", "tomatoes", "onion", "rice"]
    main = ", ".join(pantry[:5])
    return {
        "name": "Bright Pantry One-Pot Bowl",
        "description": f"A flexible, balanced meal built around: {main}.",
        "time_minutes": 30,
        "difficulty": "Easy",
        "servings": 2,
        "ingredients": [{"item": x, "amount": "to taste / available quantity"} for x in pantry[:8]],
        "steps": [
            "Wash produce and prepare ingredients; keep raw animal products separate if used.",
            "Cook the longest-cooking grain or pulse according to package directions.",
            "Sauté aromatics in a small amount of oil, then add vegetables and seasonings.",
            "Combine components and cook until all ingredients are fully cooked.",
            "Taste, adjust seasoning, and serve. Refrigerate leftovers promptly."
        ],
        "substitutions": ["Beans or lentils can replace one another for plant protein.", "Use lemon or vinegar for brightness.", "Choose a whole grain when compatible with your dietary needs."],
        "diet_note": f"Demo mode cannot guarantee compliance with {diet}; verify every ingredient and cross-contact risk."
    }

def meal_plan_demo(calories: int, diet: str, goal: str) -> dict:
    templates = [
        ("Oats with chia and berries", "Lentil-quinoa bowl", "Tofu and vegetable stir-fry"),
        ("Greek yogurt or soy yogurt bowl", "Chickpea salad with whole grain", "Bean chili with vegetables"),
        ("Vegetable omelet or tofu scramble", "Brown rice and dal", "Baked tofu with roasted vegetables"),
        ("Overnight oats", "Whole-grain wrap with beans", "Lentil soup and salad"),
        ("Cottage cheese or tofu toast", "Quinoa and edamame bowl", "Vegetable curry with protein-rich side"),
        ("Fruit with yogurt or soy yogurt", "Bean and vegetable soup", "Stuffed peppers with lentils"),
        ("Oats with nut/seed topping", "Leftover grain bowl", "Chickpea and vegetable tray bake"),
    ]
    meals = []
    for i, (b, l, d) in enumerate(templates, 1):
        meals.append({"day": f"Day {i}", "breakfast": b, "lunch": l, "dinner": d, "snacks": "Fruit; nuts/seeds if suitable"})
    return {"daily_calorie_target": calories, "diet": diet, "goal": goal, "days": meals,
            "note": "Demo menu is illustrative, not a clinical diet prescription. Adapt portions and verify dietary suitability."}

def nutrition_prompt() -> str:
    return """Analyze this meal photo as a food-science assistant. Return JSON only with:
dish_name, cuisine, ingredients (array), portion_size, nutrition (object with exactly Calories (kcal), Protein (g), Carbohydrates (g), Fats (g), Fiber (g)), allergens (array; say unknown where uncertain), health_score (integer 1-100), score_reason, confidence_note.
Estimate portion and nutrition conservatively; label estimates. Do not claim to identify hidden ingredients or allergens with certainty. The health score is a heuristic, not a medical metric. If uncertain, state so."""

def freshness_prompt() -> str:
    return """Assess only visible condition of this perishable item. Return JSON only with item, observations (array), stage (exactly one of Fresh, Moderately Fresh, Spoiled), advice (exactly one of Safe to consume, Consume within 24h, Discard immediately), storage (array), confidence_note.
Important: image-only assessment cannot establish microbiological safety. Do not declare high-risk food safe based on appearance. If meat, seafood, dairy, cooked leftovers, or food with suspicious growth/odor/storage history is involved, recommend discarding when safety is uncertain. Never recommend tasting."""

def hygiene_prompt() -> str:
    return """Review this kitchen image for visible food-safety indicators. Return JSON only with score (integer 0-100), observations (array of objects with indicator, status, severity), actions (array). Check hair restraint, hand/glove hygiene only if observable, surface sanitation (note that appearance does not prove sanitization), and raw/ready-to-eat separation including raw poultry near vegetables. Never claim regulatory certification. Mark not visible/not verifiable rather than guessing. Score is a preliminary visual checklist, not a formal inspection."""

def recipe_prompt(ingredients: list[str], diet: str, servings: int, max_time: int) -> str:
    return f"""Create one nutritious practical recipe using these pantry ingredients: {ingredients}.
Dietary preference: {diet}. Servings: {servings}. Maximum cooking time: {max_time} minutes.
Return JSON only: name, description, time_minutes, difficulty, servings, ingredients (array of objects item and amount), steps (array), substitutions (array), diet_note. Avoid unsupported medical claims, identify allergens when known, and explain if constraints cannot be met."""

def meal_plan_prompt(profile: dict, calories: int) -> str:
    return f"""Create a practical 7-day meal schedule based on this profile: {profile}. Daily calorie target estimate: {calories} kcal.
Return JSON only: daily_calorie_target, diet, goal, days (7 objects with day, breakfast, lunch, dinner, snacks), grocery_list (array of objects item and approximate quantity), note.
Provide variety, culturally flexible foods, and realistic meals. This is general wellness information, not medical advice. For diabetes, pregnancy, eating disorders, kidney disease, or other clinical needs, recommend clinician/dietitian review. Do not claim exact calories unless portions are specified."""

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🍋 Food Verse AI")
    st.caption("Multimodal Food Intelligence Agent")
    st.markdown("---")
    st.markdown("### 🔐 AI configuration")
    provider_label = st.selectbox("AI provider", ["Demonstration mode", *MODEL_OPTIONS.keys()])
    provider = "demo" if provider_label == "Demonstration mode" else MODEL_OPTIONS[provider_label]
    st.session_state["provider"] = provider
    key_env = "GEMINI_API_KEY" if provider == "gemini" else "GROQ_API_KEY"
    stored_key = get_secret(key_env)
    api_key = ""
    if provider != "demo":
        api_key = st.text_input(f"{provider_label.split()[0]} API key", value=stored_key, type="password",
                                help="Key is held in this session only unless provided through Streamlit secrets or environment variables.")
        st.caption("Recommended deployment: set GEMINI_API_KEY or GROQ_API_KEY in Streamlit Cloud Secrets.")
    st.session_state["api_key"] = api_key
    st.markdown("---")
    st.markdown("### 🧭 Intelligence pillars")
    st.caption("01 · Nutrition audit\n\n02 · Freshness diagnostics\n\n03 · Kitchen compliance\n\n04 · Recipe assistant\n\n05 · Meal planner")
    st.markdown("---")
    st.caption("Built for Skill Wallet Capstone Project 3")

# ---------- Hero ----------
st.markdown("""
<div class="hero">
  <div class="eyebrow">Skill Wallet · Capstone Project 3</div>
  <h1>Food Verse AI</h1>
  <p>Multimodal food intelligence for smarter plates, safer kitchens, and better planning.</p>
</div>
""", unsafe_allow_html=True)
st.markdown('<span class="pill">✦ Five intelligence modules</span> &nbsp; <span class="pill">Privacy-minded · No database</span>', unsafe_allow_html=True)
st.write("")

tabs = st.tabs([
    "🥗 Nutrition Audit",
    "🍓 Freshness Check",
    "🧼 Kitchen Safety",
    "👩‍🍳 Recipe Assistant",
    "📅 Meal Planner",
])

# ---------- Tab 1 ----------
with tabs[0]:
    st.subheader("Food Recognition & Nutrition Audit")
    st.write("Upload a meal photo for a structured estimate of dish identity, portion, macros, allergens, and a heuristic health score.")
    col1, col2 = st.columns([1, 1.2], gap="large")
    with col1:
        meal_file = st.file_uploader("Upload meal / dish photo", type=["jpg", "jpeg", "png", "webp"], key="meal_img")
        if meal_file:
            try:
                meal_image = parse_image(meal_file)
                st.image(meal_image, caption="Uploaded meal", use_container_width=True)
            except Exception as exc:
                st.error(f"Could not read image: {exc}")
                meal_image = None
        else:
            meal_image = None
        analyze_meal = st.button("✨ Analyze nutrition", type="primary", use_container_width=True, key="analyze_meal")
    with col2:
        st.markdown('<div class="card"><b>What you’ll receive</b><p class="small-muted">Dish and cuisine guess · Ingredient list · Portion estimate · Five nutrition metrics · Allergen cautions · Health score</p></div>', unsafe_allow_html=True)
        st.info("Nutrition values from photos are estimates. Verify ingredients and serving weights for accurate tracking. Allergy safety requires ingredient and cross-contact confirmation.")
    if analyze_meal:
        with st.spinner("Reviewing the meal…"):
            raw, mode = run_ai(nutrition_prompt(), meal_image, task="vision")
            result = display_json_or_text(raw, nutrition_demo())
        st.caption(f"Analysis source: {mode}")
        st.markdown(f"### {result.get('dish_name', 'Dish assessment')}")
        st.write(f"**Cuisine:** {result.get('cuisine', 'Uncertain')}  ·  **Portion:** {result.get('portion_size', 'Not estimated')}")
        ingredients = result.get("ingredients", [])
        st.write("**Likely ingredients:** " + (", ".join(map(str, ingredients)) if isinstance(ingredients, list) else str(ingredients)))
        nutrition = result.get("nutrition", {})
        expected = ["Calories (kcal)", "Protein (g)", "Carbohydrates (g)", "Fats (g)", "Fiber (g)"]
        values = {k: max(0, safe_float(nutrition.get(k, 0))) for k in expected}
        mcols = st.columns(5)
        for col, (label, val) in zip(mcols, values.items()):
            col.metric(label, f"{val:.0f}" if "Calories" in label else f"{val:.1f}")
        chart_df = pd.DataFrame({"Macro": ["Protein (g)", "Carbohydrates (g)", "Fats (g)", "Fiber (g)"],
                                 "Grams": [values["Protein (g)"], values["Carbohydrates (g)"], values["Fats (g)"], values["Fiber (g)"]]})
        chart_col, score_col = st.columns([1.3, 1])
        with chart_col:
            st.plotly_chart(px.bar(chart_df, x="Macro", y="Grams", color="Macro", title="Estimated macronutrients",
                                   color_discrete_sequence=["#4f9d69", "#ff875c", "#f5c451", "#8d83d7"]),
                            use_container_width=True)
        with score_col:
            score = max(1, min(100, int(safe_float(result.get("health_score", 50), 50))))
            st.metric("Composite Health Score", f"{score}/100")
            st.progress(score / 100)
            st.write(result.get("score_reason", "Heuristic score based on estimated composition."))
        st.markdown("**Allergen alerts**")
        allergens = result.get("allergens", ["Not reliably determined from image; verify ingredients."])
        if isinstance(allergens, list):
            for allergen in allergens:
                st.warning(str(allergen))
        else:
            st.warning(str(allergens))
        st.caption(result.get("confidence_note", "Image-based estimates are uncertain."))
        st.download_button("Download nutrition report (JSON)", json.dumps(result, indent=2), "food_verse_nutrition.json", "application/json")

# ---------- Tab 2 ----------
with tabs[1]:
    st.subheader("Food Freshness & Spoilage Diagnostic")
    st.write("Review visible surface condition and get storage guidance. Appearance alone cannot prove food is safe.")
    fresh_file = st.file_uploader("Upload raw fruit, vegetable, meat, or dairy photo", type=["jpg", "jpeg", "png", "webp"], key="fresh_img")
    fresh_image = None
    if fresh_file:
        try:
            fresh_image = parse_image(fresh_file)
            st.image(fresh_image, caption="Uploaded item", width=420)
        except Exception as exc:
            st.error(f"Could not read image: {exc}")
    item_history = st.text_input("Optional context", placeholder="e.g., cut melon refrigerated overnight; chicken left out for 3 hours")
    if st.button("🔎 Check visible freshness", type="primary", key="freshness_btn"):
        prompt = freshness_prompt() + f"\nUser context: {item_history or 'No storage history provided.'}"
        with st.spinner("Checking visible cues…"):
            raw, mode = run_ai(prompt, fresh_image, task="vision")
            result = display_json_or_text(raw, freshness_demo())
        st.caption(f"Analysis source: {mode}")
        stage = result.get("stage", "Uncertain")
        advice = result.get("advice", "Safety cannot be determined from the image")
        color = {"Fresh": "🟢", "Moderately Fresh": "🟡", "Spoiled": "🔴"}.get(stage, "⚪")
        st.markdown(f"### {color} {stage}")
        st.markdown(f"**Recommended action:** {advice}")
        st.write("**Visible observations**")
        obs = result.get("observations", [])
        if isinstance(obs, list):
            for item in obs: st.write(f"• {item}")
        st.write("**Storage & preservation**")
        storage = result.get("storage", [])
        if isinstance(storage, list):
            for item in storage: st.write(f"• {item}")
        st.warning("Discard food with suspicious mold, slime, unusual odor, unsafe time/temperature history, or uncertain handling. Do not taste-test. Some hazards are invisible; follow local food-safety guidance.")
        st.caption(result.get("confidence_note", "Visual classification is not a microbiological test."))

# ---------- Tab 3 ----------
with tabs[2]:
    st.subheader("Kitchen Hygiene & Food Safety Compliance")
    st.write("Use this as a preliminary visual checklist, not as a certified audit or substitute for direct inspection.")
    kitchen_file = st.file_uploader("Upload kitchen image or a representative video frame", type=["jpg", "jpeg", "png", "webp"], key="kitchen_img")
    kitchen_image = None
    if kitchen_file:
        try:
            kitchen_image = parse_image(kitchen_file)
            st.image(kitchen_image, caption="Kitchen sample", use_container_width=True)
        except Exception as exc:
            st.error(f"Could not read image: {exc}")
    st.caption("For video, upload a representative frame exported as an image. This app does not process full video streams.")
    kitchen_context = st.text_area("Optional inspection context", placeholder="e.g., raw poultry prep station, ready-to-eat salad station", height=70)
    if st.button("🧽 Run visual hygiene review", type="primary", key="hygiene_btn"):
        prompt = hygiene_prompt() + f"\nContext: {kitchen_context or 'None supplied.'}"
        with st.spinner("Reviewing visible indicators…"):
            raw, mode = run_ai(prompt, kitchen_image, task="vision")
            result = display_json_or_text(raw, hygiene_demo())
        st.caption(f"Analysis source: {mode}")
        score = max(0, min(100, int(safe_float(result.get("score", 50), 50))))
        st.metric("Kitchen Hygiene Compliance Score", f"{score}%")
        st.progress(score / 100)
        observations = result.get("observations", [])
        if isinstance(observations, list) and observations:
            st.markdown("#### Itemized review log")
            df = pd.DataFrame([x if isinstance(x, dict) else {"indicator": str(x), "status": "", "severity": ""} for x in observations])
            st.dataframe(df, use_container_width=True, hide_index=True)
        st.markdown("#### Recommended corrective actions")
        for action in result.get("actions", []):
            st.write(f"• {action}")
        st.warning("Gloves do not replace handwashing. A clean-looking surface is not proof of sanitization. Confirm temperatures, sanitizer concentration/contact time, logs, and local regulations in person.")
        st.download_button("Download review log (JSON)", json.dumps(result, indent=2), "food_verse_hygiene_review.json", "application/json")

# ---------- Tab 4 ----------
with tabs[3]:
    st.subheader("Smart Kitchen Recipe Assistant")
    st.write("Turn the ingredients you have into a flexible recipe.")
    pantry_text = st.text_area("Pantry inventory", placeholder="e.g., chickpeas, spinach, tomatoes, rice, yogurt, lemon", height=100)
    r1, r2, r3 = st.columns(3)
    with r1:
        recipe_diet = st.selectbox("Diet preference", ["No restriction", "Vegetarian", "Vegan", "Keto", "Gluten-free", "Diabetic-friendly"])
    with r2:
        servings = st.number_input("Servings", min_value=1, max_value=12, value=2)
    with r3:
        max_time = st.slider("Max cooking time (minutes)", 10, 120, 35, step=5)
    if st.button("🍳 Create my recipe", type="primary", key="recipe_btn"):
        ingredients = [x.strip() for x in re.split(r",|\n|;", pantry_text) if x.strip()]
        if not ingredients:
            st.error("Add at least one ingredient to your pantry inventory.")
        else:
            prompt = recipe_prompt(ingredients, recipe_diet, int(servings), int(max_time))
            with st.spinner("Creating a pantry-friendly recipe…"):
                raw, mode = run_ai(prompt)
                result = display_json_or_text(raw, recipe_demo(ingredients, recipe_diet))
            st.caption(f"Generation source: {mode}")
            st.markdown(f"### {result.get('name', 'Your recipe')}")
            st.write(result.get("description", ""))
            c1, c2, c3 = st.columns(3)
            c1.metric("Cooking time", f"{result.get('time_minutes', '—')} min")
            c2.metric("Difficulty", result.get("difficulty", "Easy"))
            c3.metric("Servings", result.get("servings", servings))
            st.markdown("#### Ingredients")
            for item in result.get("ingredients", []):
                if isinstance(item, dict): st.write(f"• {item.get('item', '')} — {item.get('amount', 'as needed')}")
                else: st.write(f"• {item}")
            st.markdown("#### Method")
            for i, step in enumerate(result.get("steps", []), 1): st.write(f"{i}. {step}")
            st.markdown("#### Substitutions")
            for item in result.get("substitutions", []): st.write(f"• {item}")
            st.info(result.get("diet_note", "Verify allergens and dietary requirements before cooking."))
            st.download_button("Download recipe (JSON)", json.dumps(result, indent=2), "food_verse_recipe.json", "application/json")

# ---------- Tab 5 ----------
with tabs[4]:
    st.subheader("Personalized Meal Planner")
    st.write("Calculate a rough energy target and build a flexible 7-day meal outline.")
    with st.form("profile_form"):
        p1, p2, p3 = st.columns(3)
        with p1:
            age = st.number_input("Age (years)", 18, 100, 30)
            gender = st.selectbox("Mifflin–St Jeor coefficient", ["Female", "Male", "Prefer not to say"])
        with p2:
            weight = st.number_input("Weight (kg)", 30.0, 300.0, 70.0, step=0.5)
            height = st.number_input("Height (cm)", 120.0, 230.0, 170.0, step=0.5)
        with p3:
            activity = st.selectbox("Activity level", ["Sedentary", "Lightly active", "Moderately active", "Very active", "Extra active"])
            goal = st.selectbox("Fitness goal", ["Maintenance", "Fat Loss", "Muscle Gain"])
        diet = st.selectbox("Dietary constraints", ["Balanced / no restriction", "Vegan", "Vegetarian", "Keto", "Diabetic-Friendly", "Gluten-free"])
        allergies = st.text_input("Allergies / exclusions (comma-separated)", placeholder="e.g., peanuts, shellfish")
        submit_profile = st.form_submit_button("📅 Calculate target & build 7-day plan", type="primary", use_container_width=True)
    if submit_profile:
        # Mifflin–St Jeor; coefficient requires a sex-specific constant. "Prefer not to say" uses midpoint.
        base = 5 if gender == "Male" else (-161 if gender == "Female" else -78)
        bmr = 10 * weight + 6.25 * height - 5 * age + base
        activity_factors = {"Sedentary": 1.2, "Lightly active": 1.375, "Moderately active": 1.55, "Very active": 1.725, "Extra active": 1.9}
        tdee = bmr * activity_factors[activity]
        adjustments = {"Maintenance": 0, "Fat Loss": -350, "Muscle Gain": 250}
        target = int(round(max(1200, tdee + adjustments[goal]) / 50) * 50)
        profile = {"age": age, "gender_coefficient": gender, "weight_kg": weight, "height_cm": height,
                   "activity": activity, "diet": diet, "goal": goal, "allergies_or_exclusions": allergies}
        st.markdown("#### Your estimated energy range")
        c1, c2, c3 = st.columns(3)
        c1.metric("BMR estimate", f"{bmr:.0f} kcal/day")
        c2.metric("TDEE estimate", f"{tdee:.0f} kcal/day")
        c3.metric("Suggested target", f"{target:,} kcal/day")
        st.caption("Formula estimates are approximate. The 'prefer not to say' option uses a midpoint constant, which is not a validated individualized estimate. The 1,200 kcal floor is a software guardrail, not a safe minimum for every person.")
        prompt = meal_plan_prompt(profile, target)
        with st.spinner("Building your 7-day meal schedule…"):
            raw, mode = run_ai(prompt)
            result = display_json_or_text(raw, meal_plan_demo(target, diet, goal))
        st.caption(f"Plan source: {mode}")
        days = result.get("days", [])
        if isinstance(days, list) and days:
            plan_df = pd.DataFrame(days)
            st.dataframe(plan_df, use_container_width=True, hide_index=True)
        grocery = result.get("grocery_list", [])
        if grocery:
            st.markdown("#### Grocery shopping list")
            for item in grocery:
                if isinstance(item, dict): st.checkbox(f"{item.get('item', 'Item')} — {item.get('quantity', 'quantity not specified')}", key=f"grocery_{item.get('item', str(item))}")
                else: st.checkbox(str(item), key=f"grocery_{item}")
        else:
            st.info("Grocery list is generated by the AI provider when available. In demonstration mode, use the menu below as a template and derive quantities from portions.")
        st.warning("For diabetes or other clinical nutrition needs, consult a qualified clinician/dietitian. This planner is general wellness support, not medical advice. Review allergy and cross-contact risks manually.")
        st.download_button("Download 7-day plan (JSON)", json.dumps(result, indent=2), "food_verse_7_day_meal_plan.json", "application/json")

st.markdown("---")
st.markdown('<p class="small-muted">Food Verse AI · Estimates only · No database · Images are processed in-session. Configure secrets for AI-powered analysis.</p>', unsafe_allow_html=True)
