#import all needed libraries
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State, callback_context
import dash_bootstrap_components as dbc

# Load your full dataset
df = pd.read_excel("Data.xls")

# Clean column names
df.columns = df.columns.str.strip()
df.rename(columns={
    'Singal Intensity(At most 5)': 'SignalIntensity',
    'Detection Range(Circle)': 'DetectionRange',
    'Video FeedbackOn': 'VideoFeedback'
}, inplace=True)

# Convert TimePoint to numeric order (TP1 → 1)
df['TimePoint'] = df['TimePoint'].apply(lambda x: int(x.replace('TP','')))

# Create a copy for original data preservation
original_df = df.copy()
current_df = df.copy()

# Map states to available 3D symbols
state_symbols = {
    'Taking Off': 'circle',
    'Entering Swarm': 'square', 
    'Hovering': 'diamond',
    'Passing By': 'cross',
    'Attacking': 'x',
    'Returning': 'circle-open',
    'Parachute Deployment': 'square-open',
    'Descending': 'diamond-open'
}

# State colors for markers AND cones
state_colors = {
    'Taking Off': '#FF6B00',
    'Entering Swarm': '#00A8FF',
    'Hovering': '#00D8FF',
    'Passing By': '#9C88FF',
    'Attacking': '#FF4757',
    'Returning': '#2ED573',
    'Parachute Deployment': '#FFA502',
    'Descending': '#FF6348'
}

# Enhanced Hover Information
def create_hover_info(row):
    return (f"<b>Drone {row['DroneID']}</b><br>"
            f"Swarm: {row['SwarmID'] if row['SwarmID'] != -1 else 'None'}<br>"
            f"Task: {row['TaskID'] if row['TaskID'] != -1 else 'None'}<br>"
            f"State: {row['State']}<br>"
            f"Battery: {row['Battery Percentage']}%<br>"
            f"Signal: {row['SignalIntensity']}/5<br>"
            f"Video: {row['VideoFeedback']}<br>"
            f"Position: ({row['PositionX']:.1f}, {row['PositionY']:.1f}, {row['PositionZ']:.1f})<br>"
            f"Velocity: ({row['VelocityX']:.1f}, {row['VelocityY']:.1f}, {row['VelocityZ']:.1f})<br>"
            f"Orientation: Pitch {row['Pitch']:.1f}°, Roll {row['Roll']:.1f}°, Yaw {row['Yaw']:.1f}°")

current_df['HoverInfo'] = current_df.apply(create_hover_info, axis=1)

def create_visualization(data_frame, current_timepoint=1):
    """Create the 3D visualization with current data"""
    
    # Filter data for current timepoint
    df_tp = data_frame[data_frame['TimePoint'] == current_timepoint]
    
    # Create trajectory lines
    trajectories = []
    for drone_id in data_frame['DroneID'].unique():
        drone_df = data_frame[data_frame['DroneID'] == drone_id].sort_values('TimePoint')
        
        trajectory = go.Scatter3d(
            x=drone_df['PositionX'],
            y=drone_df['PositionY'],
            z=drone_df['PositionZ'],
            mode='lines',
            line=dict(width=3, color='rgba(128, 128, 128, 0.4)', dash='dash'),
            opacity=0.4,
            name=f'Drone {drone_id} Path',
            showlegend=False,
            hoverinfo='skip'
        )
        trajectories.append(trajectory)

    # Get valid symbols and colors
    symbols = []
    marker_colors = []
    
    for state in df_tp['State']:
        symbol = state_symbols.get(state, 'circle')
        if symbol not in ['circle', 'circle-open', 'cross', 'diamond', 'diamond-open', 'square', 'square-open', 'x']:
            symbol = 'circle'
        symbols.append(symbol)
        
        color = state_colors.get(state, '#FFFFFF')
        marker_colors.append(color)
    
    # Main scatter plot for drones
    scatter = go.Scatter3d(
        x=df_tp['PositionX'],
        y=df_tp['PositionY'],
        z=df_tp['PositionZ'],
        mode='markers+text',
        marker=dict(
            size=df_tp['Battery Percentage'] / 6,
            color=marker_colors,
            opacity=0.9,
            line=dict(width=3, color='white'),
            symbol=symbols,
        ),
        text=[f'Drone {id}' for id in df_tp['DroneID']],
        textposition="top center",
        textfont=dict(size=12, color='white', family='Arial Black'),
        hoverinfo='text',
        hovertext=df_tp['HoverInfo'],
        name='Drones',
        customdata=df_tp[['DroneID', 'TimePoint']].values
    )
    
    # Create individual cones for each drone
    cone_traces = []
    for i, row in df_tp.iterrows():
        state_color = state_colors.get(row['State'], '#FFFFFF')
        cone_colorscale = [[0, state_color], [1, state_color]]
        
        cone = go.Cone(
            x=[row['PositionX']],
            y=[row['PositionY']],
            z=[row['PositionZ']],
            u=[row['VelocityX']],
            v=[row['VelocityY']],
            w=[row['VelocityZ']],
            sizemode="scaled",
            sizeref=1.5,
            anchor="tail",
            showscale=False,
            colorscale=cone_colorscale,
            opacity=0.7,
            name='Velocity',
            showlegend=False
        )
        cone_traces.append(cone)

    # Create legend traces
    legend_traces = []
    for state, symbol in state_symbols.items():
        valid_symbol = symbol
        if valid_symbol not in ['circle', 'circle-open', 'cross', 'diamond', 'diamond-open', 'square', 'square-open', 'x']:
            valid_symbol = 'circle'
        
        legend_traces.append(go.Scatter3d(
            x=[None], y=[None], z=[None],
            mode='markers',
            marker=dict(
                symbol=valid_symbol, 
                size=12, 
                color=state_colors.get(state, 'white'),
                line=dict(width=2, color='white')
            ),
            name=state,
            showlegend=True,
            hoverinfo='skip'
        ))

    swarm_legend = go.Scatter3d(
        x=[None], y=[None], z=[None],
        mode='markers',
        marker=dict(size=10, color='gray'),
        name='--- Drone States ---',
        showlegend=True,
        hoverinfo='skip'
    )

    # Create layout - USING EXACT ASSIGNMENT 2 COLORS
    layout = go.Layout(
        title=dict(
            text=f"🚁 Interactive Drone Swarm Visualization - TP{current_timepoint}",
            x=0.5,
            y=0.95,
            font=dict(size=24, color='white', family='Arial Black')
        ),
        scene=dict(
            xaxis=dict(
                title='X Position (m)', 
                gridcolor='rgba(100, 100, 100, 0.3)',
                gridwidth=1,
                backgroundcolor='rgba(20, 20, 20, 0.1)'  # From Assignment 2
            ),
            yaxis=dict(
                title='Y Position (m)', 
                gridcolor='rgba(100, 100, 100, 0.3)',
                gridwidth=1,
                backgroundcolor='rgba(20, 20, 20, 0.1)'  # From Assignment 2
            ),
            zaxis=dict(
                title='Z Position (m)', 
                gridcolor='rgba(100, 100, 100, 0.3)',
                gridwidth=1,
                backgroundcolor='rgba(20, 20, 20, 0.1)'  # From Assignment 2
            ),
            bgcolor='rgb(10, 10, 10)',  # From Assignment 2
            aspectmode='data',
            camera=dict(
                up=dict(x=0, y=0, z=1),
                center=dict(x=0, y=0, z=0),
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        paper_bgcolor='rgb(10, 10, 10)',  # From Assignment 2
        plot_bgcolor='rgb(10, 10, 10)',   # From Assignment 2
        font=dict(color='white', family='Arial'),
        legend=dict(
            x=0.02, y=0.02,
            bgcolor='rgba(0, 0, 0, 0.7)',
            bordercolor='white',
            borderwidth=1,
            font=dict(color='white', size=10)
        ),
        width=1200,
        height=800
    )

    # Combine all traces
    all_traces = [scatter] + cone_traces + trajectories + legend_traces + [swarm_legend]
    
    return go.Figure(data=all_traces, layout=layout)

# Create Dash application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

# Get unique timepoints and drones
timepoints = sorted(current_df['TimePoint'].unique())
drones = sorted(current_df['DroneID'].unique())

# Custom CSS for dark dropdowns
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Custom dark theme for dropdowns */
            .Select-control, .Select-menu-outer {
                background-color: #2b2b2b !important;
                color: white !important;
                border-color: #555 !important;
            }
            .Select-value-label, .Select-placeholder {
                color: white !important;
            }
            .Select-input > input {
                color: white !important;
            }
            .Select-option {
                background-color: #2b2b2b !important;
                color: white !important;
            }
            .Select-option.is-focused {
                background-color: #404040 !important;
                color: white !important;
            }
            .Select-option.is-selected {
                background-color: #555 !important;
                color: white !important;
            }
            .VirtualizedSelectOption {
                background-color: #2b2b2b !important;
                color: white !important;
            }
            .VirtualizedSelectFocusedOption {
                background-color: #404040 !important;
                color: white !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Interactive Drone Swarm Visualization", 
                   className="text-center mb-4",
                   style={'color': 'white'})
        ], width=12)
    ]),
    
    dbc.Row([
        # Control Panel
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🕹️ Control Panel", className="h4"),
                dbc.CardBody([
                    # Timepoint Control
                    html.H5("Time Navigation", className="mb-3", style={'color': 'white'}),
                    dcc.Slider(
                        id='timepoint-slider',
                        min=min(timepoints),
                        max=max(timepoints),
                        value=min(timepoints),
                        marks={str(tp): f'TP{tp}' for tp in timepoints},
                        step=1
                    ),
                    dbc.Row([
                        dbc.Col(dbc.Button('⏮ Previous', id='prev-btn', color='primary', className='me-2')),
                        dbc.Col(dbc.Button('Next ⏭', id='next-btn', color='primary', className='ms-2')),
                    ], className="mt-2"),
                    
                    html.Hr(style={'borderColor': 'white'}),
                    
                    # Data Modification Panel
                    html.H5("Data Modification", className="mb-3", style={'color': 'white'}),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Select Drone:", style={'color': 'white'}),
                            dcc.Dropdown(
                                id='drone-dropdown',
                                options=[{'label': f'Drone {drone}', 'value': drone} for drone in drones],
                                value=drones[0],
                                style={
                                    'backgroundColor': '#2b2b2b',
                                    'color': 'white',
                                    'border': '1px solid #555'
                                }
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Select TimePoint:", style={'color': 'white'}),
                            dcc.Dropdown(
                                id='modify-tp-dropdown',
                                options=[{'label': f'TP{tp}', 'value': tp} for tp in timepoints],
                                value=timepoints[0],
                                style={
                                    'backgroundColor': '#2b2b2b',
                                    'color': 'white',
                                    'border': '1px solid #555'
                                }
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("State:", style={'color': 'white'}),
                            dcc.Dropdown(
                                id='state-dropdown',
                                options=[{'label': state, 'value': state} for state in state_symbols.keys()],
                                value='Hovering',
                                style={
                                    'backgroundColor': '#2b2b2b',
                                    'color': 'white',
                                    'border': '1px solid #555'
                                }
                            )
                        ], width=6),
                        dbc.Col([
                            html.Label("Battery %:", style={'color': 'white'}),
                            dcc.Slider(
                                id='battery-slider',
                                min=0,
                                max=100,
                                value=50,
                                marks={0: '0%', 50: '50%', 100: '100%'}
                            )
                        ], width=6)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col([
                            html.Label("Position X:", style={'color': 'white'}),
                            dcc.Input(
                                id='pos-x-input', 
                                type='number', 
                                value=0, 
                                className='form-control',
                                style={'backgroundColor': '#2b2b2b', 'color': 'white', 'border': '1px solid #555'}
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Position Y:", style={'color': 'white'}),
                            dcc.Input(
                                id='pos-y-input', 
                                type='number', 
                                value=0, 
                                className='form-control',
                                style={'backgroundColor': '#2b2b2b', 'color': 'white', 'border': '1px solid #555'}
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("Position Z:", style={'color': 'white'}),
                            dcc.Input(
                                id='pos-z-input', 
                                type='number', 
                                value=0, 
                                className='form-control',
                                style={'backgroundColor': '#2b2b2b', 'color': 'white', 'border': '1px solid #555'}
                            )
                        ], width=4)
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col(dbc.Button('🔄 Update Drone Data', id='update-btn', color='success', className='w-100')),
                    ], className="mb-3"),
                    
                    dbc.Row([
                        dbc.Col(dbc.Button('🔄 Reset All Changes', id='reset-btn', color='warning', className='w-100')),
                    ]),
                    
                    html.Hr(style={'borderColor': 'white'}),
                    
                    # Statistics Panel
                    html.H5("Real-time Statistics", className="mb-3", style={'color': 'white'}),
                    html.Div(id='stats-panel', className="text-white")
                    
                ])
            ], color="dark")
        ], width=3),
        
        # Visualization Area
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        id='drone-visualization',
                        style={'height': '80vh'}
                    )
                ])
            ], color="dark"),
            
            # Additional Information
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardHeader("📊 Current TimePoint Details"),
                        dbc.CardBody(id='current-tp-details')
                    ], color="secondary")
                ], width=12)
            ], className="mt-3")
        ], width=9)
    ]),
    
    # Hidden div to store current data
    dcc.Store(id='data-store', data=current_df.to_json(date_format='iso', orient='split')),
    dcc.Store(id='current-timepoint', data=min(timepoints))
    
], fluid=True, style={'backgroundColor': 'rgb(10, 10, 10)', 'minHeight': '100vh'})

# Callbacks for interactivity
@app.callback(
    [Output('drone-visualization', 'figure'),
     Output('current-timepoint', 'data'),
     Output('current-tp-details', 'children')],
    [Input('timepoint-slider', 'value'),
     Input('prev-btn', 'n_clicks'),
     Input('next-btn', 'n_clicks'),
     Input('data-store', 'data')],
    [State('current-timepoint', 'data')]
)
def update_visualization(slider_value, prev_clicks, next_clicks, data_json, current_tp):
    ctx = callback_context
    if not ctx.triggered:
        trigger_id = 'timepoint-slider'
    else:
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Load current data
    current_data = pd.read_json(data_json, orient='split')
    
    # Determine current timepoint
    if trigger_id == 'prev-btn' and prev_clicks:
        new_tp = max(min(timepoints), current_tp - 1)
    elif trigger_id == 'next-btn' and next_clicks:
        new_tp = min(max(timepoints), current_tp + 1)
    else:
        new_tp = slider_value
    
    # Create visualization
    fig = create_visualization(current_data, new_tp)
    
    # Create details panel
    tp_data = current_data[current_data['TimePoint'] == new_tp]
    details = [
        html.P(f"Active Drones: {len(tp_data)}"),
        html.P(f"Total Battery: {tp_data['Battery Percentage'].sum()}%"),
        html.P(f"Average Signal: {tp_data['SignalIntensity'].mean():.1f}/5"),
        html.P("States: " + ", ".join([f"{state}: {count}" for state, count in tp_data['State'].value_counts().items()]))
    ]
    
    return fig, new_tp, details

@app.callback(
    Output('data-store', 'data'),
    [Input('update-btn', 'n_clicks')],
    [State('drone-dropdown', 'value'),
     State('modify-tp-dropdown', 'value'),
     State('state-dropdown', 'value'),
     State('battery-slider', 'value'),
     State('pos-x-input', 'value'),
     State('pos-y-input', 'value'),
     State('pos-z-input', 'value'),
     State('data-store', 'data')]
)
def update_drone_data(update_clicks, drone_id, timepoint, state, battery, pos_x, pos_y, pos_z, data_json):
    if update_clicks is None:
        return data_json
    
    current_data = pd.read_json(data_json, orient='split')
    
    # Update the specific drone data
    mask = (current_data['DroneID'] == drone_id) & (current_data['TimePoint'] == timepoint)
    if mask.any():
        current_data.loc[mask, 'State'] = state
        current_data.loc[mask, 'Battery Percentage'] = battery
        current_data.loc[mask, 'PositionX'] = pos_x
        current_data.loc[mask, 'PositionY'] = pos_y
        current_data.loc[mask, 'PositionZ'] = pos_z
        
        # Update hover info
        current_data.loc[mask, 'HoverInfo'] = current_data[mask].apply(create_hover_info, axis=1)
    
    return current_data.to_json(date_format='iso', orient='split')

@app.callback(
    Output('data-store', 'data', allow_duplicate=True),
    [Input('reset-btn', 'n_clicks')],
    prevent_initial_call=True
)
def reset_data(reset_clicks):
    if reset_clicks:
        current_df = original_df.copy()
        current_df['HoverInfo'] = current_df.apply(create_hover_info, axis=1)
        return current_df.to_json(date_format='iso', orient='split')
    return dash.no_update

@app.callback(
    [Output('pos-x-input', 'value'),
     Output('pos-y-input', 'value'),
     Output('pos-z-input', 'value'),
     Output('battery-slider', 'value'),
     Output('state-dropdown', 'value')],
    [Input('drone-dropdown', 'value'),
     Input('modify-tp-dropdown', 'value'),
     Input('data-store', 'data')]
)
def update_input_fields(drone_id, timepoint, data_json):
    current_data = pd.read_json(data_json, orient='split')
    
    mask = (current_data['DroneID'] == drone_id) & (current_data['TimePoint'] == timepoint)
    if mask.any():
        drone_data = current_data[mask].iloc[0]
        return (drone_data['PositionX'], drone_data['PositionY'], drone_data['PositionZ'],
                drone_data['Battery Percentage'], drone_data['State'])
    
    return 0, 0, 0, 50, 'Hovering'

@app.callback(
    Output('stats-panel', 'children'),
    [Input('data-store', 'data')]
)
def update_stats(data_json):
    current_data = pd.read_json(data_json, orient='split')
    
    total_modifications = len(current_data) - len(original_df)
    modified_drones = len(current_data[current_data['HoverInfo'] != original_df.apply(create_hover_info, axis=1)])
    
    return [
        html.P(f"Total Modifications: {total_modifications}"),
        html.P(f"Modified Drones: {modified_drones}"),
        html.P(f"Data Integrity: {100 - (total_modifications/len(original_df)*100):.1f}%")
    ]

if __name__ == '__main__':
    app.run(debug=True, port=8050)