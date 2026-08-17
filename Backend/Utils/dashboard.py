import json
from pathlib import Path
from threading import Lock
import traceback

DASHBOARD_FILE = Path(r"C:\Users\GenAIHYDSYPUSR35\Desktop\PNC_AI_TEAM\Utils\dashboard_data.json")

dashboard_lock = Lock()


def update_dashboard(parent: str, key: str, value: int = 1):
    """
    Increment a dashboard value.

    Example:
        update_dashboard("chat", "total_queries")
        update_dashboard("feedback", "helpful")
        update_dashboard("retrieval", "tool_calls", 5)
    """

    try:
        with dashboard_lock:

            with open(DASHBOARD_FILE, "r") as f:
                dashboard = json.load(f)

            dashboard[parent][key] += value

            with open(DASHBOARD_FILE, "w") as f:
                json.dump(dashboard, f, indent=4)

    except Exception as e:
        print("########### issue in dahsboard.py###########")
        traceback.print_exc()
        print("########### issue in dahsboard.py###########")