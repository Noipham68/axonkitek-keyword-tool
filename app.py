import os
import yaml
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google.ads.googleads.client import GoogleAdsClient

# --- Cấu hình Google Ads từ env vars hoặc google-ads.yaml ---
# Cách đơn giản: tải google-ads.yaml lên cùng repo, load từ đó.
# Hoặc build động:
# with open("google-ads.yaml","w") as f:
#     f.write(f"""
# developer_token: '{os.environ['DEV_TOKEN']}'
# client_id:     '{os.environ['CLIENT_ID']}'
# client_secret: '{os.environ['CLIENT_SECRET']}'
# refresh_token: '{os.environ['REFRESH_TOKEN']}'
# login_customer_id: '{os.environ.get('LOGIN_CUST','')}'
# """)

client = GoogleAdsClient.load_from_storage("google-ads.yaml")

app = Flask(__name__, static_folder='static')
CORS(app)

def fetch_metrics(customer_id, keywords, timeframe):
    service = client.get_service("KeywordPlanIdeaService")
    req = client.get_type("GenerateKeywordIdeasRequest")
    req.customer_id = customer_id
    # Nếu cần set GEO / LANGUAGE:
    # req.geo_target_constants.append("geoTargetConstants/2840")  # US
    # req.language = "languageConstants/1000"  # English
    for kw in keywords:
        req.keyword_seed.keywords.append(kw)
    resp = service.generate_keyword_ideas(request=req)
    out = []
    for idea in resp:
        m = idea.keyword_idea_metrics
        out.append({
            "keyword": idea.text.value,
            "volume": m.avg_monthly_searches.value,
            "competition": m.competition.name,
            "low": m.low_top_of_page_bid_micros.value / 1e6,
            "high": m.high_top_of_page_bid_micros.value / 1e6
        })
    return out

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/api/metrics", methods=["POST"])
def api_metrics():
    data = request.get_json()
    kws = data.get("keywords", [])
    tf = data.get("timeframe", "monthly")
    customer = os.environ.get("CUSTOMER_ID") or "YOUR_CUSTOMER_ID"
    results = fetch_metrics(customer, kws, tf)
    return jsonify(results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
