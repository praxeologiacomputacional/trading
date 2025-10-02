import json
import pandas as pd
from datetime import datetime
from typing import Iterable
import requests
from bs4 import BeautifulSoup


def framear_precios(func):
    def wrapper(*args, **kwargs) -> pd.DataFrame:
        data = func(*args, **kwargs)
        if not data:  # Check if data is empty
            return pd.DataFrame()  # Return empty DataFrame if no data
        sheet = {
            "fecha":       [datetime.fromtimestamp(bar['time']).strftime('%Y-%m-%d') for bar in data],
            "apertura":    [bar['open'] for bar in data],
            "maximo":      [bar['high'] for bar in data],
            "minimo":      [bar['low'] for bar in data],
            "cierre":      [bar['close'] for bar in data],
            "rendimiento": [0]+[((bar2['close']-bar1['close'])/bar1['close'])*100 for bar1, bar2 in zip(data[:-1], data[1:])], #((bar['close'] - bar['open']) / bar['open']) * 100 for bar in data],
            "volumen":     [bar['volume'] for bar in data],
        }
        return pd.DataFrame(sheet)
    return wrapper

@framear_precios
def obtener_precios(simbolo: str = "GGAL", desde: str = "2020-01-01", hasta: str = "2023-01-01", bolsa: str = "BCBA"):
    """
    Obtiene los precios históricos de un símbolo financiero.
    Args:
        simbolo (str): El símbolo financiero (por ejemplo, 'AAPL').
        desde (str): Fecha de inicio en formato 'YYYY-MM-DD'.
        hasta (str): Fecha de fin en formato 'YYYY-MM-DD'.

    Returns:
        pd.DataFrame: Un DataFrame con los precios históricos.
    """
    inicio = int(datetime.strptime(desde, "%Y-%m-%d").timestamp())
    fin = int(datetime.strptime(hasta, "%Y-%m-%d").timestamp())
    url = f"https://iol.invertironline.com/api/cotizaciones/history?symbolName={simbolo}&exchange={bolsa}&from={inicio}&to={fin}&resolution=D"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.content)
        return data["bars"]
    else:
        raise Exception(f"Error al obtener datos: {response.status_code}")

def obtener_todos_los_simbolos(pais="argentina", tipo="acciones"):
    """
    Obtiene los símbolos disponibles en InvertirOnline para un país y panel
    específicos.
    """
    if pais == "argentina" and tipo == "acciones"  :
        rq = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/{pais}/{tipo}/panel-general")
        rq2 = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/{pais}/{tipo}/panel-lideres")
        if rq.status_code == 200 and rq2.status_code == 200:
            soup = BeautifulSoup(rq.content, "html.parser")
            serie1 = pd.Series({row.get("data-symbol"): row.get("href") for row in soup.find("tbody").find_all("a")}) # type: ignore
            soup2 = BeautifulSoup(rq2.content, "html.parser")
            serie2 = pd.Series({row.get("data-symbol"): row.get("href") for row in soup2.find("tbody").find_all("a")}) # pyright: ignore[reportOptionalMemberAccess, reportArgumentType, reportAttributeAccessIssue, reportCallIssue]
            return pd.concat([serie1, serie2]).drop_duplicates()
    elif tipo == "opciones":
        rq = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/{pais}/{tipo}/todas")
        if rq.status_code == 200:
            soup = BeautifulSoup(rq.content, "html.parser")
            tabla = soup.find("tbody")
            data = {row.get("data-symbol"): row.get("href") for row in tabla.find_all("a") if row.get("data-symbol") is not None and row.get("href") is not None} # type: ignore
            return pd.Series(data) # type: ignore
    elif tipo == "bonos" or tipo == "cedears" :
        rq = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/{pais}/{tipo}/todos")
        if rq.status_code == 200:
            soup = BeautifulSoup(rq.content, "html.parser")
            tabla = soup.find("tbody")
            data = {row.get("data-symbol"): row.get("href") for row in tabla.find_all("a") if row.get("data-symbol") is not None and row.get("href") is not None} # type: ignore
            return pd.Series(data) # type: ignore
    elif pais == "estados-unidos":
        rq = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/estados-unidos")
        if rq.status_code == 200 :
            soup = BeautifulSoup(rq.content, "html.parser")
            serie1 = pd.Series({row.get("data-symbol"): row.get("href") for row in soup.find("tbody").find_all("a")}) # type: ignore
            return serie1


def obtener_id(simbolo: str , pais: str = "argentina", tipo: str = "acciones") -> str:
    """
    Obtiene el ID interno de InvertirOnline para un símbolo financiero.
    """
    simbolos = obtener_todos_los_simbolos(pais, tipo)
    if simbolos is None or simbolos.empty:
        raise ValueError("No se encontraron símbolos.")
    try:
        id_simbolo = simbolos[simbolo].split("/")[-1] # type: ignore
        return id_simbolo
    except KeyError:
        raise ValueError(f"El símbolo {simbolo} no se encontró en {pais} - {tipo}.")

def framear_intradia(func):
    def wrapper(*args, **kwargs) -> Iterable:
        data = func(*args, **kwargs)
        if not data:  # Check if data is empty
            return pd.DataFrame()  # Return empty DataFrame instead of raising error
        sheet = {
            "Hora":      [datetime.fromtimestamp(bar['FechaHora']).strftime('%H:%M:%S') for bar in data],
            "Nominales": [bar['CantidadNominal'] for bar in data],
            "Precio":    [bar['Ultima'] for bar in data],
        }
        return pd.DataFrame(sheet)
    return wrapper

@framear_intradia
def obtener_intradia(simbolo: str = "GGAL", pais: str = "argentina", tipo: str = "acciones", bolsa: str = "BCBA"):
    """
    Obtiene los precios intradía de un símbolo financiero.
    Args:
        simbolo (str): El símbolo financiero (por ejemplo, 'AAPL').
        tipo (str): El tipo de activo (por ejemplo, 'acciones').
        bolsa (str): La bolsa de valores (por ejemplo, 'BCBA').

    Returns:
        pd.DataFrame: Un DataFrame con los precios intradía.
    """
    try:
        id_simbolo = obtener_id(simbolo, pais, tipo=tipo)
    except ValueError as e:
        # Return empty list to be handled by the decorator
        print(f"Error obteniendo ID para {simbolo}: {e}")
        return []
    
    if bolsa == "BCBA":
        url = f"https://iol.invertironline.com/Titulo/GraficoIntradiario?idTitulo={id_simbolo}&idTipo=4&idMercado=1"
        response = requests.get(url)
    if bolsa == "NASDAQ":
        url = f"https://iol.invertironline.com/Titulo/GraficoIntradiario?idTitulo={id_simbolo}&idTipo=4&idMercado=3"
    if response.status_code == 200:
        data = json.loads(response.content)
        return data
    else:
        raise Exception(f"Error al obtener datos: {response.status_code}")
    

def calcular_CRO(simbolo, desde, hasta, umbral=0.5):
    datos = obtener_precios(simbolo, desde, hasta)
    
    # Handle empty DataFrame
    if datos.empty or "rendimiento" not in datos.columns:
        return 0.0  # Return default value when no data is available
    
    positives = datos["rendimiento"][datos["rendimiento"] > 0]
    negatives = datos["rendimiento"][datos["rendimiento"] <= 0]
    
    # Handle cases where there are no positive or negative returns
    if len(positives) == 0 or len(negatives) == 0:
        return 0.0
    
    pos_mean = positives.mean()
    neg_mean = negatives.mean()
    pos_std = positives.std()
    neg_std = negatives.std()

    cro = (( len(positives) * (pos_std + pos_mean - ((1 + umbral) ** (1 / 360)-1)))/ ( len(negatives) * abs(neg_std + neg_mean )))
    return cro


def obtener_opciones(simbolo: str = "GGAL", tipo: str="calls") -> pd.DataFrame: # type: ignore
    """
    Obtiene las opciones disponibles para un símbolo financiero.
    Args:
        simbolo (str): El símbolo financiero (por ejemplo, 'AAPL').
    Returns:
        pd.DataFrame: Un DataFrame con las opciones disponibles.
    """
    rq = requests.post("https://iol.invertironline.com/Titulo/Opciones", 
                       data={"id":str(obtener_id(simbolo))})
    soup = BeautifulSoup(rq.content, "html.parser")
    tb = soup.find_all("table")
    if tipo == "calls":
        html_calls = tb[0]
        calls = [row.text.split() for row in html_calls][3]
        calls_dict = {
                  'Último':    [float(r.replace(",",".")) for r in calls[1::10]], 
                  'Variación': [r for r in calls[2::10]], 
                  'Apertura':  [float(r.replace(",",".")) for r in calls[3::10]], 
                  'Max.':      [float(r.replace(",",".")) for r in calls[4::10]], 
                  'Min.':      [float(r.replace(",",".")) for r in calls[5::10]],
                  'Último':    [float(r.replace(",",".")) for r in calls[6::10]], 
                  'Cierre':    [float(r.replace(",",".")) for r in calls[7::10]], 
                  'Volúmen':   [float(r.replace(",",".")) for r in calls[8::10]], 
                  'Fecha.':    [r for r in calls[9::10]]
                  } 
        return pd.DataFrame(calls_dict, index=[r for r in calls[0::10]])
    if tipo == "puts":
        html_puts = tb[1]
        puts = [row.text.split() for row in html_puts][3]
        puts_dict = {
                  'Último':    [float(r.replace(",",".")) for r in puts[1::10]], 
                  'Variación': [r for r in puts[2::10]], 
                  'Apertura':  [float(r.replace(",",".")) for r in puts[3::10]], 
                  'Max.':      [float(r.replace(",",".")) for r in puts[4::10]], 
                  'Min.':      [float(r.replace(",",".")) for r in puts[5::10]],
                  'Último':    [float(r.replace(",",".")) for r in puts[6::10]], 
                  'Cierre':    [float(r.replace(",",".")) for r in puts[7::10]], 
                  'Volúmen':   [float(r.replace(",",".")) for r in puts[8::10]], 
                  'Fecha.':    [r for r in puts[9::10]]
                  } 
        return pd.DataFrame(puts_dict, index=[r for r in puts[0::10]])
    
if __name__ == "__main__":
    calls = obtener_opciones("GGAL","puts")
    validos = calls[calls["Último"] > 0]
    print(validos)