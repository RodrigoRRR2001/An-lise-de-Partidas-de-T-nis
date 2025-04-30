import pdfkit
from jinja2 import Template

# Crie um template HTML para o relatório
html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Relatório de Partida de Tênis - Rodrigo vs {{ adversario }}</title>
    <style>
        body { font-family: Arial, sans-serif; }
        .section { margin-bottom: 30px; }
        .chart { width: 100%; margin: 20px 0; }
        .metrics { display: flex; flex-wrap: wrap; gap: 20px; }
        .metric { background: #f5f5f5; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Relatório de Partida de Tênis</h1>
    <h2>Rodrigo vs {{ adversario }} ({{ data }})</h2>
    
    <div class="section">
        <h3>Métricas Principais</h3>
        <div class="metrics">
            <div class="metric">Total de Pontos: {{ total_pontos }}</div>
            <div class="metric">Pontos no Saque: {{ pontos_saque }} ({{ pct_pontos_saque }}%)</div>
            <div class="metric">Pontos no Recebimento: {{ pontos_recebimento }} ({{ pct_pontos_recebimento }}%)</div>
        </div>
    </div>

    <div class="section">
        <h3>Gráficos</h3>
        <div class="chart">{{ plot_erros }}</div>
        <div class="chart">{{ plot_winners }}</div>
        <div class="chart">{{ plot_heatmap }}</div>
    </div>
</body>
</html>
"""

# Renderize os gráficos como HTML
plot_erros = fig_erros.to_html(full_html=False)
plot_winners = fig_winners.to_html(full_html=False)
plot_heatmap = fig_heatmap.to_html(full_html=False)

# Preencha o template com os dados
template = Template(html_template)
html_content = template.render(
    adversario=adversario_selecionado,
    data=data_selecionada,
    total_pontos=stats['total_pontos'],
    pontos_saque=stats['pontos_saque'],
    pct_pontos_saque=f"{stats['pontos_saque']/stats['total_pontos']*100:.1f}",
    pontos_recebimento=stats['pontos_recebimento'],
    pct_pontos_recebimento=f"{stats['pontos_recebimento']/stats['total_pontos']*100:.1f}",
    plot_erros=plot_erros,
    plot_winners=plot_winners,
    plot_heatmap=plot_heatmap
)

# Salve como PDF
pdfkit.from_string(html_content, "relatorio_tenis.pdf")
