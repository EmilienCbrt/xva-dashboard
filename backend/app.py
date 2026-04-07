from flask import Flask, jsonify, request
from flask_cors import CORS
from xva_engine import run_xva

app = Flask(__name__)
CORS(app)

product_info = {
    "IRS": {"maturity": "5Y", "label": "IRS Payer"},
    "FRA": {"maturity": "6M"},
    "Cap": {"maturity": "5Y"},
    "Swaption": {"maturity": "5Yx5Y"},
    "Zero Coupon Bond": {"maturity": "7Y"},
}

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/calculate", methods=["POST"])
def calculate():
    try:
        data = request.json
        instruments = data.get("instruments", [])
        notional = data.get("notional", 10000000)
        product_param = data.get("productParam", 0.025)
        volatility = data.get("volatility", 0.01)

        # On suppose 1 seul instrument
        selected_instrument = instruments[0]

        # On appelle le moteur
        results = run_xva(instruments, notional, product_param, volatility)

        # On récupère les valeurs depuis results
        theoretical_value = results["theoretical_value"]
        total_cva = results["CVA"]
        total_dva = results["DVA"]
        total_fva = results["FVA"]
        total_kva = results["KVA"]

        # Calcul valeur économique
        economic_value = (
            theoretical_value
            - total_cva
            + total_dva
            - total_fva
            - total_kva
        )

        return jsonify({
            "product": selected_instrument,
            "maturity": product_info[selected_instrument]["maturity"],

            "theoretical_value": float(theoretical_value),
            "economic_value": float(economic_value),

            "CVA": float(total_cva),
            "DVA": float(total_dva),
            "FVA": float(total_fva),
            "KVA": float(total_kva),

            "exposure": results["exposure"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(port=5000)