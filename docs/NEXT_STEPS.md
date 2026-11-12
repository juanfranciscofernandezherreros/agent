# Evolución a la plataforma v3 completa

1. Conectar proveedor LLM mediante adaptador y gestión segura de secretos.
2. Implementar agentes con contratos tipados y evidencias.
3. Profundizar análisis por lenguaje/framework: AST, rutas, modelos, migraciones e integraciones.
4. Hacer que Reconstruction Planner ejecute tareas de desarrollo con revisión humana.
5. Añadir Docker sandbox limitado para build/test.
6. Crear manifiestos reproducibles de ambos entornos.
7. Añadir comparadores de DB, eventos, integraciones, seguridad y rendimiento.
8. Añadir normalizadores explícitos, cobertura por dimensión y oráculos versionados.
9. Implementar ciclos de root-cause/repair con presupuesto y gates.
10. Migrar SQLite a PostgreSQL y tareas background a workers durables.

No habilitar ejecución automática de repositorios no confiables antes de implementar el sandbox.
