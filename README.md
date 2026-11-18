# Captura y Auditoría de Tráfico de Red con Python y Selenium

Este proyecto automatiza la navegación e interacción sobre una aplicación web real utilizando **Selenium WebDriver** en Python, capturando de forma programática todo el tráfico HTTP/HTTPS generado por el navegador a través de los registros de rendimiento del **Chrome DevTools Protocol (CDP)**.

El flujo ejecuta una búsqueda interactiva en Wikipedia, correlaciona los eventos de red (`Network.*`) por `requestId` —conservando redirecciones, encabezados adicionales, tiempos de respuesta desglosados (DNS, TCP, TLS, TTFB, descarga) y cuerpos de APIs—, sanitiza cualquier dato sensible y exporta los resultados en formatos estructurados (`JSON` y `CSV`). Finalmente, contrasta la captura automatizada contra un archivo `.har` nativo de Chrome DevTools para validar la integridad y precisión de los datos obtenidos.

---

## Estructura del Proyecto

* `main.py`: Script principal que automatiza Chrome, captura los eventos `Network.*` vía CDP, sanitiza datos sensibles y genera los registros de salida.
* `comparar_y_sanitizar.py`: Script auxiliar que limpia cookies/tokens del archivo `.har` exportado desde Chrome y cruza los resultados contra el JSON de Selenium.
* `registro_red_completo.json`: Registro detallado de todas las solicitudes, encabezados, tiempos por fase y cuerpos de respuesta sanitizados.
* `resumen_red.csv`: Tabla resumen por solicitud con métricas clave de estado, tamaño y tiempos en milisegundos.
* `captura_chrome_sanitizada.har`: Evidencia de red exportada desde Chrome DevTools y sanitizada para comparación.
* `requirements.txt`: Dependencias del entorno Python (`selenium`).

---

## Pasos para instalar y ejecutar el proyecto

### 1. Requisitos previos
* Tener **Python 3.10+** instalado.
* Tener **Google Chrome** instalado en el sistema.

### 2. Clonar el repositorio y preparar el entorno virtual
Abre una terminal en la carpeta raíz del proyecto y ejecuta:

```bash
# Crear el entorno virtual
python -m venv venv

# Activar el entorno virtual en Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activar el entorno virtual en Linux / macOS
# source venv/bin/activate

# Instalar las dependencias del proyecto
pip install -r requirements.txt
```

### 3. Ejecutar la captura automatizada
Con el entorno virtual activo, ejecuta el script principal:

```bash
python main.py
```

Al finalizar la ejecución (toma aproximadamente 5 a 8 segundos), se generarán automáticamente los archivos `registro_red_completo.json` y `resumen_red.csv` en la raíz del proyecto.

---

## Fundamentos de Selenium WebDriver

### ¿Qué es Selenium WebDriver?
Es una herramienta que permite automatizar navegadores web. En lugar de mover el ratón y escribir manualmente con el teclado, se escriben instrucciones en código para que el navegador ejecute acciones reales de usuario, siendo ampliamente utilizado en pruebas automatizadas y análisis web.

### ¿Cómo controla Chrome desde Python?
Python no se comunica directamente con Google Chrome. Selenium actúa como intermediario enviando comandos a través del protocolo W3C WebDriver hacia **ChromeDriver** (gestionado automáticamente por Selenium Manager), el cual traduce esas órdenes directamente al navegador Chrome y expone el Chrome DevTools Protocol (CDP).

### ¿Qué son los localizadores (`Locators`)?
Para que Python pueda interactuar con un botón o campo de texto, primero debe ubicarlo dentro del DOM (HTML) de la página. Los localizadores son las estrategias de búsqueda de dichos elementos: por atributo `ID`, `NAME` (como `By.NAME, "search"` usado en este proyecto), selectores `CSS` o rutas `XPath`.

### ¿Qué son las esperas explícitas (`Explicit Waits`)?
Las páginas web cargan de forma asíncrona. Si el script intenta interactuar con un elemento antes de que exista en el DOM, fallará. Las esperas explícitas (`WebDriverWait` junto con `expected_conditions`) pausan la ejecución hasta un tiempo máximo definido (ej. 10 segundos) hasta que el elemento específico sea visible y cliqueable, continuando inmediatamente en cuanto cumple la condición.

---

## Evidencia de Comparación: Selenium (`JSON/CSV`) vs. Chrome DevTools (`HAR`)

Para validar la captura automatizada, se replicó exactamente el mismo flujo en una ventana de incógnito de Google Chrome con el panel **Network** abierto (`All`, `Preserve log` y `Disable cache` activos), navegando a `https://es.wikipedia.org/wiki/Wikipedia:Portada`, escribiendo `"Inteligencia artificial"` en el buscador (sin presionar Enter) y aplicando un punto de corte de 3 segundos.

### Tabla de Coincidencias y Diferencias

| Criterio / Solicitud | Registro Selenium (`JSON/CSV`) | Chrome DevTools (`HAR`) | Observación y Causa de Diferencia |
| :--- | :--- | :--- | :--- |
| **Total de solicitudes** | **54** solicitudes | **50** solicitudes | **49 coincidencias exactas** de red. La diferencia en el conteo total se debe a recursos embebidos (`data:`) y un evento tardío de telemetría. |
| **Documento principal**<br>(`GET .../wiki/Wikipedia:Portada`) | Estado `200`, protocolo `h2` | Estado `200`, protocolo `h2` | Carga inicial idéntica del documento HTML principal (`text/html`). |
| **API de configuración de búsqueda**<br>(`GET .../w/api.php?action=cirrus-config-dump...`) | Estado `200`, `1,032` bytes, `121.56 ms` | Estado `200`, `1,033` bytes, `144.48 ms` | Disparada al enfocar el buscador. Diferencia de 1 byte por compresión/encabezados y `22.9 ms` por variación normal de latencia de red. |
| **API de autocompletado (Interacción)**<br>(`GET .../w/rest.php/v1/search/title?q=Inteligencia+artificial&limit=10`) | Estado `200`, `1,900` bytes, `78.89 ms` | Estado `200`, `1,901` bytes, `101.36 ms` | Endpoint principal que devuelve en `application/json` las sugerencias de artículos al escribir en la barra de búsqueda. |
| **Headers, Timing, Payload y Response** | Encabezados (`ExtraInfo`), fases DNS/TCP/TLS/TTFB, query params y cuerpo JSON (`getResponseBody`) | Pestañas *Headers*, *Timing*, *Payload* y *Response* en DevTools | Coincidencia total en `content-type`, `cache-control`, parámetros `q` y `limit`, y estructura del JSON devuelto. Las fases DNS/TLS solo aplican en la conexión inicial; las peticiones siguientes reutilizan el socket TCP/TLS. |
| **Iconos embebidos en CSS**<br>(`GET data:image/svg+xml...`) | **5** registros | **0** registros | El protocolo CDP (`performance` log) reporta eventos `Network.*` incluso para recursos `data:image/svg+xml` incrustados en hojas de estilo; la exportación `.har` de DevTools los omite por no ser peticiones de red reales. |
| **Telemetría / Analítica**<br>(`POST https://intake-analytics.wikimedia.org/v1/events?hasty=true`) | **0** registros | **1** registro | Petición `beacon` de métricas de Wikimedia disparada milisegundos después del punto de corte de 3 segundos en la ejecución manual. |

### Conclusión de la Validación
La captura automatizada mediante Selenium y `ChromeDriver` registra con total fidelidad tanto los recursos estáticos de la carga inicial como las llamadas asíncronas (`Fetch/XHR`) a la API REST de Wikipedia generadas durante la interacción, manteniendo coherencia en códigos de estado HTTP, tamaños de transferencia,