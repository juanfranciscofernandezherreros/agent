"""Catalogue of security and correctness rules with CWE / OWASP Top 10:2025 mappings.

Mappings classify a finding; they never prove exploitability. Category URLs point to
the official Top 10:2025 index except where a category URL was already verified (A05).
"""
from __future__ import annotations

from dataclasses import dataclass, field

OWASP_VERSION = "2025"
OWASP_INDEX_URL = "https://owasp.org/Top10/2025/"

OWASP_TOP10_2025 = {
    "A01": "Broken Access Control",
    "A02": "Security Misconfiguration",
    "A03": "Software Supply Chain Failures",
    "A04": "Cryptographic Failures",
    "A05": "Injection",
    "A06": "Insecure Design",
    "A07": "Authentication Failures",
    "A08": "Software or Data Integrity Failures",
    "A09": "Security Logging and Alerting Failures",
    "A10": "Mishandling of Exceptional Conditions",
}
_OWASP_URLS = {"A05": "https://owasp.org/Top10/2025/A05_2025-Injection/"}

CHEAT_SHEETS = "https://cheatsheetseries.owasp.org/cheatsheets/"


def owasp(category: str) -> dict:
    return {
        "version": OWASP_VERSION,
        "id": f"{category}:{OWASP_VERSION}",
        "name": OWASP_TOP10_2025[category],
        "url": _OWASP_URLS.get(category, OWASP_INDEX_URL),
    }


def cwe(number: int, name: str) -> dict:
    return {"id": f"CWE-{number}", "name": name, "url": f"https://cwe.mitre.org/data/definitions/{number}.html"}


@dataclass(frozen=True)
class Rule:
    id: str
    title: str
    kind: str  # "taint" (source -> sink) | "pattern" (local structural check)
    category: str  # "security" | "bug"
    severity: str  # "high" | "medium" | "low"
    owasp: str | None
    cwe: tuple[int, str]
    description: str
    remediation: str
    references: tuple[str, ...] = field(default_factory=tuple)
    asvs_area: str | None = None

    def metadata(self) -> dict:
        data = {
            "rule_id": self.id,
            "title": self.title,
            "category": self.category,
            "severity": self.severity,
            "cwe": cwe(*self.cwe),
            "description": self.description,
            "remediation": self.remediation,
            "references": list(self.references),
        }
        if self.owasp:
            data["owasp"] = owasp(self.owasp)
        if self.asvs_area:
            data["asvs_area"] = self.asvs_area
        return data


def _r(*args, **kwargs) -> Rule:
    return Rule(*args, **kwargs)


RULES: dict[str, Rule] = {r.id: r for r in [
    # --- Injection (A05) -------------------------------------------------------------
    _r("SEC-SQLI", "Inyección SQL", "taint", "security", "high", "A05",
       (89, "Improper Neutralization of Special Elements used in an SQL Command"),
       "Datos controlados por el usuario llegan a una consulta SQL construida dinámicamente.",
       "Usar consultas parametrizadas (PreparedStatement con '?', parámetros con nombre de JPA/JdbcTemplate, "
       "cursor.execute(sql, params)). Para identificadores u ordenaciones, usar listas blancas.",
       (CHEAT_SHEETS + "SQL_Injection_Prevention_Cheat_Sheet.html",
        CHEAT_SHEETS + "Query_Parameterization_Cheat_Sheet.html"),
       "V5 - Validation, Sanitization and Encoding"),
    _r("SEC-CMDI", "Inyección de comandos del sistema operativo", "taint", "security", "high", "A05",
       (78, "Improper Neutralization of Special Elements used in an OS Command"),
       "Datos controlados por el usuario llegan a la ejecución de un comando del sistema.",
       "Evitar el intérprete de comandos: pasar el programa y los argumentos como lista sin shell=True, "
       "validar contra una lista blanca y, si es imprescindible, escapar con shlex.quote.",
       (CHEAT_SHEETS + "OS_Command_Injection_Defense_Cheat_Sheet.html",),
       "V5 - Validation, Sanitization and Encoding"),
    _r("SEC-CODEI", "Inyección de código o expresiones", "taint", "security", "high", "A05",
       (94, "Improper Control of Generation of Code ('Code Injection')"),
       "Datos controlados por el usuario se evalúan como código (eval/exec, ScriptEngine, SpEL, OGNL).",
       "No evaluar entradas como código. Usar un parser de datos (json, ast.literal_eval) o un "
       "SimpleEvaluationContext restringido en SpEL.",
       (CHEAT_SHEETS + "Injection_Prevention_Cheat_Sheet.html",)),
    _r("SEC-SSTI", "Inyección de plantillas en servidor", "taint", "security", "high", "A05",
       (1336, "Improper Neutralization of Special Elements Used in a Template Engine"),
       "Datos controlados por el usuario se usan como texto de una plantilla que se renderiza.",
       "Pasar los datos como variables de una plantilla fija (render_template con contexto), nunca como plantilla.",
       (CHEAT_SHEETS + "Injection_Prevention_Cheat_Sheet.html",)),
    _r("SEC-XSS", "Cross-Site Scripting (XSS)", "taint", "security", "medium", "A05",
       (79, "Improper Neutralization of Input During Web Page Generation"),
       "Datos controlados por el usuario se escriben en una respuesta HTML sin codificar.",
       "Codificar la salida según el contexto (motor de plantillas con autoescape, HtmlUtils.htmlEscape, "
       "markupsafe.escape) y no marcar como seguro contenido externo.",
       (CHEAT_SHEETS + "Cross_Site_Scripting_Prevention_Cheat_Sheet.html",),
       "V5 - Validation, Sanitization and Encoding"),
    _r("SEC-LDAPI", "Inyección LDAP", "taint", "security", "high", "A05",
       (90, "Improper Neutralization of Special Elements used in an LDAP Query"),
       "Datos controlados por el usuario se concatenan en un filtro LDAP.",
       "Escapar los valores del filtro (por ejemplo LdapEncoder.filterEncode) o usar filtros parametrizados.",
       (CHEAT_SHEETS + "LDAP_Injection_Prevention_Cheat_Sheet.html",)),
    _r("SEC-REFLECT", "Carga dinámica de clases controlada por el usuario", "taint", "security", "medium", "A05",
       (470, "Use of Externally-Controlled Input to Select Classes or Code ('Unsafe Reflection')"),
       "Un nombre de clase controlado por el usuario se carga por reflexión.",
       "Resolver la clase a partir de una lista blanca de valores conocidos.",
       (CHEAT_SHEETS + "Injection_Prevention_Cheat_Sheet.html",)),
    # --- Broken access control (A01) -------------------------------------------------
    _r("SEC-PATH", "Path traversal (acceso a ficheros arbitrarios)", "taint", "security", "high", "A01",
       (22, "Improper Limitation of a Pathname to a Restricted Directory ('Path Traversal')"),
       "Una ruta de fichero construida con datos del usuario se usa para leer, escribir o borrar.",
       "Normalizar la ruta y comprobar que queda dentro del directorio permitido, o usar solo el nombre "
       "base (secure_filename, FilenameUtils.getName) y una lista blanca.",
       (CHEAT_SHEETS + "Input_Validation_Cheat_Sheet.html",)),
    _r("SEC-SSRF", "Server-Side Request Forgery (SSRF)", "taint", "security", "high", "A01",
       (918, "Server-Side Request Forgery (SSRF)"),
       "El servidor hace una petición HTTP a una URL controlada por el usuario.",
       "Usar una lista blanca de destinos, bloquear direcciones internas y no reenviar URLs completas recibidas.",
       (CHEAT_SHEETS + "Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html",)),
    _r("SEC-REDIRECT", "Redirección abierta", "taint", "security", "medium", "A01",
       (601, "URL Redirection to Untrusted Site ('Open Redirect')"),
       "La aplicación redirige a una URL controlada por el usuario.",
       "Redirigir solo a rutas relativas propias o a destinos de una lista blanca.",
       (CHEAT_SHEETS + "Unvalidated_Redirects_and_Forwards_Cheat_Sheet.html",)),
    _r("SEC-CSRF", "Protección CSRF desactivada", "pattern", "security", "medium", "A01",
       (352, "Cross-Site Request Forgery (CSRF)"),
       "Se desactiva la protección CSRF del framework.",
       "Mantener CSRF activado en endpoints con sesión/cookies; desactivarlo solo en APIs sin estado con tokens Bearer.",
       (CHEAT_SHEETS + "Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html",)),
    # --- Misconfiguration (A02) ------------------------------------------------------
    _r("SEC-XXE", "XML External Entities (XXE)", "pattern", "security", "medium", "A02",
       (611, "Improper Restriction of XML External Entity Reference"),
       "Se crea un parser XML sin desactivar DTD/entidades externas.",
       "Activar disallow-doctype-decl o desactivar entidades externas y DTD en el factory del parser.",
       (CHEAT_SHEETS + "XML_External_Entity_Prevention_Cheat_Sheet.html",)),
    _r("SEC-DEBUG", "Modo depuración o endpoints internos expuestos", "pattern", "security", "medium", "A02",
       (489, "Active Debug Code"),
       "La configuración activa modo depuración o expone endpoints de gestión/consolas internas.",
       "Desactivar el modo depuración en producción y limitar los endpoints expuestos (health, info).",
       (CHEAT_SHEETS + "Error_Handling_Cheat_Sheet.html",)),
    _r("SEC-CORS", "CORS permisivo con credenciales", "pattern", "security", "medium", "A02",
       (942, "Permissive Cross-domain Policy with Untrusted Domains"),
       "Se permite cualquier origen ('*') en CORS.",
       "Declarar explícitamente los orígenes permitidos; nunca combinar '*' con credenciales.",
       (CHEAT_SHEETS + "HTML5_Security_Cheat_Sheet.html",)),
    # --- Cryptographic failures (A04) ------------------------------------------------
    _r("SEC-WEAKHASH", "Algoritmo de hash débil", "pattern", "security", "low", "A04",
       (328, "Use of Weak Hash"),
       "Se usa MD5 o SHA-1, que no son resistentes a colisiones.",
       "Usar SHA-256 o superior; para contraseñas, bcrypt, scrypt, Argon2 o PBKDF2.",
       (CHEAT_SHEETS + "Password_Storage_Cheat_Sheet.html",)),
    _r("SEC-WEAKCIPHER", "Cifrado débil o modo inseguro", "pattern", "security", "high", "A04",
       (327, "Use of a Broken or Risky Cryptographic Algorithm"),
       "Se usa DES/3DES/RC4/Blowfish o el modo ECB (por defecto en 'AES').",
       "Usar AES-GCM (AES/GCM/NoPadding) con IV aleatorio, o ChaCha20-Poly1305.",
       (CHEAT_SHEETS + "Cryptographic_Storage_Cheat_Sheet.html",)),
    _r("SEC-WEAKRANDOM", "Aleatoriedad no criptográfica para secretos", "pattern", "security", "medium", "A04",
       (330, "Use of Insufficiently Random Values"),
       "Se generan tokens, contraseñas o claves con un generador predecible.",
       "Usar SecureRandom (Java) o el módulo secrets (Python).",
       (CHEAT_SHEETS + "Cryptographic_Storage_Cheat_Sheet.html",)),
    _r("SEC-TLS", "Validación de certificados TLS desactivada", "pattern", "security", "high", "A04",
       (295, "Improper Certificate Validation"),
       "Se aceptan certificados o nombres de host sin validar.",
       "Mantener la validación por defecto; para certificados internos, añadir la CA al truststore.",
       (CHEAT_SHEETS + "Transport_Layer_Security_Cheat_Sheet.html",)),
    # --- Authentication failures (A07) -----------------------------------------------
    _r("SEC-SECRET", "Credencial o secreto en el código", "pattern", "security", "high", "A07",
       (798, "Use of Hard-coded Credentials"),
       "Hay una contraseña, token o clave escrita literalmente en el código o la configuración.",
       "Mover el secreto a un gestor de secretos o variable de entorno y rotarlo si llegó a publicarse.",
       (CHEAT_SHEETS + "Secrets_Management_Cheat_Sheet.html",)),
    _r("SEC-JWT", "Token JWT aceptado sin verificar la firma", "pattern", "security", "high", "A07",
       (347, "Improper Verification of Cryptographic Signature"),
       "Se decodifica un JWT sin verificar su firma o aceptando el algoritmo 'none'.",
       "Verificar siempre la firma con una clave y una lista explícita de algoritmos.",
       (CHEAT_SHEETS + "JSON_Web_Token_for_Java_Cheat_Sheet.html",)),
    # --- Integrity failures (A08) ----------------------------------------------------
    _r("SEC-DESER", "Deserialización insegura", "taint", "security", "high", "A08",
       (502, "Deserialization of Untrusted Data"),
       "Datos no confiables se deserializan con un mecanismo que puede instanciar objetos arbitrarios.",
       "Usar formatos de datos (JSON) con tipos explícitos; nunca pickle/ObjectInputStream con datos externos.",
       (CHEAT_SHEETS + "Deserialization_Cheat_Sheet.html",)),
    _r("SEC-UNSAFE-DESER-API", "API de deserialización insegura", "pattern", "security", "medium", "A08",
       (502, "Deserialization of Untrusted Data"),
       "Se usa una API de deserialización que permite instanciar tipos arbitrarios.",
       "Sustituirla por una alternativa segura (yaml.safe_load, SafeConstructor, ObjectMapper sin default typing).",
       (CHEAT_SHEETS + "Deserialization_Cheat_Sheet.html",)),
    # --- Exceptional conditions (A10) and correctness bugs ---------------------------
    _r("BUG-EMPTY-CATCH", "Excepción capturada y descartada", "pattern", "bug", "medium", "A10",
       (390, "Detection of Error Condition Without Action"),
       "Un bloque catch/except vacío oculta el error y deja el proceso en un estado desconocido.",
       "Registrar, propagar o tratar explícitamente la excepción.",
       (CHEAT_SHEETS + "Error_Handling_Cheat_Sheet.html",)),
    _r("BUG-BROAD-CATCH", "Captura genérica que oculta errores", "pattern", "bug", "low", "A10",
       (396, "Declaration of Catch for Generic Exception"),
       "Se captura cualquier excepción (except:, Throwable) y se continúa.",
       "Capturar los tipos concretos que se saben tratar y dejar propagar el resto.",
       (CHEAT_SHEETS + "Error_Handling_Cheat_Sheet.html",)),
    _r("BUG-INTERRUPTED", "InterruptedException tragada", "pattern", "bug", "medium", "A10",
       (391, "Unchecked Error Condition"),
       "Se captura InterruptedException sin restaurar el estado de interrupción del hilo.",
       "Llamar a Thread.currentThread().interrupt() o relanzar la excepción.", ()),
    _r("BUG-STRING-EQ", "Comparación de String con ==", "pattern", "bug", "high", None,
       (597, "Use of Wrong Operator in String Comparison"),
       "Se comparan cadenas por referencia (==/!=) en lugar de por contenido.",
       "Usar equals() o Objects.equals().", ()),
    _r("BUG-BIGDECIMAL-DOUBLE", "BigDecimal construido desde double", "pattern", "bug", "medium", None,
       (1339, "Insufficient Precision or Accuracy of a Real Number"),
       "new BigDecimal(double) arrastra el error binario del double (0.1 -> 0.1000000000000000055...).",
       "Usar BigDecimal.valueOf(double) o el constructor con String.", ()),
    _r("BUG-TX-PRIVATE", "@Transactional en método no público", "pattern", "bug", "medium", None,
       (1188, "Initialization of a Resource with an Insecure Default"),
       "Spring ignora @Transactional en métodos private/final/static con proxies: no hay transacción.",
       "Hacer el método público y llamarlo desde otro bean, o gestionar la transacción explícitamente.", ()),
    _r("BUG-SHARED-DATEFORMAT", "SimpleDateFormat compartido entre hilos", "pattern", "bug", "medium", None,
       (362, "Concurrent Execution using Shared Resource with Improper Synchronization ('Race Condition')"),
       "SimpleDateFormat no es thread-safe; como campo estático produce fechas corruptas bajo concurrencia.",
       "Usar java.time.format.DateTimeFormatter (inmutable) o una instancia por llamada.", ()),
    _r("BUG-IS-LITERAL", "Comparación con 'is' contra un literal", "pattern", "bug", "high", None,
       (595, "Comparison of Object References Instead of Object Contents"),
       "'is' compara identidad; con cadenas o números el resultado depende de la implementación.",
       "Usar == para comparar valores.", ()),
    _r("BUG-MUTABLE-DEFAULT", "Argumento por defecto mutable", "pattern", "bug", "medium", None,
       (1188, "Initialization of a Resource with an Insecure Default"),
       "La lista/dict por defecto se comparte entre llamadas y acumula estado.",
       "Usar None como valor por defecto y crear el objeto dentro de la función.", ()),
]}


def rule(rule_id: str) -> Rule:
    return RULES[rule_id]
