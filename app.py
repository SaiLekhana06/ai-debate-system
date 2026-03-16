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
    layout='centered'
)

# ── STYLES ────────────────────────────────────────────────────
st.markdown('''
<style>
/* ── FORCE LIGHT THEME EVERYWHERE ── */
.stApp, .stApp > * {
    background-color: #ffffff !important;
}

/* Fix ALL text to be dark and readable */
p, span, div, label, h1, h2, h3, h4 {
    color: #1a1a1a !important;
}

/* ── TEXT INPUT BOX — white background, dark text ── */
.stTextArea textarea {
    background-color: #ffffff !important;
    color: #1a1a1a !important;
    border: 2px solid #cccccc !important;
    font-size: 15px !important;
}
.stTextArea textarea::placeholder {
    color: #999999 !important;
}

/* ── ALL BUTTONS — force readable text ── */
.stButton > button {
    background-color: #f0f0f0 !important;
    color: #1a1a1a !important;
    border: 1px solid #cccccc !important;
    font-weight: 600 !important;
    font-size: 15px !important;
}
.stButton > button:hover {
    background-color: #e0e0e0 !important;
    color: #1a1a1a !important;
}

/* Primary button (Give Verdict) — keep red but white text */
[data-testid="baseButton-primary"] {
    background-color: #c62828 !important;
    color: #ffffff !important;
    border: none !important;
}
[data-testid="baseButton-primary"]:hover {
    background-color: #b71c1c !important;
    color: #ffffff !important;
}

/* ── METRIC BOX (Confidence, Truth %) ── */
[data-testid="stMetric"] {
    background-color: #f8f8f8 !important;
    border: 1px solid #dddddd !important;
    border-radius: 8px !important;
    padding: 12px !important;
}
[data-testid="stMetricLabel"] {
    color: #555555 !important;
    font-size: 13px !important;
}
[data-testid="stMetricValue"] {
    color: #1a1a1a !important;
    font-size: 18px !important;   /* smaller so text doesnt get cut off */
    white-space: normal !important;
    overflow: visible !important;
}

/* ── PROPONENT BUBBLE — LEFT ── */
.pro-bubble {
    background-color: #f0faf0 !important;
    border: 2px solid #2e7d32 !important;
    border-radius: 0px 16px 16px 16px !important;
    padding: 14px 18px !important;
    margin: 6px 80px 6px 0px !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    color: #1a1a1a !important;
}

/* ── OPPONENT BUBBLE — RIGHT ── */
.opp-bubble {
    background-color: #fff5f5 !important;
    border: 2px solid #c62828 !important;
    border-radius: 16px 0px 16px 16px !important;
    padding: 14px 18px !important;
    margin: 6px 0px 6px 80px !important;
    font-size: 15px !important;
    line-height: 1.6 !important;
    color: #1a1a1a !important;
}

.pro-label {
    color: #2e7d32 !important;
    font-weight: bold !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
    margin-left: 4px !important;
}

.opp-label {
    color: #c62828 !important;
    font-weight: bold !important;
    font-size: 13px !important;
    margin-bottom: 4px !important;
    margin-right: 4px !important;
    text-align: right !important;
}

.round-badge {
    text-align: center !important;
    color: #888888 !important;
    font-size: 12px !important;
    margin: 16px 0 !important;
    letter-spacing: 1px !important;
}
/* Fix 1 - show blinking cursor while typing */
.stTextArea textarea {
    caret-color: #1a1a1a !important;
    cursor: text !important;
}
/* Fix 2 - show hand cursor on buttons */
.stButton > button {
    cursor: pointer !important;
}
</style>
''', unsafe_allow_html=True)
# ── HEADER ────────────────────────────────────────────────────
st.title('⚖️ AI Debate System')
st.caption('Two AI agents debate your claim. You control when to stop.')
st.divider()

# ── SESSION STATE ─────────────────────────────────────────────
defaults = {
    'debate_history':  [],
    'verdict':         None,
    'started':         False,
    'claim':           '',
    'waiting':         False,  # ← KEY FIX: True = waiting for user input
    'pro_done':        False,  # ← tracks if proponent ran this round
    'opp_done':        False,  # ← tracks if opponent ran this round
}
for key, val in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ── CLAIM INPUT ───────────────────────────────────────────────
if not st.session_state.started:
    claim = st.text_area(
        label='Enter the claim to debate:',
        placeholder='e.g. 5G towers cause health problems...',
        height=80
    )
    if st.button('🚀 Start Debate', type='primary',
                 use_container_width=True, disabled=not claim):
        st.session_state.claim   = claim
        st.session_state.started = True
        st.session_state.waiting = False
        st.rerun()

# ── SHOW CLAIM ────────────────────────────────────────────────
if st.session_state.started:
    st.markdown(f"**Claim:** {st.session_state.claim}")
    st.divider()

# ── DISPLAY ALL PREVIOUS MESSAGES ────────────────────────────
for entry in st.session_state.debate_history:
    label   = entry['label']
    content = entry['content']

    if 'PROPONENT' in label:
        st.markdown(f'<div class="pro-label">🟢 {label}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pro-bubble">{content}</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:12px"></div>', unsafe_allow_html=True)

    elif 'OPPONENT' in label:
        st.markdown(f'<div class="opp-label">{label} 🔴</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="opp-bubble">{content}</div>', unsafe_allow_html=True)
        st.markdown('<div style="margin-bottom:12px"></div>', unsafe_allow_html=True)

# ── MAIN DEBATE LOGIC ─────────────────────────────────────────
if st.session_state.started and not st.session_state.verdict:

    history   = st.session_state.debate_history
    pro_count = sum(1 for e in history if 'PROPONENT' in e['label'])
    opp_count = sum(1 for e in history if 'OPPONENT'  in e['label'])

    # ── WAITING FOR USER CHOICE — show buttons, do nothing else
    if st.session_state.waiting:
        st.divider()
        st.markdown('### What would you like to do?')
        col1, col2 = st.columns(2)

        with col1:
            if st.button('▶️ Continue — Next Round',
                         use_container_width=True):
                # Reset for next round and let debate run
                st.session_state.waiting = False
                st.rerun()

        with col2:
            if st.button('⚖️ Give Verdict',
                         type='primary',
                         use_container_width=True):
                with st.spinner('⚖️ Judge is reviewing the full debate...'):
                    judge_raw = agent_judge(
                        st.session_state.claim,
                        st.session_state.debate_history
                    )
                    st.session_state.verdict = parse_judge_output(judge_raw)
                st.rerun()

    # ── NOT WAITING — run the next agent
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
            st.rerun()  # show proponent message, then opponent runs next

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
            # ── STOP HERE and wait for user ──────────────────
            st.session_state.waiting = True
            st.rerun()  # show opponent message + choice buttons

# ── VERDICT DISPLAY ───────────────────────────────────────────
if st.session_state.verdict:
    v = st.session_state.verdict
    st.divider()
    st.header("📋 Judge's Verdict")

    verdict_fn = {
        'True':       st.success,
        'False':      st.error,
        'Misleading': st.warning,
        'Unverified': st.info
    }.get(v['verdict'], st.info)

    verdict_fn(f"VERDICT: {v['verdict']}")

    col1, col2 = st.columns(2)
    with col1:
        st.metric('Confidence', v['confidence'])
    with col2:
        st.metric('Truth %', v['truth_percentage'])

    st.markdown('**Strongest Point — Proponent**')
    st.write(v['strongest_proponent'])
    st.markdown('**Strongest Point — Opponent**')
    st.write(v['strongest_opponent'])
    st.markdown('**Reasoning**')
    st.write(v['reasoning'])
    st.markdown('**Percentage Reasoning**')
    st.write(v['percentage_reasoning'])

    st.divider()
    if st.button('🔄 New Debate', use_container_width=True):
        for key, val in defaults.items():
            st.session_state[key] = val
        st.rerun()