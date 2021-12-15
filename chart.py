import pandas as pd
import math
from datetime import datetime,date
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from jupyter_dash import JupyterDash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output



# plot
class RealizedProfitLoss:
    def __init__(self,df):
        self.dataframe=df

    def plot(self,start_date=None, end_date=None):
        # 日期控制
        df=self.dataframe
        if start_date:
            df = df[df['date'] >= start_date]
        if end_date:
            df = df[df['date'] <= end_date]

        # 依照stock_id 分group計算每個標的的損益
        date_group = df.groupby(['date'])[['pnl']].sum()
        df = df.groupby(['stock_id'])[['pnl']].sum()
        df = df.reset_index()
        df = df.sort_values(['pnl'])
        # 分類賺賠
        df['category'] = ['profit' if i > 0 else 'loss' for i in df['pnl'].values]
        df['pnl_absolute_value'] = abs(df['pnl'])
        
        # 製作Sunburst賺賠合併太陽圖所需資料
        df_category = df.groupby(['category'])[['pnl_absolute_value']].sum()
        df_category = df_category.reset_index()
        df_category = df_category.rename(columns={'category': 'stock_id'})
        df_category['category'] = 'total'

        df_total = pd.DataFrame(
            {'stock_id': 'total', 'pnl_absolute_value': df['pnl_absolute_value'].sum(), 'category': ''},
            index=[0])
        df_all = pd.concat([df, df_category, df_total])

        labels = df['stock_id']

        # Create subplots: use 'domain' type for Pie subplot
        fig = make_subplots(rows=4,
                            cols=3,
                            specs=[[{'type': 'domain', "rowspan": 2}, {'type': 'domain', "rowspan": 2},{'type': 'domain', "rowspan": 2}],
                                   [None, None, None],
                                   [{'type': 'xy', "colspan": 3, "secondary_y": True}, None, None],
                                   [{'type': 'xy', "colspan": 3}, None, None]],
                            horizontal_spacing=0.03,
                            vertical_spacing=0.08,
                            subplot_titles=('Profit Pie: ' + str(df[df['pnl'] > 0]['pnl'].sum()),
                                            'Loss Pie: ' + str(df[df['pnl'] < 0]['pnl'].sum()),
                                            'Profit Loss Sunburst: '+str(df['pnl'].sum()),
                                            'Profit Loss Bar By Date',
                                            'Profit Loss Bar By Target',
                                            )

                            )
        # 獲利donut圖
        fig.add_trace(go.Pie(labels=labels, values=df['pnl'], name="profit", hole=.3, textposition='inside',
                            textinfo='percent+label'), row=1, col=1)
        # 虧損donut圖
        fig.add_trace(go.Pie(labels=labels, values=df[df['pnl'] < 0]['pnl'] * -1, name="loss", hole=.3,
                            textposition='inside', textinfo='percent+label'), row=1, col=2)
        # 賺賠合併太陽圖
        fig.add_trace(go.Sunburst(
            labels=df_all.stock_id,
            parents=df_all.category,
            values=df_all.pnl_absolute_value,
            branchvalues='total',
            marker=dict(
                colors=df_all.pnl_absolute_value.apply(lambda s: math.log(s + 0.1)),
                colorscale='earth'),
            textinfo='label+percent entry',
        ), row=1, col=3)

        # 每日已實現損益變化
        fig.add_trace(go.Bar(x=date_group.index, y=date_group['pnl'], name="date", marker_color="#636EFA"), row=3, col=1)
        fig.add_trace(
            go.Scatter(x=date_group.index, y=date_group['pnl'].cumsum(), name="cumsum_realized_pnl",
                      marker_color="#FFA15A"),
            secondary_y=True,row=3, col=1)
        
        # 標的損益變化
        fig.add_trace(go.Bar(x=df['stock_id'], y=df['pnl'], name="stock_id", marker_color="#636EFA"), row=4, col=1)
        
        # 修正Y軸標籤
        fig['layout']['yaxis']['title'] = '$NTD'
        fig['layout']['yaxis2']['showgrid']=False
        fig['layout']['yaxis2']['title'] = '$NTD(cumsum)'
        fig['layout']['yaxis3']['title'] = '$NTD'
        
        # 主圖格式設定標題，長寬
        fig.update_layout(
            title={
                'text': f"Realized Profit Loss Statistic ({start_date}~{end_date})",
                'x': 0.49,
                'y': 0.99,
                'xanchor': 'center',
                'yanchor': 'top'},
            width=1200,
            height=1000)
        return fig


    def run_dash(self):
        # Build App
        app = JupyterDash(__name__)
        app.layout = html.Div([
            html.H1("Realized Profit Loss JupyterDash"),
            html.P("date_range:"),
            dcc.DatePickerRange(
                id='my-date-picker-range',
                min_date_allowed=date(1990, 1, 1),
                max_date_allowed=date(2100, 12, 31),
                initial_visible_month=date(2021, 1, 1),
                start_date=date(2021, 1, 1),
                end_date=date(2021, 12, 31)
            ),
            dcc.Graph(id="graph")
        ])

        @app.callback(
            Output("graph", "figure"),
            [Input('my-date-picker-range', 'start_date'),
             Input('my-date-picker-range', 'end_date')])

        def update_output(start_date, end_date):
            return self.plot(start_date, end_date)
            
        # Run app and display result inline in the notebook
        app.run_server(mode='inline')