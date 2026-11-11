
from datetime import datetime, timezone

def load_user_chats(supabase, user_id):
    response = (
        supabase.table("study_chats")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    chats = {}
    for row in response.data:
        chats[row["id"]] = {
            "title": row["title"],
            "messages": row["messages"] or []
        }
    return chats

def create_chat(supabase, user_id):
    response = supabase.table("study_chats").insert({
        "user_id": user_id,
        "title": "New Chat",
        "messages": []
    }).execute()
    if not response.data:
        raise Exception("Chat could not be created.")
    return response.data[0]

def save_chat(supabase, user_id, chat_id, title, messages):
    supabase.table("study_chats").update({
        "title": title,
        "messages": messages,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }).eq("id", chat_id).eq("user_id", user_id).execute()

def delete_chat(supabase, user_id, chat_id):
    supabase.table("study_chats").delete().eq(
        "id", chat_id
    ).eq("user_id", user_id).execute()
