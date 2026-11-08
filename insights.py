
from sklearn.ensemble import IsolationForest
from database import get_monthly_trends


def detect_anomalies():
    trends = get_monthly_trends()

    if len(trends) < 12:
        return {
            "method": "Isolation Forest",
            "total_months": len(trends),
            "anomalies": [],
            "message": "Insufficient monthly data for analysis"
        }

    # One feature per month: number of sightings
    X = [[row["count"]] for row in trends]

    model = IsolationForest(
        contamination=0.05,
        random_state=42
    )

    predictions = model.fit_predict(X)
    scores = model.decision_function(X)

    anomalies = []

    for row, prediction, score in zip(
        trends, predictions, scores
    ):
        if prediction == -1:
            anomalies.append({
                "month": row["month"],
                "count": row["count"],
                "anomaly_score": round(float(score), 4)
            })

    return {
        "method": "Isolation Forest",
        "total_months": len(trends),
        "anomalies": anomalies
    }
