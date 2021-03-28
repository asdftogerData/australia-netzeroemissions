# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 17:03:09 2021

@author: asdft
"""
#Preprocessing data
import pandas as pd
from nggiaustralia import emissions

my_emissions=emissions()
#Wide Data
data=my_emissions.load_emissions_data()
data_yearly=my_emissions.create_rolling_data(data)
#Long data
data_long=pd.melt(data.drop("Total (excluding LULUCF)",axis=1),id_vars="Quarter")
data_long=data_long.rename(columns={
    'variable':'Sector',
    'value': 'Emissions',
    })
data_yearly_long=pd.melt(data_yearly.drop("Total (excluding LULUCF)",axis=1),id_vars="Quarter")
data_yearly_long=data_yearly_long.rename(columns={
    'variable':'Sector',
    'value': 'Emissions',
    })
d2013=data[data['Quarter']>=pd.to_datetime('2013-01-01')].loc[:,['Quarter',"Total (excluding LULUCF)"]]
d2013['Cumulative emissions']=d2013["Total (excluding LULUCF)"].cumsum()
#%%
d1=d2013.iloc[:2,:]

#%%
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # or plotly.express as px
from dash.dependencies import Input, Output

app=dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.Div([
        html.H1("Australia carbon emissions and budget - visualised"),
        html.H2("Introduction"),
        html.H3("<https://www.industry.gov.au/data-and-publications/national-greenhouse-gas-inventory-quarterly-updates>")
        ]),
    
    html.Div(
        [
            html.Div(
                [html.P("Australia's historical emissions from 2001-Present. LULUCF is not included in any of the visualisations.")
                    ]
                ),
            html.Div(
                [dcc.RadioItems(
                    id='yearly-quarterly',
                    options=[{'label': i, 'value': i} for i in ['Quarterly','Yearly']],
                    value="Quarterly"            
                                ),
                ]
            ),
            html.Div(
                [dcc.Graph(id="graph-historical-emissions",
                          hoverData={'points': [{'x':str(data.Quarter.max())}]})],
                style={'width': '49%', 'display': 'inline-block', 'padding': '0 20',"border":"2px black solid"},
            ),
            html.Div(
                [dcc.Graph(id="graph-emissions-breakdown")],
                style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'},
            ),
        ],
        # style={'display': 'inline-block'}, 
        # className="row flex-display",
    ),        
    html.Div(
        [
            html.Div(
                [
                    # dcc.Input(id='fair-share-input'),
                  # html.P("Fair share budget %"),
                  html.Div(id='fair-share-container',
                           # style={'width': '49%','display': 'inline-block'}
                           ),
                  html.Div([dcc.Slider(
                      id='fair-share-slider',
                        min=0.33,
                        max=1.27,
                        value=0.97,
                        step=0.01,
                        marks={
                            0.33:{'label': 'World Population %'},
                            0.97:{'label': 'CCA '},
                            # 0.73:{'label': 'Equal per capital'},
                            # 0.68:{'label': 'Equal cumulative per capital'},
                            # 0.52:{'label': 'Capability'},
                            # 1.19:{'label': 'Greenhouse development rights'},
                            # 1.27:{'label': 'Constant emissions ratio'},
                            }
                        ),
                      ],
                      style={'width': '49%','display': 'inline-block'}
                      )
                 ]
                
            ),
            html.Div(
                [dcc.Graph(id="graph-carbon-netzero")],
                style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'},
            ),
            html.Div(
                [dcc.Graph(id="graph-carbon-budget")],
                style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'},
            ),
        ],#style={'display': 'inline-block','width': '49%'}
    ),
    ],
    # style={"display": "flex", "flex-direction": "column"}
)



@app.callback(
    [Output("graph-emissions-breakdown",'figure'),
     Output("graph-historical-emissions",'figure'),
     ],
    [Input("graph-historical-emissions",'hoverData'),
     Input("yearly-quarterly",'value'),
     ]
    )
def update_historical_emissions(hoverData,time_type):
    quarter=hoverData['points'][0]['x']
    quarter_dt=pd.to_datetime(quarter)
    
    if(time_type=="Quarterly"):
        # dff=data.drop("Total (excluding LULUCF)",axis=1)
        dff=data_long
    else:
        # dff=data_yearly.drop("Total (excluding LULUCF)",axis=1)
        dff=data_yearly_long
        
    # dff=pd.melt(dff,id_vars="Quarter")
    # dff=dff.rename(columns={
    # 'variable':'Sector',
    # 'value': 'Emissions',
    # })
    
    #Plot area line chart
    fig_area=px.area(dff.round(1),x="Quarter",y='Emissions',color='Sector')
    
    fig_area.update_layout(title="Historical carbon emissions",
                             xaxis_title="Year",
                             yaxis_title="Emissions (MtCO<sub>2</sub>-e)",
                             # transition_duration=500
                             )
    
    #Plot pie chart
    dff=dff[dff.Quarter==quarter]
    dff_sum=dff['Emissions'].sum().round(1)
    fig = px.pie(dff.round(1),
                  values="Emissions",names="Sector",
                 title="{}-{}: {}MtCO<sub>2</sub>-e".format(
                     quarter_dt.strftime('%B'),
                     quarter_dt.year,
                     dff_sum,
                     )
                 )
    fig.update_layout(
        # transition_duration=500,
        )
    fig.update_traces(textposition='inside', textinfo='percent+value')
    return fig, fig_area

@app.callback(
    [
     Output("graph-carbon-netzero",'figure'),
     Output("graph-carbon-budget",'figure')
     ],
    [Input("fair-share-slider",'value'),
     ]
    )
def update_carbon_budget(share_perc):
    #Carbon budget figure
    # if(budget_type in ['1.5C','2C']):
    #     data_budget=my_emissions.create_carbon_budget_data_from_temp(
    #         data,
    #         target_type=budget_type,
    #         )
    # elif(budget_type=='28% reduction by 2030'):
    #     data_budget=my_emissions.create_carbon_budget_data_from_reduction_target(
    #         data,
    #         )
    
    
    # starting_date=pd.to_datetime('2013-01-01')
    fig_netzero=go.Figure()
    fig_budget=go.Figure()
    
    budget_15C=round(my_emissions.global_budget_2013to2050_15C*share_perc/100,0)
    budget_2C=round(my_emissions.global_budget_2013to2050_2C*share_perc/100,0)
    
    fig_budget.add_hline(
        y=budget_15C,
        line_dash="dot",
        annotation_text="1.5C - {}MtCO<sub>2</sub>-e".format(budget_15C), 
                  )
    fig_budget.add_hline(
        y=budget_2C,
        line_dash="dot",
        annotation_text="2C - {}MtCO<sub>2</sub>-e".format(budget_2C), 
                  )
    # global data
    # d2013=data[data['Quarter']>=starting_date].loc[:,['Quarter',"Total (excluding LULUCF)"]]
    d15C=my_emissions.create_carbon_budget_data_from_temp(d2013,target_type="1.5C",share_perc=share_perc)
    d2C=my_emissions.create_carbon_budget_data_from_temp(d2013,target_type="2C",share_perc=share_perc)
    d28R=my_emissions.create_carbon_budget_data_from_reduction_target(d2013)
    
    d_plot={
        "Observed 2013-2020":d2013,
        "28% reduction from 2005 levels by 2030":d28R,
        '2C':d2C,
        '1.5C':d15C,
        }
    
    for name,data_plot in d_plot.items():
        if(len(data_plot)>2):
            fig_netzero.add_trace(
                go.Line(
                    x=data_plot['Quarter'],
                    y=data_plot["Total (excluding LULUCF)"],
                    name=name,
                    # mode='lines+markers',
                    
                    )
            )
            fig_budget.add_trace(
                go.Line(
                    x=data_plot['Quarter'],
                    y=data_plot["Cumulative emissions"],
                    name=name,
                    # mode='lines+markers',
                    )
            )
    # fig_budget.update_layout(
    #     title="Carbon budget")
    fig_netzero.update_layout(
        # transition_duration=500
        )
    fig_budget.update_layout(
        # transition_duration=500
        )

    return fig_netzero, fig_budget


@app.callback(
     Output("fair-share-container",'children'),
    [Input("fair-share-slider",'value'),
     ]
    )
def update_fair_share_value(fair_share):
    return "Fair share (%): {}".format(fair_share)         
    pass
if __name__ == '__main__':
    app.run_server(
        debug=True
        )