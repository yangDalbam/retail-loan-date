"""
이 모듈은 온투업 개인신용대출 현황 엑셀 데이터를 읽어들여
대시보드의 Chart.js 에서 사용할 수 있는 JSON(data.js) 형태로 변환하는 기능을 수행합니다.
"""

import pandas as pd
import json
import os

def clean_value(val):
    if pd.isna(val) or val == '-' or val == '':
        return 0
    try:
        return float(val)
    except:
        return 0

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    file_path = os.path.join(base_dir, 'data', '온투업 기관투자 이후 개인신용대출 현황(수정).xlsx')
    
    # 엑셀 로드 (header=1 사용하면 '시기', '항목' 등이 컬럼이 됨)
    df = pd.read_excel(file_path, header=1)
    
    # 필요한 컬럼 8개만 추출
    df = df.iloc[:, 0:8]
    df.columns = ['시기', '항목', 'PFCT', '어니스트AI', '한패스파이낸셜', '에잇퍼센트', '머니무브', '모우다']
    
    # 시기 컬럼 전방 채우기
    df['시기'] = df['시기'].ffill()
    
    # 항목이 NaN인 행 제거
    df = df.dropna(subset=['항목'])
    
    # 시기 컬럼을 datetime으로 변환 시도, 안 되면 NaT
    df['시기'] = pd.to_datetime(df['시기'], errors='coerce')
    
    # 변환 실패한 시기 행은 필터링 (합계 행 등 버리기 위함)
    df = df.dropna(subset=['시기'])
    
    # 시기를 'YYYY-MM' 텍스트로 변환
    df['시기_str'] = df['시기'].dt.strftime('%Y-%m')
    
    companies = ['PFCT', '어니스트AI', '한패스파이낸셜', '에잇퍼센트', '머니무브', '모우다']
    
    # 항목명 매핑 (엑셀의 항목명에 공백이나 오타가 있을 수 있으므로)
    item_mapping = {
        '개인신용 대출잔액': '개인신용 대출잔액',
        '개인신용 대출 잔액': '개인신용 대출잔액',
        '연체금액': '연체금액',
        '연체율': '연체율',
        '매각 금액': '매각 금액',
        '매각금액': '매각 금액'
    }
    
    items = ['개인신용 대출잔액', '연체금액', '연체율', '매각 금액']
    
    labels = sorted(list(df['시기_str'].unique()))
    
    result = {
        'labels': labels,
        'companies': companies,
        'data': {item: {company: [] for company in companies} for item in items}
    }
    
    for label in labels:
        month_data = df[df['시기_str'] == label]
        for item in items:
            # 매핑된 항목명으로 데이터 찾기
            found = False
            for _, row in month_data.iterrows():
                row_item = str(row['항목']).strip()
                # mapped item name
                mapped = item_mapping.get(row_item, row_item)
                if mapped == item:
                    found = True
                    for company in companies:
                        result['data'][item][company].append(clean_value(row[company]))
                    break
            if not found:
                # 데이터가 없는 경우 0 채우기
                for company in companies:
                    result['data'][item][company].append(0)
                    
    # JS 파일로 출력
    js_content = f"const dashboardData = {json.dumps(result, ensure_ascii=False, indent=2)};"
    
    output_path = os.path.join(base_dir, 'report', 'data.js')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"변환된 레이블 수: {len(labels)}")
    print(f"데이터가 성공적으로 {output_path}에 저장되었습니다.")

if __name__ == '__main__':
    main()
