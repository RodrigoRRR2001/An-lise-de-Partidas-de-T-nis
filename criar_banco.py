import sqlite3
from openpyxl import Workbook
def criar_banco_completo():
    # Configurações
    db_path = r"C:\Users\rodri\Desktop\tenis_analises_db.db"
    excel_path = r"C:\Users\rodri\Desktop\dados_tenis.xlsx"
    
    # Conecta ao banco (cria se não existir)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # ===== 1. CRIA TABELAS COM TIPOS ESPECÍFICOS =====
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Partidas (
        partida_id INTEGER PRIMARY KEY AUTOINCREMENT,
        data TEXT,
        adversario TEXT,
        ranking_adversario INTEGER,
        resultado TEXT,
        duracao_minutos INTEGER,
        superficie TEXT,
        clima TEXT,
        cansaco_pre_jogo INTEGER,
        qualidade_sono INTEGER,
        dias_descanso INTEGER,
        observacoes TEXT
       
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Rallys (
        rally_id INTEGER PRIMARY KEY AUTOINCREMENT,
        partida_id INTEGER,
        set_num INTEGER,
        game_num INTEGER,
        ponto_num INTEGER,
        ace INTEGER,  -- BOOLEANO (0/1)
        servidor  INTEGER,  -- BOOLEANO (0/1)
        primeiro_servico INTEGER,  -- BOOLEANO (0/1)
        falha_servico INTEGER,     -- BOOLEANO (0/1)
        devolucao_dentro INTEGER,  -- BOOLEANO (0/1)
        break_point INTEGER,       -- BOOLEANO (0/1)
        subiu_rede INTEGER,        -- BOOLEANO (0/1)
        tipo_ponto TEXT,
        golpe_vencedor TEXT,
        direcao_golpe TEXT,
        num_trocas INTEGER,
        direcao_servico TEXT,
        placar TEXT  -- NOVO CAMPO,
        ganhador_ponto INTEGER     -- BOOLEANO (0/1)
    )
    """)

    # ===== 3. CRIA ARQUIVO EXCEL MODELO =====
    wb = Workbook()
    
    # Planilha Partidas (com placar)
    ws_partidas = wb.active
    ws_partidas.title = "Partidas"
    ws_partidas.append([
        "data", "adversario", "ranking_adversario", "resultado", 
        "duracao_minutos", "superficie", "clima", "cansaco_pre_jogo",
        "qualidade_sono", "dias_descanso", "observacoes"  
    ])
    
    # Planilha Rallys
    ws_rallys = wb.create_sheet("Digitação")
    ws_rallys.append([
        "partida_id", "set_num", "game_num", "ponto_num", "ace", 
        "servidor", "primeiro_servico", "falha_servico", "devolucao_dentro",
        "break_point", "subiu_rede", "tipo_ponto", "golpe_vencedor",
        "direcao_golpe", "num_trocas", "direcao_servico", "ganhador_ponto","placar"
    ])
    
    wb.save(excel_path)

    conn.commit()
    conn.close()
    print(f"""✅ Banco criado com sucesso!
    - Local do banco: {db_path}
    - Modelo Excel gerado: {excel_path}""")

# Executa a criação
criar_banco_completo()