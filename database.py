import streamlit as st
from supabase import create_client, Client
import os

# 初始化 Supabase 客户端
@st.cache_resource
def init_supabase():
    supabase_url = st.secrets["https://wvkqfjwhwdpevfnxwwgw.supabase.co"]
    supabase_key = st.secrets["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind2a3Fmandod2RwZXZmbnh3d2d3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjIwNTExNjMsImV4cCI6MjA3NzYyNzE2M30.6r80sgvf-Z9QWGDebyvsjtWnTcZE9w-pC8s8LNX79iY"]
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