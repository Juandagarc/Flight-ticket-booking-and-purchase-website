"""HU-009 · Consulta de noticias y promociones (CU-14)."""

from sqlalchemy import text

from tests.ayudas_vuelos import publicar_promocion


def test_vuelo_nuevo_aparece_en_noticias_apenas_se_programa(client, programar):
    assert client.get("/noticias").json() == []
    vuelo = programar(origen="MDE", destino="LON")
    noticias = client.get("/noticias").json()
    assert [n["vuelo_codigo"] for n in noticias] == [vuelo["codigo"]]


def test_cada_noticia_trae_imagen_ruta_fecha_y_precio(client, programar):
    vuelo = programar(origen="CLO", destino="BUE")
    n = client.get("/noticias").json()[0]
    assert n["imagen_url"]
    assert n["origen"]["codigo"] == "CLO" and n["destino"]["codigo"] == "BUE"
    assert n["salida_local"] == vuelo["salida_local"]
    assert float(n["precio_unitario"]) > 0


def test_promocion_aparece_con_su_precio_unitario(client, db, programar):
    vuelo = programar()
    publicar_promocion(db, vuelo, precio=199000)
    promos = client.get("/noticias", params={"tipo": "PROMOCION"}).json()
    assert len(promos) == 1
    assert float(promos[0]["precio_unitario"]) == 199000
    assert len(client.get("/noticias").json()) == 2


def test_no_se_necesita_iniciar_sesion(client, programar):
    programar()
    r = client.get("/noticias")
    assert r.status_code == 200 and len(r.json()) == 1


def test_mas_reciente_primero(client, programar):
    a = programar()
    b = programar(destino="MDE")
    assert [n["vuelo_codigo"] for n in client.get("/noticias").json()] == [b["codigo"], a["codigo"]]


def test_noticias_de_vuelos_cancelados_o_vencidas_no_se_muestran(client, db, programar):
    a = programar()
    b = programar(destino="MDE")
    db.execute(text("UPDATE vuelo SET estado = 'CANCELADO' WHERE codigo = :c"), {"c": a["codigo"]})
    db.execute(text("UPDATE noticia SET vigente = FALSE WHERE vuelo_codigo = :c"), {"c": b["codigo"]})
    db.commit()
    assert client.get("/noticias").json() == []
