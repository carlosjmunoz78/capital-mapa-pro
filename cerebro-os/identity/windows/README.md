# CEREBRO Browser Bridge · Windows Native V1

Estado: LAB/PREPROD. No autoriza PROD.

Esta versión elimina la dependencia de Python en el PC. El launcher y el servicio local funcionan solo con Windows PowerShell.

Uso:
1. Extraer el paquete completo.
2. Ejecutar START_CEREBRO_BROWSER_BRIDGE.bat.
3. El launcher valida que el servicio sea realmente CEREBRO.
4. Si 8765 está ocupado por otro servicio, busca automáticamente un puerto libre entre 8766 y 8785.
5. Arranca solo en 127.0.0.1 y valida /health antes de abrir el navegador.
6. Los errores quedan registrados en %LOCALAPPDATA%\CEREBRO\browser-bridge\launcher.log.

Seguridad:
- loopback únicamente;
- solo LAB/PREPROD;
- no almacena contraseñas, tokens ni claves;
- no realiza mutaciones externas;
- no toca servicios locales ajenos;
- transporte cloud permanece NOT_CONFIGURED;
- coste adicional 0 €.
