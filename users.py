"""
users.py — Hardcoded demo researcher profiles for PRISM.

Each user has a pre-assigned persona. No passwords, no database.
Session is stored in the browser (sessionStorage) via the frontend.
"""
from typing import Optional

DEMO_USERS = {
    "dr_sarah": {
        "id":      "dr_sarah",
        "name":    "Dr. Sarah Chen",
        "title":   "Senior Medicinal Chemist",
        "org":     "Gladstone Institutes",
        "persona": "medicinal_chemist",
        "initials": "SC",
        "color":   "#0ea5e9",
        "welcome_note": "Your view is focused on potency data, co-crystal structures, and SAR insights.",
    },
    "dr_james": {
        "id":      "dr_james",
        "name":    "Dr. James Okafor",
        "title":   "Clinical Pathologist",
        "org":     "UCSF Medical Center",
        "persona": "pathologist",
        "initials": "JO",
        "color":   "#f59e0b",
        "welcome_note": "Your view is focused on resistance variants, clinical significance, and diagnostic markers.",
    },
    "dr_mei": {
        "id":      "dr_mei",
        "name":    "Dr. Mei Liu",
        "title":   "Cell Biology Researcher",
        "org":     "Gladstone Institutes",
        "persona": "cell_biologist",
        "initials": "ML",
        "color":   "#10b981",
        "welcome_note": "Your view is focused on signaling pathways, mechanism of action, and protein interactions.",
    },
    "dr_alex": {
        "id":      "dr_alex",
        "name":    "Dr. Alex Rivera",
        "title":   "Computational Biologist",
        "org":     "UCSF QB3",
        "persona": "comp_biologist",
        "initials": "AR",
        "color":   "#8b5cf6",
        "welcome_note": "Your view is focused on 3D structures, protein sequences, and ML-ready bioactivity datasets.",
    },
    "dr_priya": {
        "id":      "dr_priya",
        "name":    "Dr. Priya Patel",
        "title":   "Drug Discovery Scientist",
        "org":     "Genentech",
        "persona": "medicinal_chemist",
        "initials": "PP",
        "color":   "#ec4899",
        "welcome_note": "Your view is focused on potency data, co-crystal structures, and SAR insights.",
    },
}

PERSONA_LABELS = {
    "medicinal_chemist": "Medicinal Chemist",
    "pathologist":       "Pathologist",
    "cell_biologist":    "Cell / Molecular Biologist",
    "comp_biologist":    "Computational Biologist",
}

PERSONA_EMOJIS = {
    "medicinal_chemist": "🧪",
    "pathologist":       "🔬",
    "cell_biologist":    "🧬",
    "comp_biologist":    "💻",
}


def get_user(user_id: str) -> Optional[dict]:
    return DEMO_USERS.get(user_id)


def list_users() -> list[dict]:
    return list(DEMO_USERS.values())
