# app.py
import streamlit as st
import time
from agents import agent_proponent, agent_opponent, agent_judge

# ── PARSE JUDGE OUTPUT ────────────────────────────────────────
def parse_judge_output(judge_text):
    result = {
        'strongest_proponent':  '',
        'strongest_opponent':   '',
        'verdict':              'Unverified',
        'reasoning':            '',
        'confidence':           'Medium',
        'truth_percentage':     'Truth: 50% | False: 50%',
        'percentage_reasoning': judge_text
    }
    lines = judge_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith('1. STRONGEST POINT (Proponent):'):
            result['strongest_proponent'] = line.split(':', 1)[1].strip()
        elif line.startswith('2. STRONGEST POINT (Opponent):'):
            result['strongest_opponent'] = line.split(':', 1)[1].strip()
        elif line.startswith('3. VERDICT:'):
            result['verdict'] = line.split(':', 1)[1].strip()
        elif line.startswith('4. REASONING:'):
            result['reasoning'] = line.split(':', 1)[1].strip()
        elif line.startswith('5. CONFIDENCE:'):
            result['confidence'] = line.split(':', 1)[1].strip()
        elif line.startswith('6. TRUTH PERCENTAGE:'):
            result['truth_percentage'] = line.split(':', 1)[1].strip()
        elif line.startswith('7. PERCENTAGE REASONING:'):
            result['percentage_reasoning'] = line.split(':', 1)[1].strip()
    return result

# ── PAGE CONFIG ───────────────────────────────────────────────
st.set_page_config(
    page_title='AI Debate System',
    page_icon='⚖️',
    layout='wide'
)

# ── STYLES ────────────────────────────────────────────────────
st.markdown('''
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&family=Inter+Tight:wght@600;700;800&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">

<style>

/* ── GLOBAL ─────────────────────────────────────────────── */
.stApp {
    background-color: #f6faf7 !important;
    font-family: "Inter", sans-serif !important;
}

* { color: #1a1a1a !important; }

h1, h2, h3 {
    font-family: "Inter Tight", sans-serif !important;
    color: #0a6b50 !important;
}

/* ── TEXT INPUT ─────────────────────────────────────────── */
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 2px solid #bdc9c2 !important;
    border-radius: 0.75rem !important;
    font-size: 15px !important;
    font-family: "Inter", sans-serif !important;
    caret-color: #1a1a1a !important;
    cursor: text !important;
    padding: 12px !important;
}
.stTextArea textarea::placeholder {
    color: #999999 !important;
}
.stTextArea textarea:focus {
    border-color: #0a6b50 !important;
    box-shadow: 0 0 0 3px rgba(10, 107, 80, 0.1) !important;
}

/* ── BUTTONS ────────────────────────────────────────────── */
.stButton > button {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 1.5px solid #bdc9c2 !important;
    border-radius: 9999px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    font-family: "Inter", sans-serif !important;
    cursor: pointer !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background-color: #f0f5f2 !important;
    border-color: #0a6b50 !important;
    color: #0a6b50 !important;
}

/* Primary button - Give Verdict */
[data-testid="baseButton-primary"] {
    background-color: #0a6b50 !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 9999px !important;
}
[data-testid="baseButton-primary"]:hover {
    background-color: #085a42 !important;
    color: #ffffff !important;
}

/* ── METRICS ────────────────────────────────────────────── */
[data-testid="stMetric"] {
    background-color: #ffffff !important;
    border: 1px solid #d1e7dd !important;
    border-radius: 1rem !important;
    padding: 1rem !important;
}
[data-testid="stMetricLabel"] {
    color: #3e4944 !important;
    font-size: 13px !important;
}
[data-testid="stMetricValue"] {
    color: #0a6b50 !important;
    font-size: 20px !important;
    font-weight: 700 !important;
    white-space: normal !important;
    overflow: visible !important;
}

/* ── GLASS CARD (verdict + input area) ──────────────────── */
.glass-card {
    background: rgba(255, 255, 255, 0.75) !important;
    backdrop-filter: blur(12px) !important;
    -webkit-backdrop-filter: blur(12px) !important;
    border-radius: 1.5rem !important;
    padding: 2rem !important;
    border: 1px solid rgba(10, 107, 80, 0.12) !important;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04) !important;
    margin-bottom: 1.5rem !important;
}

/* ── PROPONENT BUBBLE — LEFT ────────────────────────────── */
.pro-bubble {
    background-color: #f0f9f6 !important;
    border: 1.5px solid #2e7d32 !important;
    border-radius: 0px 16px 16px 16px !important;
    padding: 16px 20px !important;
    margin: 6px 100px 6px 0px !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: #1a2e1a !important;
    font-family: "Inter", sans-serif !important;
}

/* ── OPPONENT BUBBLE — RIGHT ────────────────────────────── */
.opp-bubble {
    background-color: #fff5f5 !important;
    border: 1.5px solid #c62828 !important;
    border-radius: 16px 0px 16px 16px !important;
    padding: 16px 20px !important;
    margin: 6px 0px 6px 100px !important;
    font-size: 15px !important;
    line-height: 1.7 !important;
    color: #2e1a1a !important;
    font-family: "Inter", sans-serif !important;
}

/* ── LABELS ─────────────────────────────────────────────── */
.pro-label {
    color: #2e7d32 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
    margin-left: 4px !important;
}
.opp-label {
    color: #c62828 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 4px !important;
    margin-right: 4px !important;
    text-align: right !important;
}

/* ── ROUND BADGE ────────────────────────────────────────── */
.round-badge {
    text-align: center !important;
    color: #888888 !important;
    font-size: 11px !important;
    letter-spacing: 2px !important;
    text-transform: uppercase !important;
    margin: 20px 0 !important;
}

/* ── VERDICT CARD ───────────────────────────────────────── */
.verdict-true    { background: #e8f5e9 !important; border-left: 5px solid #2e7d32 !important; }
.verdict-false   { background: #ffebee !important; border-left: 5px solid #c62828 !important; }
.verdict-mislead { background: #fff8e1 !important; border-left: 5px solid #f57f17 !important; }
.verdict-unknown { background: #e3f2fd !important; border-left: 5px solid #1565c0 !important; }

.verdict-box {
    padding: 1.25rem 1.5rem !important;
    border-radius: 1rem !important;
    margin-bottom: 1rem !important;
    font-size: 16px !important;
    font-weight: 600 !important;
}

/* ── STRONGEST POINTS GRID ──────────────────────────────── */
.points-grid {
    display: grid !important;
    grid-template-columns: 1fr 1fr !important;
    gap: 1rem !important;
    margin: 1rem 0 !important;
}
.pro-point {
    background: #f0f9f6 !important;
    border: 1px solid #d1e7dd !important;
    border-radius: 1rem !important;
    padding: 1rem !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}
.opp-point {
    background: #fff5f5 !important;
    border: 1px solid #f5c6cb !important;
    border-radius: 1rem !important;
    padding: 1rem !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
}
.point-label {
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    margin-bottom: 6px !important;
}

/* ── SIDEBAR ────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #f0f5f2 !important;
    border-right: 1px solid #bdc9c2 !important;
}
.history-item {
    padding: 10px 12px !important;
    margin: 4px 0 !important;
    border-radius: 8px !important;
    background-color: #ffffff !important;
    border-left: 3px solid #0a6b50 !important;
    cursor: pointer !important;
    font-size: 13px !important;
}
.history-item:hover {
    background-color: #e8f5e9 !important;
}

/* ── DIVIDER ────────────────────────────────────────────── */
hr {
    border-color: #bdc9c2 !important;
    opacity: 0.4 !important;
}

/* ── SPINNER TEXT ───────────────────────────────────────── */
.stSpinner p {
    color: #0a6b50 !important;
    font-size: 14px !important;
}

</style>
''', unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────
defaults = {
    'debate_history':  [],
    'verdict':         None,
    'started':         False,
    'claim':           '',
    'waiting':         False,
    'past_debates':    [],
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── SIDEBAR — DEBATE HISTORY ──────────────────────────────────
with st.sidebar:
    st.markdown("## 🕘 Past Debates")
    st.divider()

    if not st.session_state.past_debates:
        st.caption("Your past debates will appear here after you get a verdict.")
    else:
        for i, past in enumerate(reversed(st.session_state.past_debates)):
            short_claim = past['claim'][:35] + '...' \
                if len(past['claim']) > 35 else past['claim']

            verdict_emoji = {
                'True':       '✅',
                'False':      '❌',
                'Misleading': '⚠️',
                'Unverified': '❓'
            }.get(past['verdict']['verdict'], '❓')

            if st.button(
                f"{verdict_emoji} {short_claim}",
                key=f"history_{i}",
                use_container_width=True
            ):
                st.session_state.debate_history = past['debate_history']
                st.session_state.verdict        = past['verdict']
                st.session_state.claim          = past['claim']
                st.session_state.started        = True
                st.session_state.waiting        = False
                st.rerun()

    st.divider()
    if st.button('➕ New Debate', use_container_width=True):
        for key, val in defaults.items():
            if key != 'past_debates':
                st.session_state[key] = val
        st.rerun()

# ── HEADER ────────────────────────────────────────────────────
st.markdown('''
<div style="margin-bottom: 0.5rem;">
    <h1 style="font-family: Inter Tight, sans-serif; font-size: 2.2rem;
               color: #0a6b50 !important; margin-bottom: 0;">
        ⚖️ AI Debate System
    </h1>
    <p style="color: #3e4944 !important; font-size: 15px; margin-top: 4px;">
        Two AI agents debate your claim. You control when to stop.
    </p>
</div>
''', unsafe_allow_html=True)
st.divider()

# ── CLAIM INPUT ───────────────────────────────────────────────
if not st.session_state.started:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    claim = st.text_area(
        label='Enter the claim to debate:',
        placeholder='e.g. 5G towers cause health problems in residents...',
        height=90
    )
    if st.button('🚀 Start Debate', type='primary',
                 use_container_width=True, disabled=not claim):
        st.session_state.claim          = claim
        st.session_state.started        = True
        st.session_state.debate_history = []
        st.session_state.verdict        = None
        st.session_state.waiting        = False
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── SHOW CLAIM ────────────────────────────────────────────────
if st.session_state.started:
    st.markdown(f'''
    <div style="background: rgba(10,107,80,0.06); border-left: 4px solid #0a6b50;
                border-radius: 0 0.75rem 0.75rem 0; padding: 12px 16px;
                margin-bottom: 1rem;">
        <span style="font-size: 11px; font-weight: 700; color: #0a6b50 !important;
                     letter-spacing: 1px; text-transform: uppercase;">Claim</span>
        <p style="margin: 4px 0 0; font-size: 15px; font-weight: 500;
                  color: #1a1a1a !important;">{st.session_state.claim}</p>
    </div>
    ''', unsafe_allow_html=True)
    st.divider()

# ── DISPLAY ALL MESSAGES ──────────────────────────────────────
for entry in st.session_state.debate_history:
    label   = entry['label']
    content = entry['content']
    if 'PROPONENT' in label:
        st.markdown(f'<div class="pro-label">🟢 {label}</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="pro-bubble">{content}</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:16px"></div>',
                    unsafe_allow_html=True)
    elif 'OPPONENT' in label:
        st.markdown(f'<div class="opp-label">{label} 🔴</div>',
                    unsafe_allow_html=True)
        st.markdown(f'<div class="opp-bubble">{content}</div>',
                    unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:16px"></div>',
                    unsafe_allow_html=True)

# ── DEBATE LOGIC ──────────────────────────────────────────────
if st.session_state.started and not st.session_state.verdict:

    history   = st.session_state.debate_history
    pro_count = sum(1 for e in history if 'PROPONENT' in e['label'])
    opp_count = sum(1 for e in history if 'OPPONENT'  in e['label'])

    # ── WAITING — show choice buttons ────────────────────────
    if st.session_state.waiting:
        st.divider()
        st.markdown('''
        <p style="font-size: 15px; font-weight: 600; color: #0a6b50 !important;
                  margin-bottom: 12px;">What would you like to do?</p>
        ''', unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            if st.button('▶️ Continue - Next Round',
                         use_container_width=True):
                st.session_state.waiting = False
                st.rerun()

        with col2:
            if st.button('⚖️ Give Verdict',
                         type='primary',
                         use_container_width=True):
                with st.spinner('Judge is reviewing the full debate...'):
                    judge_raw = agent_judge(
                        st.session_state.claim,
                        st.session_state.debate_history
                    )
                    st.session_state.verdict = parse_judge_output(judge_raw)

                st.session_state.past_debates.append({
                    'claim':          st.session_state.claim,
                    'debate_history': st.session_state.debate_history,
                    'verdict':        st.session_state.verdict
                })
                st.rerun()

    # ── NOT WAITING — run next agent ─────────────────────────
    else:
        # PROPONENT'S TURN
        if pro_count == opp_count:
            round_num = pro_count + 1
            st.markdown(
                f'<div class="round-badge">── Round {round_num} ──</div>',
                unsafe_allow_html=True
            )
            with st.spinner('🟢 Proponent is thinking...'):
                time.sleep(1)
                pro = agent_proponent(
                    st.session_state.claim,
                    history if history else None
                )
            st.session_state.debate_history.append({
                'label':   f'PROPONENT (Round {round_num})',
                'content': pro
            })
            st.rerun()

        # OPPONENT'S TURN
        elif opp_count < pro_count:
            with st.spinner('🔴 Opponent is thinking...'):
                time.sleep(2)
                opp = agent_opponent(
                    st.session_state.claim,
                    st.session_state.debate_history
                )
            st.session_state.debate_history.append({
                'label':   f'OPPONENT (Round {pro_count})',
                'content': opp
            })
            st.session_state.waiting = True
            st.rerun()

# ── VERDICT ───────────────────────────────────────────────────
if st.session_state.verdict:
    v = st.session_state.verdict
    st.divider()

    # Verdict header
    st.markdown('''
    <h2 style="font-family: Inter Tight, sans-serif; color: #0a6b50 !important;
               margin-bottom: 1rem;">
        📋 Judge\'s Verdict
    </h2>
    ''', unsafe_allow_html=True)

    # Verdict badge
    verdict_styles = {
        'True':       ('verdict-true',    '✅ TRUE'),
        'False':      ('verdict-false',   '❌ FALSE'),
        'Misleading': ('verdict-mislead', '⚠️ MISLEADING'),
        'Unverified': ('verdict-unknown', '❓ UNVERIFIED'),
    }
    v_class, v_label = verdict_styles.get(
        v['verdict'], ('verdict-unknown', f"❓ {v['verdict'].upper()}")
    )
    st.markdown(f'''
    <div class="verdict-box {v_class}">
        {v_label}
    </div>
    ''', unsafe_allow_html=True)

    # Confidence + Truth %
    col1, col2 = st.columns(2)
    with col1:
        st.metric('Confidence', v['confidence'])
    with col2:
        st.markdown(f'''
        <div style="background: #ffffff; border: 1px solid #d1e7dd;
                    border-radius: 1rem; padding: 1rem;">
            <p style="font-size: 13px; color: #3e4944 !important; margin: 0 0 4px;">
                Truth Percentage
            </p>
            <p style="font-size: 18px; font-weight: 700;
                      color: #0a6b50 !important; margin: 0;">
                {v["truth_percentage"]}
            </p>
        </div>
        ''', unsafe_allow_html=True)

    # Strongest points side by side
    st.markdown(f'''
    <div class="points-grid">
        <div class="pro-point">
            <div class="point-label" style="color: #2e7d32 !important;">
                🟢 Strongest — Proponent
            </div>
            {v["strongest_proponent"]}
        </div>
        <div class="opp-point">
            <div class="point-label" style="color: #c62828 !important;">
                🔴 Strongest — Opponent
            </div>
            {v["strongest_opponent"]}
        </div>
    </div>
    ''', unsafe_allow_html=True)

    # Reasoning
    st.markdown(f'''
    <div class="glass-card" style="margin-top: 1rem;">
        <p style="font-size: 12px; font-weight: 700; color: #3e4944 !important;
                  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            Reasoning
        </p>
        <p style="font-size: 15px; line-height: 1.7; color: #1a1a1a !important; margin: 0;">
            {v["reasoning"]}
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # Percentage reasoning
    st.markdown(f'''
    <div class="glass-card">
        <p style="font-size: 12px; font-weight: 700; color: #3e4944 !important;
                  text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 8px;">
            Percentage Reasoning
        </p>
        <p style="font-size: 15px; line-height: 1.7; color: #1a1a1a !important; margin: 0;">
            {v["percentage_reasoning"]}
        </p>
    </div>
    ''', unsafe_allow_html=True)

    # New debate button
    st.divider()
    if st.button('🔄 Start a New Debate', use_container_width=True):
        for key, val in defaults.items():
            if key != 'past_debates':
                st.session_state[key] = val
        st.rerun()