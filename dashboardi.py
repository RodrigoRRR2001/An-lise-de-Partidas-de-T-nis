import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Configuração do dashboard
st.set_page_config(page_title="Análise de Tênis - Rodrigo", layout="wide")

# Conexão com o banco de dados
@st.cache_data
def carregar_dados():
    conn = sqlite3.connect('tenis_analises_db.db')
    
    # Carrega dados das partidas
    partidas = pd.read_sql("SELECT * FROM partidas", conn)
    
    # Carrega dados dos rallys
    rallys = pd.read_sql("""
        SELECT 
            partida_id, set_num, game_num, ponto_num,
            ace, servidor, primeiro_servico, falha_servico,
            devolucao_dentro, tipo_ponto, golpe_vencedor,
            direcao_golpe, num_trocas, direcao_servico, placar
        FROM rallys
    """, conn)
    
    conn.close()
    
    return partidas, rallys

# Processamento dos dados com nova lógica de placar
@st.cache_data
def processar_dados(partidas, rallys):
    # Adiciona nome do jogador
    partidas['jogador'] = 'Rodrigo R'
    df = pd.merge(rallys, partidas, on='partida_id')
    
    # Calcula quem ganhou o ponto (0 = adversário, 1 = Rodrigo)
    df['ganhador_ponto'] = df['ponto_num']
    
    # Nova lógica de placar - inicia em 00-00
    def calcular_placar(df):
        placar_sacador = 0
        placar_receptor = 0
        placares = []
        
        for idx, row in df.iterrows():
            placares.append(f"{placar_sacador}-{placar_receptor}")
            
            if row['ganhador_ponto'] == row['servidor']:
                # Ponto para o sacador
                if placar_sacador == 0: placar_sacador = 15
                elif placar_sacador == 15: placar_sacador = 30
                elif placar_sacador == 30: placar_sacador = 40
                elif placar_sacador == 40:
                    if placar_receptor == 40: placar_sacador = 'ADV'
                    elif placar_receptor == 'ADV': placar_sacador, placar_receptor = 40, 40
                    else: placar_sacador = 'V'
            else:
                # Ponto para o receptor
                if placar_receptor == 0: placar_receptor = 15
                elif placar_receptor == 15: placar_receptor = 30
                elif placar_receptor == 30: placar_receptor = 40
                elif placar_receptor == 40:
                    if placar_sacador == 40: placar_receptor = 'ADV'
                    elif placar_sacador == 'ADV': placar_sacador, placar_receptor = 40, 40
                    else: placar_receptor = 'V'
            
            if 'V' in [placar_sacador, placar_receptor]:
                placar_sacador = placar_receptor = 0
        
        return placares
    
    # Aplica a nova lógica de placar para cada game
    df['novo_placar'] = df.groupby(['partida_id', 'set_num', 'game_num']).apply(calcular_placar).explode().values
    
    # Estatísticas por jogador
    def calcular_stats_jogador(df, jogador):
        jogador_df = df[df['ganhador_ponto'] == jogador]
        adversario_df = df[df['ganhador_ponto'] == 1 - jogador]
        
        stats = {
            'total_pontos': len(jogador_df),
            'total_erros': len(jogador_df[jogador_df['tipo_ponto'].str.contains('Erro', na=False)]),
            'erros_backhand': len(jogador_df[jogador_df['golpe_vencedor'] == 'Backhand']),
            'erros_forehand': len(jogador_df[jogador_df['golpe_vencedor'] == 'Forehand']),
            'total_winners': len(jogador_df[jogador_df['tipo_ponto'] == 'Winner']),
            'winners_backhand': len(jogador_df[(jogador_df['tipo_ponto'] == 'Winner') & 
                                             (jogador_df['golpe_vencedor'] == 'Backhand')]),
            'winners_forehand': len(jogador_df[(jogador_df['tipo_ponto'] == 'Winner') & 
                                             (jogador_df['golpe_vencedor'] == 'Forehand')]),
            'duplas_faltas': len(adversario_df[(adversario_df['tipo_ponto'] == 'Dupla Falta') & 
                                             (adversario_df['falha_servico'] == 1)]),
            'devolucao_fora': len(jogador_df[(jogador_df['servidor'] == 1 - jogador) & 
                                           (jogador_df['devolucao_dentro'] == 0)]),
            'pontos_saque': len(jogador_df[jogador_df['servidor'] == jogador]),
            'pontos_recebimento': len(jogador_df[jogador_df['servidor'] == 1 - jogador])
        }
        
        # Estatísticas de saque apenas para o jogador
        if jogador == 1:
            saque_jogador = df[df['servidor'] == jogador]
            stats.update({
                'pct_primeiro_servico': (saque_jogador['primeiro_servico'] == 1).mean() * 100,
                'pct_pontos_1serv': (saque_jogador[saque_jogador['primeiro_servico'] == 1]['ganhador_ponto'] == jogador).mean() * 100,
                'pct_pontos_2serv': (saque_jogador[saque_jogador['primeiro_servico'] == 0]['ganhador_ponto'] == jogador).mean() * 100,
                'aces': saque_jogador['ace'].sum()
            })
        
        return stats
    
    # Calcula estatísticas para ambos os jogadores
    stats_rodrigo = calcular_stats_jogador(df, 1)
    stats_adversario = calcular_stats_jogador(df, 0)
    
    # Heatmap de pressão
    def calcular_pressao(placar):
        try:
            a, b = placar.split('-')
            if a == 'ADV' or b == 'ADV':
                return 'Vantagem'
            elif a == b:
                return 'Empate'
            elif a.isdigit() and b.isdigit():
                if int(a) > int(b):
                    return 'Frente'
                else:
                    return 'Atras'
            return 'Outro'
        except:
            return 'Outro'
    
    df['situacao_pressao'] = df['novo_placar'].apply(calcular_pressao)
    heatmap_data = df.groupby(['situacao_pressao', 'ganhador_ponto']).size().unstack().fillna(0)
    heatmap_data['Total'] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.div(heatmap_data['Total'], axis=0) * 100
    heatmap_data = heatmap_data.drop(columns='Total')
    
    # Sequência de pontos
    df['sequencia'] = (df['ganhador_ponto'].diff() != 0).cumsum()
    sequencia_pontos = df.groupby(['partida_id', 'set_num', 'sequencia', 'ganhador_ponto']).size().reset_index(name='count')
    
    return df, stats_rodrigo, stats_adversario, heatmap_data, sequencia_pontos

# Carrega e processa os dados
partidas, rallys = carregar_dados()
df_full, stats_rodrigo, stats_adversario, heatmap_data, sequencia_pontos = processar_dados(partidas, rallys)

# --- Sidebar (Filtros) ---
st.sidebar.header("Filtros")

# Filtro por adversário
adversarios = df_full['adversario'].unique()
adversario_selecionado = st.sidebar.selectbox(
    "Selecione o Adversário",
    options=sorted(adversarios)
)

# Filtro por data
datas = df_full[df_full['adversario'] == adversario_selecionado]['data'].unique()
data_selecionada = st.sidebar.selectbox(
    "Selecione a Data",
    options=sorted(datas, reverse=True)
)

# Filtro por set
sets_disponiveis = df_full[(df_full['adversario'] == adversario_selecionado) & 
                          (df_full['data'] == data_selecionada)]['set_num'].unique()
set_selecionado = st.sidebar.selectbox(
    "Selecione o Set",
    options=['Todos'] + sorted(sets_disponiveis.tolist())
)

# Filtro por jogador
jogador_selecionado = st.sidebar.radio(
    "Mostrar estatísticas de:",
    options=['Rodrigo', 'Adversário'],
    index=0
)

# Aplica filtros
filtro = (df_full['adversario'] == adversario_selecionado) & (df_full['data'] == data_selecionada)
if set_selecionado != 'Todos':
    filtro &= (df_full['set_num'] == set_selecionado)

df_filtrado = df_full[filtro]

# Seleciona estatísticas do jogador escolhido
stats = stats_rodrigo if jogador_selecionado == 'Rodrigo' else stats_adversario

# --- Página Principal ---
st.title(f"🎾 Análise de Desempenho - Rodrigo vs {adversario_selecionado}")
st.caption(f"Partida em {data_selecionada} | Set: {set_selecionado if set_selecionado != 'Todos' else 'Todos'}")

# Métricas Principais
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Pontos", stats['total_pontos'])
col2.metric("Pontos no Saque", f"{stats['pontos_saque']} ({stats['pontos_saque']/stats['total_pontos']*100:.1f}%)")
col3.metric("Pontos no Recebimento", f"{stats['pontos_recebimento']} ({stats['pontos_recebimento']/stats['total_pontos']*100:.1f}%)")
col4.metric("Devolução Fora", stats['devolucao_fora'])

if jogador_selecionado == 'Rodrigo':
    st.subheader("Estatísticas de Saque")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("% 1° Saque", f"{stats['pct_primeiro_servico']:.1f}%")
    col2.metric("% Pontos no 1° Saque", f"{stats['pct_pontos_1serv']:.1f}%")
    col3.metric("% Pontos no 2° Saque", f"{stats['pct_pontos_2serv']:.1f}%")
    col4.metric("Aces", stats['aces'])

st.divider()

# Gráficos de Erros e Winners
st.subheader("Distribuição de Erros e Winners")

col1, col2 = st.columns(2)

with col1:
    fig_erros = px.pie(
        names=['Backhand', 'Forehand', 'Outros'],
        values=[
            stats['erros_backhand'],
            stats['erros_forehand'],
            stats['total_erros'] - stats['erros_backhand'] - stats['erros_forehand']
        ],
        title=f'Erros de {jogador_selecionado}',
        hole=0.4,
        color_discrete_sequence=['#FFA15A', '#19D3F3', '#FF6692']
    )
    st.plotly_chart(fig_erros, use_container_width=True)

with col2:
    fig_winners = px.pie(
        names=['Backhand', 'Forehand', 'Outros'],
        values=[
            stats['winners_backhand'],
            stats['winners_forehand'],
            stats['total_winners'] - stats['winners_backhand'] - stats['winners_forehand']
        ],
        title=f'Winners de {jogador_selecionado}',
        hole=0.4,
        color_discrete_sequence=['#00CC96', '#636EFA', '#AB63FA']
    )
    st.plotly_chart(fig_winners, use_container_width=True)

# --- Página de Análise Detalhada ---
st.header("📊 Análise Detalhada")

tab1, tab2 = st.tabs(["Pressão nos Pontos", "Sequência de Pontos"])

with tab1:
    st.subheader("Desempenho em Situações de Pressão")
    
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Ganhador do Ponto", y="Situação", color="%"),
        x=['Adversário', 'Rodrigo'],
        y=heatmap_data.index,
        text_auto=".1f",
        aspect="auto",
        color_continuous_scale='RdYlGn'
    )
    fig_heatmap.update_xaxes(side="top")
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown("""
    **Legenda:**
    - **Frente**: Quando você estava ganhando no placar do game
    - **Atras**: Quando você estava perdendo no placar do game
    - **Empate**: Quando o placar estava igualado
    - **Vantagem**: Situação de vantagem no game
    """)

with tab2:
    st.subheader("Sequência de Pontos")
    
    # Calcula sequência máxima para o jogador selecionado
    jogador_num = 1 if jogador_selecionado == 'Rodrigo' else 0
    sequencia_filtrada = sequencia_pontos[
        (sequencia_pontos['partida_id'].isin(df_filtrado['partida_id'])) &
        (sequencia_pontos['set_num'] == (set_selecionado if set_selecionado != 'Todos' else sequencia_pontos['set_num'])) &
        (sequencia_pontos['ganhador_ponto'] == jogador_num)
    ]
    
    max_sequencia = sequencia_filtrada['count'].max() if not sequencia_filtrada.empty else 0
    
    st.metric(f"Maior sequência de pontos ({jogador_selecionado})", max_sequencia)
    
    # Gráfico de sequência de pontos
    df_sequencia = df_filtrado.copy()
    df_sequencia['acumulado'] = df_sequencia.groupby(
        (df_sequencia['ganhador_ponto'].diff() != 0).cumsum()
    )['ganhador_ponto'].cumcount() + 1
    
    fig_sequencia = px.line(
        df_sequencia,
        x=df_sequencia.index,
        y='acumulado',
        color='ganhador_ponto',
        color_discrete_map={0: '#EF553B', 1: '#00CC96'},
        labels={'acumulado': 'Pontos Consecutivos', 'ganhador_ponto': 'Jogador'},
        title='Sequência de Pontos durante a Partida'
    )
    fig_sequencia.update_layout(showlegend=True)
    st.plotly_chart(fig_sequencia, use_container_width=True)

# Rodapé
st.divider()
st.caption(f"Dashboard criado por Rodrigo R | Dados atualizados em {datetime.now().strftime('%d/%m/%Y %H:%M')}")