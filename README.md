## Comparación: Captura con Selenium vs. Chrome DevTools

| Criterio / Solicitud | Registro Selenium (`JSON/CSV`) | Chrome DevTools (`HAR`) | Observación / Causa de diferencia |
| :--- | :--- | :--- | :--- |
| **Total de solicitudes** | [Ej: 34] | [Ej: 36] | [Ej: Coinciden 33 peticiones. Chrome registró 2 pings tardíos de telemetría (`beacon`) tras el corte de 3s.] |
| **Documento principal** (`GET .../Wikipedia:Portada`) | Estado `200`, `[X]` bytes, `[X]` ms | Estado `200`, `[X]` bytes, `[X]` ms | Mismo código HTTP y protocolo (`h2`). Variación mínima en tiempo por latencia de red. |
| **API de autocompletado** (`GET .../rest.php/v1/search/title?q=Inteligencia%20artificial`) | Estado `200`, `[X]` bytes, `[X]` ms | Estado `200`, `[X]` bytes, `[X]` ms | Endpoint principal disparado al escribir en el buscador; devuelve sugerencias en `application/json`. |
| **Recurso estático** (ej. logo o hoja CSS `load.php`) | Estado `200`, `[X]` bytes, `[X]` ms | Estado `200`, `[X]` bytes, `[X]` ms | Descargado desde red sin caché (`Disable cache` activo). |