import json
import time
from datetime import datetime
from pathlib import Path

import requests
import streamlit as st
import streamlit.components.v1 as components

OLLAMA_URL = "http://localhost:11434/api/chat"
# Keep this set to the model that worked quickly on your computer.
MODEL = "qwen2.5:1.5b"
DATA_DIR = Path.home() / "AI-Office" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
TASKS_FILE = DATA_DIR / "tasks.json"
LOG_FILE = DATA_DIR / "activity.json"

AGENTS = {
    "Ello": {"role": "Coordinator", "color": "#9dbdff", "prompt": "You are Ello, the Coordinator of a small local AI office. Clarify goals, break work into steps, assign work to the right role, and give the user a practical plan. Be honest about what you have and have not done. You cannot access the user's files, internet, or apps unless a tool is explicitly provided."},
    "Reso": {"role": "Researcher", "color": "#8ed9c3", "prompt": "You are Reso, the Researcher. Organize known information, identify questions and uncertainty, and suggest sources to check. You do not have web access in this app, so never claim you searched the internet or verified current facts."},
    "Ana": {"role": "Analyst", "color": "#c6adff", "prompt": "You are Ana, the Analyst. Compare options, reason carefully, calculate when possible, make assumptions explicit, and present conclusions with trade-offs. Do not invent data."},
    "Exo": {"role": "Executor", "color": "#f0c58b", "prompt": "You are Exo, the Executor. Turn approved instructions into concrete steps, drafts, checklists, and code. This app does not grant you control of the computer, so never claim to have performed actions outside this chat."},
    "Revo": {"role": "Reviewer", "color": "#f0a8b7", "prompt": "You are Revo, the Reviewer. Review plans and drafts for errors, missing steps, safety issues, and unsupported claims. Be constructive and specific. You cannot verify facts externally in this app."},
}


def read_json(path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def add_activity(agent, message):
    log = read_json(LOG_FILE, [])
    log.insert(0, {"time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "agent": agent, "message": message})
    write_json(LOG_FILE, log[:100])


def ask_ollama(agent, user_text, history=None):
    messages = [{"role": "system", "content": AGENTS[agent]["prompt"] + "\n\nWork as part of a local multi-agent office. Keep answers clear and useful."}]
    if history:
        messages.extend(history[-10:])
    messages.append({"role": "user", "content": user_text})
    response = requests.post(OLLAMA_URL, json={"model": MODEL, "messages": messages, "stream": False}, timeout=240)
    response.raise_for_status()
    return response.json()["message"]["content"]


st.set_page_config(page_title="AI Office | Local Workspace", page_icon="🏢", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp { background: radial-gradient(ellipse at 12% 0%, #18283c 0%, #0b111b 42%, #080c12 100%); color: #edf2fa; font-family: 'DM Sans', sans-serif; }
.block-container { padding-top: 1.25rem; max-width: 1600px; padding-bottom: 3rem; }
section[data-testid="stSidebar"] { background: linear-gradient(180deg,#101a28,#0a1019); border-right: 1px solid #263449; }
h1,h2,h3 { font-family: 'Manrope', sans-serif; letter-spacing: -.035em; }
h1 { font-weight: 800 !important; }
.small-muted { color:#91a2b9; font-size:.9rem; }
.eyebrow { color:#91b7ff; font-size:.72rem; letter-spacing:.18em; font-weight:800; text-transform:uppercase; }
.hero { background:linear-gradient(115deg,rgba(31,49,73,.92),rgba(15,24,37,.92)); border:1px solid #30435c; border-radius:22px; padding:24px 26px; margin-bottom:18px; box-shadow:0 18px 60px rgba(0,0,0,.18); }
.agent-card { background:linear-gradient(145deg,rgba(27,42,61,.95),rgba(13,21,32,.98)); border:1px solid #2a3a50; border-radius:17px; padding:17px 16px; min-height:126px; box-shadow:0 10px 26px rgba(0,0,0,.12); transition:transform .2s ease,border-color .2s ease; }
.agent-card:hover { transform:translateY(-3px); border-color:#59749a; }
.pulse-dot { display:inline-block;width:7px;height:7px;border-radius:50%;background:#70d5ae;box-shadow:0 0 12px #70d5ae;margin-right:7px; }
div[data-testid="stMetric"] { background:rgba(22,34,51,.75); padding:14px 16px; border:1px solid #293a50; border-radius:15px; }
[data-testid="stChatMessage"] { background:rgba(17,27,41,.65); border:1px solid rgba(46,64,86,.6); border-radius:16px; padding:12px 14px; }
div.stButton>button { border-radius:11px; border:1px solid #34475f; background:#172438; color:#eef4ff; transition:all .18s ease; }
div.stButton>button:hover { border-color:#8eb1f4; color:white; background:#22344d; }
.stTextInput input, .stSelectbox div[data-baseweb="select"], .stChatInput textarea { background:#101a28 !important; }
hr { border-color:#253449; }
section[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:7px 9px; border-radius:10px; }
</style>
""", unsafe_allow_html=True)

if "chat" not in st.session_state: st.session_state.chat = []
if "active_agent" not in st.session_state: st.session_state.active_agent = "Ello"
if "last_status" not in st.session_state: st.session_state.last_status = "Ready"
if "voice_enabled" not in st.session_state: st.session_state.voice_enabled = True

with st.sidebar:
    st.markdown("<div class='eyebrow'>Local intelligence workspace</div><h2 style='margin-top:4px'>◈ AI OFFICE</h2>", unsafe_allow_html=True)
    st.caption("PRIVATE BY DEFAULT · POWERED BY OLLAMA")
    st.markdown("---")
    st.markdown("#### Your team")
    selected = st.radio("Agent", list(AGENTS.keys()), format_func=lambda n: f"{n}  ·  {AGENTS[n]['role']}", index=list(AGENTS).index(st.session_state.active_agent), label_visibility="collapsed")
    st.session_state.active_agent = selected
    st.markdown("---")
    st.markdown("#### Workspace status")
    st.write(f"**Model**  `{MODEL}`")
    st.write("**Runtime**  Local Ollama")
    st.write(f"**Status**  {st.session_state.last_status}")
    st.session_state.voice_enabled = st.toggle("Read replies aloud", value=st.session_state.voice_enabled)
    if st.button("Clear current chat", use_container_width=True):
        st.session_state.chat = []
        st.rerun()
    st.caption("Voice recognition availability depends on your browser. This app does not browse the web or control your PC.")

st.markdown("<div class='hero'><div class='eyebrow'>Executive operations · Local AI</div><h1 style='margin:8px 0 4px'>The Office</h1><div class='small-muted'>One workspace for planning, analysis, execution and review.</div></div>", unsafe_allow_html=True)
m1,m2,m3,m4 = st.columns(4)
m1.metric("TEAM MEMBERS", "05", "All roles ready")
m2.metric("AI MODEL", "Qwen 2.5 · 1.5B", "Local inference")
m3.metric("RUNTIME", "On-device", "Ollama")
m4.metric("WORKSPACE", "Active", "Local records")

st.markdown("### Team overview")
cols = st.columns(5)
for col,(name,info) in zip(cols,AGENTS.items()):
    with col:
        st.markdown(f"<div class='agent-card'><div style='font-size:1.06rem;font-weight:800;color:{info['color']}'>{name}</div><div style='font-size:.88rem;color:#dce6f4;margin-top:5px'>{info['role']}</div><div style='font-size:.78rem;color:#8fa2ba;margin-top:17px'><span class='pulse-dot'></span>Available</div></div>", unsafe_allow_html=True)

left,right = st.columns([1.65,1], gap="large")
with left:
    current = st.session_state.active_agent
    info = AGENTS[current]
    st.markdown(f"### Conversation · {current}")
    st.caption(f"{info['role']}  /  generated by your local model")
    for item in st.session_state.chat:
        with st.chat_message(item["role"], avatar="◈" if item["role"] == "assistant" else "●"):
            if item.get("agent"): st.caption(f"{item['agent']} · {AGENTS.get(item['agent'],{}).get('role','Agent')}")
            st.markdown(item["content"])
            if item["role"] == "assistant" and st.session_state.voice_enabled:
                safe_text = json.dumps(item["content"])
                components.html(f"""<script>try {{ if (window.parent && window.parent.speechSynthesis) {{ /* voice playback is available via the Speak button below */ }} }} catch(e) {{}}</script>""", height=0)
                if st.button("🔊 Speak this reply", key=f"speak_{len(st.session_state.chat)}_{item.get('agent','agent')}"):
                    components.html(f"""<script>const t={safe_text}; const u=new SpeechSynthesisUtterance(t); u.rate=1.0; u.pitch=0.96; window.speechSynthesis.cancel(); window.speechSynthesis.speak(u);</script>""", height=0)

    # Speech-to-text component returns recognized text into Streamlit's Python state.
    st.markdown("#### Voice input")
    try:
        from streamlit_mic_recorder import speech_to_text
        spoken = speech_to_text(language="en", start_prompt="🎙️ Start speaking", stop_prompt="⏹ Stop recording", just_once=True, key="ello_voice_input")
    except ImportError:
        spoken = None
        st.info("Voice input needs one small free package. Install it using the command shown below, then restart the app.")
        st.code("py -m pip install streamlit-mic-recorder", language="powershell")
    if spoken:
        st.session_state.voice_draft = spoken
    voice_draft = st.text_area("Recognized speech (you can edit it before sending)", value=st.session_state.get("voice_draft", ""), height=85, placeholder="Your recognized words will appear here…", key="voice_draft_area")
    if st.button(f"Send to {current}", type="primary", disabled=not voice_draft.strip(), use_container_width=True):
        st.session_state.pending_prompt = voice_draft.strip()
        st.session_state.voice_draft = ""
        st.rerun()

    prompt = st.chat_input(f"Give {current} a task…")
    prompt = prompt or st.session_state.pop("pending_prompt", None)
    if prompt:
        st.session_state.chat.append({"role":"user","content":prompt})
        add_activity(current, f"Received request: {prompt[:90]}")
        with st.chat_message("user"): st.markdown(prompt)
        with st.chat_message("assistant", avatar="◈"):
            st.caption(f"{current} · {info['role']}")
            with st.spinner(f"{current} is thinking locally…"):
                try:
                    history=[{"role":x["role"],"content":x["content"]} for x in st.session_state.chat[:-1] if x["role"] in ("user","assistant")]
                    answer=ask_ollama(current,prompt,history)
                    st.markdown(answer)
                    st.session_state.chat.append({"role":"assistant","content":answer,"agent":current})
                    st.session_state.last_status="Ready"
                    add_activity(current,"Completed a response")
                    if st.session_state.voice_enabled:
                        safe_answer=json.dumps(answer)
                        components.html(f"<script>try {{ const u=new SpeechSynthesisUtterance({safe_answer}); u.rate=1; u.pitch=.96; window.speechSynthesis.cancel(); window.speechSynthesis.speak(u); }} catch(e) {{}}</script>", height=0)
                except requests.exceptions.ConnectionError:
                    answer="I couldn't connect to Ollama. Make sure Ollama is running, then try again."
                    st.error(answer); st.session_state.last_status="Ollama disconnected"
                except Exception as exc:
                    st.error(f"Something went wrong: {exc}"); st.session_state.last_status="Error"
        st.rerun()

with right:
    st.markdown("### Quick actions")
    task_text=st.text_input("New task",placeholder="e.g. Compare two options")
    task_owner=st.selectbox("Assign to",list(AGENTS.keys()),index=0)
    if st.button("＋  Add task",use_container_width=True,disabled=not task_text.strip()):
        tasks=read_json(TASKS_FILE,[])
        tasks.insert(0,{"id":int(time.time()*1000),"text":task_text.strip(),"owner":task_owner,"status":"Queued","created":datetime.now().strftime("%Y-%m-%d %H:%M")})
        write_json(TASKS_FILE,tasks); add_activity(task_owner,f"Task queued: {task_text.strip()[:90]}"); st.success("Task added to the local task board."); st.rerun()
    st.markdown("### Task board")
    tasks=read_json(TASKS_FILE,[])
    if not tasks: st.caption("No tasks yet. Add one above.")
    for task in tasks[:12]:
        with st.container(border=True):
            st.markdown(f"**{task['text']}**")
            st.caption(f"{task['owner']} · {task['created']} · {task['status']}")
            c1,c2=st.columns(2)
            if task["status"]!="Done" and c1.button("Mark done",key=f"done_{task['id']}",use_container_width=True):
                for t in tasks:
                    if t["id"]==task["id"]: t["status"]="Done"
                write_json(TASKS_FILE,tasks); st.rerun()
            if c2.button("Delete",key=f"del_{task['id']}",use_container_width=True):
                write_json(TASKS_FILE,[t for t in tasks if t["id"]!=task["id"]]); st.rerun()

st.markdown("---")
st.markdown("### Activity feed")
activity=read_json(LOG_FILE,[])
if not activity: st.caption("Your team's activity will appear here.")
else:
    for event in activity[:8]: st.markdown(f"`{event['time']}` · **{event['agent']}** — {event['message']}")
st.markdown("---")
st.caption("AI Office · Runs on your computer · Task and activity records saved under ~/AI-Office/data")
