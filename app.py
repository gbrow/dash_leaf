import dash_leaflet as dl
from dash import Dash, html, dcc, callback, Output, Input
from dash_extensions.javascript import arrow_function, assign
import plotly.express as px
import pandas as pd
from unidecode import unidecode


styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

bbox = pd.read_csv('mun_bbox.csv', engine='python', sep=',')
# Create the Dash app
app = Dash()
server = app.server
df = pd.read_csv('pr_af_area.csv', engine='python', sep=';')
app.layout = [html.Pre("teste", id='click-data', style=styles['pre'])]

if __name__ == '__main__':
    app.run_server()


