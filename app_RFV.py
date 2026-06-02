# Imports
import pandas            as pd
import streamlit         as st
import numpy             as np

from datetime            import datetime
from PIL                 import Image
from io                  import BytesIO

# Configuração para evitar erros em versões recentes do Pandas
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

# Função para converter o df para excel
@st.cache_data
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.close() # Alterado de .save() para .close() para versões recentes
    processed_data = output.getvalue()
    return processed_data

### Criando os segmentos
def recencia_class(x, r, q_dict):
    if x <= q_dict[r][0.25]:
        return 'A'
    elif x <= q_dict[r][0.50]:
        return 'B'
    elif x <= q_dict[r][0.75]:
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
    st.set_page_config(page_title = 'RFV', layout="wide")

    st.write("""# RFV
    RFV significa recência, frequência, valor. É utilizado para segmentação de clientes.""")
    st.markdown("---")

    # Nome do seu arquivo fixo
    arquivo_csv = 'Profissão Cientista de Dados M31 - dados_input 1.csv'

    try:
        # Carregamento automático sem o parâmetro obsoleto
        df_compras = pd.read_csv(arquivo_csv, parse_dates=['DiaCompra'])
        st.success(f"Arquivo '{arquivo_csv}' carregado automaticamente.")
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        st.stop()

    # Processamento RFV
    dia_atual = df_compras['DiaCompra'].max()
    
    # Recência
    df_recencia = df_compras.groupby(by='ID_cliente', as_index=False)['DiaCompra'].max()
    df_recencia.columns = ['ID_cliente','DiaUltimaCompra']
    df_recencia['Recencia'] = df_recencia['DiaUltimaCompra'].apply(lambda x: (dia_atual - x).days)
    
    # Frequência
    df_frequencia = df_compras[['ID_cliente','CodigoCompra']].groupby('ID_cliente').count().reset_index()
    df_frequencia.columns = ['ID_cliente','Frequencia']
    
    # Valor
    df_valor = df_compras[['ID_cliente','ValorTotal']].groupby('ID_cliente').sum().reset_index()
    df_valor.columns = ['ID_cliente','Valor']
    
    # Tabela Final
    df_RF = df_recencia.merge(df_frequencia, on='ID_cliente')
    df_RFV = df_RF.merge(df_valor, on='ID_cliente')
    df_RFV.set_index('ID_cliente', inplace=True)
    
    st.write('## Tabela RFV final', df_RFV.head())

    # Segmentação
    quartis = df_RFV.quantile(q=[0.25,0.5,0.75])
    df_RFV['R_quartil'] = df_RFV['Recencia'].apply(recencia_class, args=('Recencia', quartis))
    df_RFV['F_quartil'] = df_RFV['Frequencia'].apply(freq_val_class, args=('Frequencia', quartis))
    df_RFV['V_quartil'] = df_RFV['Valor'].apply(freq_val_class, args=('Valor', quartis))
    df_RFV['RFV_Score'] = (df_RFV.R_quartil + df_RFV.F_quartil + df_RFV.V_quartil)

    st.write('## Quantidade de clientes por grupos', df_RFV['RFV_Score'].value_counts())

    # Download
    df_xlsx = to_excel(df_RFV)
    st.download_button(label='📥 Download RFV', data=df_xlsx, file_name='RFV_resultado.xlsx')

if __name__ == '__main__':
    main()
