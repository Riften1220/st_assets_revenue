import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# 页面配置
st.set_page_config(
    page_title="服装行业财务分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    
    .stSelectbox > label {
        font-size: 16px;
        font-weight: 600;
        color: #2E3440;
    }
    
    .stMultiSelect > label {
        font-size: 16px;
        font-weight: 600;
        color: #2E3440;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .chart-container {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .sidebar .stSelectbox {
        margin-bottom: 1rem;
    }
    
    h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 2rem;
    }
    
    .stSidebar {
        background: linear-gradient(180deg, #f8f9fa 0%, #e9ecef 100%);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """加载数据"""
    try:
        df = pd.read_excel('./服装行业总资产报酬率数据.xlsx')
        return df
    except Exception as e:
        st.error(f"数据加载失败: {e}")
        return None

def preprocess_data(df):
    """数据预处理"""
    # 将百分比字段转换为数值（保持原始小数形式）
    if '销售净利率' in df.columns:
        df['销售净利率_数值'] = pd.to_numeric(df['销售净利率'], errors='coerce') / 100
    if '总资产净利率' in df.columns:
        df['总资产净利率_数值'] = pd.to_numeric(df['总资产净利率'], errors='coerce') / 100
    
    # 确保总资产周转率为数值
    if '总资产周转率' in df.columns:
        df['总资产周转率'] = pd.to_numeric(df['总资产周转率'], errors='coerce')
    
    # 确保报告期为字符串格式
    if '报告期' in df.columns:
        df['报告期'] = df['报告期'].astype(str)
    
    return df

def create_bubble_chart(df, selected_period, selected_stocks):
    """创建气泡图"""
    # 过滤数据
    filtered_df = df[
        (df['报告期'] == selected_period) & 
        (df['股票名称'].isin(selected_stocks))
    ].copy()
    
    if filtered_df.empty:
        return None
    
    # 确保数据为数值类型
    filtered_df = filtered_df.dropna(subset=['总资产周转率', '销售净利率_数值', '总资产净利率_数值'])
    
    if filtered_df.empty:
        return None
    
    # 创建气泡图
    fig = go.Figure()
    bubble_sizes = filtered_df['总资产净利率_数值'].abs() * 500 + 20

    # 颜色映射：低值蓝色，高值红色，线性渐变
    colors = []
    edge_colors = []
    max_val = filtered_df['总资产净利率_数值'].max() if not filtered_df['总资产净利率_数值'].empty else 1
    min_val = filtered_df['总资产净利率_数值'].min() if not filtered_df['总资产净利率_数值'].empty else 0
    val_range = max_val - min_val if max_val != min_val else 1
    for val in filtered_df['总资产净利率_数值']:
        if pd.isna(val):
            colors.append('rgba(200,200,200,0.6)')
            edge_colors.append('rgba(120,120,120,1)')
        else:
            norm = (val - min_val) / val_range
            # 蓝色(0,102,255)到红色(255,60,60)
            r = int(0 + (255-0)*norm)
            g = int(102 + (60-102)*norm)
            b = int(255 + (60-255)*norm)
            a = 0.7
            colors.append(f'rgba({r},{g},{b},{a:.2f})')
            edge_colors.append(f'rgba({max(r-40,0)},{max(g-40,0)},{max(b-40,0)},0.95)')

    # 根据气泡大小调整文字显示策略
    text_labels = []
    text_sizes = []
    
    for i, (idx, row) in enumerate(filtered_df.iterrows()):
        bubble_size = bubble_sizes.iloc[i]
        stock_name = row['股票名称']
        
        # 根据气泡大小调整文字大小和显示内容
        if bubble_size < 50:
            text_size = 8
            # 小气泡显示简化文字
            if len(stock_name) > 4:
                text_labels.append(stock_name[:3] + '...')
            else:
                text_labels.append(stock_name)
        elif bubble_size < 80:
            text_size = 10
            if len(stock_name) > 6:
                text_labels.append(stock_name[:5] + '...')
            else:
                text_labels.append(stock_name)
        else:
            text_size = 12
            text_labels.append(stock_name)
        
        text_sizes.append(text_size)

    # 气泡
    fig.add_trace(go.Scatter(
        x=filtered_df['总资产周转率'],
        y=filtered_df['销售净利率_数值'] * 100,
        mode='markers+text',
        marker=dict(
            size=bubble_sizes,
            color=colors,
            line=dict(width=3, color=edge_colors),
            sizemode='diameter',
            opacity=0.7,
            sizemin=10
        ),
        text=text_labels,
        textposition='middle center',
        textfont=dict(size=text_sizes, color='#333333', family='Arial'),  # 深灰色
        hovertemplate=(
            '<b>%{customdata}</b><br>' +
            '总资产周转率: %{x:.3f}<br>' +
            '销售净利率: %{y:.2f}%<br>' +
            '总资产净利率: ' + filtered_df['总资产净利率_数值'].round(4).astype(str) + '<br>' +
            '<extra></extra>'
        ),
        customdata=filtered_df['股票名称'],  # 用于hover显示完整名称
        name=''
    ))
    # 更新布局
    fig.update_layout(
        title=dict(
            text=f"服装行业总资产收益率分析 {selected_period}",
            x=0.5,
            xanchor='center',
            yanchor='top',
            font=dict(size=24, color='#2E3440', family='Arial Black', weight='bold')
        ),
        xaxis=dict(
            title='<b>总资产周转率</b>',
            title_font=dict(size=16, color='#2E3440', family='Arial Black'),
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(128, 128, 128, 0.5)'
        ),
        yaxis=dict(
            title='<b>销售净利率 (%)</b>',
            title_font=dict(size=16, color='#2E3440', family='Arial Black'),
            gridcolor='rgba(128, 128, 128, 0.2)',
            showgrid=True,
            zeroline=True,
            zerolinecolor='rgba(128, 128, 128, 0.5)'
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=600,
        font=dict(family='Arial', size=12),
        showlegend=False,
        margin=dict(l=80, r=80, t=100, b=80)
    )
    return fig

def main():
    # 标题（无特殊字符，无副标题）
    st.markdown("<h1>服装行业总资产收益率分析</h1>", unsafe_allow_html=True)

    # 加载数据
    df = load_data()
    if df is None:
        st.stop()

    # 数据预处理
    df = preprocess_data(df)

    # 侧边栏控件
    st.sidebar.markdown("数据筛选")

    # 报告期选择器
    periods = sorted(df['报告期'].unique(), reverse=True)
    default_period = '20241231' if '20241231' in periods else periods[0]
    selected_period = st.sidebar.selectbox(
        "选择报告期",
        periods,
        index=periods.index(default_period) if default_period in periods else 0
    )

    # 股票名称多选器
    stocks = sorted(df['股票名称'].unique())
    selected_stocks = st.sidebar.multiselect(
        "选择股票",
        stocks,
        default=stocks
    )

    if not selected_stocks:
        st.warning("请至少选择一只股票")
        st.stop()

    # 创建气泡图
    fig = create_bubble_chart(df, selected_period, selected_stocks)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("没有可显示的数据")

    # 数据表格
    st.markdown("<h3 style='font-weight:bold;'>详细数据</h3>", unsafe_allow_html=True)

    # 过滤数据用于表格显示
    filtered_data = df[
        (df['报告期'] == selected_period) &
        (df['股票名称'].isin(selected_stocks))
    ].copy()

    # 显示过滤后的数据
    if not filtered_data.empty:
        display_data = filtered_data[['股票名称', '报告期', '销售净利率_数值', '总资产周转率', '总资产净利率_数值']].copy()
        display_data['销售净利率'] = display_data['销售净利率_数值'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
        display_data['总资产净利率'] = display_data['总资产净利率_数值'].apply(lambda x: f"{x*100:.2f}%" if pd.notna(x) else "N/A")
        display_data['总资产周转率'] = display_data['总资产周转率'].apply(lambda x: f"{x:.3f}" if pd.notna(x) else "N/A")
        final_display = display_data[['股票名称', '报告期', '销售净利率', '总资产周转率', '总资产净利率']]
        # 加粗表头和列名
        st.dataframe(
            final_display.style.set_table_styles([
                {'selector': 'th', 'props': [('font-weight', 'bold'), ('font-size', '16px')]},
                {'selector': 'thead th', 'props': [('font-weight', 'bold'), ('font-size', '17px')]},
                {'selector': 'td', 'props': [('font-size', '15px')]}
            ]),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.warning("没有符合条件的数据")

if __name__ == "__main__":
    main()