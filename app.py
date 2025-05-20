import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime

# Initialize the Dash app with a dark theme
app = dash.Dash(__name__, 
                external_stylesheets=[dbc.themes.DARKLY],
                suppress_callback_exceptions=True)
server = app.server  # Add this line to expose the Flask server

# Load and prepare the data
df = pd.read_csv("Supermart_Grocery_Dataset.csv")
df['Order Date'] = pd.to_datetime(df['Order Date'], format='mixed')

df['Year'] = df['Order Date'].dt.year
df['Month'] = df['Order Date'].dt.month

# Set the default template to a dark theme
px.defaults.template = "plotly_dark"

# Create the navigation bar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Sales Dashboard", href="/")),
        dbc.NavItem(dbc.NavLink("Regional Analysis", href="/region")),
        dbc.NavItem(dbc.NavLink("Category Analysis", href="/category")),
    ],
    brand="Supermart Grocery Dashboard",
    brand_href="/",
    color="primary",
    dark=True,
)

# Sales Dashboard layout
sales_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Sales Performance Dashboard", className="text-center my-4"),
            html.P("""
                This dashboard provides an interactive analysis of sales data for the Supermart Grocery store.
                Use the date range slider to filter data by time period.
            """, className="lead text-center"),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select Date Range"),
                dbc.CardBody([
                    dcc.DatePickerRange(
                        id='date-range',
                        min_date_allowed=df['Order Date'].min().date(),
                        max_date_allowed=df['Order Date'].max().date(),
                        start_date=df['Order Date'].min().date(),
                        end_date=df['Order Date'].max().date(),
                        className="mb-4"
                    )
                ])
            ])
        ])
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Sales Overview"),
                dbc.CardBody(id='sales-overview')
            ])
        ])
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='sales-trend-plot')
        ], md=6),
        dbc.Col([
            dcc.Graph(id='profit-trend-plot')
        ], md=6)
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='discount-sales-plot')
        ])
    ])
])

# Regional Analysis layout
region_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Regional Performance Analysis", className="text-center my-4"),
            html.P("""
                This page provides an analysis of sales and profit performance by region.
                Use the radio buttons to switch between different metrics.
            """, className="lead text-center"),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select Metric"),
                dbc.CardBody([
                    dbc.RadioItems(
                        id='region-metric',
                        options=[
                            {'label': 'Sales', 'value': 'Sales'},
                            {'label': 'Profit', 'value': 'Profit'},
                            {'label': 'Profit Margin', 'value': 'Margin'}
                        ],
                        value='Sales',
                        inline=True,
                        className="mb-4"
                    )
                ])
            ])
        ])
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='region-bar-plot')
        ], md=6),
        dbc.Col([
            dcc.Graph(id='region-scatter-plot')
        ], md=6)
    ])
])

# Category Analysis layout
category_layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Product Category Analysis", className="text-center my-4"),
            html.P("""
                This page provides an analysis of sales and profit by product category.
                Use the dropdown to filter by specific categories.
            """, className="lead text-center"),
        ])
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Select Categories"),
                dbc.CardBody([
                    dcc.Dropdown(
                        id='category-dropdown',
                        options=[{'label': cat, 'value': cat} for cat in df['Category'].unique()],
                        value=df['Category'].unique().tolist(),
                        multi=True,
                        className="mb-4"
                    )
                ])
            ])
        ])
    ], className="mb-4"),
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='category-bar-plot')
        ], md=6),
        dbc.Col([
            dcc.Graph(id='subcategory-bar-plot')
        ], md=6),
        dbc.Col([
            dcc.Graph(id='category-treemap')
        ])
    ])
])

# Callback for date range filter
@app.callback(
    [Output('sales-overview', 'children'),
     Output('sales-trend-plot', 'figure'),
     Output('profit-trend-plot', 'figure'),
     Output('discount-sales-plot', 'figure')],
    [Input('date-range', 'start_date'),
     Input('date-range', 'end_date')]
)
def update_sales_dashboard(start_date, end_date):
    # Convert string dates to datetime
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    
    # Filter data by date range
    filtered_df = df[(df['Order Date'] >= start_date) & (df['Order Date'] <= end_date)]
    
    # Calculate overview metrics
    total_sales = filtered_df['Sales'].sum()
    total_profit = filtered_df['Profit'].sum()
    avg_profit_margin = (total_profit / total_sales) * 100 if total_sales > 0 else 0
    order_count = filtered_df['Order ID'].nunique()
    
    # Create overview cards
    overview = dbc.Row([
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Total Sales"),
                html.H2(f"${total_sales:,.2f}")
            ])
        ])),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Total Profit"),
                html.H2(f"${total_profit:,.2f}")
            ])
        ])),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Profit Margin"),
                html.H2(f"{avg_profit_margin:.2f}%")
            ])
        ])),
        dbc.Col(dbc.Card([
            dbc.CardBody([
                html.H4("Total Orders"),
                html.H2(f"{order_count}")
            ])
        ]))
    ])
    
    # Prepare data for plots
    monthly_data = filtered_df.groupby(pd.Grouper(key='Order Date', freq='M')).agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()
    
    # Sales trend plot
    sales_fig = px.line(monthly_data, x='Order Date', y='Sales',
                        title='Monthly Sales Trend')
    sales_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    # Profit trend plot
    profit_fig = px.line(monthly_data, x='Order Date', y='Profit',
                         title='Monthly Profit Trend')
    profit_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    # Discount vs Sales plot
    discount_fig = px.scatter(filtered_df, x='Discount', y='Sales', color='Category',
                             title='Discount vs Sales by Category')
    discount_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return overview, sales_fig, profit_fig, discount_fig

# Callback for regional analysis
@app.callback(
    [Output('region-bar-plot', 'figure'),
     Output('region-scatter-plot', 'figure')],
    [Input('region-metric', 'value')]
)
def update_region_analysis(metric):
    # Prepare data for region analysis
    region_data = df.groupby('Region').agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()
    
    # Calculate profit margin
    region_data['Margin'] = (region_data['Profit'] / region_data['Sales']) * 100
    
    # Regional performance bar chart
    bar_title = f'Total {metric} by Region'
    if metric == 'Margin':
        bar_title = 'Profit Margin (%) by Region'
    
    bar_fig = px.bar(region_data, x='Region', y=metric,
                    title=bar_title,
                    color='Region')
    bar_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    # Region scatter plot
    regional_perf = df.groupby(['Region', 'Year']).agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()
    
    regional_perf['Margin'] = (regional_perf['Profit'] / regional_perf['Sales']) * 100
    
    scatter_fig = px.scatter(regional_perf,
                           x='Sales', y='Profit',
                           color='Region', size='Margin',
                           hover_data=['Year'],
                           title='Regional Performance (Sales vs Profit)')
    scatter_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return bar_fig, scatter_fig

# Callback for category analysis
@app.callback(
    [Output('category-bar-plot', 'figure'),
     Output('subcategory-bar-plot', 'figure'),
     Output('category-treemap', 'figure')],
    [Input('category-dropdown', 'value')]
)
def update_category_analysis(categories):
    # Filter by selected categories
    filtered_df = df[df['Category'].isin(categories)]
    
    # Prepare data for category analysis
    category_data = filtered_df.groupby('Category').agg({
        'Sales': 'sum',
        'Profit': 'sum'
    }).reset_index()
    
    # Category bar chart
    category_fig = px.bar(category_data,
                         x='Category', y='Sales',
                         title='Sales by Category',
                         color='Category')
    category_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    # Subcategory bar chart
    subcategory_data = filtered_df.groupby(['Category', 'Sub Category']).agg({
        'Sales': 'sum'
    }).reset_index()
    
    subcategory_data = subcategory_data.sort_values('Sales', ascending=False).head(10)
    
    subcategory_fig = px.bar(subcategory_data,
                            x='Sub Category', y='Sales',
                            title='Top 10 Sub-Categories by Sales',
                            color='Category')
    subcategory_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    # Add treemap visualization
    treemap_data = filtered_df.groupby(['Category', 'Sub Category']).agg({
        'Sales': 'sum'
    }).reset_index()
    
    treemap_fig = px.treemap(
        treemap_data,
        path=['Category', 'Sub Category'],
        values='Sales',
        title='Sales Distribution by Category and Sub-Category',
        color='Sales',
        color_continuous_scale='Viridis'
    )
    treemap_fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white')
    )
    
    return category_fig, subcategory_fig, treemap_fig

# Set up the app layout
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])

# Callback for page routing
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/region':
        return region_layout
    elif pathname == '/category':
        return category_layout
    else:
        return sales_layout

if __name__ == '__main__':
    app.run(debug=True)