# -*- coding: utf-8 -*-
"""
Created on Fri Mar 12 17:03:09 2021

@author: asdft
"""
#Preprocessing data
import pandas as pd
from nggiaustralia import emissions, DATETIME_2030

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

# Creating color map for pie chart
import plotly.express as px
colors=px.colors.qualitative.Plotly
emissions_cols=data.columns[1:]
color_map = {emissions_cols[i]:colors[i] for i,key in enumerate(emissions_cols)}

SLIDER_MARKS={
0.33:{'label': 'World Population %'},
0.97:{'label': 'CCA '},
# 0.73:{'label': 'Equal per capital'},
# 0.68:{'label': 'Equal cumulative per capital'},
# 0.52:{'label': 'Capability'},
# 1.19:{'label': 'Greenhouse development rights'},
1.27:{'label': 'Constant emissions ratio'},
}

#%%
# d15C=my_emissions.create_carbon_budget_data_from_temp(d2013,target_type="1.5C",share_perc=0.97)
# ddd=d15C[d15C['Quarter']==DATETIME_2030]['Cumulative emissions'].iloc[-1]

# e=round(ddd)

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
        html.A("Source code", href="https://github.com/asdftogerData/australia-netzeroemissions", target="_blank"),
        ],
        className="one-half column",
        ),
    
    html.Div(
        [
            html.Div(
                [
                    html.H2("Australia's historical emissions from 2001-Present. LULUCF is not included in any of the visualisations.")
                    ]
                ),
            html.Div(
                [dcc.RadioItems(
                    id='yearly-quarterly',
                    options=[{'label': 'Quarterly', 'value': 'Quarterly'},
                             {'label': 'Yearly Rolling Average', 'value': 'Yearly'},
                             ],
                    value="Quarterly"            
                                ),
                ]
            ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="graph-historical-emissions",
                                  hoverData={'points': [{'x':str(data.Quarter.max())}]})],
                        # style={'width': '49%', 'display': 'inline-block', 'padding': '0 20',"border":"2px black solid"},
                        className="pretty_container seven columns"
                    ),
                    html.Div(
                        [dcc.Graph(id="graph-emissions-breakdown")],
                        className="pretty_container five columns"
                        # style={'width': '49%', 'display': 'inline-block', 'padding': '0 20'},
                    ),
                    ],
                className="row flex-display",
            )
        ],
        # style={'display': 'inline-block'}, 
        # className="row flex-display",
    ),        
    html.Div(
        [
            html.H2("Australia's fair share of carbon budget and emissions trajectories."),
            # html.Div(
            #     [
                    # dcc.Input(id='fair-share-input'),
                  # html.P("Fair share budget %"),
             html.Div(
                 id='fair-share-container',
                  # className="pretty_container one columns"
                      # style={'width': '49%','display': 'inline-block'}
                      ),
             html.Div([
             dcc.Slider(
                 id='fair-share-slider',
                   min=0.33,
                   max=1.27,
                   value=0.97,
                   step=0.01,
                   marks=SLIDER_MARKS,
                    # className='dcc_control'
                    # className="pretty_container five columns",
                   # className='dcc_control'
                    
                   ),
                 ], 
                 style={'width': '50%', 'align': 'center'},
                 ),
                 
            # ],
                      
                # className= "row flex-display",
                # className= "pretty_container five columns",
                
            # ),
            html.Div(
                [
                    html.Div(
                        [dcc.Graph(id="graph-carbon-netzero")],
                        className="pretty_container seven columns"
                    ),
                    html.Div(
                        [dcc.Graph(id="graph-carbon-budget")],
                        className="pretty_container five columns"
                    ),
                    ],
                className="row flex-display",
                )
            
        ],
    ),
    ],
    
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
    fig_area=px.area(dff.round(1),x="Quarter",y='Emissions',color='Sector',
                     # color_discrete_map=color_discrete_map
                     )
    
    fig_area.update_layout(
        title="Historical carbon emissions",
        title_x=0.5,
        xaxis_title="Year",
        yaxis_title="Emissions (MtCO<sub>2</sub>-e)",
        legend=dict(
            orientation="h",
            y=-0.2,
        ),
        # transition_duration=500
                             )
    
    #Plot pie chart
    dff=dff[dff.Quarter==quarter]
    dff_sum=dff['Emissions'].sum().round(1)
    fig = px.pie(dff.round(1),
                 values="Emissions",
                 names="Sector",
                 color="Sector",
                 color_discrete_map=color_map,
                 )
    
    fig.update_layout(
        title="{}-{}: {}MtCO<sub>2</sub>-e".format(quarter_dt.strftime('%B'),quarter_dt.year,dff_sum),
        title_x=0.5,
        legend=dict(
            orientation="h",
            )
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
        "Observed":d2013,
        "28% reduction by 2030":d28R, #from 2005 levels by 2030"
        '2C':d2C,
        '1.5C':d15C,
        }
    
    for name,data_plot in d_plot.items():
        if(len(data_plot)>2):
            line_netzero=go.Scatter(
                    x=data_plot['Quarter'],
                    y=data_plot["Total (excluding LULUCF)"],
                    name=name,
                    # mode='lines+markers',
                    line=dict(dash='dashdot' if name!="Observed" else 'solid')
                    
                    )
            line_budget=go.Scatter(
                    x=data_plot['Quarter'],
                    y=data_plot["Cumulative emissions"],
                    name=name,
                    # mode='lines+markers',
                    line=dict(dash='dashdot' if name!="Observed" else 'solid'),
                    )
            # line_netzero.update()
            fig_netzero.add_trace(
                line_netzero
            )
            
            if(name!="Observed" and (DATETIME_2030 in data_plot['Quarter'].values)):
                fig_netzero.add_annotation(
                    x=DATETIME_2030,
                    y=data_plot[data_plot['Quarter']==DATETIME_2030]['Total (excluding LULUCF)'].iloc[-1],
                    showarrow=True,
                    arrowhead=1,
                    
                    text="{}% reduction by 2030".format(emissions.get_reduction_percentage(data_plot)),
                    align='right',
                    ax=100, #I dont have a good way of setting this other than some flat value
                    
                    )
            fig_budget.add_trace(
                line_budget
            )
    # fig_budget.update_layout(
    #     title="Carbon budget")
    
    
    
    
    fig_netzero.update_layout(
        title="Net zero emissions trajectories",
        title_x=0.5,
        legend=dict(
            orientation="h",
            )
        # transition_duration=500
        )
    fig_budget.update_layout(
        title="Cumulative emissions vs 1.5C and 2C carbon budget",
        title_x=0.5,
        yaxis_title="Cumulative emissions (MtCO<sub>2</sub>-e)",
        legend=dict(
            orientation="h",
            )
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