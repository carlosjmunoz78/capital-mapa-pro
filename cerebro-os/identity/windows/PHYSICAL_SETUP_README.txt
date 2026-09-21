CEREBRO Browser Bridge V1.4.1 · FENIX LAB PILOT

OBJETIVO
Dejar el PC emparejado en LAB sin tocar PROD ni almacenar contraseñas.

PASO 1
Ejecutar START_CEREBRO_BROWSER_BRIDGE.bat

El launcher:
- inicia el Bridge solo en 127.0.0.1;
- detecta perfiles locales de Chrome como metadatos;
- selecciona de forma determinista el perfil actual/último usado;
- fija el piloto a company_id=fenix, environment=LAB, version=v0;
- NO lee Cookies, Login Data ni contraseñas;
- NO realiza mutaciones en webs externas.

PASO 2
Si la extensión CEREBRO V1.4.1 no está instalada, ejecutar OPEN_CHROME_EXTENSION_SETUP.bat y cargar la carpeta chrome_extension_v1_4_1 como extensión descomprimida.

PASO 3
Ejecutar VERIFY_CEREBRO_BROWSER_BRIDGE.bat

Resultado esperado:
- service_found=true
- service_version=true
- paired=true
- lab_scope=true
- extension_connected=true
- extension_fresh=true

El transporte cloud puede quedar en PREPROD_DEVICE_ENROLLMENT hasta que exista un PAIRING_ONCE.txt válido y de un solo uso.

Nunca:
- introducir contraseñas/tokens en CEREBRO;
- activar PROD;
- desactivar los guardrails;
- abrir puertos entrantes.
