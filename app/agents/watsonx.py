# app/agents/watsonx.py

import os
import json
import requests

ALLOWED_CATEGORIES = [
    "open_drain",
    "pothole",
    "streetlight",
    "water_leak",
    "fallen_tree",
    "other"
]

def suggest_category_watsonx(description: str) -> dict:
    """
    Optional IBM watsonx.ai REST adapter.
    Attempts to retrieve an IAM token and perform text generation to suggest a category.
    Returns dict with 'category' and 'warning' (or None).
    """
    api_key = os.getenv("WATSONX_API_KEY")
    project_id = os.getenv("WATSONX_PROJECT_ID")
    model_id = os.getenv("WATSONX_MODEL_ID")
    url = os.getenv("WATSONX_URL")

    # If any environment variable is missing, gracefully exit and use local fallback
    if not all([api_key, project_id, model_id, url]):
        return {
            "category": None,
            "warning": "watsonx credentials not fully configured; using local keyword fallback."
        }

    try:
        # 1. Obtain IAM Token from IBM Cloud
        iam_url = "https://iam.cloud.ibm.com/identity/token"
        token_res = requests.post(
            iam_url,
            data={"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": api_key},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=5
        )
        token_res.raise_for_status()
        access_token = token_res.json().get("access_token")

        # 2. Call watsonx.ai Text Generation API
        prompt = (
            f"Classify the following civic issue into exactly one category from this list: "
            f"{', '.join(ALLOWED_CATEGORIES)}.\n"
            f"Issue: '{description}'\n"
            f"Respond with JSON in the format: {{\"category\": \"<category_name>\"}}"
        )

        payload = {
            "model_id": model_id,
            "input": prompt,
            "project_id": project_id,
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.0
            }
        }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        endpoint = f"{url.rstrip('/')}/ml/v1/text/generation?version=2023-05-29"
        gen_res = requests.post(endpoint, json=payload, headers=headers, timeout=5)
        gen_res.raise_for_status()

        res_data = gen_res.json()
        generated_text = res_data["results"][0]["generated_text"].strip()

        # 3. Parse output JSON and validate returned category name
        parsed = json.loads(generated_text)
        cat = parsed.get("category", "").lower()

        if cat in ALLOWED_CATEGORIES:
            return {"category": cat, "warning": None}
        else:
            return {
                "category": None,
                "warning": f"watsonx returned unknown category '{cat}'; falling back to keywords."
            }

    except Exception as err:
        return {
            "category": None,
            "warning": f"watsonx request failed ({type(err).__name__}); falling back to keywords."
        }