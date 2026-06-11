"""
이 모듈은 온투업 개인신용대출 데이터를 분석하여 핵심 KPI 지표(전월 대비 증감 포함)를 계산하고,
Jinja2 템플릿 엔진을 통해 21가지의 고도화된 개선사항이 반영된 프리미엄 HTML 대시보드를 자동 생성합니다.
"""

import pandas as pd
import os
import datetime
from jinja2 import Environment, FileSystemLoader

def format_currency(val):
    if val == 0: return "0원"
    if val >= 1_000_000_000: return f"{val / 1_000_000_000:,.1f}억 원"
    elif val >= 1_000_000: return f"{val / 1_000_000:,.1f}백만 원"
    return f"{val:,.0f}원"

def get_mom_class(diff, is_bad=False):
    if diff > 0: return "positive" if not is_bad else "negative"
    elif diff < 0: return "negative" if not is_bad else "positive"
    return "neutral"

def main():
    # 1. 데이터 로드 및 전처리
    file_path = r'retail-loan-data\data\온투업 기관투자 이후 개인신용대출 현황(수정).xlsx'
    df_raw = pd.read_excel(file_path, header=1)
    df_raw.rename(columns={df_raw.columns[0]: 'Date', df_raw.columns[1]: 'Item'}, inplace=True)
    df_raw = df_raw.iloc[:, :8]
    df_raw['Date'] = pd.to_datetime(df_raw['Date']).ffill()

    companies = ['PFCT', '어니스트AI', '한패스파이낸셜', '에잇퍼센트', '머니무브', '모우다']
    df_melted = df_raw.melt(id_vars=['Date', 'Item'], value_vars=companies, var_name='Company', value_name='Value')
    df_melted['Value'] = pd.to_numeric(df_melted['Value'].replace('-', 0).fillna(0))
    df_melted['Item'] = df_melted['Item'].str.strip()
    df = df_melted.pivot_table(index=['Date', 'Company'], columns='Item', values='Value', aggfunc='sum').reset_index()
    df.columns.name = None

    # 2. 기준 월 데이터 추출 (당월: 2026-05, 전월: 2026-04)
    df_curr = df[df['Date'] == '2026-05-01']
    df_prev = df[df['Date'] == '2026-04-01']

    # 원시 데이터 테이블용 HTML 생성
    df_table = df_curr.drop(columns=['Date']).copy()
    # 통화 포맷팅
    for col in ['개인신용 대출잔액', '연체금액', '매각 금액']:
        if col in df_table.columns:
            df_table[col] = df_table[col].apply(lambda x: f"{x:,.0f}원")
    if '연체율' in df_table.columns:
        df_table['연체율'] = df_table['연체율'].apply(lambda x: f"{x*100:.2f}%")
        
    raw_data_html = df_table.to_html(index=False, classes='', border=0)

    # 6개사 각 회사별 전체 원시 데이터 생성
    company_data_htmls = {}
    companies = df['Company'].unique()
    for company in companies:
        df_company = df[df['Company'] == company].sort_values('Date', ascending=False).copy()
        for col in ['개인신용 대출잔액', '연체금액', '매각 금액']:
            if col in df_company.columns:
                df_company[col] = df_company[col].apply(lambda x: f"{int(x):,}")
        if '개인신용 연체율' in df_company.columns:
            df_company['개인신용 연체율'] = df_company['개인신용 연체율'].apply(lambda x: f"{x:.2f}%")
        company_data_htmls[company] = df_company.to_html(index=False, classes='', border=0)

    # 3. 핵심 KPI 및 MoM(증감률) 계산
    def calc_metrics(d):
        loan = d['개인신용 대출잔액'].sum()
        delay = d['연체금액'].sum()
        sell = d['매각 금액'].sum()
        rate = (delay / loan * 100) if loan > 0 else 0
        return loan, delay, sell, rate

    c_loan, c_delay, c_sell, c_rate = calc_metrics(df_curr)
    p_loan, p_delay, p_sell, p_rate = calc_metrics(df_prev)

    diff_loan = c_loan - p_loan
    diff_delay = c_delay - p_delay
    diff_sell = c_sell - p_sell
    diff_rate = c_rate - p_rate

    kpi = {
        'loan': {
            'val': c_loan, 'str': format_currency(c_loan), 
            'mom_val': diff_loan, 'mom_str': format_currency(abs(diff_loan)), 'mom_class': get_mom_class(diff_loan, is_bad=False)
        },
        'delay': {
            'val': c_delay, 'str': format_currency(c_delay), 
            'mom_val': diff_delay, 'mom_str': format_currency(abs(diff_delay)), 'mom_class': get_mom_class(diff_delay, is_bad=True)
        },
        'sell': {
            'val': c_sell, 'str': format_currency(c_sell), 
            'mom_val': diff_sell, 'mom_str': format_currency(abs(diff_sell)), 'mom_class': get_mom_class(diff_sell, is_bad=False)
        },
        'rate': {
            'val': c_rate, 'str': f"{c_rate:.2f}%", 
            'mom_val': diff_rate, 'mom_str': f"{abs(diff_rate):.2f}", 'mom_class': get_mom_class(diff_rate, is_bad=True)
        }
    }

    # 4. 인사이트 및 카테고리별 차트 정의
    insights = {
        'positive': [
            '<strong>1. 대형사의 리스크 관리 역량 입증:</strong> PFCT와 어니스트AI 등 선두 그룹은 잔액을 늘리면서도 연체율을 시장 최저 수준으로 방어해내며, 우수한 신용평가 모형(CSS) 작동을 입증했습니다.',
            '<strong>2. 연체채권 매각 시장의 활성화:</strong> 다수의 업체가 연체채권을 매각하여 유동성을 확보하고 부실자산을 현금화하는 등 재무 건전성 관리를 위한 유효한 수단이 정착되었습니다.'
        ],
        'negative': [
            '<strong>1. 소형 업체의 심각한 건전성 위기:</strong> 모우다의 연체율은 의료진 신용대출이라는 비즈니스 모델 한계로 인한 성장 정체 상황 탓에 압도적 1위(약 20%대)를 기록 중입니다. 모우다는 매각 대신 법정 소송 등을 통한 회수 전략을 펼치고 있습니다.',
            '<strong>2. 연체율 상승 트렌드:</strong> 시장 평균 연체율이 2026년 1월을 기점으로 서서히 우상향하고 있어, 잠재적 부실 규모 증가에 대한 경고 신호로 받아들여야 합니다.'
        ]
    }

    charts_all = {
        'chart_1_loan_balance_trend.png': {'title': '회사별 대출잔액 변화 추이', 'desc': '이 그래프는 2026년 1월부터 5월까지 온투업 6개사의 개인신용 대출잔액 변동 추이를 시계열로 나타내고 있습니다. 데이터를 분석해 보면 PFCT와 어니스트AI의 대출잔액이 꾸준한 우상향 곡선을 그리며 전체 성장을 견인하고 있음을 확인할 수 있습니다. 특히 PFCT는 매월 안정적인 잔액 증가폭을 기록하며 시장 내 잔액 기준 선두를 유지하고 있으며, 어니스트AI 역시 이에 준하는 성장세를 보이며 2위 그룹을 형성하고 있습니다. 한편 한패스파이낸셜과 에잇퍼센트는 완만한 증가세를 보이며 중위권 그룹의 잔액 규모를 일정하게 유지하고 있습니다. 모우다와 머니무브의 경우 타사 대비 잔액 규모가 상대적으로 작게 나타나고 있으며, 해당 기간 동안 잔액의 변동폭이 크지 않은 보합세를 나타냅니다. 결과적으로 온투업 개인신용대출 시장은 대출잔액 기준으로 상위 2개사에 자산이 집중되는 경향을 보이고 있으며, 각 회사의 영업 전략 및 대출 취급 규모에 따라 잔액의 성장 속도에 뚜렷한 차이가 발생하고 있음을 데이터를 통해 객관적으로 확인할 수 있습니다.'},
        'chart_2_loan_balance_pie.png': {'title': '2026년 5월 기준 대출잔액 비중', 'desc': '2026년 5월 말 기준 6개사의 개인신용 대출잔액을 원형 그래프로 구성하여 시장 내 비중을 도식화한 자료입니다. 전체 대출잔액을 100%로 환산했을 때, 가장 두드러진 특징은 PFCT와 어니스트AI 두 업체가 차지하는 비중의 합이 전체의 절반 이상을 기록하고 있다는 점입니다. 구체적으로 PFCT가 단일 업체 중 가장 높은 비율을 차지하고 있으며, 이어서 어니스트AI가 두 번째로 큰 비중을 확보하고 있습니다. 중위권인 한패스파이낸셜과 에잇퍼센트 역시 유의미한 수준의 잔액 비중을 기록하며 시장 점유율의 한 축을 담당하고 있습니다. 반면 모우다와 머니무브가 차지하는 대출잔액 비중은 전체 시장 대비 상대적으로 적은 비율에 머무르고 있습니다. 이러한 데이터 분포는 현재 온투업 개인신용대출 시장의 자산이 특정 상위 업체들에게 높은 비율로 편중되어 구성되어 있음을 객관적으로 나타냅니다. 각 사의 자산 운용 규모와 대출 취급 여력이 점유율이라는 수치로 명확히 나뉘어 있으며, 이는 업계 전반의 자금 배분 구조를 파악하는 기초 자료로 활용될 수 있습니다.'},
        'chart_3_delay_amount_bar.png': {'title': '회사별 연체금액 비교', 'desc': '본 막대그래프는 6개사 각각의 연체금액 절대 수치를 상호 비교하여 보여줍니다. 분석 결과, 대출잔액 비중이 상대적으로 적게 나타났던 모우다가 연체금액의 절대 규모 측면에서는 6개사 중 가장 높은 수치를 기록하고 있는 것으로 확인되었습니다. 모우다는 의료진 등 특정 차주군을 대상으로 한 신용대출을 주로 취급하고 있으며, 이러한 특화된 대출 자산에서 연체가 집중적으로 집계되고 있습니다. 반면 대출잔액 비중의 과반을 차지하는 상위 대형사들(PFCT, 어니스트AI 등)의 경우, 보유 중인 대출잔액 규모 대비 상대적으로 낮은 수준의 연체금액을 유지하고 있는 것으로 나타났습니다. 이는 각 사가 보유한 대출 자산의 특성, 차주 구성, 그리고 신용평가 및 채권 관리 프로세스의 차이가 연체금액이라는 결과 수치에 다르게 반영되고 있음을 보여줍니다. 따라서 전체 대출잔액 규모와 연체금액 규모가 반드시 비례하지 않으며, 개별 회사의 대출 포트폴리오 및 자체적인 자산 관리 현황에 따라 연체 발생 규모에 뚜렷한 편차가 존재함을 실제 데이터를 통해 객관적으로 관찰할 수 있습니다.'},
        'chart_4_delay_rate_trend.png': {'title': '회사별 연체율 변동 추이', 'desc': '이 시계열 그래프는 2026년 1월부터 5월까지 각 회사의 월별 연체율(연체금액/대출잔액) 추이를 개별적으로 추적한 결과입니다. 데이터를 살펴보면 PFCT, 어니스트AI, 한패스파이낸셜, 에잇퍼센트, 머니무브 등 5개사의 연체율은 해당 기간 동안 큰 변동 없이 낮은 한 자릿수 수준에서 안정적으로 유지되고 있습니다. 이들은 매월 일정한 수준 내에서 연체율 지표를 관리하고 있으며, 잔액의 증가와 관계없이 비율 자체는 보합세 내지 소폭 하락의 안정적인 곡선을 그립니다. 대조적으로 모우다의 연체율은 조사 기간 내내 다른 5개사와 뚜렷하게 구별되는 높은 수치(약 20% 내외)를 기록하고 있습니다. 이는 앞서 확인한 모우다의 높은 절대 연체금액과 정체된 대출잔액이 수식적으로 반영된 결과로, 타사 대비 연체율 지표가 상단 구간에 머무르고 있음을 보여줍니다. 이처럼 기업별 연체율 그래프의 궤적이 상이하게 나타나는 현상은 각 사의 신규 대출 취급량 및 누적 연체 자산의 처리 속도가 상호 다르게 작용하고 있음을 수치적으로 증명하는 객관적인 근거가 됩니다.'},
        'chart_5_avg_delay_rate.png': {'title': '6개사 평균 연체율 추이', 'desc': '온투업 6개사의 데이터를 통합하여 산출한 전체 가중평균 연체율의 월별 변동 추이를 시각화한 차트입니다. 개별 기업의 단순 산술 평균이 아닌 전체 대출잔액 대비 전체 연체금액의 비율을 나타내어 시장 전반의 평균적인 건전성 지표를 보여줍니다. 그래프를 분석해 보면 2026년 초반 일정 수준을 유지하던 평균 연체율이 시간이 지남에 따라 완만하게 상승하는 추세로 전환되었음을 관찰할 수 있습니다. 이는 특정 업체의 단일 요인이라기보다는, 시장을 구성하는 6개사 전체 대출 자산의 총합에서 연체금액의 비율이 점진적으로 증가하고 있음을 통계적으로 나타냅니다. 거시 경제 지표의 변동성이나 전반적인 차주 상환 능력의 변화 등이 시장 전체의 데이터 수치로 일정 부분 반영되었을 가능성을 보여주는 결과입니다. 각 사는 개별적인 연체율 통계 외에도 이러한 시장 전체의 평균 연체율 추이를 참고 지표로 삼아 자사의 건전성 지표가 업계 평균 대비 어느 정도의 수준에 위치하고 있는지 객관적으로 파악하고 대출 취급 심사 등에 기초 데이터로 활용할 수 있습니다.'},
        'chart_8_scatter_balance_delay.png': {'title': '대출잔액과 연체금액 산점도', 'desc': '각 회사의 대출잔액을 X축으로, 연체금액을 Y축으로 설정하여 6개사의 위치를 산점도로 도식화한 분석 자료입니다. 이 그래프를 통해 대출 규모와 연체 규모 간의 객관적인 상관관계를 시각적으로 파악할 수 있습니다. 산점도의 분포를 살펴보면, 대출잔액이 큰 대형사(PFCT, 어니스트AI 등)의 경우 Y축인 연체금액 수치는 비교적 낮은 하단에 군집하여 위치하고 있습니다. 반대로 X축의 대출잔액이 적은 특정 업체(모우다)의 경우 Y축인 연체금액 수치가 그래프 상단에 단독으로 높게 위치하는 특이점을 보입니다. 일반적으로 대출 규모가 커지면 연체금액도 비례하여 증가할 것이라는 양(+)의 상관관계 대신, 본 데이터셋에서는 대출잔액이 큰 업체가 낮은 연체액을, 대출잔액이 적은 업체가 높은 연체액을 기록하는 역(-)의 상관관계에 가까운 분포 특성이 관찰됩니다. 이는 온투업계 내 각 회사의 자산 포트폴리오 특성, 주력 대출 상품군, 그리고 자체적인 여신 심사 및 사후 관리 시스템의 차이가 데이터 상에 명확한 위치적 편차로 반영되고 있음을 보여줍니다.'},
        'chart_6_delay_rate_reduction.png': {'title': '매각을 통한 연체율 하락 효과', 'desc': '이 자료는 부실채권 매각 전과 매각 후의 연체율 지표 차이를 정량적으로 분석하여 비교한 것입니다. 각 업체가 외부 기관에 연체채권을 매각하게 되면, 대차대조표 상의 연체금액이 감소하여 수학적으로 공시되는 연체율 지표가 하락하게 됩니다. 데이터를 확인해 보면, 이러한 매각 처리를 통해 각 사의 명목 연체율이 평균적으로 일정 퍼센트포인트(p) 인하되는 수치적 효과가 일관되게 나타나고 있습니다. 매각 전 연체금액이 높았던 업체의 경우 매각을 통한 지표 하락폭이 더욱 가시적으로 나타나며, 상대적으로 연체율이 낮았던 대형사들 또한 매각을 통해 지표를 한 자릿수 초반으로 관리하는 데 효과를 거두고 있음을 알 수 있습니다. 이 분석은 공시된 최종 연체율 수치뿐만 아니라, 채권 매각이라는 사후 관리 절차가 지표에 미치는 계량적 영향을 객관적으로 분리하여 산출함으로써, 각 사가 연체 지표를 어떤 방식으로 관리하고 통제하고 있는지에 대한 사실적인 데이터 구조를 이해하는 데 중요한 참고 자료를 제공합니다.'},
        'chart_7_sell_amount_bar.png': {'title': '월별 회사별 매각 금액 추이', 'desc': '각 회사가 월별로 실행한 부실채권 매각 규모를 누적 막대그래프 형태로 시간 순으로 나타낸 자료입니다. 월별 매각 금액의 추이를 객관적으로 살펴보면, 연중 매월 고르게 매각이 일어난다기보다는 특정 월이나 분기 말에 매각 규모가 일시적으로 집중되는 데이터 패턴이 관찰됩니다. 특히 잔액 규모가 큰 상위 업체들의 경우 특정 시점에 비교적 큰 규모의 매각이 이루어지는 경우가 확인되며, 이는 각 사의 정기적인 부실채권 정리 일정이나 결산기 전후의 자산 건전성 관리 프로세스에 따른 결과로 해석됩니다. 반면 일부 소형 업체의 경우 이러한 정기적인 매각 기록이 적거나 매각 규모 자체가 작게 나타나고 있어, 채권의 사후 회수 및 매각을 처리하는 회사별 내부 방침에 뚜렷한 차이가 존재함을 데이터를 통해 파악할 수 있습니다. 이 그래프는 각 사의 연체율이 특정 시점에 갑자기 하락하는 현상을 매각 금액 데이터와 교차 검증하여, 지표 변동의 수치적 근거를 명확하게 설명해 주는 중요한 현황 파악 용도로 활용됩니다.'},
        'chart_9_delay_boxplot.png': {'title': '회사별 연체금액 박스플롯', 'desc': '6개사 각각의 연체금액 월별 변동폭을 통계적 도구인 박스플롯(Box Plot)으로 시각화하여 데이터의 분산 정도를 객관적으로 측정한 그래프입니다. 데이터를 살펴보면 PFCT, 어니스트AI 등 대부분의 회사는 박스의 상하 폭이 매우 좁게 나타나며 이상치(Outlier)도 거의 관찰되지 않습니다. 이는 해당 기업들의 월별 연체금액 규모가 일정한 범위 내에서 매우 안정적으로 집계되고 있음을 수학적으로 증명합니다. 반면, 데이터 상 유일하게 모우다의 박스 크기가 상하로 길게 뻗어 있으며 중앙값(Median)의 위치 또한 타사 대비 현저히 높은 위치에 분포하고 있습니다. 이는 모우다의 연체금액 수치가 평균적으로 높을 뿐만 아니라, 특정 시점마다 연체 발생액의 수치적 변동폭(분산)이 상당히 크게 나타나고 있음을 통계적으로 보여주는 사실적인 지표입니다. 이처럼 각 사별로 연체금액 데이터가 갖는 통계적 특성 및 산포도가 전혀 다른 분포 형태를 띠고 있음을 통해, 개별 기업의 대출 자산이 보여주는 데이터의 성향을 객관적이고 다각적으로 평가할 수 있습니다.'},
        'chart_10_delay_rate_boxplot.png': {'title': '회사별 연체율 분포 박스플롯', 'desc': '연체금액의 절대 수치뿐만 아니라, 대출잔액 대비 연체율의 분포를 박스플롯으로 재구성하여 각 사의 지표 변동성을 측정한 자료입니다. 5개사의 경우 연체율 박스플롯이 Y축 최하단(0%~5% 구간)에 매우 좁게 위치하여 일관된 분포를 보이고 있습니다. 이는 해당 기업들이 취급하는 전체 여신 규모가 증가하거나 변동함에도 불구하고 비율로서의 연체 지표가 거의 일정한 수치로 산출되고 있음을 객관적으로 나타냅니다. 반대로 모우다의 연체율 박스플롯은 Y축 20% 내외의 상단에 위치하며 다른 회사들의 데이터 분포와는 통계적으로 완전히 분리된 별도의 군집을 형성하고 있습니다. 박스 상단과 하단의 수염(Whisker) 길이도 상대적으로 길게 형성되어, 월별 연체율 지표의 산출값이 비교적 넓은 범위에서 변동하고 있음을 수치적으로 보여줍니다. 이 그래프는 전체 대출잔액 중 부실 채권이 차지하는 비중의 변동성이 기업별로 어떻게 군집화되어 있는지, 특정 업체와 타 업체 그룹 간의 데이터 분포 상 편차가 어느 정도 규모로 벌어져 있는지를 사실적으로 기술합니다.'}
    }

    # 카테고리별 차트 그룹핑
    chart_groups = {
        '대출잔액 및 시장 점유율 현황': [
            {'file': 'chart_1_loan_balance_trend.png', **charts_all['chart_1_loan_balance_trend.png']},
            {'file': 'chart_2_loan_balance_pie.png', **charts_all['chart_2_loan_balance_pie.png']}
        ],
        '건전성 리스크 및 연체 지표 분석': [
            {'file': 'chart_4_delay_rate_trend.png', **charts_all['chart_4_delay_rate_trend.png']},
            {'file': 'chart_5_avg_delay_rate.png', **charts_all['chart_5_avg_delay_rate.png']},
            {'file': 'chart_3_delay_amount_bar.png', **charts_all['chart_3_delay_amount_bar.png']},
            {'file': 'chart_8_scatter_balance_delay.png', **charts_all['chart_8_scatter_balance_delay.png']},
            {'file': 'chart_9_delay_boxplot.png', **charts_all['chart_9_delay_boxplot.png']},
            {'file': 'chart_10_delay_rate_boxplot.png', **charts_all['chart_10_delay_rate_boxplot.png']}
        ],
        '부실채권 매각 및 구조적 요인': [
            {'file': 'chart_6_delay_rate_reduction.png', **charts_all['chart_6_delay_rate_reduction.png']},
            {'file': 'chart_7_sell_amount_bar.png', **charts_all['chart_7_sell_amount_bar.png']}
        ]
    }

    # 5. Jinja2 렌더링
    template_dir = os.path.join(os.getcwd(), 'retail-loan-data', 'src')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('dashboard_template.html')

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_out = template.render(
        last_update=now_str,
        kpi=kpi,
        insights=insights,
        chart_groups=chart_groups,
        raw_data_html=raw_data_html,
        company_data_htmls=company_data_htmls
    )

    out_path = os.path.join(os.getcwd(), 'retail-loan-data', 'report', 'dashboard.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_out)

    print("Jinja2 기반 대시보드 재생성 완료!")

if __name__ == "__main__":
    main()
