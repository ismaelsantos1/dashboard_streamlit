import pandas as pd
import requests
import streamlit as st
import numpy as np
from datetime import datetime, timedelta, date
import plotly.express as px
import time


#Transformar e ativando wide-mode por padrão
st.set_page_config(layout= 'wide')


#Função para formatar o valor e adicionar unidade monetária
def formata_num(valor, prefixo= ''):
    for unidade in ['', 'mil'] :
        if valor  < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'

        valor /=1000

    return f'{prefixo} {valor:.2f} Mi'

#Filtrando os dados por regiao, data

st.title("DASHBOARD DE VENDAS :shopping_trolley:")



#Aplicando os filtros
#Filtro de regiões e data
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)

if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox("Dados de todo o período", value= True)

if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider("Ano", 2020, 2023)

##API está FUNCIONANDO

url = 'https://labdados.com/produtos'
query_string = {'regiao':regiao.lower(), 'ano': ano}
response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')


##Filtro de vendedores

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
                    #Se não selecionar nhm, mantenha todos


##Tabelas
###Tabelas de receita

####Atualizar todas as visualizações com dados_filtrados
with st.spinner('Atualizando visualizações...'):
    time.sleep(3)
    #1. Mapa de receita por estado
    receitas_estados = dados.groupby('Local da compra')[['Preço']].sum()
    receitas_estados = dados.drop_duplicates(subset= 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receitas_estados, left_on = 'Local da compra', right_index=True).sort_values('Preço', ascending=False)

    #st.map(dados[['lat', 'lon']].drop_duplicates())


    #Criando uma tabela que set como index a coluna da data da compra e agrupa as datas com base na informação do preço
    receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq= 'M'))['Preço'].sum().reset_index()

    #Tabela para informações dos meses e do ano
    receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
    receita_mensal['Mensal'] = receita_mensal['Data da Compra'].dt.month_name()

    #Agrupando dados com base na categoria do produto
    #Informações da receita pra cada categoria de produto
    receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

    ###Tabelas de quantidade de vendas                          #soma e contagem
    vendedores = pd.DataFrame(dados.groupby("Vendedor")['Preço'].agg(['sum', 'count']))



    ###Tabelas vendedores

    ##Gráficos
    fig_mapa_receita = px.scatter_geo(
        receitas_estados,
        lat='lat',
        lon='lon',
        scope='south america',
        size='Preço',
        template='seaborn',
        hover_name='Local da compra',
        hover_data={'lat': False, 'lon': False, 'Preço': ':.2f'},
        title=f'Receita por estado{" - Região: " + regiao if regiao and regiao != "Brasil" else ""}',
        color='Preço',
        color_continuous_scale='Blues'
    )

    #Removendo o background de fundo do gráfico
    fig_mapa_receita.update_layout(width=500, height=550,  plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        geo=dict(bgcolor= 'rgba(0,0,0,0)'))

    # Ajustes finais no layout do mapa
    fig_mapa_receita.update_layout(
        geo=dict(
            #landcolor='lightgray',
            lakecolor='lightblue',
            oceancolor='azure',
            showcountries=True,
            showsubunits=True,
            #countrycolor='white'
        ),
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )

    # Centralizar o mapa na região selecionada
    if regiao and regiao != 'Brasil':
        regioes_centro = {
            'Centro-Oeste': {'lat': -15.83, 'lon': -54.92},
            'Nordeste': {'lat': -9.65, 'lon': -37.77},
            'Norte': {'lat': -3.47, 'lon': -62.21},
            'Sudeste': {'lat': -19.92, 'lon': -43.17},
            'Sul': {'lat': -27.45, 'lon': -52.43}
        }
        centro = regioes_centro.get(regiao)
        if centro:
            fig_mapa_receita.update_geos(
                center=centro,
                projection_scale=4  # Zoom mais próximo
            )

    #Gráfico de linhas
    if ano and not todos_anos:
        receita_mensal = receita_mensal[receita_mensal['Ano'] == int(ano)]
    fig_receita_mensal = px.line(receita_mensal,
                                    x='Mensal', y='Preço', markers= True,
                                    range_y = (0, receita_mensal['Preço'].max()),
                                    color = 'Ano',
                                    line_dash='Ano',
                                    title='Receita Mensal')
    fig_receita_mensal.update_layout(yaxis_title= 'Receita')



    #Gráfico de barras mostrando a receita por estados
    fig_receita_estados = px.bar(receitas_estados.head(),
                                 x= 'Local da compra',
                                 y= 'Preço',
                                 color= 'Local da compra',
                                 text_auto= True,
                                 title= 'Top Estados (receita)')
    fig_receita_estados.update_layout(yaxis_title='Receita')

    #Gráfico de barras para a receita de cada categoria de produtos

    fig_receita_categorias = px.bar(receita_categorias,
                                    #color = ['#0066CC', '#80CFFF', '#FF2E2E', '#FF9999', '#36A89E', '#ADFF2F'],
                                    text_auto=True,
                                    title='Receita por categoria')
    fig_receita_categorias.update_layout(yaxis_title='Receita', showlegend= False )


#Tabela de quantidade de vendas por estado
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra','lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
#Tabela de quantidade de vendas mensal
vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'M'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month_name()

#Tabela de quantidade de vendas por categoria de produtos
vendas_categorias = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending = False))

#Plot qtd vendas/estado
fig_mapa_vendas = px.scatter_geo(vendas_estados,
                     lat = 'lat',
                     lon= 'lon',
                     scope = 'south america',
                     #fitbounds = 'locations',
                     template='seaborn',
                     size = 'Preço',
                     hover_name ='Local da compra',
                     hover_data = {'lat':False,'lon':False},
                     title = 'Vendas por estado',
                     )

#Plot qtd vendas mensal
fig_vendas_mensal = px.line(vendas_mensal,
              x = 'Mes',
              y='Preço',
              markers = True,
              range_y = (0,vendas_mensal.max()),
              color = 'Ano',
              line_dash = 'Ano',
              title = 'Quantidade de vendas mensal')

fig_vendas_mensal.update_layout(yaxis_title='Quantidade de vendas')

#Plot 5 estados com maior quantidade de vendas
fig_vendas_estados = px.bar(vendas_estados.head(),
                             x ='Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top 5 estados'
)

fig_vendas_estados.update_layout(yaxis_title='Quantidade de vendas')

#Plot qtd de vendas por categoria de produto
fig_vendas_categorias = px.bar(vendas_categorias,
                                text_auto = True,
                                title = 'Vendas por categoria')
fig_vendas_categorias.update_layout(showlegend=False, yaxis_title='Quantidade de vendas')



#Trabalhando com métricas para aprimorar a visualização dos dados
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_num(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
        with coluna2:
            st.metric('Quantidade de vendas', formata_num(dados.shape[0]))
            st.plotly_chart(fig_receita_mensal, use_container_width=True)
            st.plotly_chart(fig_receita_categorias, use_container_width=True)
with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_num(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_vendas, use_container_width=True)
        st.plotly_chart(fig_vendas_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_num(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_vendas_categorias, use_container_width=True)
with aba3:                                                  #min, max, padrão
    qtd_vendedores = st.number_input('Quantidade Vendedores', 2, 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_num(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(
            vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
            x='sum',
            y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
            text_auto=True,
            title=f'Top {qtd_vendedores} vendedores (receita)'
        )

        st.plotly_chart(fig_receita_vendedores)
        with coluna2:
           st.metric('Quantidade de vendas', formata_num(dados.shape[0]))
           fig_vendas_vendedores = px.bar(
               vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
               x='count',
               y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
               text_auto=True,
               title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)'
           )

           st.plotly_chart(fig_vendas_vendedores)
#st.map(dados)






#print(dados)