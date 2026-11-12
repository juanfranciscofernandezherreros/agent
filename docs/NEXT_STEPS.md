# Alcance actual y evolución

## Versión 4.0 — análisis-only

La aplicación se centra en descargar e inspeccionar el microservicio original. El análisis genera:
- Inventario de archivos, lenguajes y manifiestos.
- Candidatos de arquitectura, entrypoints y despliegue.
- Rutas HTTP reconocibles estáticamente.
- Dependencias declaradas en package.json y manifiestos detectados.
- Candidatos de modelos, esquemas y migraciones.
- Indicios de autenticación, autorización, validación y criptografía.
- Indicios de integraciones HTTP, bases de datos, mensajería, cloud, pagos y email.
- Variables de entorno por nombre, ficheros de configuración y tests.
- Símbolos Python (clases y funciones) y problemas de parseo.
- Evidencias con fichero y línea.

Artefactos: analysis.json y analysis.md en el workspace del proyecto.

## Límites conocidos

Es un análisis estático. No ejecuta código ni inspecciona comportamiento dinámico. No certifica que una ruta detectada esté activa ni que se hayan encontrado todas las rutas, reglas de negocio o integraciones. No lee valores de archivos .env. Los resultados deben revisarse y completarse con análisis dinámico autorizado cuando sea necesario.

## Siguiente evolución recomendada

1. Parsers específicos por stack (FastAPI, Django, Flask, Express, NestJS, Spring, .NET, Go).
2. Extracción más precisa de contratos OpenAPI, esquemas ORM y migraciones.
3. Análisis de flujos de llamadas y dependencias entre módulos.
4. Análisis semántico de reglas de negocio asistido por LLM, siempre con citas de fichero/línea y estados verified/inferred/unknown.
5. Análisis dinámico opcional en sandbox aislado, con credenciales y servicios externos protegidos.
