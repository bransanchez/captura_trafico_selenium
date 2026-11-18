import json
import re
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

CLAVES_SENSIBLES = {
    "cookie", "set-cookie", "authorization", "x-csrf-token", "proxy-authorization",
    "x-api-key", "api_key", "apikey", "token", "access_token", "refresh_token",
    "id_token", "session", "session_id", "sessionid", "password", "email"
}


def limpiar_texto(texto: str) -> str:
    if not isinstance(texto, str):
        return texto
    texto = re.sub(r'eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[JWT_REDACTADO]', texto)
    texto = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[EMAIL_REDACTADO]', texto)
    return texto


def limpiar_url(url: str) -> str:
    if not url or url.startswith(("data:", "blob:")):
        return url
    parsed = urlparse(url)
    if not parsed.query:
        return url
    params = parse_qs(parsed.query, keep_blank_values=True)
    limpios = {
        k: ["[REDACTADO]"] if k.lower() in CLAVES_SENSIBLES or "token" in k.lower() else v
        for k, v in params.items()
    }
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(limpios, doseq=True), parsed.fragment))


def limpiar_lista_headers(headers: list) -> list:
    for h in headers:
        nombre = h.get("name", "").lower()
        if nombre in CLAVES_SENSIBLES or any(s in nombre for s in ("cookie", "token", "auth", "key", "secret")):
            h["value"] = "[REDACTADO]"
    return headers


def procesar_y_comparar():
    # 1. Cargar HAR original de Chrome y sanitizarlo
    with open("captura_chrome.har", "r", encoding="utf-8") as f:
        har = json.load(f)

    entradas_har = har.get("log", {}).get("entries", [])

    for entry in entradas_har:
        req = entry.get("request", {})
        res = entry.get("response", {})

        # Limpiar cookies explícitas del HAR
        req["cookies"] = []
        res["cookies"] = []

        # Limpiar encabezados y URLs
        req["headers"] = limpiar_lista_headers(req.get("headers", []))
        res["headers"] = limpiar_lista_headers(res.get("headers", []))
        req["url"] = limpiar_url(req.get("url", ""))

        # Limpiar parámetros queryString
        for q in req.get("queryString", []):
            if q.get("name", "").lower() in CLAVES_SENSIBLES:
                q["value"] = "[REDACTADO]"

        # Limpiar cuerpos (postData y content.text)
        if "postData" in req and "text" in req["postData"]:
            req["postData"]["text"] = limpiar_texto(req["postData"]["text"])
        if "content" in res and "text" in res["content"]:
            res["content"]["text"] = limpiar_texto(res["content"]["text"])

    with open("captura_chrome_sanitizada.har", "w", encoding="utf-8") as f_out:
        json.dump(har, f_out, ensure_ascii=False, indent=2)

    # 2. Cargar registro de Selenium para cruzar datos
    with open("registro_red_completo.json", "r", encoding="utf-8") as f_sel:
        datos_sel = json.load(f_sel)

    solicitudes_sel = datos_sel.get("solicitudes", [])

    # Emparejar por (Método, URL limpia)
    mapa_sel = {}
    for s in solicitudes_sel:
        clave = (s["solicitud"]["metodo_http"], s["solicitud"]["url"])
        mapa_sel.setdefault(clave, []).append(s)

    mapa_har = {}
    for e in entradas_har:
        clave = (e["request"]["method"], e["request"]["url"])
        mapa_har.setdefault(clave, []).append(e)

    todas_claves = set(mapa_sel.keys()) | set(mapa_har.keys())
    coincidencias = 0
    solo_selenium = []
    solo_chrome = []

    for clave in sorted(todas_claves):
        cant_s = len(mapa_sel.get(clave, []))
        cant_h = len(mapa_har.get(clave, []))
        coincidencias += min(cant_s, cant_h)
        if cant_s > cant_h:
            solo_selenium.append((clave[0], clave[1], cant_s - cant_h))
        elif cant_h > cant_s:
            solo_chrome.append((clave[0], clave[1], cant_h - cant_s))

    print("\n" + "=" * 70)
    print("RESUMEN PARA TU TABLA DE COMPARACIÓN (SELENIUM VS CHROME DEVTOOLS)")
    print("=" * 70)
    print(f"Total solicitudes en Selenium : {len(solicitudes_sel)}")
    print(f"Total solicitudes en Chrome   : {len(entradas_har)}")
    print(f"Coincidencias exactas         : {coincidencias}")
    print("-" * 70)

    print("\n[A] DETALLE DE LLAMADA A API DE BÚSQUEDA (rest.php / api.php):")
    for clave in sorted(todas_claves):
        if "rest.php" in clave[1] or "api.php" in clave[1]:
            s_item = mapa_sel.get(clave, [None])[0]
            h_item = mapa_har.get(clave, [None])[0]
            print(f"  Endpoint: {clave[0]} {clave[1]}")
            if s_item:
                print(f"    -> Selenium: Estado={s_item['respuesta']['estado_http']}, "
                      f"Bytes={s_item['respuesta']['bytes_transferidos']}, "
                      f"Duración={s_item['tiempos']['duracion_ms']} ms")
            if h_item:
                print(f"    -> Chrome  : Estado={h_item['response']['status']}, "
                      f"Bytes={h_item['response'].get('_transferSize', h_item['response']['bodySize'])}, "
                      f"Duración={round(h_item['time'], 2)} ms")

    print("\n[B] DIFERENCIAS ENCONTRADAS:")
    if solo_selenium:
        print("  Adicionales en Selenium:")
        for m, u, c in solo_selenium:
            print(f"    + ({c}x) {m} {u[:90]}")
    if solo_chrome:
        print("  Adicionales en Chrome DevTools:")
        for m, u, c in solo_chrome:
            print(f"    + ({c}x) {m} {u[:90]}")
    if not solo_selenium and not solo_chrome:
        print("  ¡100% de coincidencia en las URLs solicitadas!")

    print("\nArchivo limpio listo para entregar: captura_chrome_sanitizada.har")


if __name__ == "__main__":
    procesar_y_comparar()