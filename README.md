<<<<<<< HEAD
# Food Verse AI — Multimodal Food Intelligence Agent
**Skill Wallet Capstone Project 3**

A modular Streamlit prototype with five modules:
1. Food recognition and nutrition audit
2. Freshness and spoilage visual diagnostics
3. Kitchen hygiene visual checklist
4. Pantry-based recipe assistant
5. Personalized 7-day meal planner with energy estimates

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## AI configuration
The app runs in **Demonstration mode** without keys. To enable AI, choose a provider in the sidebar and paste a key, or set a Streamlit secret.

`.streamlit/secrets.toml`:
```toml
GEMINI_API_KEY = "your-key"
# or
GROQ_API_KEY = "your-key"
```
Never commit `secrets.toml`. The app uses Gemini 2.5 Flash for multimodal analysis. Groq is wired for text generation; in this implementation image tasks intentionally fall back to demo mode because vision model availability varies.

## Streamlit Community Cloud
1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. In Streamlit Community Cloud, deploy `app.py` as the entry point.
3. Add `GEMINI_API_KEY` (or `GROQ_API_KEY`) in app Secrets.
4. Deploy. No database or external storage is required.

## Important limitations
- Nutrition, ingredient, portion, freshness, and visual hygiene findings are estimates, not ground truth.
- Image-only analysis cannot confirm allergens, pathogens, safe time/temperature history, or actual sanitization.
- Kitchen video is not processed directly; upload an exported frame.
- Meal planning is general wellness support, not medical advice. BMR/TDEE use the Mifflin–St Jeor estimate and activity multipliers; individual needs vary.
- For real deployment, add automated tests, observability, rate limiting, key rotation, data retention review, and domain expert validation.
=======
# food-verse-ai
Multimodal Food Intelligence Agent — Skill Wallet Capstone Project 3
>>>>>>> 6a7b4599a22f73c0af6ac97d432f284a62262316
