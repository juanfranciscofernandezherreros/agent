# Roadmap — Deep Reverse Engineering

## v5.0 — Orquestación de análisis estático
- Coordinación de análisis de uno o varios repositorios.
- Inventario y análisis funcional por servicio.
- Extracción Java/Spring de clases, métodos, anotaciones, dependencias inyectadas, listeners Kafka y SQL.
- Detección de contratos Avro/Proto y correlación de nombres de topics/contratos entre repositorios.
- Informes JSON, Markdown y HTML.
- No ejecuta código ni valida comportamiento runtime.

## Siguientes mejoras
1. Parser semántico Java basado en AST/compiler model para resolver tipos, overloads, beans y llamadas reales.
2. Parsers específicos para Spring JDBC/JPA, MyBatis, SQL embebido, Avro schemas, Kafka producer/consumer config y OpenAPI.
3. Contratos de datos con comparación estructural de esquemas, compatibilidad y mapeo campo a campo productor-consumidor.
4. Grafo de llamadas y flujo de datos con trazabilidad origen-transformación-destino y evidencia por línea.
5. Reglas de negocio con estados observed_static, inferred, unknown; análisis asistido por LLM opcional con repositorio tratado como input no confiable.
6. Correlación multi-repo avanzada: topic → schema → producer → consumer → persistencia/archivo/evento downstream.
7. Análisis dinámico opcional únicamente en sandbox aislado, con autorización y credenciales protegidas.

## Criterio de calidad
No presentar inferencias como hechos verificados. Cada hallazgo debe conservar repositorio, archivo, línea, evidencia y nivel de confianza. La ausencia de detección no prueba ausencia de comportamiento.
