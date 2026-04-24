"""
utils/firebase.py — Firebase init and all Firestore operations.
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime


@st.cache_resource
def get_db():
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("firebase_key.json")
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase init failed: {e}")
        return None


def save_detection(result: dict) -> bool:
    db = get_db()
    if db is None:
        return False
    try:
        db.collection("detections").add({
            "timestamp":       datetime.utcnow(),
            "steel_prob":      round(result["steel_prob"] * 100, 2),
            "defect_detected": result["defect_detected"],
            "severity":        result["severity"],
            "defect_ratio":    result["defect_area"],
        })
        return True
    except Exception as e:
        st.warning(f"Save failed: {e}")
        return False


def fetch_history(limit: int = 200) -> list:
    db = get_db()
    if db is None:
        return []
    try:
        docs = (db.collection("detections")
                .order_by("timestamp", direction=firestore.Query.DESCENDING)
                .limit(limit).stream())
        return [{**d.to_dict(), "id": d.id} for d in docs]
    except Exception as e:
        st.warning(f"Fetch failed: {e}")
        return []


def delete_all() -> bool:
    db = get_db()
    if db is None:
        return False
    try:
        for doc in db.collection("detections").stream():
            doc.reference.delete()
        return True
    except Exception as e:
        st.warning(f"Clear failed: {e}")
        return False
