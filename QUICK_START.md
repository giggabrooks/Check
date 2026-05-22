# Quick Start Guide

## Step 1: Install Dependencies

Open PowerShell in the project folder and run:

```powershell
pip install -r requirements.txt
```

## Step 2: Install Playwright Browsers

```powershell
python -m playwright install chromium
```

## Step 3: Prepare Your Excel File

Create an Excel file with your landline numbers. The file must have a column named "Landline":

Example: `landlines.xlsx`
```
Landline
2123456
2234567
0507890
```

## Step 4: Run the App

```powershell
streamlit run app.py
```

The app will automatically open in your browser (usually at http://localhost:8501)

## Step 5: Upload and Check

1. Click "Upload Excel file"
2. Select your file with landline numbers
3. Preview the data
4. Click "🚀 Start Validity Check"
5. Wait for processing to complete
6. Download your results

## What the App Does

✅ Reads your Excel file  
✅ Checks each number on the E&O website  
✅ Records if the account is Valid or Invalid  
✅ Extracts bill amount for valid accounts  
✅ Creates a results Excel file with all findings  
✅ Shows summary statistics  

## Expected Processing Time

- **10 numbers**: ~2-3 minutes
- **50 numbers**: ~5-7 minutes  
- **100 numbers**: ~10-15 minutes
- **1000+ numbers**: 30+ minutes

Processing time depends on internet speed and website response time.

## Questions?

Refer to README.md for detailed documentation.
