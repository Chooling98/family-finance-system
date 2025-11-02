import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, date
import requests
import json
from database import get_transactions, add_transaction

# 页面配置
st.set_page_config(page_title="家庭理财系统", layout="wide", page_icon="💰")

# Telegram 配置 (将这些信息移到 secrets 管理或环境变量中更安全)
TELEGRAM_BOT_TOKEN = st.secrets.get("TELEGRAM_BOT_TOKEN", "8537018580:AAG1kPxlkpH-3Ov2XHueMZMA5OCjQISz7pk")
TELEGRAM_CHAT_ID = st.secrets.get("TELEGRAM_CHAT_ID", "-1003286262121")

def send_telegram_message(message):
    """发送消息到 Telegram"""
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        st.warning("⚠️ 请先配置 Telegram Bot Token 和 Chat ID")
        return False
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': message,
        'parse_mode': 'HTML'
    }
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return True
        else:
            st.error(f"发送 Telegram 消息失败: {response.text}")
            return False
    except Exception as e:
        st.error(f"发送 Telegram 消息时出错: {str(e)}")
        return False

def format_transaction_message(transaction):
    """格式化交易信息为 Telegram 消息"""
    emoji = "💰" if transaction['amount'] > 0 else "💸"
    sign = "+" if transaction['amount'] > 0 else "-"
    
    message = f"""
{emoji} <b>新交易记录</b> {emoji}

👤 <b>用户:</b> {transaction['user_name']}
📅 <b>日期:</b> {transaction['date']}
🏷️ <b>分类:</b> {transaction['category']}
💳 <b>方式:</b> {transaction['account']}
📝 <b>描述:</b> {transaction['description']}

💵 <b>金额:</b> <code>{sign}RM {abs(transaction['amount']):,.2f}</code>
    
💼 <b>当前余额更新</b>
"""
    return message

# 初始化session state
if 'transactions' not in st.session_state:
    try:
        transactions = get_transactions()
        st.session_state.transactions = transactions if transactions else []
    except Exception as e:
        st.error(f"初始化数据失败: {e}")
        st.session_state.transactions = []

if 'users' not in st.session_state:
    st.session_state.users = [
        {'id': 1, 'name': 'Lynn'}, 
        {'id': 2, 'name': 'Lincoln'}
    ]
if 'accounts' not in st.session_state:
    st.session_state.accounts = {
        'Lynn': {'现金': 1000, '银行卡': 5000, '信用卡': -1500},
        'Lincoln': {'现金': 2000, '银行卡': 15000, '信用卡': -2000}
    }
if 'last_summary_date' not in st.session_state:
    st.session_state.last_summary_date = None

# 预定义分类（保持不变）
INCOME_CATEGORIES = {
    "主业收入": "#4CAF50",
    "Lynn工资": "#4CAF50",    
    "Lincoln工资": "#4CAF50", 
    "副业收入": "#8BC34A", 
    "租金收入": "#2196F3",
    "投资回报": "#009688",
    "其他收入": "#CDDC39"
}

EXPENSE_CATEGORIES = {
    # Lynn的固定支出
    "PTPTN": "#9C27B0",
    "SPPTN": "#E91E63", 
    "张明添基金": "#673AB7",
    "信用卡": "#F44336",
    "Shopee Pay Later": "#FF5722",
    "保险": "#3F51B5",
    "手机卡": "#2196F3",
    "房贷款": "#FF9800",
    "车贷款": "#FFC107",
    "家WiFi": "#00BCD4",
    "门牌税": "#607D8B",
    "地税": "#795548",
    "Indah Water": "#9E9E9E",
    
    # 共同开销
    "车油": "#795548",
    "Toll": "#8D6E63", 
    "食物": "#FF9800",
    "日常购物": "#FF5722",
    "娱乐": "#E91E63",
    "医疗": "#F44336",
    "其他": "#607D8B"
}

def update_account_balance(user_name, account, amount):
    """更新账户余额"""
    if user_name in st.session_state.accounts and account in st.session_state.accounts[user_name]:
        st.session_state.accounts[user_name][account] += amount

def get_user_balance(user_id):
    """获取用户总余额"""
    user_name = 'Lynn' if user_id == 1 else 'Lincoln'
    if user_name in st.session_state.accounts:
        return sum(st.session_state.accounts[user_name].values())
    return 0

def add_transaction(date, amount, category, description, user_id, account="默认"):
    """添加新交易并发送 Telegram 通知"""
    transaction_data = {
        'id': len(st.session_state.transactions) + 1,
        'date': date.isoformat(),
        'amount': amount,
        'category': category,
        'description': description,
        'user_id': user_id,
        'user_name': 'Lynn' if user_id == 1 else 'Lincoln',
        'account': account,
        'type': 'income' if amount > 0 else 'expense'
    }

    # 保存到数据库
    new_transaction = add_transaction(transaction_data)
    
    # 更新本地状态
    st.session_state.transactions.append(new_transaction[0])

    # 发送 Telegram 通知
    message = format_transaction_message(new_transaction)
    telegram_success = send_telegram_message(message)
        
    if telegram_success:
        st.success("✅ 交易已记录并发送到 Telegram")
    else:
        st.success("✅ 交易已记录")
    
    # 更新账户余额
    update_account_balance(new_transaction['user_name'], account, amount)
    
    # 发送 Telegram 通知
    message = format_transaction_message(new_transaction)
    
    # 添加余额信息到消息
    user_balance = get_user_balance(user_id)
    message += f"👤 {new_transaction['user_name']} 总余额: <code>RM {user_balance:,.2f}</code>"
    
    return new_transaction[0]

def send_daily_summary():
    """发送每日交易总结"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    today = date.today()
    
    # 检查是否已经发送过今日总结
    if st.session_state.last_summary_date == today:
        return False
    
    # 获取今日交易
    today_transactions = [
        t for t in st.session_state.transactions 
        if t['date'] == today
    ]
    
    if not today_transactions:
        return False
    
    # 计算统计
    total_income = sum(t['amount'] for t in today_transactions if t['amount'] > 0)
    total_expense = sum(t['amount'] for t in today_transactions if t['amount'] < 0)
    
    # 按分类统计支出
    expense_by_category = {}
    for t in today_transactions:
        if t['amount'] < 0:
            category = t['category']
            expense_by_category[category] = expense_by_category.get(category, 0) + abs(t['amount'])
    
    # 生成总结消息
    message = f"""
    📊 <b>每日财务总结 - {today}</b>

    📈 <b>今日收入:</b> RM {total_income:,.2f}
    📉 <b>今日支出:</b> RM {abs(total_expense):,.2f}
    💰 <b>今日结余:</b> RM {total_income + total_expense:,.2f}

    📝 <b>交易笔数:</b> {len(today_transactions)}

    <b>支出分类:</b>
    """
    for category, amount in expense_by_category.items():
        message += f"  • {category}: RM {amount:.2f}\n"
    
    # 发送消息
    success = send_telegram_message(message)
    if success:
        st.session_state.last_summary_date = today
    
    return success

# 侧边栏导航
st.sidebar.title("💰 家庭理财")
menu = st.sidebar.selectbox("导航", ["总览", "记录开销", "交易历史", "管理房产","分类分析", "AI分析", "Telegram设置"])

if menu == "Telegram设置":
    st.title("⚙️ Telegram 通知设置")
    
    st.info("""
    **设置步骤:**
    1. 在 Telegram 中搜索 `@BotFather`
    2. 发送 `/newbot` 创建新 bot
    3. 获取 bot token
    4. 与你的 bot 开始对话
    5. 获取你的 chat ID
    """)
    
    with st.form("telegram_config"):
        bot_token = st.text_input("Bot Token", value=TELEGRAM_BOT_TOKEN, type="password")
        chat_id = st.text_input("Chat ID", value=TELEGRAM_CHAT_ID)
        
        if st.form_submit_button("保存配置"):
            # 在实际应用中，你应该将这些保存到安全的地方
            # 这里为了演示，我们只是显示成功消息
            st.success("配置已保存！")
            
            # 测试消息
            if st.button("发送测试消息"):
                test_message = "🧪 <b>测试消息</b>\n\n这是从你的理财系统发送的测试消息。如果收到此消息，说明配置正确！"
                if send_telegram_message(test_message):
                    st.success("✅ 测试消息发送成功！")

if menu == "总览":
    st.title("🏠 家庭财务总览")
    
    # 显示账户余额
    st.subheader("账户余额")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Lynn 的账户")
        if 'Lynn' in st.session_state.accounts:
            for account, balance in st.session_state.accounts['Lynn'].items():
                color = "green" if balance >= 0 else "red"
                st.write(f"{account}: <span style='color:{color}'>RM {balance:,.2f}</span>", 
                        unsafe_allow_html=True)
    
    with col2:
        st.write("### Lincoln 的账户")
        if 'Lincoln' in st.session_state.accounts:
            for account, balance in st.session_state.accounts['Lincoln'].items():
                color = "green" if balance >= 0 else "red"
                st.write(f"{account}: <span style='color:{color}'>RM {balance:,.2f}</span>", 
                        unsafe_allow_html=True)
    
    # 关键指标（保持不变）
    col1, col2, col3, col4 = st.columns(4)
    
    total_income = sum(t['amount'] for t in st.session_state.transactions if t['amount'] > 0)
    total_expense = sum(t['amount'] for t in st.session_state.transactions if t['amount'] < 0)
    monthly_saving = total_income + total_expense  # 因为支出是负数
    
    with col1:
        st.metric("本月总收入", f"RM {total_income:,.2f}")
    with col2:
        st.metric("本月总支出", f"RM {abs(total_expense):,.2f}")
    with col3:
        st.metric("本月结余", f"RM {monthly_saving:,.2f}")
    with col4:
        saving_rate = (monthly_saving / total_income * 100) if total_income > 0 else 0
        st.metric("储蓄率", f"{saving_rate:.1f}%")

elif menu == "记录开销":
    st.title("📝 记录日常开销")
    
    with st.form("transaction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            transaction_date = st.date_input("日期", value=date.today())
            amount = st.number_input("金额 (RM)", min_value=0.0, step=0.01, format="%.2f")
            user = st.selectbox("用户", ["Lynn", "Lincoln"])
            account = st.selectbox("支付方式", ["现金", "银行卡", "信用卡", "电子钱包"])
            
        with col2:
            # 根据金额正负自动选择分类类型
            if amount > 0:
                category = st.selectbox("收入分类", list(INCOME_CATEGORIES.keys()))
            else:
                category = st.selectbox("支出分类", list(EXPENSE_CATEGORIES.keys()))
            
            description = st.text_input("描述/备注")
            
            # Telegram 通知开关
            send_notification = st.checkbox("发送 Telegram 通知", value=True)
        
        submitted = st.form_submit_button("记录交易")
        
        if submitted:
            user_id = 1 if user == "Lynn" else 2
            
            # 临时关闭通知（如果用户选择不发送）
            original_token = TELEGRAM_BOT_TOKEN
            if not send_notification:
                # 临时修改 token 使其无效，这样就不会发送通知
                TELEGRAM_BOT_TOKEN = "NO_TOKEN"
            
            new_txn = add_transaction(transaction_date, amount, category, description, user_id, account)
            
            # 恢复原始 token
            TELEGRAM_BOT_TOKEN = original_token

elif menu == "交易历史":
    st.title("📊 交易历史")
    
    if not st.session_state.transactions:
        st.info("暂无交易记录")
    else:
        # 筛选选项
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_user = st.selectbox("筛选用户", ["全部", "Lynn", "Lincoln"])
        with col2:
            selected_type = st.selectbox("筛选类型", ["全部", "收入", "支出"])
        with col3:
            selected_category = st.selectbox("筛选分类", ["全部"] + list(INCOME_CATEGORIES.keys()) + list(EXPENSE_CATEGORIES.keys()))
        
        # 过滤数据
        filtered_data = st.session_state.transactions.copy()
        if selected_user != "全部":
            filtered_data = [t for t in filtered_data if t['user_name'] == selected_user]
        if selected_type != "全部":
            filtered_data = [t for t in filtered_data if t['type'] == selected_type.lower()]
        if selected_category != "全部":
            filtered_data = [t for t in filtered_data if t['category'] == selected_category]
        
        # 显示表格
        if filtered_data:
            df = pd.DataFrame(filtered_data)
            # 格式化显示
            df_display = df[['date', 'user_name', 'category', 'description', 'amount', 'account']].copy()
            df_display['amount'] = df_display['amount'].apply(lambda x: f"RM {x:,.2f}")
            df_display = df_display.sort_values('date', ascending=False)
            st.dataframe(df_display, use_container_width=True)
        else:
            st.info("没有找到符合条件的交易记录")

elif menu == "分类分析":
    st.title("📈 支出分类分析")
    
    if not st.session_state.transactions:
        st.info("暂无数据可供分析")
    else:
        # 支出数据
        expense_data = [t for t in st.session_state.transactions if t['amount'] < 0]
        
        if expense_data:
            # 按分类汇总
            expense_df = pd.DataFrame(expense_data)
            category_summary = expense_df.groupby('category')['amount'].sum().abs().reset_index()
            category_summary = category_summary.sort_values('amount', ascending=False)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("支出分类占比")
                fig = px.pie(category_summary, values='amount', names='category', 
                            color_discrete_sequence=px.colors.qualitative.Set3)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("支出分类排名")
                fig2 = px.bar(category_summary.head(10), x='amount', y='category', 
                             orientation='h', color='amount',
                             color_continuous_scale='Blues')
                fig2.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig2, use_container_width=True)
            
            # 用户对比
            st.subheader("用户支出对比")
            user_expense = expense_df.groupby('user_name')['amount'].sum().abs().reset_index()
            fig3 = px.bar(user_expense, x='user_name', y='amount', color='user_name',
                         color_discrete_map={'Lynn': '#FF6B6B', 'Lincoln': '#4ECDC4'})
            st.plotly_chart(fig3, use_container_width=True)

# 在侧边栏显示快速统计和 Telegram 状态
st.sidebar.markdown("---")
st.sidebar.subheader("快速统计")
if st.session_state.transactions:
    total = sum(t['amount'] for t in st.session_state.transactions)
    st.sidebar.write(f"总交易数: {len(st.session_state.transactions)}")
    st.sidebar.write(f"净现金流: RM {total:,.2f}")

# Telegram 状态
st.sidebar.markdown("---")
st.sidebar.subheader("Telegram 状态")
if TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE" and TELEGRAM_CHAT_ID != "YOUR_CHAT_ID_HERE":
    st.sidebar.success("✅ Telegram 已配置")
    if st.sidebar.button("测试通知"):
        test_msg = "🔔 <b>系统运行状态</b>\n\n理财系统正在正常运行，通知功能已启用！"
        if send_telegram_message(test_msg):
            st.sidebar.success("测试消息已发送")
else:
    st.sidebar.error("❌ Telegram 未配置")

#每日交易总结
st.sidebar.markdown("---")
if st.sidebar.button("发送今日总结"):
    if send_daily_summary():
        st.sidebar.success("今日总结已发送")
    else:
        st.sidebar.info("今日暂无交易或已发送过总结")

# if __name__ == "__main__":
#     # 添加示例数据（保持不变）
#     if not st.session_state.transactions:
#         # 添加一些示例交易
#         add_transaction(date(2024, 1, 15), 5000, "主业收入", "1月工资", 1, "银行卡")
#         add_transaction(date(2024, 1, 16), -50, "食物", "午餐", 1, "现金")
#         add_transaction(date(2024, 1, 17), -200, "车油", "打油", 1, "银行卡")
#         add_transaction(date(2024, 1, 18), -300, "PTPTN", "教育贷款", 1, "银行卡")
#         add_transaction(date(2024, 1, 15), 8000, "主业收入", "1月工资", 2, "银行卡")
#         add_transaction(date(2024, 1, 16), -150, "食物", "超市采购", 2, "银行卡")

#         add_transaction(date(2024, 1, 20), -500, "保险", "人寿保险", 2, "银行卡")
