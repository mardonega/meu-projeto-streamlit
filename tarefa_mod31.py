import pandas as pd
import streamlit as st
import numpy as np
from datetime import datetime
from io import BytesIO
import matplotlib.pyplot as plt
import seaborn as sns

# Configuração inicial da página do Streamlit
st.set_page_config(page_title='Análise RFV', layout="wide")

# Funções auxiliares para exportação de dados e categorização


@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')


@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()
    processed_data = output.getvalue()
    return processed_data


def recencia_class(x, q_dict):
    if x <= q_dict['Recencia'][0.25]:
        return 'A'
    elif x <= q_dict['Recencia'][0.50]:
        return 'B'
    elif x <= q_dict['Recencia'][0.75]:
        return 'C'
    else:
        return 'D'


def freq_val_class(x, fv, q_dict):
    if x <= q_dict[fv][0.25]:
        return 'D'
    elif x <= q_dict[fv][0.50]:
        return 'C'
    elif x <= q_dict[fv][0.75]:
        return 'B'
    else:
        return 'A'

# Função principal da aplicação


def main():
    st.title("Análise RFV - Recência, Frequência e Valor")
    st.write("""
    **RFV** significa recência, frequência, valor e é utilizado para segmentação de clientes baseado no comportamento de compras dos clientes e agrupa eles em clusters parecidos. Utilizando esse tipo de agrupamento podemos realizar ações de marketing e CRM melhores direcionadas, ajudando assim na personalização do conteúdo e até a retenção de clientes.

    Para cada cliente é preciso calcular cada uma das componentes abaixo:

    - **Recência (R)**: Quantidade de dias desde a última compra.
    - **Frequência (F)**: Quantidade total de compras no período.
    - **Valor (V)**: Total de dinheiro gasto nas compras do período.

    E é isso que iremos fazer abaixo.
    """)

    # Carregando arquivo do usuário
    data_file = st.sidebar.file_uploader(
        "Carregue seu arquivo de dados", type=['csv', 'xlsx'])
    if data_file is not None:
        try:
            # Carregando os dados
            df_compras = pd.read_csv(data_file) if data_file.name.endswith(
                '.csv') else pd.read_excel(data_file)
            df_compras['DiaCompra'] = pd.to_datetime(
                df_compras['DiaCompra'], errors='coerce')

            # Cálculo de Recência
            dia_atual = datetime.now()
            df_recencia = df_compras.groupby('ID_cliente', as_index=False)[
                'DiaCompra'].max()
            df_recencia.columns = ['ID_cliente', 'DiaUltimaCompra']
            df_recencia['Recencia'] = (
                dia_atual - df_recencia['DiaUltimaCompra']).dt.days

            # Cálculo de Frequência
            df_frequencia = df_compras.groupby(
                'ID_cliente').CodigoCompra.nunique().reset_index(name='Frequencia')

            # Cálculo de Valor
            df_valor = df_compras.groupby(
                'ID_cliente').ValorTotal.sum().reset_index(name='Valor')

            # Combinação das métricas
            df_rfv = df_recencia.merge(df_frequencia, on='ID_cliente').merge(
                df_valor, on='ID_cliente')

            # Quartis
            q_dict = df_rfv[['Recencia', 'Frequencia', 'Valor']
                            ].quantile([0.25, 0.5, 0.75]).to_dict()

            # Classificação RFV
            df_rfv['R'] = df_rfv['Recencia'].apply(
                lambda x: recencia_class(x, q_dict))
            df_rfv['F'] = df_rfv['Frequencia'].apply(
                lambda x: freq_val_class(x, 'Frequencia', q_dict))
            df_rfv['V'] = df_rfv['Valor'].apply(
                lambda x: freq_val_class(x, 'Valor', q_dict))
            df_rfv['RFV'] = df_rfv['R'] + df_rfv['F'] + df_rfv['V']

            # Dicionário de Ações de Marketing
            action_dict = {
                'AAA': 'Clientes VIP: foco em retenção e programas de fidelidade',
                'AAB': 'Clientes importantes: mantenha o relacionamento ativo',
                'ABB': 'Clientes em crescimento: ofereça incentivos',
                'BBB': 'Clientes comuns: monitore e ofereça promoções',
                'BBC': 'Clientes em recuperação: crie campanhas de reativação',
                'CCC': 'Clientes de risco: considere reativação ou incentivo',
                'CCD': 'Clientes inativos: campanhas de reativação específicas',
                'DDD': 'Clientes perdidos: análise de feedback e retenção'
            }
            df_rfv['Ação'] = df_rfv['RFV'].map(action_dict)

            # Sidebar interativa para selecionar o grupo RFV
            st.sidebar.write("## Selecione o Grupo RFV")
            rfv_selection = st.sidebar.selectbox(
                "Escolha o segmento RFV para análise", sorted(df_rfv['RFV'].unique()))

            # Filtra o DataFrame pelo grupo selecionado
            df_selected_rfv = df_rfv[df_rfv['RFV'] == rfv_selection]

            st.write(f"### Análise do Grupo {rfv_selection}")
            st.write(
                f"Ação recomendada: {action_dict.get(rfv_selection, 'Ação não encontrada')}")
            st.write("Tabela de clientes selecionados:")
            st.write(df_selected_rfv)

            # Visualizações detalhadas
            st.write(
                "Distribuição de Recência, Frequência e Valor para o Grupo Selecionado")
            fig, ax = plt.subplots(1, 3, figsize=(20, 5))

            # Distribuição de Recência
            sns.histplot(df_selected_rfv['Recencia'],
                         bins=10, ax=ax[0], color='skyblue')
            ax[0].set_title("Distribuição de Recência (dias)")

            # Distribuição de Frequência
            sns.histplot(df_selected_rfv['Frequencia'],
                         bins=10, ax=ax[1], color='salmon')
            ax[1].set_title("Distribuição de Frequência")

            # Distribuição de Valor
            sns.histplot(df_selected_rfv['Valor'],
                         bins=10, ax=ax[2], color='lightgreen')
            ax[2].set_title("Distribuição de Valor")

            st.pyplot(fig)

            # Exportação dos dados
            csv_data = convert_df(df_selected_rfv)
            st.download_button("📥 Baixar segmento RFV como CSV",
                               data=csv_data, file_name=f'{rfv_selection}_RFV.csv')

            # Exibição de contagem de ações de marketing para todos os grupos
            st.write("### Quantidade de Clientes por Ação de Marketing:")
            action_counts = df_rfv['Ação'].value_counts().reset_index()
            action_counts.columns = [
                'Ação de Marketing', 'Quantidade de Clientes']
            st.table(action_counts)

            # Gráfico de barras das ações de marketing
            st.write("Gráfico de Ações de Marketing por Quantidade de Clientes:")
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=action_counts, x='Quantidade de Clientes',
                        y='Ação de Marketing', ax=ax)
            ax.set_title("Distribuição de Clientes por Ação de Marketing")
            st.pyplot(fig)

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o arquivo: {e}")


if __name__ == "__main__":
    main()
