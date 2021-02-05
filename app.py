import os
import math
import datetime
import pathlib
import pandas as pd
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.express as px

####################################################################################################
# TODO: REQUIREMENTS

# Connect to any data source, be it a static CSV or database, and incorporate it into your app
# A call back that uses Input, State, Output
# At least one Plotly graph

####################################################################################################
# INITIATE APP

app = dash.Dash(
    __name__,
    # external_stylesheets=[
    #     'https://codepen.io/chriddyp/pen/bWLwgP.css',
    #     'https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css'
    # ]
)

####################################################################################################
# IMPORT & MANAGE DATA

# get current date
current_date = datetime.datetime.now()
current_year = int(current_date.year)
current_month = int(current_date.month)

# import data from .csv file
APP_PATH = str(pathlib.Path(__file__).parent.resolve())
df = pd.read_csv(os.path.join(APP_PATH, os.path.join('data', 'goodreads_library_export.csv')))

# get desired columns
# desired_columns = ['Book Id', 'Title', 'Author', 'Number of Pages', 'Average Rating', 'My Rating', 'Bookshelves', 'Exclusive Shelf', 'Date Read', 'Date Added']
desired_columns = ['Book Id', 'Title', 'Author', 'Number of Pages', 'Bookshelves', 'Exclusive Shelf', 'Date Read']
df = df[desired_columns]

# function to get a clean list from a string of shelves
def shelf_list_from_str(str_shelves, undesired_shelves):
    clean_shelves = []
    if isinstance(str_shelves, str):
        list_shelves = str_shelves.split(', ')
        for shelf in list_shelves:
            if shelf not in undesired_shelves:
                clean_shelves.append(shelf)
    else: 
        print(str_shelves)
    return clean_shelves

# combine [currently-reading, to-read] as [to-read] in exclusive shelves
df['Exclusive Shelf'] = df['Exclusive Shelf'].replace('currently-reading', 'to-read')

# clean shelves list
exclusive_shelves = df['Exclusive Shelf'].unique().tolist()
undesired_shelves = ['blinked', 'next', 'recent', 'reference', 'shelf', 'update']
df['Bookshelves'] = df['Bookshelves'].apply(lambda x: shelf_list_from_str(x, exclusive_shelves + undesired_shelves))

# replace dates with years
df['Date Read'] = df['Date Read'].apply(lambda x: int(x[:4]) if isinstance(x, str) else x)

# sort
df = df.sort_values(by=['Exclusive Shelf', 'Date Read'])

# split by exclusive shelves i.e. [read, currently-reading, to-read]
library = {}
for shelf in exclusive_shelves:
    library[shelf] = df.loc[df['Exclusive Shelf'] == shelf]

graph = {shelf: {} for shelf in exclusive_shelves}

graph['read']['book_data'] = library['read']['Date Read'].value_counts().to_frame('books').rename_axis('year')
graph['read']['page_data'] = library['read'].groupby(['Date Read']).sum().rename_axis('year').rename(columns={"Number of Pages": "pages"})[['pages']]
graph['read']['data_current'] = graph['read']['book_data'].join(graph['read']['page_data']).reset_index()
graph['read']['years_current'] = graph['read']['data_current']['year'].unique().tolist()
graph['read']['min'] = int(min(graph['read']['years_current']))
graph['read']['max'] = current_year
graph['read']['years_all'] = list(range(graph['read']['min'], graph['read']['max']+1))
graph['read']['years_add'] = [year for year in graph['read']['years_all'] if year not in graph['read']['years_current']]
graph['read']['books_add']  = [0 for year in graph['read']['years_add']]
graph['read']['pages_add']  = [0 for year in graph['read']['years_add']]
graph['read']['data_add'] = pd.DataFrame(data={'year': graph['read']['years_add'], 'books': graph['read']['books_add'], 'pages': graph['read']['pages_add']})
graph['read']['data'] = pd.concat([graph['read']['data_current'], graph['read']['data_add']]).sort_values(by='year')

graph['to-read']['min'] = current_year
graph['to-read']['max'] = 2030 # TODO: reconsider max year allowed
graph['to-read']['years'] = list(range(graph['to-read']['min'], graph['to-read']['max']+1))
graph['to-read']['books'] = [0 for year in graph['to-read']['years']]
graph['to-read']['pages'] = [0 for year in graph['to-read']['years']]
graph['to-read']['data'] = pd.DataFrame(data={'year': graph['to-read']['years'], 'books': graph['to-read']['books'], 'pages': graph['to-read']['pages']})

def get_matrix(shelves_per_book):
    unique_shelves = list({shelf for shelves in shelves_per_book for shelf in shelves})
    shelf_dict = {unique_shelves[i]: i for i in range(len(unique_shelves))}
    translated_shelves_per_book = [[shelf_dict[shelf] for shelf in shelves] for shelves in shelves_per_book]
    matrix = [[0 for s2 in unique_shelves] for s1 in unique_shelves]
    for shelves in translated_shelves_per_book:
        for s1 in shelves:
            for s2 in shelves:
                matrix[s1][s2] += 1
    return matrix, unique_shelves

####################################################################################################
# DEFINE VARIABLES FOR STYLE



####################################################################################################
# DEFINE VARIABLES & FUNCTIONS FOR APP LAYOUT



####################################################################################################
# DEFINE APP LAYOUT

app.layout = html.Div(
    id='container',
    children=[
        # statement
        html.Div(
            id='statement',
            children=[
                html.P(children='I'),
                dcc.Dropdown(
                    id='statement-tense',
                    options=[
                        {'label': 'have read', 'value': 'read'},
                        {'label': 'plan to read', 'value': 'to-read'},
                    ],
                    value='read',
                    clearable=False,
                    style={'width': '120px'},
                ),
                dcc.Input(
                    id='statement-average',
                    type='number',
                ),
                dcc.Dropdown(
                    id='statement-object',
                    options=[
                        {'label': 'books', 'value': 'books'},
                        {'label': 'pages', 'value': 'pages'},
                    ],
                    value='books',
                    clearable=False,
                ),
                html.P(children='on average per year from'),
                dcc.Input(
                    id='statement-year-start',
                    type='number',
                    placeholder='starting year',
                ),
                html.P(children='to'),
                dcc.Input(
                    id='statement-year-end',
                    type='number',
                    placeholder='ending year',
                ),
            ],
        ),
        html.Div(
            id='dashboard',
            children=[
                # bar graph
                html.Div(
                    id='dashboard-left',
                    children=[
                        dcc.Graph(id='graph'),
                    ]
                ),
                # heatmap diagram
                html.Div(
                    id='dashboard-right',
                    children=[
                        dcc.Graph(id='heatmap'),
                    ]
                )
            ]
        )
    ]
)

####################################################################################################
# DEFINE APP CALLBACKS

@app.callback(
    [Output('statement-year-start', 'value'),
    Output('statement-year-end', 'value')], 
    [Input('statement-tense', 'value'),
    Input('statement-year-start', 'value'),
    Input('statement-year-end', 'value')]
)
def define_range(tense, start, end):
    input_fired = dash.callback_context.triggered[0]['prop_id'].split('.')[0]
    minimum = graph[tense]['min']
    maximum = graph[tense]['max']
    if input_fired == 'statement-tense':
        start = minimum
        end = maximum
    else:
        start = minimum if start is None or start <= minimum else start
        end = maximum if end is None or end >= maximum else end
    return start, end

@app.callback(
    [Output('graph', 'figure'),
    Output('statement-average', 'value')],
    [Input('statement-tense', 'value'),
    Input('statement-object', 'value'),
    Input('statement-average', 'value'),
    Input('statement-year-start', 'value'),
    Input('statement-year-end', 'value')]
)
def define_graph_and_average(tense, noun, average, start, end):
    if tense == 'to-read':
        graph[tense]['data'][noun] = 20 if average is None else average
    included_years = list(range(start, end+1))
    data = graph[tense]['data'][graph[tense]['data']['year'].isin(included_years)]
    fig = px.bar(data, x='year', y=noun)
    average = math.ceil(data[noun].mean())
    return fig, average

@app.callback(
    Output('heatmap', 'figure'),
    [Input('graph', 'figure')],
    [State('statement-tense', 'value'),
    State('statement-year-start', 'value'),
    State('statement-year-end', 'value')]
)
def define_heatmap(graph, tense, start, end):
    included_years = list(range(start, end+1))
    if tense == 'read':
        data = library[tense][library[tense]['Date Read'].isin(included_years)]
    elif tense == 'to-read':
        data = library[tense]
    matrix, shelves = get_matrix(data['Bookshelves'].tolist())
    heatmap_df = pd.DataFrame.from_records(matrix, columns=shelves).join(pd.DataFrame({'shelves': shelves})).set_index('shelves')
    fig = px.imshow(heatmap_df)
    fig.update_xaxes(side="top")
    return fig

####################################################################################################
# RUN SERVER

if __name__ == '__main__':
    app.run_server(debug=True)