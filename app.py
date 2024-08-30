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

n_mun='Escolha um município'
iniTest='Estado do Paraná'
#bounds = oeste, sul, leste, norte
bbox = pd.read_csv('mun_bbox.csv', engine='python', sep=',')
f_bbox = bbox[bbox.NM_MUN==n_mun]
f_bbox=f_bbox.reset_index()

image_bounds = [[float(f_bbox.o_lim[0].replace(',','.')),float(f_bbox.s_lim[0].replace(',','.'))], [float(f_bbox.l_lim[0].replace(',','.')),float(f_bbox.n_lim[0].replace(',','.'))]]

classes = [0, 10, 20, 30, 40, 50, 60, 70,80]
classes_txt = [0, 10, 20, 50, 100, 200, 500, 1000," "]
colorscale = ['#FFEDA0', '#FED976', '#FEB24C', '#FD8D3C', '#FC4E2A', '#E31A1C', '#BD0026', '#800026']
style = dict(weight=0, opacity=1, color='white', dashArray='3', fillOpacity=0.7)
# Create colorbar.
#ctg = ["{}+".format(cls, classes[i + 1]) for i, cls in enumerate(classes[:-1])] + ["{}+".format(classes[-1])]
#colorbar = dlx.categorical_colorbar(categories=ctg, colorscale=colorscale, width=300, height=30, position="bottomleft", id="c_bar", opacity=0)
colorbar = dl.Colorbar(colorscale=colorscale, classes=classes, tickText=classes_txt, tickValues=classes, unit="+ ha", min=0, max=80, width=300, height=30, position="bottomleft", id="c_bar", opacity=0)
# Geojson rendering logic, must be JavaScript as it is executed in clientside.
style_handle = assign("""function(feature, context){
    let {iniTest,classes, colorscale, style, colorProp} = context.hideout;  // get props from hideout
    let value = feature.properties[colorProp];  // get value the determines the color
    if (iniTest!=feature.properties.cod_tema) {
        for (let i = 0; i < classes.length; ++i) {
            if (value > classes[i]) {
                style.fillColor = colorscale[i];  // set the fill color according to the class
            }
        }
    } else {
        style.fillColor = '#CCCCCC'
    }
    return style;
}""")
geojson_filter = assign("function(feature, context){{return ['Em analise'].includes(feature.properties.des_condic);}}")
geojson_filter2 = assign("function (feature) {if (feature.properties.num_area > 0) return true}")
# Create geojson.
geojson = dl.GeoJSON(url="/assets/geodados/municipios/municipio_"+unidecode(n_mun.lower().replace(' ','').replace("'",""))+".geojson",  # url to geojson file
                     style=style_handle,  # how to style each polygon
                     zoomToBoundsOnClick=False,  # when true, zooms to bounds of feature (e.g. polygon) on click
                     hoverStyle=arrow_function(dict(weight=5, color='#666', dashArray='')),  # style applied on hover
                     hideout=dict(iniTest=iniTest, colorscale=colorscale, classes=classes_txt[:-1], style=style, colorProp="num_area"),
                     id="geojson", filter=geojson_filter2)

# Create the Dash app
app = Dash()
server = app.server
df = pd.read_csv('pr_af_area.csv', engine='python', sep=';')
#image_overlay = dl.ImageOverlay(opacity=0.8, url="assets/render/png/"+n_mun+".png", bounds=image_bounds, id="imgoverlay")
app.layout = [dcc.Dropdown(bbox.NM_MUN.unique(), 'Escolha um município', id='dropdown-selection'), 
              #dash_table.DataTable(data=df.to_dict('records'), page_size=10, id='mun_table'),
              #dcc.Graph(figure={}, id='graph-content'),
              dl.Map([dl.TileLayer(), geojson, colorbar], bounds=image_bounds, style={'height': '50vh'}, id='map'),
              dcc.Graph(figure={}, id='graph-content'),
              html.Pre("Teste", id='click-data', style=styles['pre'])]

@callback(
    [Output("map", "viewport"), Output('geojson', 'url'), Output('graph-content', 'figure'),Output('c_bar', 'opacity')],
    [Input('dropdown-selection', 'value')]
)
def update_output(value):
    f_bbox = bbox[bbox.NM_MUN==value]
    f_bbox=f_bbox.reset_index()
    n_mun=value
    #image_bounds = [[float(f_bbox.o_lim[0].replace(',','.')),float(f_bbox.s_lim[0].replace(',','.'))], [float(f_bbox.l_lim[0].replace(',','.')),float(f_bbox.n_lim[0].replace(',','.'))]]
    geo_url= "/assets/geodados/municipios/municipio_"+unidecode(value.lower().replace(' ','').replace("'",""))+".geojson"
    #img_url= "assets/render/png/" + value + ".png"
    centerX= float(f_bbox.o_lim[0].replace(',','.'))+(float(f_bbox.l_lim[0].replace(',','.'))-float(f_bbox.o_lim[0].replace(',','.')))/2
    centerY= float(f_bbox.n_lim[0].replace(',','.'))-(float(f_bbox.n_lim[0].replace(',','.'))-float(f_bbox.s_lim[0].replace(',','.')))/2
    #(value == 'Escolha um município') ? dff = df[df.mun=="Paraná"] : dff = df[df.mun==value]
    if value == "Escolha um município":
        dff = df[df.mun=="Paraná"][["grupos","n_af_nao", "n_af_sim"]].rename(columns={'grupos':'Grupos','n_af_nao':'Não','n_af_sim':'Sim'})
        zoom_lvl = 6
        o_c_bar = 0
    else:
        dff = df[df.mun==value][["grupos","n_af_nao", "n_af_sim"]].rename(columns={'grupos':'Grupos','n_af_nao':'Não','n_af_sim':'Sim'})
        zoom_lvl = 10
        o_c_bar = 0.8
    

    return dict(center=[centerX, centerY], zoom=zoom_lvl, transition="flyTo"),geo_url, px.bar(dff, x='Grupos', y=[dff['Não'], dff['Sim']], barmode='stack', labels={"variable": "Agricultura familiar", "value":"Número de propriedades"}), o_c_bar

@callback(
    Output('click-data', 'children'),
    Input('geojson', 'clickData'))
def display_click_data(clickData):
    return clickData['properties']['cod_tema']

if __name__ == '__main__':
    app.run_server()


