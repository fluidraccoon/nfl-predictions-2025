import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os
import subprocess
from datetime import datetime

st.title("2025 NFL Predictions 🏈")

# Load the data
@st.cache_data
def load_data():
    afc_data = pd.read_csv("categories/afc_winner.csv")
    nfc_data = pd.read_csv("categories/nfc_winner.csv")
    return afc_data, nfc_data

def load_selections():
    """Load existing selections or create empty DataFrame"""
    if os.path.exists("selections.csv"):
        return pd.read_csv("selections.csv")
    else:
        return pd.DataFrame(columns=['name', 'afc_winner', 'nfc_winner', 'timestamp'])

def save_selection(name, afc_winner, nfc_winner):
    """Save user selection to CSV"""
    selections_df = load_selections()
    
    # Check if user already exists
    if name in selections_df['name'].values:
        # Update existing row
        selections_df.loc[selections_df['name'] == name, ['afc_winner', 'nfc_winner', 'timestamp']] = [
            afc_winner, nfc_winner, datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
    else:
        # Add new row
        new_row = pd.DataFrame({
            'name': [name],
            'afc_winner': [afc_winner],
            'nfc_winner': [nfc_winner],
            'timestamp': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        })
        selections_df = pd.concat([selections_df, new_row], ignore_index=True)
    
    selections_df.to_csv("selections.csv", index=False)
    return selections_df

def commit_to_github(name):
    """Commit changes to GitHub"""
    try:
        # Add the selections.csv file
        subprocess.run(["git", "add", "selections.csv"], check=True)
        
        # Commit with user's name in message
        commit_message = f"Add/update predictions for {name}"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # Push to GitHub
        subprocess.run(["git", "push"], check=True)
        
        return True, "Successfully committed to GitHub!"
    except subprocess.CalledProcessError as e:
        return False, f"Error committing to GitHub: {str(e)}"

afc_df, nfc_df = load_data()

# User input section
col1, col2 = st.columns([2, 1])

with col1:
    user_name = st.text_input("Enter your name:", placeholder="e.g., John Doe")

st.divider()

# Create tabs
tab1, tab2, tab3 = st.tabs(["🔴 AFC Winner", "🔵 NFC Winner", "📝 Submit Predictions"])

with tab1:
    st.header("AFC Conference Winner")
    
    # Sort AFC teams by points (lowest first), then alphabetically by team name
    afc_sorted = afc_df.sort_values(['points', 'selection'], ascending=[True, True])
    afc_options = ["-- Select a team --"]
    for _, row in afc_sorted.iterrows():
        afc_options.append(f"{row['selection']} - {row['points']} points")
    
    selected_afc_raw = st.radio("Choose AFC Winner:", afc_options, key="afc_select")
    
    # Only set selected_afc if a real team is selected
    if selected_afc_raw != "-- Select a team --":
        selected_afc = selected_afc_raw.split(" - ")[0]
        points = int(selected_afc_raw.split(" - ")[1].split(" ")[0])
        st.success(f"**{selected_afc}** - {points} points")
    else:
        selected_afc = None
        st.info("Please select an AFC team")

with tab2:
    st.header("NFC Conference Winner")
    
    # Sort NFC teams by points (lowest first), then alphabetically by team name
    nfc_sorted = nfc_df.sort_values(['points', 'selection'], ascending=[True, True])
    nfc_options = ["-- Select a team --"]
    for _, row in nfc_sorted.iterrows():
        nfc_options.append(f"{row['selection']} - {row['points']} points")
    
    selected_nfc_raw = st.radio("Choose NFC Winner:", nfc_options, key="nfc_select")
    
    # Only set selected_nfc if a real team is selected
    if selected_nfc_raw != "-- Select a team --":
        selected_nfc = selected_nfc_raw.split(" - ")[0]
        points = int(selected_nfc_raw.split(" - ")[1].split(" ")[0])
        st.success(f"**{selected_nfc}** - {points} points")
    else:
        selected_nfc = None
        st.info("Please select an NFC team")

with tab3:
    st.header("Submit Your Predictions")
    
    # Summary of current selections
    col1, col2 = st.columns(2)
    
    with col1:
        if 'selected_afc' in locals() and selected_afc:
            afc_points = afc_df[afc_df['selection'] == selected_afc]['points'].iloc[0]
            st.metric("AFC Winner", selected_afc, f"{afc_points} pts")
        else:
            st.metric("AFC Winner", "Not selected", "0 pts")
    
    with col2:
        if 'selected_nfc' in locals() and selected_nfc:
            nfc_points = nfc_df[nfc_df['selection'] == selected_nfc]['points'].iloc[0]
            st.metric("NFC Winner", selected_nfc, f"{nfc_points} pts")
        else:
            st.metric("NFC Winner", "Not selected", "0 pts")
    
    st.divider()
    
    # Submission section
    if user_name and 'selected_afc' in locals() and selected_afc and 'selected_nfc' in locals() and selected_nfc:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 Save Predictions", type="primary", use_container_width=True):
                try:
                    updated_df = save_selection(user_name, selected_afc, selected_nfc)
                    st.success(f"✅ Predictions saved for {user_name}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving predictions: {str(e)}")
        
        with col2:
            if st.button("🚀 Save & Commit to GitHub", type="secondary", use_container_width=True):
                try:
                    # First save the selection
                    updated_df = save_selection(user_name, selected_afc, selected_nfc)
                    st.success(f"✅ Predictions saved for {user_name}!")
                    
                    # Then commit to GitHub
                    with st.spinner("Committing to GitHub..."):
                        success, message = commit_to_github(user_name)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving/committing predictions: {str(e)}")
    else:
        st.warning("⚠️ Please enter your name and make both AFC and NFC selections before submitting.")
        
        missing_items = []
        if not user_name:
            missing_items.append("👤 Your name")
        if 'selected_afc' not in locals() or not selected_afc:
            missing_items.append("🔴 AFC Winner selection")
        if 'selected_nfc' not in locals() or not selected_nfc:
            missing_items.append("🔵 NFC Winner selection")
        
        st.write("Missing:")
        for item in missing_items:
            st.write(f"- {item}")