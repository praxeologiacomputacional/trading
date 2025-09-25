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
            serie1 = pd.Series({row.get("data-symbol"): row.get("href") for row in soup.find("tbody").find_all("a")})
            soup2 = BeautifulSoup(rq2.content, "html.parser")
            serie2 = pd.Series({row.get("data-symbol"): row.get("href") for row in soup2.find("tbody").find_all("a")})
            return pd.concat([serie1, serie2]).drop_duplicates()
    elif tipo == "opciones":
        rq = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/{pais}/{tipo}/todas")
        if rq.status_code == 200:
            soup = BeautifulSoup(rq.content, "html.parser")
            tabla = soup.find("tbody")
            return pd.Series({row.get("data-symbol"): row.get("href") for row in tabla.find_all("a")})
    elif tipo == "bonos" or tipo == "cedears" :
        rq = requests.get(f"https://iol.invertironline.com/mercado/cotizaciones/{pais}/{tipo}/todos")
        if rq.status_code == 200:
            soup = BeautifulSoup(rq.content, "html.parser")
            tabla = soup.find("tbody")
            return pd.Series({row.get("data-symbol"): row.get("href") for row in tabla.find_all("a")})
        