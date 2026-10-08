import streamlit as st
import json
import redis
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from config import Config

st.set_page_config(page_title="AuraGuard Clinical Monitor", layout="wide")
st.title("🏥 AuraGuard: NHS Patient Safety & Ward Flow Monitor")
st.markdown("🔒 **Compliance State:** Edge-Anonymised Node | Zero Local Storage Active")

# Setup Redis Client
r = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, decode_responses=True)
p = r.pubsub()
p.subscribe(Config.STREAM_CHANNEL)

# Init layout blocks
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Live Top-Down Ward Footprints Map")
    map_placeholder = st.empty()

with col2:
    st.subheader("🚨 Active Clinical Alerts")
    alert_placeholder = st.empty()

# Persistent tracking dictionary simulating runtime cache
if "positions" not in st.session_state:
    st.session_state.positions = {}
if "alerts" not in st.session_state:
    st.session_state.alerts = []

# Event loop to draw incoming spatial vectors
while True:
    message = p.get_message(ignore_subscribe_messages=True)
    if message:
        payload = json.loads(message["data"])
        p_id = payload["patient_token"]
        
        # Track historical coordinate movement patterns
        st.session_state.positions[p_id] = (payload["ward_x"], payload["ward_y"], payload["status"])
        
        if payload["status"] == "FALL_CRITICAL" and p_id not in st.session_state.alerts:
            st.session_state.alerts.insert(0, f"⚠️ PATIENT FALL DETECTED: Token #{p_id}")
            
    # Render Dashboard Components
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_xlim(0, 800)
    ax.set_ylim(0, 1000)
    ax.set_title("Real-Time Ward Blueprint Projection Mapping")
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Render patient tokens down onto the 2D map layout
    for pid, (wx, wy, status) in st.session_state.positions.items():
        marker_color = 'red' if status == "FALL_CRITICAL" else 'green'
        ax.scatter(wx, wy, c=marker_color, s=200, edgecolors='black')
        ax.text(wx + 15, wy + 15, f"P#{pid}", fontsize=9, weight='bold')

    map_placeholder.pyplot(fig)
    plt.close(fig)
    
    # Dynamic Alert Log
    alert_placeholder.write(st.session_state.alerts[:10])
