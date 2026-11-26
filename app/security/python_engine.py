"""AST-based taint tracking and structural checks for Python sources.

The analysed code is parsed with :mod:`ast`; it is never imported or executed.
Taint is tracked per function (flow-insensitive inside a function body) with
one-level-deep summaries for functions defined in the same module.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from .contracts import SecurityFinding, TraceStep

MAX_STEPS = 8

# ---------------------------------------------------------------------------- catalogues
FLASK_REQUEST_IGNORED = {"method", "endpoint", "blueprint", "url_rule", "is_json", "is_secure", "scheme"}
DJANGO_REQUEST_ATTRS = {"GET", "POST", "body", "COOKIES", "META", "FILES", "headers", "data", "query_params",
                        "path", "path_info", "get_full_path"}
ROUTE_DECORATORS = {"route", "get", "post", "put", "delete", "patch", "api_route", "websocket", "head", "options"}
NON_INPUT_PARAMS = {"self", "cls", "request", "req", "db", "session", "background_tasks", "response"}

# Calls whose result is never attacker-controlled (type conversion / pure metadata).
CLEANSING_CALLS = {"int", "float", "bool", "len", "abs", "round", "hash", "id", "isinstance", "uuid.UUID",
                   "decimal.Decimal", "datetime.date.fromisoformat", "datetime.datetime.fromisoformat"}
# Calls that neutralise taint for specific rules.
RULE_SANITIZERS = {
    "shlex.quote": {"SEC-CMDI"}, "pipes.quote": {"SEC-CMDI"},
    "werkzeug.utils.secure_filename": {"SEC-PATH"}, "secure_filename": {"SEC-PATH"},
    "os.path.basename": {"SEC-PATH"},
    "html.escape": {"SEC-XSS"}, "markupsafe.escape": {"SEC-XSS"}, "flask.escape": {"SEC-XSS"},
    "django.utils.html.escape": {"SEC-XSS"}, "bleach.clean": {"SEC-XSS"}, "cgi.escape": {"SEC-XSS"},
    "urllib.parse.quote": {"SEC-XSS", "SEC-PATH"},
    "ldap.filter.escape_filter_chars": {"SEC-LDAPI"}, "ldap3.utils.conv.escape_filter_chars": {"SEC-LDAPI"},
}

HTTP_CLIENT_FUNCS = {"get", "post", "put", "delete", "patch", "head", "options", "request", "stream"}
PATH_FUNCS = {"open", "io.open", "codecs.open", "os.remove", "os.unlink", "os.rmdir", "os.removedirs",
              "os.makedirs", "os.mkdir", "os.listdir", "os.rename", "os.replace", "os.scandir", "shutil.rmtree",
              "shutil.copy", "shutil.copy2", "shutil.copyfile", "shutil.copytree", "shutil.move",
              "flask.send_file", "django.http.FileResponse", "fastapi.responses.FileResponse",
              "starlette.responses.FileResponse"}
PATH_METHODS = {"read_text", "read_bytes", "write_text", "write_bytes", "unlink", "rmdir", "mkdir", "touch"}
SQL_METHODS = {"execute", "executemany", "executescript", "raw", "read_sql", "read_sql_query", "exec_driver_sql"}
SQL_FUNCS = {"sqlalchemy.text", "sqlalchemy.sql.text", "pandas.read_sql", "pandas.read_sql_query",
             "django.db.models.expressions.RawSQL"}
CMD_FUNCS = {"os.system", "os.popen", "subprocess.getoutput", "subprocess.getstatusoutput", "commands.getoutput",
             "os.popen2", "os.popen3", "os.popen4"}
SHELL_FUNCS = {"subprocess.run", "subprocess.call", "subprocess.check_call", "subprocess.check_output",
               "subprocess.Popen", "asyncio.create_subprocess_shell"}
EXEC_FUNCS = {"os.execl", "os.execlp", "os.execv", "os.execvp", "os.execve", "os.spawnl", "os.spawnv"}
CODE_FUNCS = {"eval", "exec", "compile", "builtins.eval", "builtins.exec"}
DESER_FUNCS = {"pickle.loads", "pickle.load", "cPickle.loads", "marshal.loads", "dill.loads", "jsonpickle.decode",
               "shelve.open", "yaml.unsafe_load", "_pickle.loads"}
XSS_FUNCS = {"markupsafe.Markup", "flask.Markup", "django.utils.safestring.mark_safe", "django.http.HttpResponse",
             "fastapi.responses.HTMLResponse", "starlette.responses.HTMLResponse"}
SSTI_FUNCS = {"flask.render_template_string", "jinja2.Template", "jinja2.Environment.from_string"}
REDIRECT_FUNCS = {"flask.redirect", "django.shortcuts.redirect", "django.http.HttpResponseRedirect",
                  "fastapi.responses.RedirectResponse", "starlette.responses.RedirectResponse"}
URL_FUNCS = {"urllib.request.urlopen", "urllib.request.Request", "urllib.urlopen", "urllib2.urlopen"}

SENSITIVE_NAME = re.compile(r"(?i)(passw(or)?d|passwd|\bpwd\b|_pwd$|secret|api[_-]?key|access[_-]?key|private[_-]?key|"
                            r"auth[_-]?token|access[_-]?token|refresh[_-]?token|client[_-]?secret|bearer)")
NON_SECRET_NAME = re.compile(r"(?i)(_url|_uri|_path|_file|_dir|_name|_field|_header|_type|_env|_var|_label|_prompt|"
                             r"_length|_len|_hint|_policy|_regex|_pattern|_endpoint|_message|_msg|_template|_link|_text|"
                             r"_title|_placeholder|_param|_parameter|_property|_column|_table|_id|_key_name|_route)$")
PLACEHOLDER = re.compile(r"(?i)^(\$\{.*\}|<.*>|\{\{.*\}\}|%\(.*\)s|x+|\*+|\.+|-+|your[_-].*|change[_-]?me|"
                         r"example.*|dummy.*|placeholder.*|test.*|fake.*|sample.*|none|null|todo)$")
SECRET_TOKENS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "clave de acceso de AWS"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"), "token de GitHub"),
    (re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"), "token de Slack"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH |ENCRYPTED )?PRIVATE KEY-----(?:\s|\\n)*[A-Za-z0-9+/=]{64,}"),
     "clave privada"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "clave de API de Google"),
    (re.compile(r"sk_live_[0-9a-zA-Z]{20,}"), "clave secreta de Stripe"),
    (re.compile(r"glpat-[0-9A-Za-z\-_]{20}"), "token de GitLab"),
]
SECURITY_RANDOM_NAME = re.compile(r"(?i)(token|passw|secret|otp|nonce|salt|api_?key|session|csrf|reset|verification)")


def looks_like_secret(name: str, value: str) -> bool:
    if not SENSITIVE_NAME.search(name) or NON_SECRET_NAME.search(name):
        return False
    value = value.strip()
    if len(value) < 8 or PLACEHOLDER.match(value) or " " in value.strip():
        return False
    if re.match(r"^[a-z][a-z_\-.]*$", value):  # field/property names such as "password_hash"
        return False
    if re.fullmatch(r"[^\W\d_]+", value):  # a plain word ("Password", "Contraseña"): a label, not a credential
        return False
    if re.match(r"^(https?|ftp|file)://", value) and "@" not in value:
        return False
    if value.startswith(("/", "./", "../", "classpath:", "env:", "vault:")):
        return False
    return True


def find_token_secrets(value: str) -> str | None:
    for pattern, label in SECRET_TOKENS:
        if pattern.search(value):
            return label
    return None


def redact(text: str, secret: str) -> str:
    return text.replace(secret, "***") if secret else text


# ---------------------------------------------------------------------------- taint values
@dataclass(frozen=True)
class Taint:
    steps: tuple[TraceStep, ...]
    sanitized_for: frozenset = frozenset()
    confidence: str = "high"
    # Function-summary tags: names of parameters this value derives from (summary mode).
    params: frozenset = frozenset()

    def extend(self, step: TraceStep) -> "Taint":
        last = self.steps[-1] if self.steps else None
        redundant = last is not None and last.line == step.line and last.file == step.file
        steps = self.steps if redundant or len(self.steps) >= MAX_STEPS else self.steps + (step,)
        return Taint(steps, self.sanitized_for, self.confidence, self.params)

    def sanitize(self, rules) -> "Taint":
        return Taint(self.steps, self.sanitized_for | frozenset(rules), self.confidence, self.params)

    def weaken(self) -> "Taint":
        return Taint(self.steps, self.sanitized_for, "medium", self.params)

    def blocked(self, rule_id: str) -> bool:
        return rule_id in self.sanitized_for


def merge(*values: Taint | None) -> Taint | None:
    present = [v for v in values if v is not None]
    if not present:
        return None
    first = present[0]
    sanitized = frozenset.intersection(*(v.sanitized_for for v in present))
    confidence = "high" if all(v.confidence == "high" for v in present) else "medium"
    params = frozenset().union(*(v.params for v in present))
    return Taint(first.steps, sanitized, confidence, params)


@dataclass
class Summary:
    returns: set = field(default_factory=set)  # parameter names that flow to the return value
    sinks: list = field(default_factory=list)  # (param name, rule id, sink step, steps inside callee)


# ---------------------------------------------------------------------------- analyzer
class PythonAnalyzer:
    def __init__(self, source: str, rel: str, is_test: bool = False, project: "PythonProject | None" = None):
        self.source = source
        self.rel = rel
        self.is_test = is_test
        self.project = project
        self.module = rel.rsplit("/", 1)[-1].removesuffix(".py")
        self.tree = None
        self.lines = source.splitlines()
        self.aliases: dict[str, str] = {}
        self.findings: list[SecurityFinding] = []
        self.functions: dict[str, ast.AST] = {}
        self.summaries: dict[str, Summary] = {}
        self._seen: set = set()
        self.error: str | None = None

    # ------------------------------------------------------------------ helpers
    def code(self, node) -> str:
        line = getattr(node, "lineno", 0)
        return self.lines[line - 1].strip()[:200] if 0 < line <= len(self.lines) else ""

    def step(self, kind: str, node, note: str = "") -> TraceStep:
        return TraceStep(kind, self.rel, getattr(node, "lineno", 0), self.code(node), note)

    def qualname(self, node) -> str | None:
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(self.aliases.get(node.id, node.id))
        elif isinstance(node, ast.Call):
            inner = self.qualname(node.func)
            if inner is None:
                return None
            parts.append(inner + "()")
        else:
            return None
        return ".".join(reversed(parts))

    def add(self, rule_id: str, node, message: str, *, trace=(), confidence="high", severity=None, snippet=None):
        key = (rule_id, getattr(node, "lineno", 0))
        if key in self._seen:
            return
        self._seen.add(key)
        self.findings.append(SecurityFinding(
            rule_id=rule_id, file=self.rel, line=getattr(node, "lineno", 0), column=getattr(node, "col_offset", 0),
            snippet=snippet if snippet is not None else self.code(node), message=message, language="python",
            confidence=confidence, trace=list(trace), severity=severity, is_test=self.is_test))

    # ------------------------------------------------------------------ entry point
    def parse(self) -> bool:
        try:
            self.tree = ast.parse(self.source)
        except (SyntaxError, ValueError, RecursionError, MemoryError) as exc:
            self.error = f"{type(exc).__name__}: {exc}"
            return False
        self._collect_imports(self.tree)
        for fn in ast.walk(self.tree):
            if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.functions.setdefault(fn.name, fn)
        return True

    def summarise(self):
        """Compute this module's function summaries (two rounds for helper -> helper chains)."""
        for _ in range(2):
            for fn in self.functions.values():
                self.summaries[fn.name] = self._summarise(fn)

    def report(self) -> list[SecurityFinding]:
        for fn in self.functions.values():
            FunctionTaint(self, fn, mode="report").run()
        module_scope = ast.Module(body=[s for s in self.tree.body if not isinstance(
            s, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))], type_ignores=[])
        FunctionTaint(self, module_scope, mode="report").run()
        PatternChecks(self, self.tree).run()
        return self.findings

    def run(self) -> list[SecurityFinding]:
        if not self.parse():
            return []
        self.summarise()
        return self.report()

    def resolve(self, func) -> tuple["PythonAnalyzer | None", str | None]:
        """Module analyzer and function name targeted by a call (same module or imported)."""
        if isinstance(func, ast.Name):
            if func.id in self.functions:
                return self, func.id
            target = self.aliases.get(func.id, "")
            if "." in target and self.project is not None:
                module, _, name = target.rpartition(".")
                return self.project.module(module, self.rel), name
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name) and self.project is not None:
            module = self.aliases.get(func.value.id)
            if module:
                return self.project.module(module, self.rel), func.attr
        return None, None

    def _collect_imports(self, tree):
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.aliases[alias.asname or alias.name.split(".")[0]] = alias.name if alias.asname else alias.name.split(".")[0]
            elif isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    self.aliases[alias.asname or alias.name] = f"{node.module}.{alias.name}"

    def _summarise(self, fn) -> Summary:
        runner = FunctionTaint(self, fn, mode="summary")
        runner.run()
        return runner.summary


class FunctionTaint:
    """Taint propagation over one function body (or the module scope)."""

    def __init__(self, analyzer: PythonAnalyzer, node, mode: str):
        self.a = analyzer
        self.node = node
        self.mode = mode  # "summary" (parameters are symbolic sources) | "report"
        self.env: dict[str, Taint] = {}
        self.summary = Summary()
        self.reported_flows: set = set()
        self.request_names: set[str] = set()
        self.is_route = False

    # ------------------------------------------------------------------ setup
    def run(self):
        node = self.node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self._init_params(node)
        for stmt in getattr(node, "body", []):
            self.stmt(stmt)

    def _init_params(self, fn):
        args = fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs
        defaults = dict(zip([a.arg for a in (fn.args.posonlyargs + fn.args.args)][-len(fn.args.defaults):] if fn.args.defaults else [],
                            fn.args.defaults))
        defaults.update({a.arg: d for a, d in zip(fn.args.kwonlyargs, fn.args.kw_defaults) if d is not None})
        self.is_route = any(self._is_route_decorator(d) for d in fn.decorator_list)
        for arg in args:
            name = arg.arg
            if name in ("request", "req"):
                self.request_names.add(name)
            if self.mode == "summary":
                if name not in ("self", "cls"):
                    self.env[name] = Taint((), params=frozenset({name}))
                continue
            if self.is_route and name not in NON_INPUT_PARAMS and not self._is_dependency(defaults.get(name), arg) \
                    and not self._is_scalar(arg):
                self.env[name] = Taint((self.a.step("source", arg, f"parámetro '{name}' de un endpoint HTTP"),))

    def _is_route_decorator(self, dec) -> bool:
        target = dec.func if isinstance(dec, ast.Call) else dec
        return isinstance(target, ast.Attribute) and target.attr in ROUTE_DECORATORS and isinstance(dec, ast.Call)

    @staticmethod
    def _is_scalar(arg) -> bool:
        """Typed numeric/boolean/UUID/date parameters cannot carry an injection payload."""
        if arg.annotation is None:
            return False
        annotation = ast.unparse(arg.annotation).split(".")[-1]
        return annotation in {"int", "float", "bool", "UUID", "date", "datetime", "Decimal", "conint", "PositiveInt"}

    def _is_dependency(self, default, arg) -> bool:
        if isinstance(default, ast.Call):
            name = self.a.qualname(default.func) or ""
            if name.split(".")[-1] in {"Depends", "Security", "BackgroundTasks"}:
                return True
        annotation = ast.unparse(arg.annotation) if arg.annotation is not None else ""
        return bool(re.search(r"\b(Request|Session|Response|BackgroundTasks|WebSocket|AsyncSession|User)\b", annotation))

    # ------------------------------------------------------------------ statements
    def stmt(self, node):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return  # analysed separately
        if isinstance(node, ast.Assign):
            value = self.expr(node.value)
            for target in node.targets:
                self.assign(target, value, node)
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            self.assign(node.target, self.expr(node.value), node)
        elif isinstance(node, ast.AugAssign):
            value = merge(self.expr(node.value), self.expr(node.target))
            self.assign(node.target, value, node)
        elif isinstance(node, (ast.For, ast.AsyncFor)):
            self.assign(node.target, self.expr(node.iter), node)
            self.block(node.body)
            self.block(node.orelse)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for item in node.items:
                value = self.expr(item.context_expr)
                if item.optional_vars is not None:
                    self.assign(item.optional_vars, value, node)
            self.block(node.body)
        elif isinstance(node, ast.Return):
            value = self.expr(node.value) if node.value is not None else None
            if value is not None:
                self.summary.returns |= set(value.params)
                if self.mode == "report" and self.is_route and not value.params:
                    self._check_html_return(node, value)
        elif isinstance(node, (ast.If, ast.While)):
            self.expr(node.test)
            self.block(node.body)
            self.block(node.orelse)
        elif isinstance(node, ast.Try) or (hasattr(ast, "TryStar") and isinstance(node, ast.TryStar)):
            self.block(node.body)
            for handler in node.handlers:
                self.block(handler.body)
            self.block(node.orelse)
            self.block(node.finalbody)
        elif isinstance(node, ast.Expr):
            self.expr(node.value)
        elif hasattr(ast, "Match") and isinstance(node, ast.Match):
            self.expr(node.subject)
            for case in node.cases:
                self.block(case.body)
        else:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.expr):
                    self.expr(child)

    def block(self, statements):
        for stmt in statements:
            self.stmt(stmt)

    def assign(self, target, value: Taint | None, node):
        if isinstance(target, (ast.Tuple, ast.List)):
            for element in target.elts:
                self.assign(element, value, node)
            return
        if isinstance(target, ast.Starred):
            self.assign(target.value, value, node)
            return
        key = self._key(target)
        if key is None:
            return
        if value is None:
            if isinstance(target, (ast.Name, ast.Attribute)):
                self.env.pop(key, None)
            return
        new = value.extend(self.a.step("propagation", node, f"asignado a '{key}'"))
        if isinstance(target, ast.Subscript):  # d[k] = tainted  -> d becomes tainted
            new = merge(self.env.get(key), new)
        self.env[key] = new

    def _key(self, target) -> str | None:
        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target, ast.Attribute):
            base = self._key(target.value)
            return f"{base}.{target.attr}" if base else None
        if isinstance(target, ast.Subscript):
            return self._key(target.value)
        return None

    # ------------------------------------------------------------------ expressions
    def expr(self, node) -> Taint | None:
        if node is None:
            return None
        if isinstance(node, ast.Name):
            return self.env.get(node.id)
        if isinstance(node, ast.Attribute):
            source = self._source(node)
            if source is not None:
                return source
            key = self._key(node)
            if key in self.env:
                return self.env[key]
            return self.expr(node.value)
        if isinstance(node, ast.Subscript):
            source = self._source(node)
            if source is not None:
                return source
            self.expr(node.slice)
            return self.expr(node.value)
        if isinstance(node, ast.Call):
            return self.call(node)
        if isinstance(node, ast.JoinedStr):
            return merge(*(self.expr(v) for v in node.values))
        if isinstance(node, ast.FormattedValue):
            return self.expr(node.value)
        if isinstance(node, ast.BinOp):
            return merge(self.expr(node.left), self.expr(node.right))
        if isinstance(node, ast.BoolOp):
            return merge(*(self.expr(v) for v in node.values))
        if isinstance(node, ast.IfExp):
            self.expr(node.test)
            return merge(self.expr(node.body), self.expr(node.orelse))
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return merge(*(self.expr(e) for e in node.elts))
        if isinstance(node, ast.Dict):
            return merge(*(self.expr(v) for v in node.values), *(self.expr(k) for k in node.keys if k is not None))
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            taints = [self.expr(g.iter) for g in node.generators]
            for g in node.generators:
                self.assign(g.target, self.expr(g.iter), g.iter)
            return merge(self.expr(node.elt), *taints)
        if isinstance(node, ast.DictComp):
            for g in node.generators:
                self.assign(g.target, self.expr(g.iter), g.iter)
            return merge(self.expr(node.key), self.expr(node.value))
        if isinstance(node, (ast.Await, ast.Starred)):
            return self.expr(node.value)
        if isinstance(node, ast.NamedExpr):
            value = self.expr(node.value)
            self.assign(node.target, value, node)
            return value
        if isinstance(node, ast.Compare):
            self.expr(node.left)
            for c in node.comparators:
                self.expr(c)
            return None  # booleans carry no attacker-controlled content
        if isinstance(node, ast.UnaryOp):
            return None if isinstance(node.op, ast.Not) else self.expr(node.operand)
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.expr):
                self.expr(child)
        return None

    def _source(self, node) -> Taint | None:
        """Framework request data (Flask ``request.*``, Django/DRF ``request.GET`` ...)."""
        if self.a.qualname(node) is None:
            return None
        name = self.a.qualname(node)
        if name.startswith("flask.request."):
            attr = name.split(".")[2].rstrip("()")
            if attr in FLASK_REQUEST_IGNORED:
                return None
            return Taint((self.a.step("source", node, "dato de la petición HTTP (Flask request)"),))
        base = node
        while isinstance(base, (ast.Attribute, ast.Subscript, ast.Call)):
            inner = base.value if not isinstance(base, ast.Call) else base.func
            if isinstance(inner, ast.Name) and inner.id in self.request_names and isinstance(base, ast.Attribute):
                if base.attr in DJANGO_REQUEST_ATTRS:
                    return Taint((self.a.step("source", node, f"dato de la petición HTTP (request.{base.attr})"),))
                return None
            base = inner
        return None

    # ------------------------------------------------------------------ calls
    def call(self, node: ast.Call) -> Taint | None:
        name = self.a.qualname(node.func) or ""
        short = name.split(".")[-1]
        source = self._source(node)
        receiver = self.expr(node.func.value) if isinstance(node.func, ast.Attribute) else None
        args = [self.expr(a) for a in node.args]
        kwargs = {k.arg: self.expr(k.value) for k in node.keywords}
        if source is not None:
            return source
        self.check_sinks(node, name, short, receiver, args, kwargs)
        combined = merge(receiver, *args, *kwargs.values())
        if combined is None:
            return None
        if name in CLEANSING_CALLS or short in {"int", "float", "bool", "len"}:
            return None
        for sanitizer, rules in RULE_SANITIZERS.items():
            if name == sanitizer or (name == sanitizer.split(".")[-1] and "." in sanitizer and
                                     self.a.aliases.get(name) == sanitizer):
                return combined.sanitize(rules).extend(self.a.step("sanitizer", node, f"saneado con {sanitizer}"))
        owner, function = self.a.resolve(node.func)
        summary = owner.summaries.get(function) if owner is not None else None
        if summary is not None:
            return self._apply_summary(node, summary, args, kwargs, owner.functions.get(function), function)
        return combined

    def _apply_summary(self, node, summary: Summary, args, kwargs, fn=None, function="") -> Taint | None:
        params = [a.arg for a in (fn.args.posonlyargs + fn.args.args)] if fn else []
        bound = {params[i]: t for i, t in enumerate(args) if i < len(params) and t is not None}
        bound.update({k: v for k, v in kwargs.items() if k and v is not None})
        for param, rule_id, sink_step, inner in summary.sinks:
            taint = bound.get(param)
            if taint is None or taint.blocked(rule_id):
                continue
            if self.mode == "summary":
                if taint.params:
                    self.summary.sinks.append((next(iter(taint.params)), rule_id, sink_step,
                                               inner + (self.a.step("propagation", node, "llamada a función auxiliar"),)))
                continue
            if taint.steps and self._first_report(rule_id, taint):
                call_step = self.a.step("propagation", node, f"pasado a {function}()")
                trace = taint.steps + (call_step,) + tuple(inner) + (sink_step,)
                self.a.add(rule_id, node, self._message(rule_id, sink_step.note.removeprefix("llega a ")), trace=trace,
                           confidence="medium" if taint.confidence != "high" else "high")
        returned = [bound[p] for p in summary.returns if p in bound]
        return merge(*returned)

    # ------------------------------------------------------------------ sinks
    def check_sinks(self, node, name, short, receiver, args, kwargs):
        def first(index=0, kw=None):
            if kw and kwargs.get(kw) is not None:
                return kwargs[kw]
            return args[index] if len(args) > index else None

        hits: list[tuple[str, Taint | None]] = []
        if name in CODE_FUNCS and "." not in name.replace("builtins.", ""):
            hits.append(("SEC-CODEI", first()))
        if name in CMD_FUNCS:
            hits.append(("SEC-CMDI", first(0, "cmd")))
        if name in SHELL_FUNCS and any(k.arg == "shell" and isinstance(k.value, ast.Constant) and k.value.value is True
                                       for k in node.keywords) or name == "asyncio.create_subprocess_shell":
            hits.append(("SEC-CMDI", first(0, "args")))
        if name in EXEC_FUNCS:
            hits.append(("SEC-CMDI", merge(*args)))
        if name in SQL_FUNCS or (isinstance(node.func, ast.Attribute) and short in SQL_METHODS):
            hits.append(("SEC-SQLI", first(0, "sql")))
        if name in PATH_FUNCS:
            hits.append(("SEC-PATH", first(0, "file") or first(0, "path")))
        if isinstance(node.func, ast.Attribute) and short in PATH_METHODS and receiver is not None:
            hits.append(("SEC-PATH", receiver))
        root = name.split(".")[0]
        if root in {"requests", "httpx"} and short in HTTP_CLIENT_FUNCS and name.count(".") == 1:
            hits.append(("SEC-SSRF", first(1 if short == "request" else 0, "url")))
        if name in URL_FUNCS:
            hits.append(("SEC-SSRF", first(0, "url")))
        if name in SSTI_FUNCS:
            hits.append(("SEC-SSTI", first(0, "source")))
        if name in XSS_FUNCS:
            hits.append(("SEC-XSS", first(0, "content")))
        if name in REDIRECT_FUNCS:
            hits.append(("SEC-REDIRECT", first(0, "location") or first(0, "url")))
        if name in DESER_FUNCS:
            hits.append(("SEC-DESER", first(0, "data")))
        if name == "yaml.load":
            hits.append(("SEC-DESER", first(0, "stream")))
        if root in {"ldap", "ldap3"} or (isinstance(node.func, ast.Attribute) and short in {"search_s", "search_st", "search_ext_s"}
                                        and any(v.startswith(("ldap", "ldap3")) for v in self.a.aliases.values())):
            if short in {"search_s", "search_st", "search_ext_s"}:
                hits.append(("SEC-LDAPI", first(2, "filterstr")))
            elif short == "search":
                hits.append(("SEC-LDAPI", first(1, "search_filter")))
        for rule_id, taint in hits:
            if taint is None or taint.blocked(rule_id):
                continue
            sink = self.a.step("sink", node, f"llega a {name or short}()")
            if self.mode == "summary":
                for param in taint.params:
                    self.summary.sinks.append((param, rule_id, sink, taint.steps))
                continue
            if not taint.steps or not self._first_report(rule_id, taint):
                continue
            self.a.add(rule_id, node, self._message(rule_id, name or short), trace=taint.steps + (sink,),
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

    def _check_html_return(self, node, value: Taint):
        """Flask/FastAPI view returning a string that mixes HTML markup with request data."""
        if value.blocked("SEC-XSS"):
            return
        html_literal = any(isinstance(n, ast.Constant) and isinstance(n.value, str) and re.search(r"<\s*[a-zA-Z/]", n.value)
                           for n in ast.walk(node.value))
        if html_literal:
            self.a.add("SEC-XSS", node, "La vista devuelve HTML construido con datos de la petición sin codificar.",
                       trace=value.steps + (self.a.step("sink", node, "respuesta HTML de la vista"),),
                       confidence=value.confidence)

    @staticmethod
    def _message(rule_id: str, sink: str) -> str:
        texts = {
            "SEC-SQLI": "Datos de la petición llegan a una consulta SQL sin parametrizar",
            "SEC-CMDI": "Datos de la petición llegan a un comando del sistema",
            "SEC-CODEI": "Datos de la petición se evalúan como código",
            "SEC-PATH": "Datos de la petición controlan una ruta de fichero",
            "SEC-SSRF": "Datos de la petición controlan la URL de una petición saliente",
            "SEC-SSTI": "Datos de la petición se usan como plantilla",
            "SEC-XSS": "Datos de la petición se devuelven como HTML sin codificar",
            "SEC-REDIRECT": "Datos de la petición controlan el destino de una redirección",
            "SEC-DESER": "Datos de la petición se deserializan con un formato inseguro",
            "SEC-LDAPI": "Datos de la petición forman un filtro LDAP",
        }
        return f"{texts.get(rule_id, 'Flujo de datos no confiables')} ({sink})."


class PatternChecks(ast.NodeVisitor):
    """Structural checks that do not need data flow."""

    def __init__(self, analyzer: PythonAnalyzer, tree):
        self.a = analyzer
        self.tree = tree
        self.settings_file = bool(re.search(r"(^|/)settings[^/]*\.py$|(^|/)config[^/]*\.py$", analyzer.rel))

    def run(self):
        self.visit(self.tree)

    # exceptions ----------------------------------------------------------------
    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        body = [s for s in node.body if not (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant))]
        empty = not body or all(isinstance(s, (ast.Pass, ast.Continue)) or
                                (isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)) for s in body)
        if empty:
            caught = ast.unparse(node.type) if node.type is not None else "todas las excepciones"
            if re.fullmatch(r"\(?\s*(ImportError|ModuleNotFoundError)(\s*,\s*(ImportError|ModuleNotFoundError))*\s*\)?", caught):
                self.generic_visit(node)
                return  # optional-dependency idiom
            broad = node.type is None or re.search(r"\b(Exception|BaseException)\b", caught)
            self.a.add("BUG-EMPTY-CATCH", node, f"Se captura {caught} y se descarta sin registrar ni propagar.",
                       severity=None if broad else "low")
        elif node.type is None and not any(isinstance(n, ast.Raise) for n in ast.walk(node)):
            self.a.add("BUG-BROAD-CATCH", node, "except: sin tipo captura también KeyboardInterrupt y SystemExit.")
        self.generic_visit(node)

    # comparisons / defaults ----------------------------------------------------
    def visit_Compare(self, node: ast.Compare):
        for op, right in zip(node.ops, node.comparators):
            for side in (node.left, right):
                if isinstance(op, (ast.Is, ast.IsNot)) and isinstance(side, ast.Constant) and \
                        isinstance(side.value, (str, bytes, int, float)) and not isinstance(side.value, bool):
                    self.a.add("BUG-IS-LITERAL", node, f"'{ast.unparse(node)}' compara identidad con un literal.")
        self.generic_visit(node)

    def _defaults(self, node):
        for default in [*node.args.defaults, *[d for d in node.args.kw_defaults if d is not None]]:
            mutable = isinstance(default, (ast.List, ast.Dict, ast.Set)) or (
                isinstance(default, ast.Call) and isinstance(default.func, ast.Name) and default.func.id in {"list", "dict", "set"})
            if mutable:
                self.a.add("BUG-MUTABLE-DEFAULT", default, f"La función '{node.name}' usa un valor por defecto mutable.")

    def visit_FunctionDef(self, node):
        self._defaults(node)
        for dec in node.decorator_list:
            name = self.a.qualname(dec.func if isinstance(dec, ast.Call) else dec) or ""
            if name.endswith("csrf_exempt"):
                self.a.add("SEC-CSRF", dec, f"La vista '{node.name}' desactiva la protección CSRF.")
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    # calls ----------------------------------------------------------------------
    def visit_Call(self, node: ast.Call):
        name = self.a.qualname(node.func) or ""
        kw = {k.arg: k.value for k in node.keywords}
        short = name.split(".")[-1]
        if name in {"hashlib.md5", "hashlib.sha1"} or (name == "hashlib.new" and node.args and isinstance(node.args[0], ast.Constant)
                                                        and str(node.args[0].value).lower() in {"md5", "sha1"}):
            if not (isinstance(kw.get("usedforsecurity"), ast.Constant) and kw["usedforsecurity"].value is False):
                context = self._context_name(node)
                severity = "medium" if re.search(r"(?i)passw|pwd|secret|token|sign", context) else None
                self.a.add("SEC-WEAKHASH", node, f"Se usa {short.upper() if short != 'new' else 'MD5/SHA-1'} ({context or 'hash'}).",
                           severity=severity, confidence="medium")
        if name.split(".")[0] in {"requests", "httpx"} and isinstance(kw.get("verify"), ast.Constant) and kw["verify"].value is False:
            self.a.add("SEC-TLS", node, "La petición HTTPS se hace con verify=False.")
        if name in {"ssl._create_unverified_context", "urllib3.disable_warnings"} and name.startswith("ssl"):
            self.a.add("SEC-TLS", node, "Se crea un contexto SSL que no valida certificados.")
        if name == "jwt.decode":
            options = kw.get("options")
            unsafe = isinstance(kw.get("verify"), ast.Constant) and kw["verify"].value is False
            if isinstance(options, ast.Dict):
                for key, value in zip(options.keys, options.values):
                    if isinstance(key, ast.Constant) and key.value == "verify_signature" and \
                            isinstance(value, ast.Constant) and value.value is False:
                        unsafe = True
            algorithms = kw.get("algorithms")
            if algorithms is not None and "none" in ast.unparse(algorithms).lower():
                unsafe = True
            if unsafe:
                self.a.add("SEC-JWT", node, "jwt.decode se llama sin verificar la firma.")
        if name == "yaml.load":
            loader = kw.get("Loader") or (node.args[1] if len(node.args) > 1 else None)
            loader_name = ast.unparse(loader) if loader is not None else ""
            if not re.search(r"Safe|CSafe|BaseLoader", loader_name):
                self.a.add("SEC-UNSAFE-DESER-API", node, "yaml.load sin SafeLoader puede construir objetos arbitrarios.")
        if name in {"yaml.unsafe_load", "yaml.unsafe_load_all"}:
            self.a.add("SEC-UNSAFE-DESER-API", node, "yaml.unsafe_load puede construir objetos arbitrarios.")
        if short == "run" and isinstance(kw.get("debug"), ast.Constant) and kw["debug"].value is True and \
                isinstance(node.func, ast.Attribute):
            self.a.add("SEC-DEBUG", node, "La aplicación se arranca con debug=True (consola interactiva expuesta).")
        if name.endswith("CORS") and name.startswith("flask_cors"):
            text = ast.unparse(node)
            if "'*'" in text or '"*"' in text or len(node.args) == 1 and not node.keywords:
                self.a.add("SEC-CORS", node, "CORS permite cualquier origen.")
        if name.split(".")[0] == "random" and short in {"random", "randint", "choice", "choices", "getrandbits", "randrange", "sample"}:
            context = self._context_name(node)
            if SECURITY_RANDOM_NAME.search(context):
                self.a.add("SEC-WEAKRANDOM", node, f"'{context}' se genera con random (predecible); usar secrets.")
        for keyword in node.keywords:
            if keyword.arg and isinstance(keyword.value, ast.Constant) and isinstance(keyword.value.value, str):
                self._secret(keyword.arg, keyword.value.value, keyword.value)
        self.generic_visit(node)

    def _context_name(self, node) -> str:
        """Name of the variable or function receiving/containing a value."""
        for parent in ast.walk(self.tree):
            if isinstance(parent, (ast.Assign, ast.AnnAssign)) and any(n is node for n in ast.walk(parent.value or parent)):
                targets = parent.targets if isinstance(parent, ast.Assign) else [parent.target]
                return " ".join(ast.unparse(t) for t in targets)
            if isinstance(parent, ast.Return) and parent.value is not None and any(n is node for n in ast.walk(parent.value)):
                for fn in ast.walk(self.tree):
                    if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and any(n is parent for n in ast.walk(fn)):
                        return fn.name
        return ""

    # assignments: secrets and settings ---------------------------------------------
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            name = ast.unparse(target)
            self._assignment(name, node.value, node)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if node.value is not None:
            self._assignment(ast.unparse(node.target), node.value, node)
        self.generic_visit(node)

    def visit_Dict(self, node: ast.Dict):
        for key, value in zip(node.keys, node.values):
            if isinstance(key, ast.Constant) and isinstance(key.value, str) and isinstance(value, ast.Constant) \
                    and isinstance(value.value, str):
                self._secret(key.value, value.value, value)
        self.generic_visit(node)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, str):
            label = find_token_secrets(node.value)
            if label:
                self.a.add("SEC-SECRET", node, f"El código contiene un/a {label}.",
                           snippet=redact(self.a.code(node), node.value), confidence="high")

    def _assignment(self, name: str, value, node):
        short = name.split(".")[-1]
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            self._secret(short, value.value, node)
        if self.settings_file or short.isupper():
            if short == "DEBUG" and isinstance(value, ast.Constant) and value.value is True and self.settings_file:
                self.a.add("SEC-DEBUG", node, "DEBUG = True en la configuración.")
            if short == "ALLOWED_HOSTS" and "'*'" in ast.unparse(value):
                self.a.add("SEC-DEBUG", node, "ALLOWED_HOSTS acepta cualquier host.", severity="low")
            if short in {"CORS_ALLOW_ALL_ORIGINS", "CORS_ORIGIN_ALLOW_ALL"} and isinstance(value, ast.Constant) and value.value is True:
                self.a.add("SEC-CORS", node, f"{short} = True permite cualquier origen.")
            if short == "WTF_CSRF_ENABLED" and isinstance(value, ast.Constant) and value.value is False:
                self.a.add("SEC-CSRF", node, "WTF_CSRF_ENABLED = False desactiva la protección CSRF.")
        if short == "debug" and isinstance(value, ast.Constant) and value.value is True and name.endswith(".debug"):
            self.a.add("SEC-DEBUG", node, f"{name} = True activa el modo depuración.")

    def _secret(self, name: str, value: str, node):
        if looks_like_secret(name, value):
            self.a.add("SEC-SECRET", node, f"'{name}' tiene un valor literal que parece una credencial.",
                       snippet=redact(self.a.code(node), value), confidence="medium")


class PythonProject:
    """All Python modules of a repository analysed together (cross-module summaries)."""

    def __init__(self):
        self.analyzers: list[PythonAnalyzer] = []
        self._by_module: dict[str, list[PythonAnalyzer]] = {}

    def add(self, source: str, rel: str, is_test: bool = False):
        analyzer = PythonAnalyzer(source, rel, is_test, project=self)
        self.analyzers.append(analyzer)
        if analyzer.parse():
            dotted = rel.removesuffix(".py").replace("/", ".").removesuffix(".__init__")
            parts = dotted.split(".")
            for i in range(len(parts)):  # every dotted suffix: "a.b.c", "b.c", "c"
                self._by_module.setdefault(".".join(parts[i:]), []).append(analyzer)

    def module(self, name: str, near: str = "") -> PythonAnalyzer | None:
        """Resolve an imported module, preferring the one closest to the importing file."""
        candidates = self._by_module.get(name) or self._by_module.get(name.rsplit(".", 1)[-1]) or []
        if len(candidates) <= 1:
            return candidates[0] if candidates else None
        here = near.rsplit("/", 1)[0].split("/") if "/" in near else []

        def shared(candidate):
            there = candidate.rel.split("/")[:-1]
            common = 0
            for a, b in zip(here, there):
                if a != b:
                    break
                common += 1
            return (common, -len(there))
        return max(candidates, key=shared)

    def run(self) -> tuple[list[SecurityFinding], list[dict]]:
        parsed = [a for a in self.analyzers if a.tree is not None]
        for _ in range(3):  # view -> service -> data-access chains across modules
            for analyzer in parsed:
                try:
                    analyzer.summarise()
                except RecursionError:
                    analyzer.error = "RecursionError: código demasiado anidado; se omite su resumen"
        findings = []
        for analyzer in parsed:
            try:
                findings.extend(analyzer.report())
            except RecursionError:
                analyzer.error = "RecursionError: código demasiado anidado; análisis parcial"
                findings.extend(analyzer.findings)
        errors = [{"file": a.rel, "error": a.error} for a in self.analyzers if a.error]
        return findings, errors


def analyze_python(source: str, rel: str, is_test: bool = False) -> tuple[list[SecurityFinding], str | None]:
    analyzer = PythonAnalyzer(source, rel, is_test)
    findings = analyzer.run()
    return findings, analyzer.error
