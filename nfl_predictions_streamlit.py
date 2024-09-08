import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

st.title("2024 NFL Predictions 🏈")

# define the scope
scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

# add credentials to the account
creds = ServiceAccountCredentials.from_json_keyfile_name('add_json_file_here.json', scope)

# authorize the clientsheet 
client = gspread.authorize(creds)