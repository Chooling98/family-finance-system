import streamlit as st
from supabase import create_client, Client
import os

# 初始化 Supabase 客户端
@st.cache_resource
def init_supabase():
    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]
    return create_client(supabase_url, supabase_key)

def get_transactions():
    supabase = init_supabase()
    response = supabase.table("transactions").select("*").execute()
    return response.data

def add_transaction(transaction_data):
    supabase = init_supabase()
    response = supabase.table("transactions").insert(transaction_data).execute()
    return response.data


# 其他数据库操作函数...
