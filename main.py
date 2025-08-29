import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import os
import subprocess
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

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

def check_gsheets_setup():
    """Check if Google Sheets is properly configured and show setup status"""
    try:
        if "gsheets" not in st.secrets.get("connections", {}):
            return False, "❌ Google Sheets not configured"
        
        gsheets_config = st.secrets["connections"]["gsheets"]
        required_fields = ["type", "project_id", "private_key", "client_email", "spreadsheet"]
        missing_fields = [field for field in required_fields if not gsheets_config.get(field)]
        
        if missing_fields:
            return False, f"❌ Missing: {', '.join(missing_fields)}"
        
        if gsheets_config.get("type") != "service_account":
            return False, "❌ Must use service_account type"
        
        return True, "✅ Google Sheets configured"
        
    except Exception as e:
        return False, f"❌ Configuration error: {str(e)}"

def save_selection_to_gsheets(name, afc_winner, nfc_winner):
    """Save user selection to Google Sheets with Service Account authentication"""
    try:
        # Check if we have proper service account credentials
        if "gsheets" not in st.secrets.get("connections", {}):
            return False, "Google Sheets connection not configured in secrets.toml"
        
        gsheets_config = st.secrets["connections"]["gsheets"]
        
        # Check for required service account fields
        required_fields = ["type", "project_id", "private_key", "client_email"]
        missing_fields = [field for field in required_fields if not gsheets_config.get(field)]
        
        if missing_fields:
            return False, f"Missing service account credentials: {', '.join(missing_fields)}"
        
        if gsheets_config.get("type") != "service_account":
            return False, "Google Sheets connection must use 'service_account' type for write operations"
        
        # Create connection to Google Sheets with service account
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Read existing data from Google Sheets
        try:
            existing_data = conn.read(worksheet="predictions", usecols=list(range(4)))
            if existing_data.empty:
                existing_data = pd.DataFrame(columns=['name', 'afc_winner', 'nfc_winner', 'timestamp'])
        except Exception as read_error:
            # If worksheet doesn't exist, create empty DataFrame
            existing_data = pd.DataFrame(columns=['name', 'afc_winner', 'nfc_winner', 'timestamp'])
        
        # Prepare new row data
        new_row = {
            'name': name,
            'afc_winner': afc_winner,
            'nfc_winner': nfc_winner,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Check if user already exists
        if not existing_data.empty and 'name' in existing_data.columns and name in existing_data['name'].values:
            # Update existing row
            existing_data.loc[existing_data['name'] == name, ['afc_winner', 'nfc_winner', 'timestamp']] = [
                afc_winner, nfc_winner, new_row['timestamp']
            ]
        else:
            # Add new row
            new_row_df = pd.DataFrame([new_row])
            existing_data = pd.concat([existing_data, new_row_df], ignore_index=True)
        
        # Write updated data back to Google Sheets
        conn.update(worksheet="predictions", data=existing_data)
        
        return True, "Successfully saved to Google Sheets!"
        
    except Exception as e:
        error_msg = str(e)
        
        # Provide specific guidance for common errors
        if "Public Spreadsheet cannot be written to" in error_msg:
            return False, "Cannot write to public sheet. Please: 1) Create a service account in Google Cloud Console, 2) Share your Google Sheet with the service account email, 3) Add service account credentials to secrets.toml"
        elif "Forbidden" in error_msg:
            return False, "Access denied. Please share your Google Sheet with the service account email address"
        elif "not found" in error_msg.lower():
            return False, "Spreadsheet or worksheet not found. Check your spreadsheet ID and worksheet name in secrets.toml"
        else:
            return False, f"Error saving to Google Sheets: {error_msg}"

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

afc_df, nfc_df = load_data()

conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read()
st.dataframe(df)

# User input section
col1, col2 = st.columns([2, 1])

with col1:
    user_name = st.text_input("Enter your name:", placeholder="e.g., John Doe")

with col2:
    # Show Google Sheets setup status
    gsheets_ok, gsheets_status = check_gsheets_setup()
    if gsheets_ok:
        st.success(gsheets_status)
    else:
        st.error(gsheets_status)
        with st.expander("🔧 Google Sheets Setup Guide"):
            st.markdown("""
            **To enable Google Sheets saving:**
            
            1. **Create a Service Account:**
               - Go to [Google Cloud Console](https://console.cloud.google.com/)
               - Create or select a project
               - Enable Google Sheets API
               - Create a Service Account and download JSON key
            
            2. **Share your Google Sheet:**
               - Share your Google Sheet with the service account email
               - Give it "Editor" permissions
            
            3. **Update secrets.toml:**
               - Add service account credentials to `.streamlit/secrets.toml`
               - Include spreadsheet ID and worksheet name
            
            **For now, predictions will be saved locally only.**
            """)

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
                    # Save to local CSV
                    updated_df = save_selection(user_name, selected_afc, selected_nfc)
                    
                    # Save to Google Sheets
                    with st.spinner("Saving to Google Sheets..."):
                        gsheets_success, gsheets_message = save_selection_to_gsheets(user_name, selected_afc, selected_nfc)
                        
                        if gsheets_success:
                            st.success(f"✅ Predictions saved for {user_name}!")
                            st.success(gsheets_message)
                        else:
                            st.success(f"✅ Predictions saved locally for {user_name}!")
                            st.warning(f"Google Sheets: {gsheets_message}")
                    
                    # st.rerun()
                except Exception as e:
                    st.error(f"Error saving predictions: {str(e)}")
                    
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