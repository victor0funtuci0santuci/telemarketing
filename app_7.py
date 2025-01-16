# Imports
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from PIL import Image
from io import BytesIO

# Configuração da página
st.set_page_config(
    page_title='Telemarketing Analysis',
    page_icon='📊',
    layout='wide',
    initial_sidebar_state='expanded'
)

# Set no tema do seaborn para melhorar o visual dos plots
custom_params = {"axes.spines.right": False, "axes.spines.top": False}
sns.set_theme(style="ticks", rc=custom_params)

# Função para ler os dados
@st.cache_data(show_spinner=True)
def load_data(file_data):
    try:
        return pd.read_csv(file_data, sep=';')
    except:
        return pd.read_excel(file_data)

# Função para filtrar baseado na multiseleção de categorias
@st.cache_data
def multiselect_filter(relatorio, col, selecionados):
    if 'all' in selecionados:
        return relatorio
    else:
        return relatorio[relatorio[col].isin(selecionados)].reset_index(drop=True)

# Função para converter o df para CSV
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# Função para converter o df para Excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close()  # Usando close() em vez de save()
    processed_data = output.getvalue()
    return processed_data

# Função principal da aplicação
def main():
    # Título principal da aplicação
    st.write('# Telemarketing Analysis')
    st.markdown("---")
    
    # Apresenta a imagem na barra lateral da aplicação
    image = Image.open("Bank-Branding.jpg")
    st.sidebar.image(image)

    # Botão para carregar arquivo na aplicação
    st.sidebar.write("## Suba o arquivo")
    data_file_1 = st.sidebar.file_uploader("Bank marketing data", type=['csv', 'xlsx'])

    # Verifica se há conteúdo carregado na aplicação
    if data_file_1 is not None:
        bank_raw = load_data(data_file_1)
        bank = bank_raw.copy()

        st.write('## Antes dos filtros')
        st.write(bank_raw.head())

        with st.sidebar.form(key='my_form'):
            # SELECIONA O TIPO DE GRÁFICO
            graph_type = st.radio('Tipo de gráfico:', ('Barras', 'Pizza'))
        
            # IDADES
            max_age = int(bank.age.max())
            min_age = int(bank.age.min())
            idades = st.slider(label='Idade', 
                               min_value=min_age,
                               max_value=max_age, 
                               value=(min_age, max_age),
                               step=1)

            # PROFISSÕES
            jobs_list = bank.job.unique().tolist()
            jobs_list.append('all')
            jobs_selected = st.multiselect("Profissão", jobs_list, ['all'])

            # Estado civil
            marital_list = bank.marital.unique().tolist()
            marital_list.append('all')
            marital_selected = st.multiselect("Estado civil", marital_list, ['all'])

            # Tem empréstimo?
            loan_list = bank.loan.unique().tolist()
            loan_list.append('all')
            loan_selected = st.multiselect("Tem empréstimo?", loan_list, ['all'])

            # Encadeamento de filtros
            bank = (bank.query("age >= @idades[0] and age <= @idades[1]")
                        .pipe(multiselect_filter, 'job', jobs_selected)
                        .pipe(multiselect_filter, 'marital', marital_selected)
                        .pipe(multiselect_filter, 'loan', loan_selected)
                    )

            submit_button = st.form_submit_button(label='Aplicar')
        
        # Botões de download dos dados filtrados
        st.write('## Após os filtros')
        st.write(bank.head())
        
        df_xlsx = to_excel(bank)
        st.download_button(label='📥 Download tabela filtrada em EXCEL',
                           data=df_xlsx,
                           file_name='bank_filtered.xlsx')
        st.markdown("---")

        # Gráficos
        st.write('## Proporção de Aceite')

        fig, ax = plt.subplots(1, 2, figsize=(12, 6))  # Ajuste de tamanho

        # Dados originais
        bank_raw_target_perc = bank_raw.y.value_counts(normalize=True).to_frame() * 100
        bank_raw_target_perc.columns = ['percentage']  # Renomear coluna
        bank_raw_target_perc = bank_raw_target_perc.sort_index()

        # Dados filtrados
        try:
            bank_target_perc = bank.y.value_counts(normalize=True).to_frame() * 100
            bank_target_perc.columns = ['percentage']
            bank_target_perc = bank_target_perc.sort_index()
        except:
            bank_target_perc = pd.DataFrame(columns=['percentage'])

        # Verifica se há dados para plotar
        if not bank_raw_target_perc.empty and not bank_target_perc.empty:
            if graph_type == 'Barras':
                sns.barplot(
                    x=bank_raw_target_perc.index,
                    y='percentage',
                    data=bank_raw_target_perc,
                    ax=ax[0]
                )
                ax[0].bar_label(ax[0].containers[0])
                ax[0].set_title('Dados brutos', fontweight="bold")

                sns.barplot(
                    x=bank_target_perc.index,
                    y='percentage',
                    data=bank_target_perc,
                    ax=ax[1]
                )
                ax[1].bar_label(ax[1].containers[0])
                ax[1].set_title('Dados filtrados', fontweight="bold")
            else:
                bank_raw_target_perc.plot(
                    kind='pie',
                    y='percentage',
                    autopct='%.2f',
                    ax=ax[0],
                    legend=False
                )
                ax[0].set_ylabel('')
                ax[0].set_title('Dados brutos', fontweight="bold")

                bank_target_perc.plot(
                    kind='pie',
                    y='percentage',
                    autopct='%.2f',
                    ax=ax[1],
                    legend=False
                )
                ax[1].set_ylabel('')
                ax[1].set_title('Dados filtrados', fontweight="bold")

            st.pyplot(fig)
        else:
            st.warning('Sem dados suficientes para exibir os gráficos.')

if __name__ == '__main__':
    main()
