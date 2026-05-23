import os
import glob
import pandas as pd
import unicodedata

GP_POINTS = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}

def normalizar_columnas(df):
    """Mapea las columnas de chess-results a nombres fijos y maneja el bug de TB1."""
    mapping = {}
    for col in df.columns:
        col_clean = str(col).lower().strip()
        if col_clean in ['rk.', 'rk', 'pos', 'pos.', 'posicion', 'no.']:
            mapping[col] = 'Posicion'
        elif col_clean in ['name', 'nombre', 'jugador']:
            mapping[col] = 'Jugador'
        elif col_clean in ['pts', 'pts.', 'puntos', 'ptos']:
            mapping[col] = 'Puntos'
        elif col_clean == 'tb1':
            mapping[col] = 'TB1'
            
    df = df.rename(columns=mapping)
    
    # Fallback: Si no existe 'Puntos' pero sí 'TB1', asumimos que los puntos están ahí
    if 'Puntos' not in df.columns and 'TB1' in df.columns:
        df = df.rename(columns={'TB1': 'Puntos'})
        
    return df

def quitar_tildes(texto):
    """Elimina acentos y marcas diacríticas de un string."""
    texto = unicodedata.normalize('NFD', texto)
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return texto

def limpiar_nombre(nombre_crudo):
    """
    Toma 'apellido, nombre', quita tildes, ajusta espacios extra y 
    estandariza la capitalización (Title Case).
    """
    if not isinstance(nombre_crudo, str):
        return "Desconocido"
    
    nombre_limpio = quitar_tildes(nombre_crudo)
    partes = nombre_limpio.split(',')
    
    if len(partes) >= 2:
        apellido = partes[0]
        nombres = partes[1]
        apellido = " ".join(apellido.split()).title()
        nombres = " ".join(nombres.split()).title()
        return f"{apellido}, {nombres}"
    else:
        limpio = " ".join(nombre_limpio.split()).title()
        return limpio

def cargar_y_procesar_categoria(categoria):
    carpetas_fases = sorted(glob.glob("data/fase_*"))
    dfs_posiciones = []
    
    for idx, carpeta in enumerate(carpetas_fases, start=1):
        archivo_pos = os.path.join(carpeta, f"posiciones_{categoria}.csv")
        if os.path.exists(archivo_pos):
            df = pd.read_csv(archivo_pos)
            df = normalizar_columnas(df)
            df['Fase'] = f"Fase {idx}"
            dfs_posiciones.append(df)
            
    if not dfs_posiciones:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    df_consolidado = pd.concat(dfs_posiciones, ignore_index=True)

    if 'Jugador' in df_consolidado.columns:
        df_consolidado['Jugador'] = df_consolidado['Jugador'].apply(limpiar_nombre)

    # Asegurarnos de que los Puntos sean un número para poder sumarlos
    if 'Puntos' in df_consolidado.columns:
        df_consolidado['Puntos'] = pd.to_numeric(df_consolidado['Puntos'], errors='coerce').fillna(0)
    else:
        df_consolidado['Puntos'] = 0

    if 'Posicion' in df_consolidado.columns:
        df_consolidado['Posicion'] = pd.to_numeric(df_consolidado['Posicion'], errors='coerce')
        df_consolidado['Puntos_GP'] = df_consolidado['Posicion'].map(GP_POINTS).fillna(0)
    else:
        df_consolidado['Puntos_GP'] = 0

    # Acumulado tradicional
    acumulado_puntos = df_consolidado.groupby('Jugador')['Puntos'].sum().reset_index()
    acumulado_puntos = acumulado_puntos.sort_values(by='Puntos', ascending=False).reset_index(drop=True)
    acumulado_puntos.index += 1 

    # Acumulado Grand Prix
    acumulado_gp = df_consolidado.groupby('Jugador')['Puntos_GP'].sum().reset_index()
    acumulado_gp = acumulado_gp.sort_values(by='Puntos_GP', ascending=False).reset_index(drop=True)
    acumulado_gp.index += 1

    return df_consolidado, acumulado_puntos, acumulado_gp
