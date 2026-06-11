"""
이 모듈은 온투업 개인신용대출 데이터를 분석하고 시각화 이미지를 생성하는 기능을 수행합니다.
주요 기능:
- 데이터 전처리 (결측치 처리, 형태 변환)
- 주요 통계 지표 추출 및 출력
- 10종 이상의 다양한 시각화 차트 생성 (images 폴더에 저장)
"""

import pandas as pd
import matplotlib.pyplot as plt
import koreanize_matplotlib
import os
import numpy as np
import io

# 폴더 생성
os.makedirs(r'retail-loan-data/images', exist_ok=True)
os.makedirs(r'retail-loan-data/report', exist_ok=True)

# 1. 데이터 로드 및 전처리
file_path = r'retail-loan-data\data\온투업 기관투자 이후 개인신용대출 현황(수정).xlsx'
df_raw = pd.read_excel(file_path, header=1)

# '시기' 컬럼명 변경 (첫 번째 열)
df_raw.rename(columns={df_raw.columns[0]: 'Date', df_raw.columns[1]: 'Item'}, inplace=True)

# 필요 없는 비고 컬럼 등 제거 (8번 인덱스 이후)
df_raw = df_raw.iloc[:, :8]

# Date 컬럼 결측치 앞의 값으로 채우기
df_raw['Date'] = pd.to_datetime(df_raw['Date']).ffill()

# 회사 컬럼명 추출
companies = ['PFCT', '어니스트AI', '한패스파이낸셜', '에잇퍼센트', '머니무브', '모우다']

# 데이터 길게 풀기 (Melt)
df_melted = df_raw.melt(id_vars=['Date', 'Item'], value_vars=companies, var_name='Company', value_name='Value')

# Value의 '-' 및 결측치를 0으로 변경 후 수치형 변환
df_melted['Value'] = pd.to_numeric(df_melted['Value'].replace('-', 0).fillna(0))

# 'Item' 컬럼의 값 정리 (공백 제거)
df_melted['Item'] = df_melted['Item'].str.strip()

# 피벗해서 각 항목을 컬럼으로 (Date, Company, 대출잔액, 연체금액, 연체율, 매각 금액)
df = df_melted.pivot_table(index=['Date', 'Company'], columns='Item', values='Value', aggfunc='sum').reset_index()

# 컬럼명 정리
df.columns.name = None

# 통계 출력용 버퍼
stats_out = io.StringIO()

def print_stat(text):
    stats_out.write(text + "\n")
    print(text)

print_stat("=== 1. 기본 정보 ===")
buf = io.StringIO()
df.info(buf=buf)
print_stat(buf.getvalue())

print_stat("\n=== 2. 상위/하위 5개행 ===")
print_stat("Head:\n" + df.head().to_string())
print_stat("Tail:\n" + df.tail().to_string())

print_stat(f"\n=== 3. 전체 행렬 수: {df.shape} ===")
print_stat(f"=== 4. 중복 데이터 수: {df.duplicated().sum()} ===")

print_stat("\n=== 5. 기술 통계 (수치형) ===")
print_stat(df.describe().to_string())

print_stat("\n=== 6. 기술 통계 (범주형) ===")
print_stat(df.describe(include=['object', 'datetime64']).to_string())

# 범주형 빈도
print_stat("\n=== 회사별 데이터 빈도 ===")
print_stat(df['Company'].value_counts().to_string())

# 피봇/교차표 출력
print_stat("\n=== 회사별 대출잔액 평균 피봇 ===")
print_stat(df.pivot_table(index='Company', values='개인신용 대출잔액', aggfunc='mean').to_string())
print_stat("\n=== 연월별 전체 연체금액 합산 ===")
print_stat(df.pivot_table(index='Date', values='연체금액', aggfunc='sum').to_string())


# 시각화 시작
# 1. 회사별 대출잔액 변화 추이 (선 그래프)
plt.figure(figsize=(10, 6))
for comp in companies:
    temp = df[df['Company'] == comp]
    plt.plot(temp['Date'], temp['개인신용 대출잔액'], marker='o', label=comp)
plt.title("회사별 대출잔액 변화 추이")
plt.xlabel("시기")
plt.ylabel("대출잔액")
plt.legend()
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_1_loan_balance_trend.png')
plt.close()

# 2. 2026년 5월 기준 회사별 대출잔액 비중 (파이 차트)
df_2606 = df[df['Date'] == '2026-05-01']
# 대출잔액 0보다 큰 경우만
df_2606_pos = df_2606[df_2606['개인신용 대출잔액'] > 0]
plt.figure(figsize=(8, 8))
plt.pie(df_2606_pos['개인신용 대출잔액'], labels=df_2606_pos['Company'], autopct='%1.1f%%', startangle=140)
plt.title("2026년 5월 기준 대출잔액 비중")
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_2_loan_balance_pie.png')
plt.close()

# 3. 2026년 5월 기준 회사별 연체금액 (막대 차트)
plt.figure(figsize=(10, 6))
plt.bar(df_2606['Company'], df_2606['연체금액'], color='salmon')
plt.title("2026년 5월 기준 회사별 연체금액")
plt.xlabel("회사명")
plt.ylabel("연체금액")
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_3_delay_amount_bar.png')
plt.close()

# 4. 회사별 연체율 변동 추이 (선 그래프)
plt.figure(figsize=(10, 6))
for comp in companies:
    temp = df[df['Company'] == comp]
    plt.plot(temp['Date'], temp['연체율'] * 100, marker='s', label=comp)
plt.title("회사별 연체율 변동 추이 (%)")
plt.xlabel("시기")
plt.ylabel("연체율(%)")
plt.legend()
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_4_delay_rate_trend.png')
plt.close()

# 5. 6개사 평균 연체율 추이 (선 그래프)
mean_delay = df.groupby('Date')['연체율'].mean().reset_index()
plt.figure(figsize=(10, 6))
plt.plot(mean_delay['Date'], mean_delay['연체율'] * 100, marker='D', color='purple')
plt.title("6개사 평균 연체율 변동 추이 (%)")
plt.xlabel("시기")
plt.ylabel("평균 연체율(%)")
plt.grid(True, linestyle='--', alpha=0.6)
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_5_avg_delay_rate.png')
plt.close()

# 6. 연체금액 매각을 통한 전체 연체율 하락 효과 비교 (전/후)
sum_df = df.groupby('Date')[['개인신용 대출잔액', '연체금액', '매각 금액']].sum().reset_index()
sum_df['실제연체율'] = sum_df['연체금액'] / sum_df['개인신용 대출잔액'] * 100
sum_df['매각전연체율(가상)'] = (sum_df['연체금액'] + sum_df['매각 금액']) / sum_df['개인신용 대출잔액'] * 100

plt.figure(figsize=(10, 6))
plt.plot(sum_df['Date'], sum_df['매각전연체율(가상)'], marker='^', linestyle='--', label='매각 전 가상 연체율', color='red')
plt.plot(sum_df['Date'], sum_df['실제연체율'], marker='o', label='실제 연체율(매각 후)', color='blue')
plt.title("연체채권 매각을 통한 전체 연체율 하락 효과 (%)")
plt.xlabel("시기")
plt.ylabel("연체율(%)")
plt.legend()
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_6_delay_rate_reduction.png')
plt.close()

# 7. 각 회사별 월별 매각 금액 (막대 차트)
pivot_sell = df.pivot_table(index='Date', columns='Company', values='매각 금액', aggfunc='sum')
pivot_sell.index = pivot_sell.index.strftime('%Y-%m')
pivot_sell.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='Set2')
plt.title("월별 회사별 연체채권 매각 금액")
plt.xlabel("시기 (년-월)")
plt.ylabel("매각 금액")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_7_sell_amount_bar.png')
plt.close()

# 8. 대출잔액과 연체금액 간의 산점도 (Scatter)
plt.figure(figsize=(8, 6))
plt.scatter(df['개인신용 대출잔액'], df['연체금액'], alpha=0.7, color='teal')
plt.title("대출잔액과 연체금액 산점도")
plt.xlabel("개인신용 대출잔액")
plt.ylabel("연체금액")
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_8_scatter_balance_delay.png')
plt.close()

# 9. 회사별 연체금액 박스플롯 (Box plot)
plt.figure(figsize=(10, 6))
df.boxplot(column='연체금액', by='Company', grid=False, figsize=(10, 6))
plt.title("회사별 연체금액 분포")
plt.suptitle("")
plt.xlabel("회사명")
plt.ylabel("연체금액")
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_9_delay_boxplot.png')
plt.close()

# 10. 회사별 연체율 분포 박스플롯 (Box plot)
plt.figure(figsize=(10, 6))
df.boxplot(column='연체율', by='Company', grid=False, figsize=(10, 6))
plt.title("회사별 연체율 분포")
plt.suptitle("")
plt.xlabel("회사명")
plt.ylabel("연체율")
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_10_delay_rate_boxplot.png')
plt.close()

# 11. 회사 빈도수 차트 (범주형)
plt.figure(figsize=(8, 6))
df['Company'].value_counts().plot(kind='bar', color='orange')
plt.title("데이터 내 회사별 출현 빈도수")
plt.xlabel("회사명")
plt.ylabel("빈도수")
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_11_company_freq.png')
plt.close()

# 12. 전체 연체금액 대비 회사별 비중 파이 (전 기간)
total_delay = df.groupby('Company')['연체금액'].sum()
total_delay = total_delay[total_delay > 0]
plt.figure(figsize=(8, 8))
plt.pie(total_delay, labels=total_delay.index, autopct='%1.1f%%', startangle=90)
plt.title("전체 기간 합산 회사별 연체금액 발생 비중")
plt.tight_layout()
plt.savefig('retail-loan-data/images/chart_12_total_delay_pie.png')
plt.close()

# 결과를 텍스트로 저장
with open('retail-loan-data/src/stats_output.txt', 'w', encoding='utf-8') as f:
    f.write(stats_out.getvalue())

print("완료")
