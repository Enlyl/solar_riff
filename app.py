import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import streamlit.components.v1 as components

# --- КОНФИГУРАЦИЯ И СТИЛИЗАЦИЯ ---
st.set_page_config(page_title="Solar Riff v2.0", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');

    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'JetBrains Mono', monospace; }

    /* Заголовки */
    h1, h2, h3 { 
        color: #8bff00 !important; 
        text-transform: uppercase; 
        letter-spacing: 2px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 10px;
    }

    /* Карточки метрик */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
        transition: border-color 0.3s;
    }
    div[data-testid="stMetric"]:hover { border-color: #8bff00; }

    /* Метрики текст */
    div[data-testid="stMetricValue"] { color: #8bff00 !important; font-size: 2.5rem !important; }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 0.9rem !important; }

    /* Линии разделения */
    hr { border-top: 1px solid #30363d; margin: 30px 0; }
    </style>
""", unsafe_allow_html=True)


# --- ЛОГИКА ДАННЫХ ---
@st.cache_data(ttl=300)
def get_solar_data():
    url = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"
    try:
        res = requests.get(url)
        df = pd.DataFrame(res.json()[1:], columns=res.json()[0])
        df['time_tag'] = pd.to_datetime(df['time_tag'])
        df['Kp'] = df['Kp'].astype(float)
        df['Kp_Diff'] = df['Kp'].diff()
        return df.dropna()
    except:
        return pd.DataFrame()


# --- ФИЗИЧЕСКИЙ ГИТАРНЫЙ ПРОЦЕССОР (JS) ---
def solar_processor_ui(bpm, kp_value):
    is_storm = kp_value >= 4.0
    tuning = "DROP A // SUB-SONIC" if is_storm else "STANDARD E // CLEAN"

    notes = [
        {"f": 55.00, "n": "A1", "c": "A5"}, {"f": 61.74, "n": "B1", "c": "B5"},
        {"f": 65.41, "n": "C2", "c": "C5"}, {"f": 73.42, "n": "D2", "c": "D5"}
    ] if is_storm else [
        {"f": 82.41, "n": "E2", "c": "E5"}, {"f": 87.31, "n": "F2", "c": "F5"},
        {"f": 98.00, "n": "G2", "c": "G5"}, {"f": 110.00, "n": "A2", "c": "A5"}
    ]

    js_code = f"""
    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 16px; padding: 40px; font-family: 'JetBrains Mono', monospace; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">

        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px;">
            <div style="text-align: left;">
                <div style="font-size: 0.7em; color: #8b949e; margin-bottom: 5px;">SYSTEM STATUS</div>
                <div id="statusLed" style="width: 12px; height: 12px; border-radius: 50%; background: #30363d; display: inline-block;"></div>
                <span style="font-size: 0.9em; color: #c9d1d9; margin-left: 10px;">IDLE</span>
            </div>
            <button id="playBtn" style="background: transparent; border: 2px solid #8bff00; color: #8bff00; padding: 12px 30px; font-weight: bold; cursor: pointer; border-radius: 4px; transition: all 0.3s;">
                ENGAGE CORE
            </button>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; background: #0d1117; padding: 25px; border-radius: 8px; border: 1px solid #30363d;">
            <div style="border-right: 1px solid #30363d;">
                <div style="color: #8b949e; font-size: 0.7em; margin-bottom: 10px;">OSCILLATOR NOTE</div>
                <div id="noteLabel" style="font-size: 2.8em; color: #8bff00;">--</div>
            </div>
            <div style="padding-left: 10px;">
                <div style="color: #8b949e; font-size: 0.7em; margin-bottom: 10px;">POWER CHORD</div>
                <div id="chordLabel" style="font-size: 1.8em; color: #c9d1d9; margin-top: 10px;">--</div>
            </div>
        </div>

        <div id="visGrid" style="display: flex; gap: 12px; justify-content: center; margin-top: 35px;">
            {" ".join(['<div class="step" style="width:12%; height:8px; background:#30363d; border-radius:2px; transition: all 0.1s;"></div>' for _ in range(8)])}
        </div>

        <div style="margin-top: 30px; display: flex; justify-content: space-between; font-size: 0.65em; color: #484f58;">
            <div>MODE: {tuning}</div>
            <div>INTENSITY: {(kp_value / 9 * 100):.1f}%</div>
        </div>
    </div>

    <script>
    const btn = document.getElementById('playBtn');
    const statusLed = document.getElementById('statusLed');
    const noteLbl = document.getElementById('noteLabel');
    const chordLbl = document.getElementById('chordLabel');
    const steps = document.querySelectorAll('.step');
    const notesData = {notes};

    let ctx = null, loop = null, isPlaying = false, stepIdx = 0;

    function playTone(freq, duration) {{
        const osc = ctx.createOscillator();
        const dist = ctx.createWaveShaper();
        const filter = ctx.createBiquadFilter();
        const gain = ctx.createGain();

        osc.type = 'sawtooth';
        osc.frequency.setValueAtTime(freq, ctx.currentTime);
        osc.detune.setValueAtTime(Math.random() * 10 - 5, ctx.currentTime);

        dist.curve = (a => {{
            let k = a, n = 44100, c = new Float32Array(n);
            for (let i = 0; i < n; ++i) {{
                let x = i * 2 / n - 1;
                c[i] = (3 + k) * x * 20 * (Math.PI/180) / (Math.PI + k * Math.abs(x));
            }}
            return c;
        }})(900);

        filter.type = 'lowpass'; filter.frequency.setValueAtTime(2000, ctx.currentTime);

        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

        osc.connect(dist).connect(filter).connect(gain).connect(ctx.destination);
        osc.start(); osc.stop(ctx.currentTime + duration);
    }}

    btn.onclick = () => {{
        if (!ctx) ctx = new AudioContext();
        if (isPlaying) {{
            clearInterval(loop);
            btn.innerText = "ENGAGE CORE"; btn.style.borderColor = "#8bff00"; btn.style.color = "#8bff00";
            statusLed.style.background = "#30363d";
            noteLbl.innerText = "--"; chordLbl.innerText = "--";
            steps.forEach(s => s.style.background = "#30363d");
            isPlaying = false;
        }} else {{
            const ms = (60 / {bpm}) * 1000 / 2;
            loop = setInterval(() => {{
                steps.forEach(s => s.style.background = "#30363d");
                if (Math.random() < 0.7) {{
                    const n = notesData[Math.floor(Math.random() * notesData.length)];
                    playTone(n.f, ms/1000);
                    noteLbl.innerText = n.n; chordLbl.innerText = n.c;
                    steps[stepIdx].style.background = "#8bff00";
                    steps[stepIdx].style.boxShadow = "0 0 15px #8bff00";
                }} else {{
                    noteLbl.innerText = "P.M."; chordLbl.innerText = "---";
                    steps[stepIdx].style.background = "#4e9a06";
                }}
                stepIdx = (stepIdx + 1) % 8;
            }}, ms);
            btn.innerText = "TERMINATE"; btn.style.borderColor = "#f85149"; btn.style.color = "#f85149";
            statusLed.style.background = "#8bff00";
            isPlaying = true;
        }}
    }};
    </script>
    """
    components.html(js_code, height=420)


# --- ГЛАВНЫЙ ЭКРАН ---
st.title("Solar Riff Engine // v2.0")
df = get_solar_data()

if not df.empty:
    latest = df.iloc[-1]
    kp = latest['Kp']
    bpm = int(90 + (kp * 12))

    # Панель управления
    col_l, col_r = st.columns([1, 1.5])

    with col_l:
        st.subheader("Telemetry")
        st.metric("Geomagnetic Index", f"{kp:.2f} Kp", f"{latest['Kp_Diff']:.2f}")
        st.metric("Temporal Speed", f"{bpm} BPM")
        st.write("---")
        st.subheader("Audio Module")
        solar_processor_ui(bpm, kp)

    with col_r:
        st.subheader("Historical Flux")
        fig = px.line(df, x='time_tag', y='Kp', template="plotly_dark")
        fig.update_traces(line_color='#8bff00', line_width=2)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#161b22')
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.caption("Data source: NOAA Space Weather Prediction Center. Audio generated via Web Audio API.")