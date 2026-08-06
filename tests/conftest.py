"""Shared fixtures for study-superz tests."""
import sys
import os

TOOLS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools")
KNOWLEDGE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "KNOWLEDGE", "public", "flux-programs")
FOR_FLEET_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "for-fleet")

for d in [TOOLS_DIR, KNOWLEDGE_DIR, FOR_FLEET_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)
