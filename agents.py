# agents.py
import os
import time
from dotenv import load_dotenv
from groq import Groq

load_dotenv('.env.txt')
client = Groq(api_key=os.getenv('GROQ_API_KEY'))
MODEL = 'llama-3.3-70b-versatile'


# ============================================================
# HELPER — formats debate history into clean readable text
# instead of confusing role:user/assistant format
# ============================================================
def format_history_as_text(debate_history):
    '''
    Converts debate history list into a plain transcript string.
    This way agents read it as a STORY not as chat roles.
    Avoids the confusion of who is "user" vs "assistant".
    '''
    transcript = ""
    for entry in debate_history:
        transcript += f"{entry['label']}: {entry['content']}\n\n"
    return transcript.strip()


# ============================================================
# AGENT 1: PROPONENT
# ============================================================
def agent_proponent(claim, debate_history=None):
    system_prompt = '''
You are a highly skilled debate analyst playing the role of a PROPONENT.
Your job is to argue WHY the given claim could be TRUE or credible.

Rules:
- Round 1: Give a strong opening argument for the claim.
- Later rounds: FIRST directly address the Opponent's last argument 
  point by point, THEN reinforce your own position with new reasoning.
- Never say "as the proponent" or refer to yourself in third person.
- Never ask for the next point — just argue your case.
- Keep response to 4-5 sentences max.
Be analytical, confident, and logical.
    '''

    if debate_history:
        transcript = format_history_as_text(debate_history)
        user_message = f'''
Claim being debated: {claim}

Debate so far:
{transcript}

Now give YOUR response as the PROPONENT. 
Directly counter the Opponent's last argument, then reinforce your position.
        '''
    else:
        user_message = f'''
Claim being debated: {claim}

Give your opening argument as the PROPONENT for why this claim could be true.
        '''

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': user_message}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


# ============================================================
# AGENT 2: OPPONENT
# ============================================================
def agent_opponent(claim, debate_history=None):
    system_prompt = '''
You are a highly skilled debate analyst playing the role of an OPPONENT.
Your job is to argue WHY the given claim could be FALSE or misleading.

Rules:
- ALWAYS directly counter the Proponent's last argument point by point first.
- Then introduce a NEW flaw, weakness, or missing evidence to strengthen your case.
- Never say "as the opponent" or refer to yourself in third person.
- Never ask for the next point — just argue your case.
- Keep response to 4-5 sentences max.
Be analytical, skeptical, and precise.
    '''

    if debate_history:
        transcript = format_history_as_text(debate_history)
        user_message = f'''
Claim being debated: {claim}

Debate so far:
{transcript}

Now give YOUR response as the OPPONENT.
Directly counter the Proponent's last argument, then add a new weakness to your case.
        '''
    else:
        user_message = f'''
Claim being debated: {claim}

Give your opening counter-argument as the OPPONENT for why this claim could be false.
        '''

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': user_message}
        ],
        temperature=0.7,
        max_tokens=300
    )
    return response.choices[0].message.content.strip()


# ============================================================
# AGENT 3: JUDGE
# ============================================================
def agent_judge(claim, debate_history):
    system_prompt = '''
You are an impartial judge evaluating a debate between a Proponent and an Opponent.
You have read the full debate transcript.

Give your verdict in this EXACT structure:

1. STRONGEST POINT (Proponent): One sentence
2. STRONGEST POINT (Opponent): One sentence
3. VERDICT: Choose one — True / False / Misleading / Unverified
4. REASONING: 2-3 sentences explaining your verdict based on the debate
5. CONFIDENCE: Low / Medium / High
6. TRUTH PERCENTAGE: "Truth: X% | False: Y%" (must add to 100)
7. PERCENTAGE REASONING: 2 sentences explaining WHY you assigned 
   those percentages based on argument strength and evidence quality.

Be fair and base your ruling ONLY on the arguments made in the debate.
    '''

    transcript = format_history_as_text(debate_history)
    user_message = f"CLAIM: {claim}\n\nFULL DEBATE TRANSCRIPT:\n{transcript}"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user',   'content': user_message}
        ],
        temperature=0.3,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()


# ============================================================
# PRINT SLOWLY — simulates one character at a time
# so response feels like it's being "typed out"
# ============================================================
def print_slowly(text, delay=0.02):
    '''
    Prints text character by character with a small delay.
    Makes it feel like the agent is thinking/typing in real time.
    Replace this with a streaming API call on your website.
    '''
    for char in text:
        print(char, end='', flush=True)
        time.sleep(delay)
    print()  # newline at end


# ============================================================
# RUN ONE BATCH: 3 full rounds (Pro → Opp × 3)
# ============================================================
def run_debate_batch(claim, debate_history, batch_number):
    start_round = (batch_number - 1) * 3 + 1

    for i in range(3):
        round_number = start_round + i

        # --- PROPONENT speaks ---
        print(f"\n🟢 PROPONENT (Round {round_number}):")
        print("-" * 50)
        pro_argument = agent_proponent(claim, debate_history if debate_history else None)
        print_slowly(pro_argument)          # Prints gradually

        # Store with a clear label — no role confusion
        debate_history.append({
            'label': f'PROPONENT (Round {round_number})',
            'content': pro_argument
        })

        time.sleep(1)  # 1 second pause before opponent replies

        # --- OPPONENT responds ---
        print(f"\n🔴 OPPONENT (Round {round_number}):")
        print("-" * 50)
        opp_argument = agent_opponent(claim, debate_history)
        print_slowly(opp_argument)          # Prints gradually

        debate_history.append({
            'label': f'OPPONENT (Round {round_number})',
            'content': opp_argument
        })

        # Pause between rounds so it doesn't feel instant
        if i < 2:  # No pause after the last round of a batch
            print(f"\n  ⏳ Next round starting shortly...")
            time.sleep(2)

    return debate_history


# ============================================================
# USER CHOICE
# ============================================================
def get_user_choice():
    '''
    Numbered options — maps directly to buttons on your website.
    Website: replace input() with two buttons sending "1" or "2".
    '''
    print("\n" + "=" * 50)
    print("  What would you like to do next?")
    print("  [1] Continue    — 3 more rounds of debate")
    print("  [2] Give Verdict — Let the Judge decide now")
    print("=" * 50)

    while True:
        choice = input("  Enter 1 or 2: ").strip()
        if choice == '1':
            return 'continue'
        elif choice == '2':
            return 'verdict'
        else:
            print("  ⚠️  Please enter 1 or 2 only.")


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':

    print("=" * 50)
    print("     WELCOME TO THE AI DEBATE SYSTEM")
    print("=" * 50)
    claim = input("\nEnter the claim to debate:\n> ")

    print("\n  Debate runs in batches of 3 rounds.")
    print("  After each batch, choose to continue or get the verdict.\n")

    debate_history = []
    batch_number   = 1

    while True:
        print(f"\n{'='*50}")
        print(f"  📢 BATCH {batch_number} — Rounds {(batch_number-1)*3+1} to {batch_number*3}")
        print(f"{'='*50}")

        debate_history = run_debate_batch(claim, debate_history, batch_number)

        choice = get_user_choice()

        if choice == 'verdict':
            break
        else:
            batch_number += 1
            print(f"\n  ✅ Starting Batch {batch_number}...\n")

    # Judge delivers verdict
    print("\n" + "=" * 50)
    print("  ⚖️  Judge reviewing full transcript...")
    print("=" * 50)
    time.sleep(1)

    verdict = agent_judge(claim, debate_history)

    print("\n📋 JUDGE'S VERDICT:")
    print("=" * 50)
    print_slowly(verdict, delay=0.01)
    print("=" * 50)