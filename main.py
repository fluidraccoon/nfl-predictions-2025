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
    mvp_data = pd.read_csv("categories/mvp.csv")
    dpoy_data = pd.read_csv("categories/dpoy.csv")
    oroy_data = pd.read_csv("categories/oroy.csv")
    return afc_data, nfc_data, mvp_data, dpoy_data, oroy_data

def load_selections():
    """Load existing selections or create empty DataFrame"""
    return pd.DataFrame(columns=['name', 'category', 'points', 'timestamp'])

def save_selection_to_gsheets(name, afc_winner, nfc_winner, sb_winner, mvp_winner, dpoy_winner, oroy_winner):
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
                existing_data = pd.DataFrame(columns=['name', 'category', 'points', 'timestamp'])
        except Exception as read_error:
            # If worksheet doesn't exist, create empty DataFrame
            existing_data = pd.DataFrame(columns=['name', 'category', 'points', 'timestamp'])
        
        # Remove existing entries for this user
        if not existing_data.empty and 'name' in existing_data.columns:
            existing_data = existing_data[existing_data['name'] != name]
        
        # Prepare new row data for each category
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_rows = []
        
        # Add AFC Winner row
        afc_points = afc_df[afc_df['selection'] == afc_winner]['points'].iloc[0]
        new_rows.append({
            'name': name,
            'category': 'AFC Winner',
            'points': afc_points,
            'timestamp': timestamp
        })
        
        # Add NFC Winner row
        nfc_points = nfc_df[nfc_df['selection'] == nfc_winner]['points'].iloc[0]
        new_rows.append({
            'name': name,
            'category': 'NFC Winner',
            'points': nfc_points,
            'timestamp': timestamp
        })
        
        # Add Super Bowl Winner row
        if sb_winner == afc_winner:
            sb_points = afc_df[afc_df['selection'] == sb_winner]['points'].iloc[0]
        else:
            sb_points = nfc_df[nfc_df['selection'] == sb_winner]['points'].iloc[0]
        new_rows.append({
            'name': name,
            'category': 'Super Bowl Winner',
            'points': sb_points,
            'timestamp': timestamp
        })
        
        # Add MVP Winner row
        mvp_points = mvp_df[mvp_df['selection'] == mvp_winner]['points'].iloc[0]
        new_rows.append({
            'name': name,
            'category': 'MVP',
            'points': mvp_points,
            'timestamp': timestamp
        })
        
        # Add DPOY Winner row
        dpoy_points = dpoy_df[dpoy_df['selection'] == dpoy_winner]['points'].iloc[0]
        new_rows.append({
            'name': name,
            'category': 'DPOY',
            'points': dpoy_points,
            'timestamp': timestamp
        })
        
        # Add OROY Winner row
        oroy_points = oroy_df[oroy_df['selection'] == oroy_winner]['points'].iloc[0]
        new_rows.append({
            'name': name,
            'category': 'OROY',
            'points': oroy_points,
            'timestamp': timestamp
        })
        
        # Add new rows to existing data
        new_rows_df = pd.DataFrame(new_rows)
        updated_data = pd.concat([existing_data, new_rows_df], ignore_index=True)
        
        # Write updated data back to Google Sheets
        conn.update(worksheet="predictions", data=updated_data)
        
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

def save_selection(name, afc_winner, nfc_winner, sb_winner, mvp_winner, dpoy_winner, oroy_winner):
    """Save user selection to CSV"""
    selections_df = load_selections()
    
    # Remove existing entries for this user
    if 'name' in selections_df.columns:
        selections_df = selections_df[selections_df['name'] != name]
    
    # Prepare new row data for each category
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_rows = []
    
    # Add AFC Winner row
    afc_points = afc_df[afc_df['selection'] == afc_winner]['points'].iloc[0]
    new_rows.append({
        'name': name,
        'category': 'AFC Winner',
        'points': afc_points,
        'timestamp': timestamp
    })
    
    # Add NFC Winner row
    nfc_points = nfc_df[nfc_df['selection'] == nfc_winner]['points'].iloc[0]
    new_rows.append({
        'name': name,
        'category': 'NFC Winner',
        'points': nfc_points,
        'timestamp': timestamp
    })
    
    # Add Super Bowl Winner row
    if sb_winner == afc_winner:
        sb_points = afc_df[afc_df['selection'] == sb_winner]['points'].iloc[0]
    else:
        sb_points = nfc_df[nfc_df['selection'] == sb_winner]['points'].iloc[0]
    new_rows.append({
        'name': name,
        'category': 'Super Bowl Winner',
        'points': sb_points,
        'timestamp': timestamp
    })
    
    # Add MVP Winner row
    mvp_points = mvp_df[mvp_df['selection'] == mvp_winner]['points'].iloc[0]
    new_rows.append({
        'name': name,
        'category': 'MVP',
        'points': mvp_points,
        'timestamp': timestamp
    })
    
    # Add DPOY Winner row
    dpoy_points = dpoy_df[dpoy_df['selection'] == dpoy_winner]['points'].iloc[0]
    new_rows.append({
        'name': name,
        'category': 'DPOY',
        'points': dpoy_points,
        'timestamp': timestamp
    })
    
    # Add OROY Winner row
    oroy_points = oroy_df[oroy_df['selection'] == oroy_winner]['points'].iloc[0]
    new_rows.append({
        'name': name,
        'category': 'OROY',
        'points': oroy_points,
        'timestamp': timestamp
    })
    
    # Add new rows to existing data
    new_rows_df = pd.DataFrame(new_rows)
    updated_df = pd.concat([selections_df, new_rows_df], ignore_index=True)
    
    return updated_df

afc_df, nfc_df, mvp_df, dpoy_df, oroy_df = load_data()

conn = st.connection("gsheets", type=GSheetsConnection)

df = conn.read()

# User input section
col1, col2 = st.columns([2, 1])

with col1:
    user_name = st.text_input("Enter your name:", placeholder="e.g., John Doe")

st.divider()

# Create tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🔴 AFC Winner",
    "🔵 NFC Winner", 
    "🏆 Super Bowl Winner",
    "🏅 MVP",
    "🛡️ DPOY",
    "⭐ OROY",
    "📝 Submit Predictions"
])

with tab1:
    st.header("AFC Conference Winner")
    
    # Sort AFC teams by points (lowest first), then alphabetically by team name
    afc_sorted = afc_df.sort_values(['points', 'selection'], ascending=[True, True])
    afc_options = ["-- Select a team --"]
    for _, row in afc_sorted.iterrows():
        # Format points to avoid unnecessary decimals
        points_display = f"{row['points']:g}"  # This removes trailing zeros
        afc_options.append(f"**{row['selection']}** - *{points_display} points*")
    
    selected_afc_raw = st.radio("Choose AFC Winner:", afc_options, key="afc_select")
    
    # Only set selected_afc if a real team is selected
    if selected_afc_raw != "-- Select a team --":
        selected_afc = selected_afc_raw.split(" - ")[0].replace("**", "")  # Remove markdown formatting
        points_str = selected_afc_raw.split(" - ")[1].replace("*", "").split(" ")[0]  # Remove markdown formatting
        points = float(points_str)
        # Format points to avoid unnecessary decimals
        points_display = f"{points:g}"
        st.success(f"**{selected_afc}** - *{points_display} points*")
    else:
        selected_afc = None
        st.info("Please select an AFC team")

with tab2:
    st.header("NFC Conference Winner")
    
    # Sort NFC teams by points (lowest first), then alphabetically by team name
    nfc_sorted = nfc_df.sort_values(['points', 'selection'], ascending=[True, True])
    nfc_options = ["-- Select a team --"]
    for _, row in nfc_sorted.iterrows():
        # Format points to avoid unnecessary decimals
        points_display = f"{row['points']:g}"  # This removes trailing zeros
        nfc_options.append(f"**{row['selection']}** - *{points_display} points*")
    
    selected_nfc_raw = st.radio("Choose NFC Winner:", nfc_options, key="nfc_select")
    
    # Only set selected_nfc if a real team is selected
    if selected_nfc_raw != "-- Select a team --":
        selected_nfc = selected_nfc_raw.split(" - ")[0].replace("**", "")  # Remove markdown formatting
        points_str = selected_nfc_raw.split(" - ")[1].replace("*", "").split(" ")[0]  # Remove markdown formatting
        points = float(points_str)
        # Format points to avoid unnecessary decimals
        points_display = f"{points:g}"
        st.success(f"**{selected_nfc}** - *{points_display} points*")
    else:
        selected_nfc = None
        st.info("Please select an NFC team")

with tab3:
    st.header("Super Bowl Winner")
    
    # Super Bowl selection can only be made if both AFC and NFC winners are selected
    if 'selected_afc' in locals() and selected_afc and 'selected_nfc' in locals() and selected_nfc:
        st.info("Choose the Super Bowl winner from your conference champions. You will get the following points on top of the previous points for winning the conference.")
        
        # Create Super Bowl options from the selected AFC and NFC winners
        sb_options = ["-- Select Super Bowl winner --"]
        
        # Add AFC winner option
        afc_points = afc_df[afc_df['selection'] == selected_afc]['points'].iloc[0]
        afc_points_display = f"{afc_points:g}"
        sb_options.append(f"**{selected_afc}** (AFC) - *{afc_points_display} points*")
        
        # Add NFC winner option  
        nfc_points = nfc_df[nfc_df['selection'] == selected_nfc]['points'].iloc[0]
        nfc_points_display = f"{nfc_points:g}"
        sb_options.append(f"**{selected_nfc}** (NFC) - *{nfc_points_display} points*")
        
        selected_sb_raw = st.radio("Choose Super Bowl Winner:", sb_options, key="sb_select")
        
        # Only set selected_sb if a real team is selected
        if selected_sb_raw != "-- Select Super Bowl winner --":
            selected_sb = selected_sb_raw.split(" (")[0].replace("**", "")  # Remove markdown formatting
            points_str = selected_sb_raw.split(" - ")[1].replace("*", "").split(" ")[0]  # Remove markdown formatting
            points = float(points_str)
            # Format points to avoid unnecessary decimals
            points_display = f"{points:g}"
            conference = "AFC" if selected_sb == selected_afc else "NFC"
            st.success(f"**{selected_sb}** ({conference}) - *{points_display} points*")
        else:
            selected_sb = None
            st.info("Please select a Super Bowl winner")
    else:
        selected_sb = None
        st.warning("⚠️ Please select both AFC and NFC winners first before choosing the Super Bowl winner.")
        
        missing_for_sb = []
        if 'selected_afc' not in locals() or not selected_afc:
            missing_for_sb.append("🔴 AFC Winner")
        if 'selected_nfc' not in locals() or not selected_nfc:
            missing_for_sb.append("🔵 NFC Winner")
        
        if missing_for_sb:
            st.write("Still needed:")
            for item in missing_for_sb:
                st.write(f"- {item}")

with tab4:
    st.header("MVP")
    
    # Sort MVP candidates by points (lowest first), then alphabetically by name
    mvp_sorted = mvp_df.sort_values(['points', 'selection'], ascending=[True, True])
    mvp_options = ["-- Select MVP --"]
    for _, row in mvp_sorted.iterrows():
        # Format points to avoid unnecessary decimals
        points_display = f"{row['points']:g}"  # This removes trailing zeros
        mvp_options.append(f"**{row['selection']}** - *{points_display} points*")
    
    selected_mvp_raw = st.radio("Choose MVP:", mvp_options, key="mvp_select")
    
    # Only set selected_mvp if a real player is selected
    if selected_mvp_raw != "-- Select MVP --":
        selected_mvp = selected_mvp_raw.split(" - ")[0].replace("**", "")  # Remove markdown formatting
        points_str = selected_mvp_raw.split(" - ")[1].replace("*", "").split(" ")[0]  # Remove markdown formatting
        points = float(points_str)
        # Format points to avoid unnecessary decimals
        points_display = f"{points:g}"
        st.success(f"**{selected_mvp}** - *{points_display} points*")
    else:
        selected_mvp = None
        st.info("Please select an MVP")

with tab5:
    st.header("DPOY (Defensive Player of the Year)")
    
    # Sort DPOY candidates by points (lowest first), then alphabetically by name
    dpoy_sorted = dpoy_df.sort_values(['points', 'selection'], ascending=[True, True])
    dpoy_options = ["-- Select DPOY --"]
    for _, row in dpoy_sorted.iterrows():
        # Format points to avoid unnecessary decimals
        points_display = f"{row['points']:g}"  # This removes trailing zeros
        dpoy_options.append(f"**{row['selection']}** - *{points_display} points*")
    
    selected_dpoy_raw = st.radio("Choose DPOY:", dpoy_options, key="dpoy_select")
    
    # Only set selected_dpoy if a real player is selected
    if selected_dpoy_raw != "-- Select DPOY --":
        selected_dpoy = selected_dpoy_raw.split(" - ")[0].replace("**", "")  # Remove markdown formatting
        points_str = selected_dpoy_raw.split(" - ")[1].replace("*", "").split(" ")[0]  # Remove markdown formatting
        points = float(points_str)
        # Format points to avoid unnecessary decimals
        points_display = f"{points:g}"
        st.success(f"**{selected_dpoy}** - *{points_display} points*")
    else:
        selected_dpoy = None
        st.info("Please select a DPOY")

with tab6:
    st.header("OROY (Offensive Rookie of the Year)")
    
    # Sort OROY candidates by points (lowest first), then alphabetically by name
    oroy_sorted = oroy_df.sort_values(['points', 'selection'], ascending=[True, True])
    oroy_options = ["-- Select OROY --"]
    for _, row in oroy_sorted.iterrows():
        # Format points to avoid unnecessary decimals
        points_display = f"{row['points']:g}"  # This removes trailing zeros
        oroy_options.append(f"**{row['selection']}** - *{points_display} points*")
    
    selected_oroy_raw = st.radio("Choose OROY:", oroy_options, key="oroy_select")
    
    # Only set selected_oroy if a real player is selected
    if selected_oroy_raw != "-- Select OROY --":
        selected_oroy = selected_oroy_raw.split(" - ")[0].replace("**", "")  # Remove markdown formatting
        points_str = selected_oroy_raw.split(" - ")[1].replace("*", "").split(" ")[0]  # Remove markdown formatting
        points = float(points_str)
        # Format points to avoid unnecessary decimals
        points_display = f"{points:g}"
        st.success(f"**{selected_oroy}** - *{points_display} points*")
    else:
        selected_oroy = None
        st.info("Please select an OROY")

with tab7:
    st.header("Submit Your Predictions")
    
    # Create predictions table
    predictions_data = []
    
    # Add AFC prediction
    if 'selected_afc' in locals() and selected_afc:
        afc_points = afc_df[afc_df['selection'] == selected_afc]['points'].iloc[0]
        afc_points_display = f"{afc_points:g}"
        predictions_data.append({
            "Category": "AFC Winner",
            "Prediction": selected_afc,
            "Points": afc_points_display
        })
    else:
        predictions_data.append({
            "Category": "AFC Winner", 
            "Prediction": "Not selected",
            "Points": "0"
        })
    
    # Add NFC prediction
    if 'selected_nfc' in locals() and selected_nfc:
        nfc_points = nfc_df[nfc_df['selection'] == selected_nfc]['points'].iloc[0]
        nfc_points_display = f"{nfc_points:g}"
        predictions_data.append({
            "Category": "NFC Winner",
            "Prediction": selected_nfc,
            "Points": nfc_points_display
        })
    else:
        predictions_data.append({
            "Category": "NFC Winner",
            "Prediction": "Not selected", 
            "Points": "0"
        })
    
    # Add Super Bowl prediction
    if 'selected_sb' in locals() and selected_sb:
        # Get points from the appropriate conference data
        if selected_sb == selected_afc:
            sb_points = afc_df[afc_df['selection'] == selected_sb]['points'].iloc[0]
        else:
            sb_points = nfc_df[nfc_df['selection'] == selected_sb]['points'].iloc[0]
        sb_points_display = f"{sb_points:g}"
        predictions_data.append({
            "Category": "Super Bowl Winner",
            "Prediction": selected_sb,
            "Points": sb_points_display
        })
    else:
        predictions_data.append({
            "Category": "Super Bowl Winner",
            "Prediction": "Not selected",
            "Points": "0"
        })
    
    # Add MVP prediction
    if 'selected_mvp' in locals() and selected_mvp:
        mvp_points = mvp_df[mvp_df['selection'] == selected_mvp]['points'].iloc[0]
        mvp_points_display = f"{mvp_points:g}"
        predictions_data.append({
            "Category": "MVP",
            "Prediction": selected_mvp,
            "Points": mvp_points_display
        })
    else:
        predictions_data.append({
            "Category": "MVP",
            "Prediction": "Not selected",
            "Points": "0"
        })
    
    # Add DPOY prediction
    if 'selected_dpoy' in locals() and selected_dpoy:
        dpoy_points = dpoy_df[dpoy_df['selection'] == selected_dpoy]['points'].iloc[0]
        dpoy_points_display = f"{dpoy_points:g}"
        predictions_data.append({
            "Category": "DPOY",
            "Prediction": selected_dpoy,
            "Points": dpoy_points_display
        })
    else:
        predictions_data.append({
            "Category": "DPOY",
            "Prediction": "Not selected",
            "Points": "0"
        })
    
    # Add OROY prediction
    if 'selected_oroy' in locals() and selected_oroy:
        oroy_points = oroy_df[oroy_df['selection'] == selected_oroy]['points'].iloc[0]
        oroy_points_display = f"{oroy_points:g}"
        predictions_data.append({
            "Category": "OROY",
            "Prediction": selected_oroy,
            "Points": oroy_points_display
        })
    else:
        predictions_data.append({
            "Category": "OROY",
            "Prediction": "Not selected",
            "Points": "0"
        })
    
    # Display the table
    predictions_df = pd.DataFrame(predictions_data)
    st.dataframe(predictions_df, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Submission section
    if user_name and 'selected_afc' in locals() and selected_afc and 'selected_nfc' in locals() and selected_nfc and 'selected_sb' in locals() and selected_sb and 'selected_mvp' in locals() and selected_mvp and 'selected_dpoy' in locals() and selected_dpoy and 'selected_oroy' in locals() and selected_oroy:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("💾 Save Predictions", type="primary", use_container_width=True):
                try:
                    # Save to local CSV
                    updated_df = save_selection(user_name, selected_afc, selected_nfc, selected_sb, selected_mvp, selected_dpoy, selected_oroy)
                    
                    # Save to Google Sheets
                    with st.spinner("Saving to Google Sheets..."):
                        gsheets_success, gsheets_message = save_selection_to_gsheets(user_name, selected_afc, selected_nfc, selected_sb, selected_mvp, selected_dpoy, selected_oroy)
                        
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
        st.warning("⚠️ Please enter your name and make all selections before submitting.")
        
        missing_items = []
        if not user_name:
            missing_items.append("👤 Your name")
        if 'selected_afc' not in locals() or not selected_afc:
            missing_items.append("🔴 AFC Winner")
        if 'selected_nfc' not in locals() or not selected_nfc:
            missing_items.append("🔵 NFC Winner")
        if 'selected_sb' not in locals() or not selected_sb:
            missing_items.append("🏆 Super Bowl Winner")
        if 'selected_mvp' not in locals() or not selected_mvp:
            missing_items.append("🏅 MVP")
        if 'selected_dpoy' not in locals() or not selected_dpoy:
            missing_items.append("🛡️ DPOY")
        if 'selected_oroy' not in locals() or not selected_oroy:
            missing_items.append("⭐ OROY")
        
        st.write("Missing:")
        for item in missing_items:
            st.write(f"- {item}")