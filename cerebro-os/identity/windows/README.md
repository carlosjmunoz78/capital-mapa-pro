# CEREBRO Browser Bridge · Windows Launcher V0

Estado: LAB/PREPROD. No autoriza PROD.

Uso previsto:
1. ejecutar `START_CEREBRO_BROWSER_BRIDGE.bat`;
2. el launcher arranca un servicio local en `127.0.0.1:8765`;
3. abre la interfaz `CEREBRO Browser Bridge` en el navegador;
4. el usuario confirma empresa, perfil de navegador y entorno;
5. el estado local queda persistido en `%LOCALAPPDATA%\CEREBRO\browser-bridge\state.json`.

Seguridad V0:
- solo escucha en loopback;
- no acepta PROD;
- no almacena contraseñas, tokens ni credenciales;
- kill switch lógico requerido;
- no ejecuta acciones externas;
- el transporte cloud permanece `NOT_CONFIGURED` hasta validación física del PC.

Este launcher resuelve el acceso físico/local al Bridge. La siguiente fase conecta de forma controlada el heartbeat/worker local con el CEREBRO Gateway, sin exponer secretos.
