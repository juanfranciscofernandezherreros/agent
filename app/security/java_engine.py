"""Taint tracking and structural checks for Java / Spring sources using tree-sitter.

Sources are parsed into a syntax tree; nothing is compiled or executed. Method
summaries (which parameters reach a sink or the return value) are computed for the
whole repository so that controller -> service -> repository flows across files are
followed. Summaries are keyed by method name and arity, so overloaded/homonymous
methods are merged conservatively and such flows are reported with medium confidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from .contracts import SecurityFinding, TraceStep
from .python_engine import (MAX_STEPS, SECURITY_RANDOM_NAME, find_token_secrets, looks_like_secret, redact)

try:  # optional dependency: the Java profile is skipped (and reported) when unavailable
    import tree_sitter_java as _tsj
    from tree_sitter import Language, Parser
    _PARSER = Parser(Language(_tsj.language()))
    JAVA_AVAILABLE = True
except Exception:  # pragma: no cover - depends on the environment
    _PARSER = None
    JAVA_AVAILABLE = False

SOURCE_ANNOTATIONS = {"RequestParam", "PathVariable", "RequestBody", "RequestHeader", "CookieValue", "ModelAttribute",
                      "MatrixVariable", "RequestPart", "QueryParam", "PathParam", "FormParam", "HeaderParam",
                      "CookieParam", "BeanParam", "Payload"}
MAPPING_ANNOTATIONS = {"GetMapping", "PostMapping", "PutMapping", "DeleteMapping", "PatchMapping", "RequestMapping",
                       "GET", "POST", "PUT", "DELETE", "PATCH"}
LISTENER_ANNOTATIONS = {"KafkaListener", "RabbitListener", "JmsListener", "StreamListener", "SqsListener", "KafkaHandler"}
FRAMEWORK_TYPES = {"HttpServletRequest", "HttpServletResponse", "ServletRequest", "ServletResponse", "Model", "ModelMap",
                   "BindingResult", "Errors", "Principal", "Authentication", "Pageable", "Sort", "Locale", "HttpSession",
                   "WebRequest", "ServerWebExchange", "ServerHttpRequest", "ServerHttpResponse", "SessionStatus",
                   "UriComponentsBuilder", "RedirectAttributes", "Acknowledgment", "Consumer", "TimeZone", "ZoneId",
                   "HttpHeaders", "ServerRequest", "Jwt", "OAuth2User", "UserDetails"}
SAFE_TYPES = {"int", "long", "short", "byte", "boolean", "double", "float", "char", "Integer", "Long", "Short", "Byte",
              "Boolean", "Double", "Float", "BigDecimal", "BigInteger", "UUID", "LocalDate", "LocalDateTime", "Instant",
              "OffsetDateTime", "ZonedDateTime", "Date", "Duration", "Year", "YearMonth"}
REQUEST_SOURCE_METHODS = {"getParameter", "getParameterValues", "getParameterMap", "getParameterNames", "getHeader",
                          "getHeaders", "getQueryString", "getCookies", "getInputStream", "getReader", "getRequestURI",
                          "getRequestURL", "getPathInfo", "getPart", "getParts", "getServletPath",
                          "queryParam", "queryParams", "pathVariable", "pathVariables", "bodyToMono", "bodyToFlux",
                          "getQueryParams", "formData", "multipartData"}
REQUEST_TYPES = {"HttpServletRequest", "ServletRequest", "ServerRequest", "ServerHttpRequest", "MultipartHttpServletRequest"}

CLEANSING_CALLS = {"parseInt", "parseLong", "parseDouble", "parseFloat", "parseShort", "parseBoolean", "fromString",
                   "equals", "equalsIgnoreCase", "isEmpty", "isBlank", "contains", "startsWith", "endsWith", "matches",
                   "length", "size", "hashCode", "compareTo", "isPresent", "hasText", "hasLength", "exists", "count",
                   "existsById", "indexOf", "getClass"}
CLEANSING_QUALIFIED = {"Integer.valueOf", "Long.valueOf", "Double.valueOf", "Short.valueOf", "Boolean.valueOf",
                       "UUID.fromString", "LocalDate.parse", "LocalDateTime.parse", "Instant.parse"}
RULE_SANITIZERS = {
    "htmlEscape": {"SEC-XSS"}, "escapeHtml4": {"SEC-XSS"}, "escapeHtml": {"SEC-XSS"}, "forHtml": {"SEC-XSS"},
    "forHtmlContent": {"SEC-XSS"}, "forHtmlAttribute": {"SEC-XSS"}, "encodeForHTML": {"SEC-XSS"}, "escape": {"SEC-XSS"},
    "getName": set(),  # FilenameUtils.getName handled below (receiver-specific)
    "filterEncode": {"SEC-LDAPI"}, "encodeForLDAP": {"SEC-LDAPI"},
    "encodeForSQL": {"SEC-SQLI"}, "escapeSql": {"SEC-SQLI"},
}
SQL_ALWAYS = {"executeQuery", "executeUpdate", "executeLargeUpdate", "addBatch", "prepareStatement", "prepareCall",
              "createNativeQuery", "createQuery", "createSQLQuery", "createNativeMutationQuery", "queryForObject",
              "queryForList", "queryForMap", "queryForRowSet", "queryForStream", "batchUpdate", "nativeQuery"}
SQL_RECEIVER_ONLY = {"query", "update", "execute", "sql"}
SQL_RECEIVER = re.compile(r"(?i)(jdbc|template|stmt|statement|conn|connection|\bem\b|entitymanager|session|database|"
                          r"\bdb\b|client|dao)")
SQL_TYPES = {"Statement", "PreparedStatement", "CallableStatement", "Connection", "JdbcTemplate",
             "NamedParameterJdbcTemplate", "EntityManager", "Session", "DatabaseClient", "JdbcClient", "JdbcOperations"}
REST_METHODS = {"getForObject", "getForEntity", "postForObject", "postForEntity", "postForLocation", "exchange", "put",
                "delete", "patchForObject", "headForHeaders", "optionsForAllow", "execute"}
FILE_CLASSES = {"File", "FileInputStream", "FileOutputStream", "FileReader", "FileWriter", "RandomAccessFile",
                "FileSystemResource", "PrintWriter", "ZipFile"}
FILES_METHODS = {"readAllBytes", "readAllLines", "readString", "newInputStream", "newOutputStream", "newBufferedReader",
                 "newBufferedWriter", "delete", "deleteIfExists", "write", "writeString", "copy", "move", "lines", "list",
                 "walk", "createFile", "createDirectories", "createDirectory", "newByteChannel"}
TRUST_RECEIVERS = re.compile(r"(?i)(webclient|restclient|httprequest|builder|\.get\(\)|\.post\(\)|\.put\(\)|\.delete\(\)|"
                             r"\.method\()")


def _txt(node) -> str:
    return node.text.decode("utf-8", errors="replace") if node is not None else ""


def _line(node) -> int:
    return node.start_point[0] + 1


@dataclass(frozen=True)
class Taint:
    steps: tuple = ()
    sanitized_for: frozenset = frozenset()
    confidence: str = "high"
    params: frozenset = frozenset()  # parameter indexes (summary mode)

    def extend(self, step: TraceStep) -> "Taint":
        last = self.steps[-1] if self.steps else None
        if (last is not None and last.line == step.line and last.file == step.file) or len(self.steps) >= MAX_STEPS:
            return self
        return Taint(self.steps + (step,), self.sanitized_for, self.confidence, self.params)

    def sanitize(self, rules) -> "Taint":
        return Taint(self.steps, self.sanitized_for | frozenset(rules), self.confidence, self.params)

    def weaken(self) -> "Taint":
        return Taint(self.steps, self.sanitized_for, "medium", self.params)

    def blocked(self, rule_id) -> bool:
        return rule_id in self.sanitized_for


def merge(*values):
    present = [v for v in values if v is not None]
    if not present:
        return None
    return Taint(present[0].steps, frozenset.intersection(*(v.sanitized_for for v in present)),
                 "high" if all(v.confidence == "high" for v in present) else "medium",
                 frozenset().union(*(v.params for v in present)))


@dataclass
class Summary:
    returns: set = field(default_factory=set)
    sinks: list = field(default_factory=list)  # (param index, rule id, sink step, inner steps)
    defined: int = 0


@dataclass
class JavaFile:
    rel: str
    source: bytes
    tree: object
    is_test: bool
    lines: list


class JavaProject:
    """Analyses every Java file of a repository together (cross-file summaries)."""

    def __init__(self):
        self.files: list[JavaFile] = []
        self.summaries: dict[tuple, Summary] = {}
        self.findings: list[SecurityFinding] = []
        self.errors: list[dict] = []
        self._seen: set = set()

    def add(self, source: str, rel: str, is_test: bool = False):
        data = source.encode("utf-8", errors="replace")
        tree = _PARSER.parse(data)
        if tree.root_node.has_error:
            self.errors.append({"file": rel, "error": "Errores de sintaxis parciales; se analiza lo reconocible."})
        self.files.append(JavaFile(rel, data, tree, is_test, source.splitlines()))

    def run(self) -> list[SecurityFinding]:
        methods = [(f, m) for f in self.files for m in _methods(f.tree.root_node)]
        for _ in range(3):  # controller -> service -> repository chains
            new: dict[tuple, Summary] = {}
            for jf, method in methods:
                runner = MethodTaint(self, jf, method, mode="summary")
                if not self._safely(runner.run, jf):
                    continue
                for key in ((runner.class_name, runner.name, runner.arity), (None, runner.name, runner.arity)):
                    bucket = new.setdefault(key, Summary())
                    bucket.returns |= runner.summary.returns
                    bucket.sinks.extend(runner.summary.sinks)
                    bucket.defined += 1
            self.summaries = new
        for jf, method in methods:
            self._safely(MethodTaint(self, jf, method, mode="report").run, jf)
        for jf in self.files:
            self._safely(JavaPatterns(self, jf).run, jf)
        return self.findings

    def _safely(self, action, jf) -> bool:
        """Untrusted code may nest deeply enough to exhaust recursion: contain it per method/file."""
        try:
            action()
            return True
        except RecursionError:
            error = {"file": jf.rel, "error": "RecursionError: código demasiado anidado; análisis parcial"}
            if error not in self.errors:
                self.errors.append(error)
            return False

    def report(self, jf: JavaFile, rule_id: str, node, message: str, *, trace=(), confidence="high",
               severity=None, snippet=None):
        line = _line(node)
        key = (rule_id, jf.rel, line)
        if key in self._seen:
            return
        self._seen.add(key)
        code = snippet if snippet is not None else (jf.lines[line - 1].strip() if 0 < line <= len(jf.lines) else "")
        self.findings.append(SecurityFinding(rule_id=rule_id, file=jf.rel, line=line, column=node.start_point[1],
                                             snippet=code, message=message, language="java", confidence=confidence,
                                             trace=list(trace), severity=severity, is_test=jf.is_test))


def _methods(root):
    stack = [root]
    while stack:
        node = stack.pop()
        if node.type in ("method_declaration", "constructor_declaration"):
            yield node
        stack.extend(reversed(node.named_children))


def _annotations(node) -> list:
    """Annotation nodes in the modifiers of a declaration/parameter."""
    result = []
    for child in node.children:
        if child.type == "modifiers":
            result.extend(c for c in child.named_children if c.type in ("annotation", "marker_annotation"))
    return result


def _annotation_name(annotation) -> str:
    name = annotation.child_by_field_name("name")
    return _txt(name).split(".")[-1]


def _modifiers(node) -> set:
    for child in node.children:
        if child.type == "modifiers":
            return {_txt(c) for c in child.children if c.type not in ("annotation", "marker_annotation")}
    return set()


def _simple_type(type_node) -> str:
    text = _txt(type_node)
    text = re.sub(r"<.*>", "", text).replace("[]", "").strip()
    return text.split(".")[-1]


def _descendants(node):
    stack = [node] if node is not None else []
    while stack:
        current = stack.pop()
        yield current
        stack.extend(current.named_children)


def _inside(node, kind: str, stop) -> bool:
    current = node.parent
    while current is not None and current != stop:
        if current.type == kind:
            return True
        current = current.parent
    return False


def _enclosing(node, kinds):
    node = node.parent
    while node is not None and node.type not in kinds:
        node = node.parent
    return node


class MethodTaint:
    def __init__(self, project: JavaProject, jf: JavaFile, method, mode: str):
        self.p = project
        self.f = jf
        self.m = method
        self.mode = mode
        self.env: dict[str, Taint] = {}
        self.types: dict[str, str] = {}
        self.request_vars: set[str] = set()
        self.summary = Summary()
        self.name = _txt(method.child_by_field_name("name"))
        params = method.child_by_field_name("parameters")
        self.params = [p for p in params.named_children if p.type in ("formal_parameter", "spread_parameter")] if params else []
        self.arity = len(self.params)
        self.annotations = {_annotation_name(a) for a in _annotations(method)}
        cls = _enclosing(method, ("class_declaration", "record_declaration", "enum_declaration"))
        self.class_name = _txt(cls.child_by_field_name("name")) if cls is not None else ""
        self.reported_flows: set = set()
        self.class_annotations = {_annotation_name(a) for a in _annotations(cls)} if cls is not None else set()
        self.is_controller = bool(self.class_annotations & {"RestController", "Controller", "Path"})
        self._fields(cls)

    def _fields(self, cls):
        if cls is None:
            return
        body = cls.child_by_field_name("body")
        for member in body.named_children if body else []:
            if member.type == "field_declaration":
                ftype = _simple_type(member.child_by_field_name("type"))
                for decl in member.children_by_field_name("declarator"):
                    name = _txt(decl.child_by_field_name("name"))
                    self.types[name] = ftype
                    self.types["this." + name] = ftype

    def step(self, kind, node, note="") -> TraceStep:
        line = _line(node)
        code = self.f.lines[line - 1].strip()[:200] if 0 < line <= len(self.f.lines) else ""
        return TraceStep(kind, self.f.rel, line, code, note)

    # ------------------------------------------------------------------ setup
    def run(self):
        handler = bool(self.annotations & MAPPING_ANNOTATIONS)
        listener = bool(self.annotations & LISTENER_ANNOTATIONS)
        for index, param in enumerate(self.params):
            name = _txt(param.child_by_field_name("name"))
            ptype = _simple_type(param.child_by_field_name("type"))
            self.types[name] = ptype
            annotations = {_annotation_name(a) for a in _annotations(param)}
            if ptype in REQUEST_TYPES:
                self.request_vars.add(name)
            if self.mode == "summary":
                if ptype not in SAFE_TYPES:
                    self.env[name] = Taint(params=frozenset({index}))
                continue
            if ptype in SAFE_TYPES or ptype in FRAMEWORK_TYPES:
                continue
            if annotations & SOURCE_ANNOTATIONS or (handler and not annotations - {"Valid", "Validated", "NonNull", "NotNull"}):
                origin = next(iter(annotations & SOURCE_ANNOTATIONS), "parámetro del endpoint")
                self.env[name] = Taint((self.step("source", param, f"@{origin} '{name}' (entrada HTTP)"
                                                  if origin != "parámetro del endpoint" else f"parámetro '{name}' del endpoint HTTP"),))
            elif listener:
                self.env[name] = Taint((self.step("source", param, f"mensaje recibido por @{next(iter(self.annotations & LISTENER_ANNOTATIONS))}"),),
                                       confidence="medium")
        body = self.m.child_by_field_name("body")
        if body is not None:
            self.walk(body)

    # ------------------------------------------------------------------ statements
    def walk(self, node):
        t = node.type
        if t in ("class_declaration", "lambda_expression", "interface_declaration"):
            if t == "lambda_expression":
                body = node.child_by_field_name("body")
                if body is not None:
                    self.walk(body) if body.type == "block" else self.expr(body)
            return
        if t == "local_variable_declaration":
            vtype = _simple_type(node.child_by_field_name("type"))
            for decl in node.children_by_field_name("declarator"):
                name = _txt(decl.child_by_field_name("name"))
                if vtype != "var":
                    self.types[name] = vtype
                value = decl.child_by_field_name("value")
                if value is not None:
                    self.assign(name, self.expr(value), decl)
                    if vtype == "var" and value.type == "object_creation_expression":
                        self.types[name] = _simple_type(value.child_by_field_name("type"))
            return
        if t == "expression_statement":
            for child in node.named_children:
                self.expr(child)
            return
        if t == "return_statement":
            value = node.named_children[0] if node.named_children else None
            taint = self.expr(value) if value is not None else None
            if taint is not None:
                self.summary.returns |= set(taint.params)
                if self.mode == "report" and taint.steps and value is not None:
                    self._check_redirect_return(value, taint, node)
            return
        if t == "enhanced_for_statement":
            name = _txt(node.child_by_field_name("name"))
            self.assign(name, self.expr(node.child_by_field_name("value")), node)
            body = node.child_by_field_name("body")
            if body is not None:
                self.walk(body)
            return
        for child in node.named_children:
            if child.type.endswith("expression") or child.type in ("method_invocation", "object_creation_expression"):
                self.expr(child)
            else:
                self.walk(child)

    def assign(self, name: str, taint, node):
        if taint is None:
            self.env.pop(name, None)
            return
        self.env[name] = taint.extend(self.step("propagation", node, f"asignado a '{name}'"))

    # ------------------------------------------------------------------ expressions
    def expr(self, node):
        if node is None:
            return None
        t = node.type
        if t == "identifier":
            return self.env.get(_txt(node))
        if t in ("string_literal", "character_literal", "decimal_integer_literal", "decimal_floating_point_literal",
                 "true", "false", "null_literal", "class_literal", "hex_integer_literal", "text_block"):
            return None
        if t == "parenthesized_expression" or t == "cast_expression":
            inner = node.child_by_field_name("value") if t == "cast_expression" else node.named_children[0]
            return self.expr(inner)
        if t == "binary_expression":
            left, right = self.expr(node.child_by_field_name("left")), self.expr(node.child_by_field_name("right"))
            operator = _txt(node.child_by_field_name("operator"))
            return merge(left, right) if operator == "+" else None
        if t == "ternary_expression":
            self.expr(node.child_by_field_name("condition"))
            return merge(self.expr(node.child_by_field_name("consequence")), self.expr(node.child_by_field_name("alternative")))
        if t == "assignment_expression":
            left = node.child_by_field_name("left")
            value = self.expr(node.child_by_field_name("right"))
            if _txt(node.child_by_field_name("operator")) == "+=":
                value = merge(value, self.expr(left))
            key = _txt(left) if left.type == "identifier" else (
                "this." + _txt(left.child_by_field_name("field")) if left.type == "field_access" and _txt(left.child_by_field_name("object")) == "this" else None)
            if key:
                self.assign(key, value, node)
            return value
        if t == "field_access":
            obj = node.child_by_field_name("object")
            key = _txt(node)
            if key in self.env:
                return self.env[key]
            return self.expr(obj) if obj is not None and obj.type != "this" else None
        if t == "array_access":
            return self.expr(node.child_by_field_name("array"))
        if t == "array_creation_expression":
            init = node.child_by_field_name("value")
            return merge(*(self.expr(c) for c in init.named_children)) if init is not None else None
        if t == "array_initializer":
            return merge(*(self.expr(c) for c in node.named_children))
        if t == "method_invocation":
            return self.invocation(node)
        if t == "object_creation_expression":
            return self.creation(node)
        if t == "lambda_expression":
            self.walk(node)
            return None
        if t in ("update_expression", "unary_expression", "instanceof_expression"):
            return None
        result = None
        for child in node.named_children:
            result = merge(result, self.expr(child))
        return result

    def _args(self, node) -> list:
        args = node.child_by_field_name("arguments")
        return [a for a in args.named_children] if args is not None else []

    def invocation(self, node):
        name = _txt(node.child_by_field_name("name"))
        obj = node.child_by_field_name("object")
        obj_text = _txt(obj)
        receiver = self.expr(obj) if obj is not None and obj.type != "this" else None
        arg_nodes = self._args(node)
        args = [self.expr(a) for a in arg_nodes]
        # sources
        root = obj_text.split(".")[0].split("(")[0] if obj is not None else ""
        if name in REQUEST_SOURCE_METHODS and (root in self.request_vars or self.types.get(root) in REQUEST_TYPES):
            return Taint((self.step("source", node, f"{obj_text}.{name}() (entrada HTTP)"),))
        self.check_sinks(node, name, obj, obj_text, receiver, args, arg_nodes)
        qualified = f"{obj_text}.{name}" if obj is not None else name
        if name in CLEANSING_CALLS or qualified in CLEANSING_QUALIFIED:
            return None
        combined = merge(receiver, *args)
        if combined is None:
            return None
        if name in RULE_SANITIZERS and RULE_SANITIZERS[name]:
            return combined.sanitize(RULE_SANITIZERS[name]).extend(self.step("sanitizer", node, f"saneado con {name}()"))
        if name == "getName" and obj_text.endswith("FilenameUtils") or name == "getFileName":
            return combined.sanitize({"SEC-PATH"})
        # Builder-style mutation: sb.append(tainted) taints sb
        if obj is not None and obj.type == "identifier" and name in {"append", "insert", "add", "addAll", "put", "putAll",
                                                                     "set", "concat", "replace"} and merge(*args) is not None:
            self.env[obj_text] = merge(receiver, *args).extend(self.step("propagation", node, f"añadido a '{obj_text}'"))
        owner = self.class_name if obj is None or obj.type == "this" else self._receiver_type(obj)
        summary = self.p.summaries.get((owner, name, len(arg_nodes))) if owner else None
        if summary is None:
            summary = self.p.summaries.get((None, name, len(arg_nodes)))
        if summary is not None and (obj is None or obj.type in ("identifier", "field_access", "this")) and \
                name not in {"append", "toString", "get", "format", "valueOf"}:
            return self._apply_summary(node, name, summary, args)
        return combined

    def _apply_summary(self, node, name, summary: Summary, args):
        homonyms = summary.defined > 1
        for index, rule_id, sink_step, inner in summary.sinks:
            taint = args[index] if index < len(args) else None
            if taint is None or taint.blocked(rule_id):
                continue
            if self.mode == "summary":
                for param in taint.params:
                    self.summary.sinks.append((param, rule_id, sink_step,
                                               tuple(inner) + (self.step("propagation", node, f"llamada a {name}()"),)))
                continue
            if taint.steps and self._first_report(rule_id, taint):
                trace = taint.steps + (self.step("propagation", node, f"pasado a {name}()"),) + tuple(inner) + (sink_step,)
                self.p.report(self.f, rule_id, node, _message(rule_id, sink_step.note), trace=trace[: MAX_STEPS + 3],
                              confidence="medium" if homonyms or taint.confidence != "high" else "high")
        returned = [args[i] for i in summary.returns if i < len(args) and args[i] is not None]
        return merge(*returned) if summary.returns or not summary.sinks else merge(*args)

    def creation(self, node):
        ctype = _simple_type(node.child_by_field_name("type"))
        arg_nodes = self._args(node)
        args = [self.expr(a) for a in arg_nodes]
        first = args[0] if args else None
        hits = []
        if ctype in FILE_CLASSES:
            hits.append(("SEC-PATH", merge(*args[:2])))
        if ctype == "URL":
            hits.append(("SEC-SSRF", first))
        if ctype == "ProcessBuilder":
            hits.append(("SEC-CMDI", merge(*args)))
        if ctype in ("RedirectView",):
            hits.append(("SEC-REDIRECT", first))
        if ctype == "ModelAndView" and arg_nodes and arg_nodes[0].type == "binary_expression" and \
                _txt(arg_nodes[0]).lstrip('"').startswith("redirect:"):
            hits.append(("SEC-REDIRECT", first))
        if ctype in ("XMLDecoder",):
            hits.append(("SEC-DESER", first))
        self.fire(node, hits, f"new {ctype}()")
        if ctype in ("ObjectInputStream", "XMLDecoder") and first is not None:
            return first.extend(self.step("propagation", node, f"new {ctype}(...)"))
        result = merge(*args)
        if result is not None and ctype in FILE_CLASSES:
            result = result.sanitize({"SEC-PATH"})  # already reported here: do not repeat on every later use
        return result

    # ------------------------------------------------------------------ sinks
    def _receiver_type(self, obj) -> str:
        if obj is None:
            return ""
        text = _txt(obj)
        return self.types.get(text, "")

    def check_sinks(self, node, name, obj, obj_text, receiver, args, arg_nodes):
        first = args[0] if args else None
        rtype = self._receiver_type(obj)
        hits = []
        if name in SQL_ALWAYS or (name in SQL_RECEIVER_ONLY and (rtype in SQL_TYPES or SQL_RECEIVER.search(obj_text or ""))):
            hits.append(("SEC-SQLI", first))
        if name == "exec" and ("getRuntime" in obj_text or rtype == "Runtime"):
            hits.append(("SEC-CMDI", merge(*args)))
        if name == "command" and (rtype == "ProcessBuilder" or "ProcessBuilder" in obj_text):
            hits.append(("SEC-CMDI", merge(*args)))
        if name == "eval" and (rtype in ("ScriptEngine", "GroovyShell") or re.search(r"(?i)engine|script", obj_text)):
            hits.append(("SEC-CODEI", first))
        if name in ("evaluate", "parse") and (rtype == "GroovyShell" or "GroovyShell" in obj_text):
            hits.append(("SEC-CODEI", first))
        if name == "parseExpression":
            hits.append(("SEC-CODEI", first))
        if name == "getValue" and obj_text == "Ognl":
            hits.append(("SEC-CODEI", first))
        if name == "forName" and obj_text == "Class":
            hits.append(("SEC-REFLECT", first))
        if obj_text in ("Files",) and name in FILES_METHODS:
            hits.append(("SEC-PATH", merge(*args[:2])))
        if name in ("getResource",) and re.search(r"(?i)resourceloader|context", obj_text + rtype):
            hits.append(("SEC-PATH", first))
        if name in REST_METHODS and (rtype in ("RestTemplate", "RestOperations") or re.search(r"(?i)rest|template", obj_text)):
            hits.append(("SEC-SSRF", first))
        if name in ("uri", "url") and TRUST_RECEIVERS.search(obj_text or ""):
            hits.append(("SEC-SSRF", first))
        if name in ("newBuilder",) and obj_text == "HttpRequest":
            hits.append(("SEC-SSRF", first))
        if name in ("write", "print", "println", "append", "printf", "format") and (
                "getWriter" in obj_text or "getOutputStream" in obj_text or rtype in ("PrintWriter", "ServletOutputStream")):
            hits.append(("SEC-XSS", merge(*args)))
        if name == "sendRedirect":
            hits.append(("SEC-REDIRECT", first))
        if name == "search" and (rtype in ("DirContext", "InitialDirContext", "LdapContext", "LdapTemplate") or
                                 re.search(r"(?i)ldap|dircontext|\bctx\b", obj_text)):
            hits.append(("SEC-LDAPI", args[1] if len(args) > 1 else None))
        if name == "readObject" and receiver is not None:
            hits.append(("SEC-DESER", receiver))
        if name in ("load", "loadAs", "loadAll") and (rtype == "Yaml" or re.search(r"\bnew Yaml\(|yaml", obj_text, re.I)):
            hits.append(("SEC-DESER", first))
        if name == "fromXML" and re.search(r"(?i)xstream", obj_text + rtype):
            hits.append(("SEC-DESER", first))
        self.fire(node, hits, f"{obj_text + '.' if obj_text else ''}{name}()")

    def fire(self, node, hits, sink_label):
        for rule_id, taint in hits:
            if taint is None or taint.blocked(rule_id):
                continue
            sink = self.step("sink", node, sink_label)
            if self.mode == "summary":
                for param in taint.params:
                    self.summary.sinks.append((param, rule_id, sink, taint.steps))
                continue
            if taint.steps and self._first_report(rule_id, taint):
                self.p.report(self.f, rule_id, node, _message(rule_id, sink_label), trace=taint.steps + (sink,),
                              confidence=taint.confidence)

    def _first_report(self, rule_id, taint) -> bool:
        """The same variable reaching several sinks of one rule is one flaw (e.g. delete + copy of one path)."""
        last = taint.steps[-1]
        match = re.match(r"asignado a '([^']+)'", last.note or "")
        if last.kind != "propagation" or not match:
            return True
        key = (rule_id, match.group(1), last.file, last.line)
        if key in self.reported_flows:
            return False
        self.reported_flows.add(key)
        return True

    def _check_redirect_return(self, value, taint, node):
        text = _txt(value)
        if self.is_controller and value.type == "binary_expression" and text.lstrip().startswith('"redirect:'):
            if not taint.blocked("SEC-REDIRECT"):
                self.p.report(self.f, "SEC-REDIRECT", node, _message("SEC-REDIRECT", "return \"redirect:\" + ..."),
                              trace=taint.steps + (self.step("sink", node, "redirect: con dato del usuario"),),
                              confidence=taint.confidence)


def _message(rule_id: str, sink: str) -> str:
    texts = {
        "SEC-SQLI": "Datos externos llegan a una consulta SQL construida dinámicamente",
        "SEC-CMDI": "Datos externos llegan a la ejecución de un comando del sistema",
        "SEC-CODEI": "Datos externos se evalúan como código o expresión",
        "SEC-PATH": "Datos externos controlan una ruta de fichero",
        "SEC-SSRF": "Datos externos controlan la URL de una petición saliente",
        "SEC-XSS": "Datos externos se escriben en la respuesta HTML sin codificar",
        "SEC-REDIRECT": "Datos externos controlan el destino de una redirección",
        "SEC-DESER": "Datos externos se deserializan con un mecanismo inseguro",
        "SEC-LDAPI": "Datos externos forman un filtro LDAP",
        "SEC-REFLECT": "Datos externos eligen la clase que se carga por reflexión",
    }
    return f"{texts.get(rule_id, 'Flujo de datos no confiables')} ({sink})."


class JavaPatterns:
    """Structural security/correctness checks on one Java file."""

    XXE_FACTORIES = {"DocumentBuilderFactory", "SAXParserFactory", "XMLInputFactory", "TransformerFactory",
                     "SchemaFactory", "XMLReaderFactory", "SAXTransformerFactory"}
    XXE_GUARDS = re.compile(r"disallow-doctype-decl|FEATURE_SECURE_PROCESSING|ACCESS_EXTERNAL_DTD|SUPPORT_DTD|"
                            r"external-general-entities|IS_SUPPORTING_EXTERNAL_ENTITIES|setExpandEntityReferences\(false\)|"
                            r"load-external-dtd")

    def __init__(self, project: JavaProject, jf: JavaFile):
        self.p = project
        self.f = jf
        self.text = jf.source.decode("utf-8", errors="replace")

    def add(self, rule_id, node, message, **kw):
        self.p.report(self.f, rule_id, node, message, **kw)

    def run(self):
        stack = [self.f.tree.root_node]
        while stack:
            node = stack.pop()
            handler = getattr(self, "on_" + node.type, None)
            if handler is not None:
                handler(node)
            stack.extend(reversed(node.named_children))

    # exceptions ---------------------------------------------------------------------
    def on_catch_clause(self, node):
        param = next((c for c in node.named_children if c.type == "catch_formal_parameter"), None)
        caught = _txt(param.child_by_field_name("type") if param is not None and param.child_by_field_name("type") else
                      next((c for c in (param.named_children if param else []) if c.type == "catch_type"), None))
        body = node.child_by_field_name("body")
        statements = [c for c in body.named_children if c.type not in ("line_comment", "block_comment")] if body else []
        body_text = _txt(body)
        variable = _txt(param.child_by_field_name("name")) if param is not None and param.child_by_field_name("name") else ""
        if not statements and variable.lower() in {"ignored", "ignore", "expected", "ignorable", "unused", "_"}:
            self.add("BUG-EMPTY-CATCH", node, f"Se descarta {caught or 'una excepción'} de forma intencionada "
                                              f"('{variable}'); confirmar que no oculta fallos.", severity="low")
        elif not statements:
            broad = re.search(r"\b(Exception|Throwable|RuntimeException|Error)\b", caught or "")
            self.add("BUG-EMPTY-CATCH", node, f"Se captura {caught or 'una excepción'} y se descarta sin registrar ni propagar.",
                     severity=None if broad else "low")
        elif "InterruptedException" in caught and "interrupt()" not in body_text and "throw" not in body_text:
            self.add("BUG-INTERRUPTED", node, "Se captura InterruptedException sin restaurar la interrupción del hilo.")
        elif re.search(r"\b(Throwable|Exception)\b", caught or "") and len(statements) == 1 and \
                re.fullmatch(r"\s*\w+\.printStackTrace\(\);\s*", _txt(statements[0])):
            self.add("BUG-BROAD-CATCH", node, f"Se captura {caught} y solo se imprime la traza; el error se pierde.")

    # comparisons / numbers ------------------------------------------------------------
    def on_binary_expression(self, node):
        operator = _txt(node.child_by_field_name("operator"))
        if operator not in ("==", "!="):
            return
        left, right = node.child_by_field_name("left"), node.child_by_field_name("right")
        if "string_literal" in (left.type, right.type) and "null_literal" not in (left.type, right.type):
            self.add("BUG-STRING-EQ", node, f"'{_txt(node)}' compara referencias de String, no su contenido.")

    def on_object_creation_expression(self, node):
        ctype = _simple_type(node.child_by_field_name("type"))
        args = node.child_by_field_name("arguments")
        first = args.named_children[0] if args is not None and args.named_children else None
        if ctype == "BigDecimal" and first is not None and first.type == "decimal_floating_point_literal":
            self.add("BUG-BIGDECIMAL-DOUBLE", node, f"new BigDecimal({_txt(first)}) no representa exactamente el valor.")
        if ctype == "ObjectInputStream":
            self.add("SEC-UNSAFE-DESER-API", node, "ObjectInputStream deserializa objetos arbitrarios.", confidence="medium")
        if ctype == "XMLDecoder":
            self.add("SEC-UNSAFE-DESER-API", node, "XMLDecoder puede ejecutar código a partir del XML.", severity="high")
        if ctype == "Yaml" and (args is None or not args.named_children) and "SafeConstructor" not in self.text:
            self.add("SEC-UNSAFE-DESER-API", node, "new Yaml() sin SafeConstructor permite instanciar tipos arbitrarios "
                                                   "(SnakeYAML < 2.0).", confidence="medium")
        if ctype in ("SAXReader", "SAXBuilder") and not self.XXE_GUARDS.search(self.text):
            self.add("SEC-XXE", node, f"{ctype} sin desactivar DTD/entidades externas.")
        if ctype == "Random":
            context = self._context_name(node)
            if SECURITY_RANDOM_NAME.search(context):
                self.add("SEC-WEAKRANDOM", node, f"'{context}' se genera con java.util.Random (predecible).")
        if ctype in ("TrustAllStrategy", "TrustSelfSignedStrategy", "NoopHostnameVerifier"):
            self.add("SEC-TLS", node, f"{ctype} desactiva la validación TLS.")

    # invocations ------------------------------------------------------------------
    def on_method_invocation(self, node):
        name = _txt(node.child_by_field_name("name"))
        obj = _txt(node.child_by_field_name("object"))
        args = node.child_by_field_name("arguments")
        arg_nodes = args.named_children if args is not None else []
        literal = _txt(arg_nodes[0]).strip('"') if arg_nodes and arg_nodes[0].type == "string_literal" else None
        if name == "getInstance" and obj == "MessageDigest" and literal and literal.upper().replace("-", "") in {"MD5", "SHA1", "MD2", "MD4"}:
            context = self._context_name(node)
            self.add("SEC-WEAKHASH", node, f"MessageDigest '{literal}' es un hash débil.",
                     severity="medium" if re.search(r"(?i)passw|pwd|secret|token|sign", context) else None)
        if obj == "DigestUtils" and re.match(r"(md5|sha1|md2)(Hex)?$", name, re.I):
            self.add("SEC-WEAKHASH", node, f"DigestUtils.{name} usa un hash débil.")
        if name == "getInstance" and obj == "Cipher" and literal:
            upper = literal.upper()
            if re.match(r"(DES|DESEDE|RC4|RC2|BLOWFISH|ARCFOUR)\b", upper) or "/ECB/" in upper or upper in ("AES", "DES"):
                self.add("SEC-WEAKCIPHER", node, f"Cipher.getInstance(\"{literal}\") usa un algoritmo o modo inseguro.")
        if name in ("newInstance", "newFactory", "newDefaultInstance") and obj in self.XXE_FACTORIES:
            self._xxe(node, obj)
        if name == "parse" and re.search(r"Jwts\.parser|parserBuilder\(\)|\bjwtParser\b|JwtParser", obj):
            self.add("SEC-JWT", node, "JwtParser.parse() acepta tokens sin firma (alg: none); usar parseClaimsJws() "
                                      "o parseSignedClaims().")
        if name == "random" and obj == "Math":
            context = self._context_name(node)
            if SECURITY_RANDOM_NAME.search(context):
                self.add("SEC-WEAKRANDOM", node, f"'{context}' se genera con Math.random() (predecible).")
        if name in ("setHostnameVerifier", "setDefaultHostnameVerifier", "hostnameVerifier") and arg_nodes:
            arg = _txt(arg_nodes[0])
            if re.search(r"->\s*true\b|ALLOW_ALL|NoopHostnameVerifier", arg):
                self.add("SEC-TLS", node, "Se acepta cualquier nombre de host en TLS.")
        if name == "disable" and re.search(r"\bcsrf\(\)", obj) or (
                name == "csrf" and arg_nodes and re.search(r"::disable|\.disable\(\)", _txt(arg_nodes[0]))):
            stateless = "STATELESS" in self.text
            self.add("SEC-CSRF", node, "Se desactiva la protección CSRF de Spring Security."
                     + (" La configuración es STATELESS; si solo se usan tokens Bearer el riesgo es bajo." if stateless else ""),
                     severity="low" if stateless else None)
        if name in ("allowedOrigins", "addAllowedOrigin", "setAllowedOrigins", "allowedOriginPatterns") and \
                any('"*"' in _txt(a) for a in arg_nodes):
            scope = _enclosing(node, ("method_declaration",))
            credentials = scope is not None and re.search(r"allowCredentials\(\s*true|setAllowCredentials\(\s*true", _txt(scope))
            self.add("SEC-CORS", node, "CORS permite cualquier origen" + (" con credenciales." if credentials else "."),
                     severity="medium" if credentials else "low")
        if name in ("parseClaimsJwt", "parseUnsecuredClaims", "parseUnsecuredContent"):
            self.add("SEC-JWT", node, f"{name}() acepta JWT sin firma.")
        if name == "none" and obj == "Algorithm":
            self.add("SEC-JWT", node, "Algorithm.none() desactiva la firma del JWT.")
        if name in ("enableDefaultTyping", "activateDefaultTyping"):
            self.add("SEC-UNSAFE-DESER-API", node, f"ObjectMapper.{name}() permite deserializar tipos arbitrarios.",
                     severity="high")

    def _xxe(self, node, factory: str):
        method = _enclosing(node, ("method_declaration", "constructor_declaration", "lambda_expression"))
        guards = [n for n in _descendants(method) if n.type == "method_invocation" and self.XXE_GUARDS.search(_txt(n))] \
            if method is not None else []
        if guards:
            if all(_inside(guard, "if_statement", method) for guard in guards):
                self.add("SEC-XXE", node, f"{factory}: la protección contra XXE solo se aplica dentro de un if; "
                                          "en el resto de casos el parser resuelve entidades externas.", confidence="medium")
            return
        cls = _enclosing(node, ("class_declaration",))
        if not self.XXE_GUARDS.search(_txt(cls) if cls is not None else self.text):
            self.add("SEC-XXE", node, f"{factory} creado sin desactivar DTD/entidades externas.")

    def on_field_access(self, node):
        text = _txt(node)
        if text.endswith("ALLOW_ALL_HOSTNAME_VERIFIER") or text.endswith("InsecureTrustManagerFactory.INSTANCE"):
            self.add("SEC-TLS", node, f"{text} desactiva la validación TLS.")

    # declarations -----------------------------------------------------------------
    def on_method_declaration(self, node):
        annotations = {_annotation_name(a) for a in _annotations(node)}
        modifiers = _modifiers(node)
        name = _txt(node.child_by_field_name("name"))
        if "Transactional" in annotations and modifiers & {"private", "final", "static"}:
            self.add("BUG-TX-PRIVATE", node.child_by_field_name("name"),
                     f"@Transactional en el método {' '.join(sorted(modifiers & {'private', 'final', 'static'}))} '{name}' se ignora.")
        if name in ("checkServerTrusted", "checkClientTrusted"):
            body = node.child_by_field_name("body")
            statements = [c for c in body.named_children if c.type not in ("line_comment", "block_comment")] if body else []
            if body is not None and not statements:
                self.add("SEC-TLS", node.child_by_field_name("name"), f"{name}() vacío: se confía en cualquier certificado.")
        if name == "verify" and "HostnameVerifier" in _txt(_enclosing(node, ("class_declaration", "object_creation_expression"))):
            body = _txt(node.child_by_field_name("body"))
            if re.fullmatch(r"\{\s*return\s+true;\s*\}", body or ""):
                self.add("SEC-TLS", node.child_by_field_name("name"), "HostnameVerifier.verify() devuelve siempre true.")

    def on_field_declaration(self, node):
        ftype = _simple_type(node.child_by_field_name("type"))
        modifiers = _modifiers(node)
        if ftype in ("SimpleDateFormat", "DateFormat") and "static" in modifiers:
            self.add("BUG-SHARED-DATEFORMAT", node, f"Campo static {ftype} compartido entre hilos.")
        self._declared_secrets(node, ftype)

    def on_local_variable_declaration(self, node):
        self._declared_secrets(node, _simple_type(node.child_by_field_name("type")))

    def _declared_secrets(self, node, vtype):
        if vtype not in ("String", "var", "char"):
            return
        for decl in node.children_by_field_name("declarator"):
            name = _txt(decl.child_by_field_name("name"))
            value = decl.child_by_field_name("value")
            if value is not None and value.type == "string_literal":
                literal = _txt(value)[1:-1]
                if looks_like_secret(name, literal):
                    line_text = self.f.lines[_line(node) - 1]
                    self.add("SEC-SECRET", node, f"'{name}' tiene un valor literal que parece una credencial.",
                             snippet=redact(line_text.strip(), literal), confidence="medium")

    def on_string_literal(self, node):
        literal = _txt(node)[1:-1]
        label = find_token_secrets(literal)
        if label:
            self.add("SEC-SECRET", node, f"El código contiene un/a {label}.",
                     snippet=redact(self.f.lines[_line(node) - 1].strip(), literal))

    def on_annotation(self, node):
        name = _annotation_name(node)
        args = _txt(node.child_by_field_name("arguments"))
        if name == "Value":
            match = re.search(r'"\$\{([^:}]+):([^}]*)\}"', args)
            if match and looks_like_secret(match.group(1).replace(".", "_"), match.group(2)):
                self.add("SEC-SECRET", node, f"Valor por defecto literal para '{match.group(1)}'.",
                         snippet=redact(_txt(node), match.group(2)), confidence="medium")
        if name == "CrossOrigin" and ('"*"' in args or not args or args == "()"):
            credentials = 'allowCredentials = "true"' in args.replace("'", '"')
            self.add("SEC-CORS", node, "@CrossOrigin permite cualquier origen" + (" con credenciales." if credentials else "."),
                     severity="medium" if credentials else "low")

    def on_marker_annotation(self, node):
        if _annotation_name(node) == "CrossOrigin":
            self.add("SEC-CORS", node, "@CrossOrigin sin orígenes permite cualquier origen.", severity="low")

    def _context_name(self, node) -> str:
        current = node.parent
        while current is not None:
            if current.type == "variable_declarator":
                return _txt(current.child_by_field_name("name"))
            if current.type == "assignment_expression":
                return _txt(current.child_by_field_name("left"))
            if current.type in ("method_declaration", "constructor_declaration"):
                return _txt(current.child_by_field_name("name"))
            current = current.parent
        return ""
