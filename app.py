import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google.ads.googleads.client import GoogleAdsClient

# --- Initialize Flask ---
app = Flask(__name__, static_folder="static")
CORS(app)

# --- Build Google Ads config dict from your ENV VAR keys ---
config_dict = {
    "developer_token":   os.environ["developer_token"],       # đổi lại từ DEV_TOKEN → developer_token
    "client_id":         os.environ["client_id"],             # giữ nguyên như trên Render
    "client_secret":     os.environ["client_secret"],         # giữ nguyên
    "refresh_token":     os.environ["refresh_token"],         # giữ nguyên
    "login_customer_id": os.environ.get("login_customer_id"),  # giữ nguyên
}

# LẤY CUSTOMER_ID (trên Render bạn khai là CUSTOMER_ID)
customer_id = os.environ["CUSTOMER_ID"]

# Khởi tạo client
client = GoogleAdsClient.load_from_dict(config_dict)

def fetch_metrics(keywords):
    service = client.get_service("KeywordPlanIdeaService")
    req = client.get_type("GenerateKeywordIdeasRequest")
    req.customer_id = customer_id
    # Bạn có thể add geo_target_constants, language nếu cần
    for kw in keywords:
        req.keyword_seed.keywords.append(kw)

    resp = service.generate_keyword_ideas(request=req)
    out = []
    for idea in resp:
        m = idea.keyword_idea_metrics
        out.append({
            "keyword":    idea.text.value,
            "volume":     m.avg_monthly_searches.value,
            "competition": m.competition.name,
            "low":        round(m.low_top_of_page_bid_micros.value / 1e6, 2),
            "high":       round(m.high_top_of_page_bid_micros.value / 1e6, 2),
        })
    return out

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/metrics", methods=["POST"])
def api_metrics():
    data = request.get_json(force=True)
    kws  = data.get("keywords", [])
    results = fetch_metrics(kws)
    return jsonify(results)

# --- Entrypoint ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
