from source.market_data import *
import pytest
import pandas as pd
symb = ["GGAL", "AAPL", "MSFT", "TSLA", "AMZN"]

def test_obtener_precios():
    for s in symb:
        df = obtener_precios(s)
        if not isinstance(df, pd.DataFrame):
            df = pd.DataFrame(df)
        assert not df.empty, "El DataFrame no debe estar vacío"
        assert list(df.columns) == ["fecha", "apertura", "maximo", "minimo", "cierre", "rendimiento", "volumen"], "Las columnas del DataFrame no son correctas"
        assert len(df) > 0, "El DataFrame debe contener datos"
    df = obtener_precios("INVALID", "2020-01-01", "2020-01-10")
    assert df.empty, "El DataFrame debe estar vacío para un símbolo inválido"

def test_obtener_todos_los_simbolos():
    df = obtener_todos_los_simbolos("argentina", "acciones")
    assert isinstance(df, pd.Series), "La función debe retornar una Serie de pandas"
    assert not df.empty, "La Serie no debe estar vacía"
    assert all(isinstance(sym, str) for sym in df.index), "Todos los símbolos deben ser cadenas de texto"
    assert all(isinstance(url, str) for url in df.values), "Todas las URLs deben ser cadenas de texto"
    df2 = obtener_todos_los_simbolos("argentina", "acciones")
    assert df.equals(df2), "Las llamadas repetidas deben retornar el mismo resultado"
    df3 = obtener_todos_los_simbolos("argentina", "opciones")
    assert isinstance(df3, pd.Series), "La función debe retornar una Serie de pandas"
    assert not df3.empty, "La Serie no debe estar vacía"
    assert all(isinstance(sym, str) for sym in df3.index), "Todos los símbolos deben ser cadenas de texto"
    assert all(isinstance(url, str) for url in df3.values), "Todas las URLs deben ser cadenas de texto"

def test_obtener_intradia():
    for simb in ("GGAL", "ALUA", "METR"):
        df = obtener_intradia(simb, tipo="acciones", bolsa="BCBA")
        assert not df.empty, "El DataFrame no debe estar vacío"
        assert list(df.columns) == ["Hora", "Nominales", "Precio"], "Las columnas del DataFrame no son correctas"
        assert len(df) > 0, "El DataFrame debe contener datos"
    for simb in ("AAPL", "MSFT", "TSLA"):
        df = obtener_intradia(simb, tipo="acciones", bolsa="NASDAQ")
        assert not df.empty, "El DataFrame debe estar vacío para bolsas no soportadas"
        assert list(df.columns) == ["Hora", "Nominales", "Precio"], "Las columnas del DataFrame no son correctas"
        assert len(df) > 0, "El DataFrame debe contener datos"
def test_calcular_CRO():
    for s in symb:
        cro = calcular_CRO(s, "2023-01-01", "2023-12-31")
        assert isinstance(cro, float), "El CRO debe ser un número flotante"
        assert cro >= 0, "El CRO debe ser un valor no negativo"
    cro = calcular_CRO("INVALID", "2023-01-01", "2023-12-31")
    assert cro == 0, "El CRO debe ser 0 para un símbolo inválido"