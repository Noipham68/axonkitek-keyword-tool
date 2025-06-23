import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from google.ads.googleads.client import GoogleAdsClient

# --- Initialize Flask app ---
app = Flask(__name__, static_folder="static")
CORS(app)

# --- Initialize Google Ads client from ENV vars ---
config_dict = {
    "developer_token": os.environ["DEV_TOKEN"],
    "client_id":       os.environ["CLIENT_ID"],
    "client_secret":   os.environ["CLIENT_SECRET"],
    "refresh_token":   os.environ["REFRESH_TOKEN"],
}
# Optionally set a manager customer ID
login_cust = os.environ.get("LOGIN_CUSTOMER")
if login_cust:
    config_dict["login_customer_id"] = login_cust

client = GoogleAdsClient.load_from_dict(config_dict)

def fetch_metrics(customer_id, keywords, timeframe):
    """
    Call Google Ads KeywordPlanIdeaService to fetch:
      - avg_monthly_searches
      - competition
      - low/high top-of-page bid
    """
    service = client.get_service("KeywordPlanIdeaService")
    request_proto = client.get_type("GenerateKeywordIdeasRequest")
    request_proto.customer_id = customer_id
    # If desired, add geo_target_constants or language:
    # request_proto.geo_target_constants.append("geoTargetConstants/2840")  # US
    # request_proto.language = "languageConstants/1000"  # English

    for kw in keywords:
        request_proto.keyword_seed.keywords.append(kw)

    response = service.generate_keyword_ideas(request=request_proto)
    results = []
    for idea in response:
        m = idea.keyword_idea_metrics
        results.append({
            "keyword":    idea.text.value,
            "volume":     m.avg_monthly_searches.value,
            "competition": m.competition.name,
            "low":        round(m.low_top_of_page_bid_micros.value / 1e6, 2),
            "high":       round(m.high_top_of_page_bid_micros.value / 1e6, 2),
        })
    return results

# --- Routes ---
@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/api/metrics", methods=["POST"])
def api_metrics():
    data = request.get_json(force=True)
    keywords = data.get("keywords", [])
    timeframe = data.get("timeframe", "monthly")  # currently unused but available
    customer_id = os.environ["CUSTOMER_ID"]
    metrics = fetch_metrics(customer_id, keywords, timeframe)
    return jsonify(metrics)

# --- Entry point ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
