import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import streamlit.components.v1 as components

# --- CONFIG & STYLES ---
st.set_page_config(page_title="Solar Riff Engine v2.0", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #0d1117; color: #c9d1d9; font-family: 'JetBrains Mono', monospace; }

    h1, h2, h3 { 
        color: #8bff00 !important; 
        text-transform: uppercase; 
        letter-spacing: 2px;
        border-bottom: 1px solid #30363d;
        padding-bottom: 10px;
    }

    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 20px;
    }
    div[data-testid="stMetricValue"] { color: #8bff00 !important; font-size: 2.2rem !important; }
    div[data-testid="stMetricLabel"] { color: #8b949e !important; }

    hr { border-top: 1px solid #30363d; margin: 30px 0; }
    </style>
""", unsafe_allow_html=True)


# --- DATA ENGINE ---
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


# --- SONIC PROCESSOR COMPONENT ---
def solar_processor_ui(bpm, kp_value):
    is_storm = kp_value >= 4.0
    tuning = "DROP A // SUB-SONIC" if is_storm else "STANDARD E // CLEAN"

    notes = [
        {"f": 55.00, "n": "A1", "c": "A5 (Power)"}, {"f": 61.74, "n": "B1", "c": "B5 (Power)"},
        {"f": 65.41, "n": "C2", "c": "C5 (Power)"}, {"f": 73.42, "n": "D2", "c": "D5 (Power)"}
    ] if is_storm else [
        {"f": 82.41, "n": "E2", "c": "E5 (Power)"}, {"f": 87.31, "n": "F2", "c": "F5 (Power)"},
        {"f": 98.00, "n": "G2", "c": "G5 (Power)"}, {"f": 110.00, "n": "A2", "c": "A5 (Power)"}
    ]

    js_code = f"""
    <div style="background: #161b22; border: 1px solid #30363d; border-radius: 16px; padding: 30px; font-family: 'JetBrains Mono', monospace; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">

        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="font-size: 0.7em; color: #8b949e;">CHRONICLE LOG v2.0</div>
            <button id="playBtn" style="background: transparent; border: 2px solid #8bff00; color: #8bff00; padding: 10px 25px; font-weight: bold; cursor: pointer; border-radius: 4px; transition: 0.3s;">
                ENGAGE CORE
            </button>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; background: #0d1117; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-bottom: 20px;">
            <div style="border-right: 1px solid #30363d;">
                <div style="color: #8b949e; font-size: 0.6em; margin-bottom: 5px;">ACTIVE NOTE</div>
                <div id="noteLabel" style="font-size: 2.2em; color: #8bff00;">--</div>
            </div>
            <div style="padding-left: 10px;">
                <div style="color: #8b949e; font-size: 0.6em; margin-bottom: 5px;">CHORD TYPE</div>
                <div id="chordLabel" style="font-size: 1.4em; color: #c9d1d9; margin-top: 5px;">--</div>
            </div>
        </div>

        <div id="chordHistory" style="height: 120px; background: #0a0e14; border: 1px solid #1f242b; border-radius: 4px; padding: 12px; font-size: 0.7em; overflow-y: hidden; display: flex; flex-direction: column; color: #586069; line-height: 1.6;">
            <div style="color: #30363d;">> Initializing telemetry log...</div>
        </div>

        <div id="visGrid" style="display: flex; gap: 8px; justify-content: center; margin-top: 25px;">
            {" ".join(['<div class="step" style="width:10%; height:6px; background:#30363d; border-radius:1px; transition: 0.1s;"></div>' for _ in range(8)])}
        </div>

        <div style="margin-top: 20px; display: flex; justify-content: space-between; font-size: 0.6em; color: #484f58;">
            <div>MODE: {tuning}</div>
            <div>BPM: {bpm}</div>
        </div>
    </div>

    <script>
    const btn = document.getElementById('playBtn');
    const noteLbl = document.getElementById('noteLabel');
    const chordLbl = document.getElementById('chordLabel');
    const historyBox = document.getElementById('chordHistory');
    const steps = document.querySelectorAll('.step');
    const notesData = {notes};

    let ctx = null, loop = null, isPlaying = false, stepIdx = 0;

    function addToHistory(note, chord) {{
        const time = new Date().toLocaleTimeString([], {{hour12: false, minute:'2-digit', second:'2-digit'}});
        const entry = document.createElement('div');
        entry.innerHTML = `<span style="color: #484f58;">[${{time}}]</span> <span style="color: #8bff00;">${{note}}</span> <span style="color: #c9d1d9;">${{chord}}</span> detected`;

        historyBox.prepend(entry);
        if (historyBox.children.length > 7) historyBox.lastElementChild.remove();
    }}

    function playTone(freq, duration, noteInfo) {{
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

        filter.type = 'lowpass'; filter.frequency.setValueAtTime(2200, ctx.currentTime);
        gain.gain.setValueAtTime(0.3, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + duration);

        osc.connect(dist).connect(filter).connect(gain).connect(ctx.destination);
        osc.start(); osc.stop(ctx.currentTime + duration);

        addToHistory(noteInfo.n, noteInfo.c);
    }}

    btn.onclick = () => {{
        if (!ctx) ctx = new (window.AudioContext || window.webkitAudioContext)();
        if (isPlaying) {{
            clearInterval(loop);
            btn.innerText = "ENGAGE CORE"; btn.style.borderColor = "#8bff00"; btn.style.color = "#8bff00";
            noteLbl.innerText = "--"; chordLbl.innerText = "--";
            steps.forEach(s => {{ s.style.background = "#30363d"; s.style.boxShadow = "none"; }});
            isPlaying = false;
        }} else {{
            const ms = (60 / {bpm}) * 1000 / 2;
            loop = setInterval(() => {{
                steps.forEach(s => {{ s.style.background = "#30363d"; s.style.boxShadow = "none"; }});
                if (Math.random() < 0.7) {{
                    const n = notesData[Math.floor(Math.random() * notesData.length)];
                    playTone(n.f, ms/1000, n);
                    noteLbl.innerText = n.n; chordLbl.innerText = n.c;
                    steps[stepIdx].style.background = "#8bff00";
                    steps[stepIdx].style.boxShadow = "0 0 10px #8bff00";
                }} else {{
                    noteLbl.innerText = "P.M."; chordLbl.innerText = "MUTE";
                    steps[stepIdx].style.background = "#4e9a06";
                }}
                stepIdx = (stepIdx + 1) % 8;
            }}, ms);
            btn.innerText = "TERMINATE"; btn.style.borderColor = "#f85149"; btn.style.color = "#f85149";
            isPlaying = true;
        }}
    }};
    </script>
    """
    components.html(js_code, height=480)


# --- MAIN RENDER ---
st.title("🛰️ SOLAR RIFF ENGINE // V2.0")

data = get_solar_data()

if not data.empty:
    curr = data.iloc[-1]
    kp = curr['Kp']
    bpm = int(90 + (kp * 12))

    c1, c2 = st.columns([1, 1.5])

    with c1:
        st.subheader("SYSTEM TELEMETRY")
        st.metric("Geomagnetic Flux", f"{kp:.2f} Kp", f"{curr['Kp_Diff']:.2f} 3h")
        st.metric("Temporal Speed", f"{bpm} BPM")
        st.write("---")
        solar_processor_ui(bpm, kp)

    with c2:
        st.subheader("FLUX HISTORY (NOAA)")
        fig = px.line(data, x='time_tag', y='Kp', template="plotly_dark")
        fig.update_traces(line_color='#8bff00', line_width=2)
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False), yaxis=dict(gridcolor='#161b22'),
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.caption("Data source: NOAA Space Weather Prediction Center. Synthesized via Web Audio API.")
else:
    st.error("Searching for satellite signal... Please wait.")