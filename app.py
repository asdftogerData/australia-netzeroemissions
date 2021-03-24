# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 17:03:09 2021

@author: asdft
"""
import requests
import pandas as pd
import os


import sys
# sys.path.append(".")

from nggiaustralia import emissions

my_emissions=emissions()
data=my_emissions.load_emissions_data()

#%%
# Creating long data
data_long=pd.melt(data.drop("Total (excluding LULUCF)",axis=1),id_vars="Quarter")

# Create rolling data
data_yearly_rolling=my_emissions.create_rolling_data(data)

# Create 1.5C budget data
data_budget=my_emissions.create_carbon_budget_data(data.loc[:,['Quarter',"Total (excluding LULUCF)"]],
                                                   target_type="1.5C",
                                                   # target_type="custom",
                                                   # target_budget=20000
                                                   )

#%%

import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # or plotly.express as px

from dash.dependencies import Input, Output

# fig_pie = px.pie(data_melt__,values="value",names="variable").update_traces(textinfo='percent+value+label',textposition='inside')
# fig_line_total=px.line(data,
#                        x="Quarter",
#                        y=["National Inventory Total","Total (excluding LULUCF)"],
#                        )
# fig_line_total=px.area(data_yearly_breakdown_melt,x="Quarter",y='value',color='variable')
fig_line_total=px.area(data_long,x="Quarter",y='value',color='variable')

# fig_line_total.update_traces(mode='lines+markers')
fig_line_total.update_layout(title="Historical carbon emissions, Australia",
                             xaxis_title="Year",
                             yaxis_title="Emissions (MtCO<sub>2</sub>-e)"
                             )


# fig_line_breakdown = px.line(data_yearly_breakdown_melt, x="Quarter", y="value", color="variable",
#               hover_name="variable")
# fig_line_breakdown.update_traces(mode='lines+markers')


# data_15C_plot=data_15C.loc[:,['Quarter','Cumulative emissions']]
# data_15C_plot=data_15C_plot.set_index('Quarter')         
                           
# fig_line_carbon_budget=px.line(data_15C,
#                        x="Quarter",
#                        y=["Cumulative emissions"],
#                        )

fig_line_carbon_budget=px.line(data_budget, x="Quarter",y="Cumulative emissions")

#Problem with hlines and vlines
# fig_line_carbon_budget.add_hline(y=100,
#                                   line_dash="dot")
fig_line_carbon_budget.add_hline(y=my_emissions.carbon_budget_15C,
                                   line_dash="dash",
               annotation_text="1.5C Carbon Budget", 
              )
fig_line_carbon_budget.add_hline(y=my_emissions.carbon_budget_2C,
                                   line_dash="dash",
               annotation_text="2C Carbon Budget", 
              )
# ,style={'display': 'inline-block'#,'width': '49%'}
app=dash.Dash(__name__)
app.layout = html.Div([
    html.Div(
        [
            html.Div(
                [dcc.Graph(id="graph-line",figure=fig_line_total,
                          hoverData={'points': [{'x':str(data.Quarter.max())}]})],
                style={'display': 'inline-block'}, 
        
            ),
            html.Div(
                [dcc.Graph(id="graph-pie")],
                style={'display': 'inline-block'}, 
            ),
        ],
        # style={'display': 'inline-block'}, 
        # className="row flex-display",
    ),        
    html.Div(
        [
            html.Div(
                [dcc.Graph(id="carbon-budget",figure=fig_line_carbon_budget)]
                ),
        ],#style={'display': 'inline-block','width': '49%'}
    ),
    ],
    # style={"display": "flex", "flex-direction": "column"}
)

@app.callback(
    Output("graph-pie",'figure'),
    [Input("graph-line",'hoverData')
           ]
    )
def update_pie_chart(hoverData):
    quarter=hoverData['points'][0]['x']
    dff=data.drop("Total (excluding LULUCF)",axis=1)
    dff=pd.melt(dff[dff.Quarter==quarter],id_vars="Quarter")
    dff=dff.round(1)
    fig = px.pie(dff,
                  values="value",names="variable",
                 title="Sectoral emissions of {}".format(quarter))
    fig.update_traces(textposition='inside', textinfo='percent+value')
    return fig


# @app.callback(
#     Output("carbon-budget","figure"),
#     [Input("graph-line","hoverData"),
#      ])
# def update_carbon_budget(hoverData):
#     quarter=hoverData['points'][0]['x']
#     fig=px.line(data_budget_2013,)
#     return fig
    
    
    
if __name__ == '__main__':
    app.run_server(debug=True)