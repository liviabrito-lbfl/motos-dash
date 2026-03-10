import pandas as pd


def tratarDados(df):
    """
    Trata e limpa o dataset de motos removendo registros inválidos.
    
    Args:
        df (pd.DataFrame): DataFrame contendo os dados das motos
        
    Returns:
        pd.DataFrame: DataFrame limpo sem motos inválidas
    """
    
    # Copiar para não modificar o original
    df = df.copy()
    
    # Apaga as motos inválidas do dataset
    df = df[df["Moto"].notnull()]  # motos com valores não nulos
    df = df[df["Moto"] != "Escolha a moto"]  # motos com valor "Escolha a moto"
    
    # atualizar o nome da Moto para ocultar a placa da moto (4 últimos dígitos)
    df["Moto"] = df["Moto"].apply(lambda x: x[:-4] + "****" if pd.notnull(x) else x)

    # Verificar e processar colunas apenas se necessário
    
    # Renomear coluna "Observação " (com espaço) se existir
    if "Observação " in df.columns:
        df.rename(columns={"Observação ": "Observação"}, inplace=True)

    #renomear "Observação" para "Obs" se existir
    if "Observação" in df.columns and "Obs" not in df.columns:
        df.rename(columns={"Observação": "Obs"}, inplace=True)        
    
    # Preenche a coluna Obs/Observação vazia se existir
    if "Obs" in df.columns:
        df["Obs"] = df["Obs"].fillna("Sem observações")    
    
    # Renomear coluna "Tipo (Entrada / Saída)" para "Tipo" se existir
    if "Tipo (Entrada / Saída)" in df.columns:
        df.rename(columns={"Tipo (Entrada / Saída)": "Tipo"}, inplace=True)
    
    # Processar coluna Valor apenas se for string/object
    if "Valor" in df.columns and df["Valor"].dtype == 'object':
        df["Valor"] = df["Valor"].astype(str).str.replace("R$", "", regex=False)
        df["Valor"] = df["Valor"].str.replace(".", "", regex=False)
        df["Valor"] = df["Valor"].str.replace(",", ".", regex=False)
        df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce")
    
    # Processar Data e criar Periodo apenas se necessário
    if "Data" in df.columns:
        # Garantir que Data é datetime
        if df["Data"].dtype == 'object':
            df["Data"] = pd.to_datetime(df["Data"], errors="coerce", dayfirst=True)
        
        # Criar colunas Mes, Ano e Periodo se não existirem
        if "Ano" not in df.columns:
            df["Ano"] = df["Data"].dt.year.astype("Int64")
        if "Mes" not in df.columns:
            df["Mes"] = df["Data"].dt.month.astype("Int64")
        if "Periodo" not in df.columns:
            df['Periodo'] = df['Ano'].astype(str) + '-' + df['Mes'].astype(str).str.zfill(2)
        
        # Remover linhas com Data inválida
        df.dropna(subset=["Data"], inplace=True)
    
    return df
