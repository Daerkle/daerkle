#!/bin/bash

# Start Scanner HTTP Server im Hintergrund
cd eodstockscans/site && python3 -m http.server 8080 &
SCANNER_PID=$!

# Start Streamlit App
streamlit run app.py

# Cleanup: Scanner-Server beenden wenn die Streamlit App beendet wird
kill $SCANNER_PID