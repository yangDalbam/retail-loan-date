import pandas as pd

file_path = r'retail-loan-data\data\온투업 기관투자 이후 개인신용대출 현황(수정).xlsx'
try:
    df = pd.read_excel(file_path)
    print("--- DataFrame Info ---")
    df.info()
    print("\n--- DataFrame Head ---")
    print(df.head())
    print("\n--- Unique Values in Categorical Columns ---")
    for col in df.select_dtypes(include=['object']).columns:
        print(f"[{col}] : {df[col].unique()}")
except Exception as e:
    print(f"Error reading file: {e}")
