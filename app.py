import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np 

FILE_NAME = "expenses_web.csv"
TOTAL_BUDGET = 10000


if not os.path.exists(FILE_NAME):
    df = pd.DataFrame(columns=["Khath", "Amount"])
    df.to_csv(FILE_NAME, index=False)


st.set_page_config(page_title="স্মার্ট মানি ম্যানেজার", layout="centered")
st.title("💰 আমার স্মার্ট মানি ম্যানেজার")
st.write("সহজে খরচ ট্র্যাক করুন এবং হিসেব রাখুন।")


st.subheader("নতুন খরচ যোগ করুন")
with st.form(key='expense_form', clear_on_submit=True):
    khat = st.text_input("কোথায় খরচ করলেন? (যেমন: খাবার, রিকশা)")
    taka = st.number_input("কত টাকা খরচ হলো?", min_value=1, step=1)
    submit_button = st.form_submit_button(label="সেভ করুন")

if submit_button and khat:
    new_data = pd.DataFrame([[khat, taka]], columns=["Khath", "Amount"])
    new_data.to_csv(FILE_NAME, mode='a', header=False, index=False)
    st.success(f"সফলভাবে সেভ হয়েছে: {khat} -> {taka} টাকা")


df = pd.read_csv(FILE_NAME)
total_spent = df["Amount"].sum()
remaining_budget = TOTAL_BUDGET - total_spent

st.write("---")
col1, col2, col3 = st.columns(3)
col1.metric("মোট বাজেট", f"{TOTAL_BUDGET} ৳")
col2.metric("মোট খরচ", f"{total_spent} ৳", delta=f"-{total_spent} ৳", delta_color="inverse")
col3.metric("অবশিষ্ট বাজেট", f"{remaining_budget} ৳")


if not df.empty:
    st.subheader("📊 খরচের বিশ্লেষণ")
    category_df = df.groupby("Khath")["Amount"].sum().reset_index()
    
    col_left, col_right = st.columns(2)
    with col_left:
        st.write("খরচের তালিকা:")
        st.dataframe(category_df, use_container_width=True)
    with col_right:
        fig, ax = plt.subplots()
        ax.pie(category_df["Amount"], labels=category_df["Khath"], autopct='%1.1f%%', startangle=90)
        st.pyplot(fig)
        

    st.write("---")
    st.subheader("📊 লোকাল স্মার্ট বাজেট ফোরকাস্টিং")
    
    if st.button("বাজেট ফোরকাস্ট ও পরামর্শ জেনারেট করুন"):
     
        spent_amounts = df["Amount"].tolist()
        days = np.arange(len(spent_amounts))
        
        if len(spent_amounts) > 1:
          
            slope, intercept = np.polyfit(days, spent_amounts, 1)
            predicted_next = max(100, int(slope * (len(spent_amounts)) + intercept))
        else:
            predicted_next = spent_amounts[0]
            
    
        highest_expense_row = category_df.loc[category_df['Amount'].idxmax()]
        highest_khat = highest_expense_row['Khath']
        highest_amount = highest_expense_row['Amount']
        
      
        st.info("💡 **আপনার খরচের লোকাল অ্যানালাইসিস রিপোর্ট:**")
        st.markdown(f"**১. খরচের অভ্যাস:** আপনি এ পর্যন্ত সবচেয়ে বেশি খরচ করেছেন **'{highest_khat}'** খাতে, যার পরিমাণ মোট **{highest_amount} ৳**।")
        
       
        st.markdown(f"**২. ভবিষ্যৎ ফোরকাস্ট (Forecasting):** আপনার বর্তমান খরচের গতিবিধি এবং প্যাটার্ন অনুযায়ী, আপনার পরবর্তী ট্রানজেকশনে সম্ভাব্য খরচের পরিমাণ হতে পারে প্রায় **{predicted_next} ৳**।")
        
        st.markdown("**৩. টাকা বাঁচানোর জন্য ৩টি গাইডলাইন:**")
        st.markdown(f"* **নিয়ন্ত্রণ করুন:** আপনার মোট খরচের একটা বড় অংশ যাচ্ছে '{highest_khat}'-এ। আগামী সপ্তাহে এই খাতের খরচ ২০% কমানোর চেষ্টা করুন।")
        if remaining_budget < (TOTAL_BUDGET * 0.3):
            st.markdown("* 🚨 **জরুরি সতর্কতা:** আপনার মূল বাজেটের ৩০%-এর কম অবশিষ্ট আছে! এখন থেকে শুধুমাত্র অতি প্রয়োজনীয় জিনিস (Needs) ছাড়া অন্য সব খরচ বন্ধ রাখুন।")
        else:
            st.markdown("* **বাজেট ট্র্যাকিং:** প্রতিদিন রাতে ঘুমানোর আগে অন্তত একবার এই ড্যাশবোর্ডটি চেক করার অভ্যাস করুন।")
        st.markdown("* **সঞ্চয়:** টাকা খরচ করার পর যা বাঁচে তা জমানোর চেয়ে, মাসের শুরুতেই বাজেট থেকে ১০% টাকা আলাদা কোনো অ্যাকাউন্টে সরিয়ে রাখুন।")
else:
    st.info("এখনো কোনো খরচের রেকর্ড নেই। ওপরের ফর্ম থেকে যোগ করুন।")