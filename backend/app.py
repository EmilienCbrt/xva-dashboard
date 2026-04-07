from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/calculate", methods=["POST"])
def calculate():
    data = request.json

    result = {
        "price": 100,
        "CVA": 1.2,
        "DVA": 0.5,
        "FVA": 0.3,
        "KVA": 0.2,
        "EE": [0, 1, 2, 1, 0]
    }

    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True)