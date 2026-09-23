import os
from datetime import timedelta

# Define the follow-up delays
# Example: 3 days for Follow-up 1, 4 days for Follow-up 2
FOLLOW_UP_SCHEDULE = [
    timedelta(days=3),
    timedelta(days=4)
]

# The time window in which an action is considered "DUE_NOW"
DUE_WINDOW_MINUTES = int(os.environ.get("DUE_WINDOW_MINUTES", 15))
