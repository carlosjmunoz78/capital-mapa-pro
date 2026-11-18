# NEWS001 · Fuente oficial independiente de ChatGPT (LAB)

Recolector sin IA ni costes adicionales que consulta RSS público de Banco de España y BCE. Extrae titulares/resúmenes literales, exige origen oficial, fecha reciente y no reutiliza fechas futuras ni vencidas. Genera exclusivamente evidencia para el motor editorial, **NO aprueba los hechos y NO envía correos**. Ejecutar `python observer.py --output /tmp/news001_official.json` desde CEREBRO; el contrato editorial no admite esta prueba por sí sola como aprobación para PROD.

Próximos gates: verificación de texto completo contra el documento oficial, extracción de hechos sin alteración, renderer de las dos audiencias, imágenes UMS aprobadas, prueba real de listas/suscripción/baja, y orquestación semanal protegida. Si no hay noticias adecuadas, HOLD y no repetir contenido obsoleto.
