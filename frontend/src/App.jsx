const API_URL = import.meta.env.VITE_API_URL;
import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

function App() {
  const instrumentsList = [
    "IRS",
    "FRA",
    "Cap",
    "Swaption",
    "Zero Coupon Bond",
  ];

  const [selectedInstrument, setSelectedInstrument] = useState("IRS");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [backendError, setBackendError] = useState(null);
  const [notional, setNotional] = useState(10000000);
  const [productParam, setProductParam] = useState(0.025);
  const [volatility, setVolatility] = useState(0.01);

  const handleCalculate = async () => {
    setLoading(true);
    setBackendError(null);
    setResults(null);

    try {
      const response = await fetch(`${API_URL}/calculate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          instruments: [selectedInstrument],
          notional: notional,
          productParam: productParam,
          volatility: volatility,
        }),
      });

      const data = await response.json();
      console.log(data);

      if (data.error) {
        setBackendError(data.error);
        setResults(null);
      } else {
        setResults(data);
      }
    } catch (error) {
      console.error("Erreur:", error);
      setBackendError("Erreur de connexion au backend.");
      setResults(null);
    } finally {
      setLoading(false);
    }
  };

  const paramLabel =
  selectedInstrument === "Cap" || selectedInstrument === "Swaption"
    ? "Strike"
    : "Rate";

  const showVolatility =
  selectedInstrument === "Cap" || selectedInstrument === "Swaption";
    
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0f172a, #1e293b)",
        padding: "40px",
        fontFamily: "Arial",
        color: "white",
      }}
    >
      <h1>📊 XVA lab Dashboard</h1>

      <div style={{ display: "flex", gap: "40px", alignItems: "flex-start" }}>
  <div
    style={{
      display: "flex",
      flexDirection: "column",
      gap: "20px",
      width: "280px",
      paddingRight: "40px",
      borderRight: "1px solid #334155",
    }}
  >
    <div
      style={{
        backgroundColor: "#1e293b",
        padding: "20px",
        borderRadius: "15px",
        width: "100%",
        height: "fit-content",
      }}
    >
      <h3>Instrument</h3>

      <label style={{ display: "block", marginBottom: "10px" }}>
        Sélection du produit
      </label>

      <select
        value={selectedInstrument}
        onChange={(e) => setSelectedInstrument(e.target.value)}
        style={{
          width: "100%",
          padding: "10px",
          borderRadius: "10px",
          border: "none",
          marginBottom: "20px",
          fontSize: "16px",
        }}
      >
        {instrumentsList.map((instrument) => (
          <option key={instrument} value={instrument}>
            {instrument}
          </option>
        ))}
      </select>
      <label style={{ display: "block", marginBottom: "10px" }}>
        Notional
      </label>

      <input
        type="number"
        value={notional}
        onChange={(e) => setNotional(Number(e.target.value))}
        style={{
          width: "100%",
          padding: "10px",
          borderRadius: "10px",
          border: "none",
          marginBottom: "20px",
          fontSize: "16px",
          boxSizing: "border-box",
        }}
      />

      {selectedInstrument !== "Zero Coupon Bond" && (
        <>
          <label style={{ display: "block", marginBottom: "10px" }}>
            {paramLabel}
          </label>

          <input
            type="number"
            step="0.001"
            value={productParam}
            onChange={(e) => setProductParam(Number(e.target.value))}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "10px",
              border: "none",
              marginBottom: "20px",
              fontSize: "16px",
              boxSizing: "border-box",
            }}
          />
        </>
      )}
      {showVolatility && (
        <>
          <label style={{ display: "block", marginBottom: "10px" }}>
            Volatility
          </label>

          <input
            type="number"
            step="0.001"
            value={volatility}
            onChange={(e) => setVolatility(Number(e.target.value))}
            style={{
              width: "100%",
              padding: "10px",
              borderRadius: "10px",
              border: "none",
              marginBottom: "20px",
              fontSize: "16px",
              boxSizing: "border-box",
            }}
          />
        </>
      )}
      <button
        onClick={handleCalculate}
        style={{
          width: "100%",
          padding: "12px",
          borderRadius: "10px",
          backgroundColor: "#2563eb",
          color: "white",
          border: "none",
          cursor: "pointer",
          fontSize: "16px",
          fontWeight: "bold",
        }}
      >
        Calculer
      </button>
    </div>

    {results && !loading && (
      <div
        style={{
          backgroundColor: "#1e293b",
          padding: "20px",
          borderRadius: "15px",
          width: "100%",
          height: "fit-content",
          boxSizing: "border-box",
        }}
      >
        <h4 style={{ marginTop: 0, marginBottom: "15px" }}>Product Information</h4>

        <div style={{ marginBottom: "10px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8" }}>Product</div>
          <div style={{ fontWeight: "bold" }}>{results.product}</div>
        </div>

        <div style={{ marginBottom: "10px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8" }}>Maturity</div>
          <div>{results.maturity}</div>
        </div>

        <div style={{ marginBottom: "10px" }}>
          <div style={{ fontSize: "14px", color: "#94a3b8" }}>Theoretical Value</div>
          <div>
            {typeof results.theoretical_value === "number"
              ? results.theoretical_value.toLocaleString()
              : "-"}
          </div>
        </div>

        <div>
          <div style={{ fontSize: "14px", color: "#94a3b8" }}>Economic Value</div>
          <div
            style={{
              fontWeight: "bold",
              color:
                typeof results.economic_value === "number" &&
                results.economic_value < 0
                  ? "#f87171"
                  : "#34d399",
            }}
          >
            {typeof results.economic_value === "number"
              ? results.economic_value.toLocaleString()
              : "-"}
          </div>
        </div>
      </div>
    )}
  </div>

  <div style={{ flex: 1 }}> 
          {loading && (
            <div
              style={{
                backgroundColor: "#1e293b",
                padding: "20px",
                borderRadius: "15px",
                flex: 1,
                minWidth: "120px",
                boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
              }}
            >
              Calcul en cours...
            </div>
          )}

          {backendError && (
            <div
              style={{
                backgroundColor: "#7f1d1d",
                padding: "20px",
                borderRadius: "15px",
              }}
            >
              Erreur backend : {backendError}
            </div>
          )}

          {results && !loading && (
            <>
              <div style={{ display: "flex", gap: "20px", marginBottom: "30px" }}>
                {["CVA", "DVA", "FVA", "KVA"].map((metric) => (
                  <div
                    key={metric}
                    style={{
                      backgroundColor: "#1e293b",
                      padding: "20px",
                      borderRadius: "15px",
                      flex: 1,
                    }}
                  >
                    <h4 style={{ marginTop: 0, marginBottom: "10px", color: "#cbd5e1" }}>
                      {metric}
                    </h4>
                    <p style={{ fontSize: "22px", fontWeight: "bold", margin: 0 }}>
                      {typeof results[metric] === "number"
                        ? results[metric].toLocaleString()
                        : "-"} €
                    </p>
                  </div>
                ))}
              </div>

              <div
                style={{
                  backgroundColor: "#1e293b",
                  padding: "20px",
                  borderRadius: "15px",
                }}
              >
                <h3>Expected Exposure Profile</h3>
                <LineChart
                  width={700}
                  height={300}
                  data={results.exposure || []}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="EE+"
                    stroke="#60a5fa"
                    strokeWidth={3}
                    dot={false}
                  />
                </LineChart>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 