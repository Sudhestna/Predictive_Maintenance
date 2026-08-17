from db import ChatSession, get_db

with get_db() as db:
    sessions = db.query(ChatSession).all()
    for session in sessions:
        print("-" * 50)
        print("Session ID :", session.session_id)
        print("Created At :", session.created_at)
        print("Updated At :", session.updated_at)
        print("\nMessages:")
        for msg in session.messages:
            print(f'{msg["role"]}: {msg["content"]}')
        print()