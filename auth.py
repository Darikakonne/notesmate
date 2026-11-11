
from supabase import create_client

def create_supabase_client(url, key):
    return create_client(url, key)

def register_user(supabase, email, password):
    return supabase.auth.sign_up({
        "email": email,
        "password": password
    })

def login_user(supabase, email, password):
    return supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })

def logout_user(supabase):
    supabase.auth.sign_out()
