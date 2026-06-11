import pandas as pd

file_path = r'retail-loan-data\data\온투업 기관투자 이후 개인신용대출 현황(수정).xlsx'
try:
    df = pd.read_excel(file_path)
    with open(r'retail-loan-data\data\data_head.txt', 'w', encoding='utf-8') as f:
        f.write("Columns:\n")
        f.write(str(df.columns.tolist()) + "\n\n")
        f.write("Head (first 10 rows):\n")
        f.write(df.head(10).to_string() + "\n")
except Exception as e:
    with open(r'retail-loan-data\data\data_head.txt', 'w', encoding='utf-8') as f:
        f.write(f"Error: {e}")
