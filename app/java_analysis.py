from pathlib import Path
import re

SKIP = {".git", ".venv", "venv", "node_modules", "target", "build", "dist", "vendor"}
ANNOTATIONS = re.compile(r'@(GetMapping|PostMapping|PutMapping|PatchMapping|DeleteMapping|RequestMapping|KafkaListener|KafkaHandler|Scheduled)\s*(?:\(([^)]*)\))?', re.S)
CLASS = re.compile(r'\b(class|interface|enum|record)\s+([A-Za-z_$][\w$]*)')
METHOD = re.compile(r'(?m)^\s*(?:(?:public|protected|private|static|final|synchronized|abstract|native|default)\s+)+[\w<>,.?\[\] @]+\s+([A-Za-z_$][\w$]*)\s*\(([^;{}]*)\)\s*(?:throws\s+[\w., ]+)?\s*\{')
INJECT = re.compile(r'@(Autowired|Inject|Resource)\s+(?:private|protected|public)?\s*([\w<>?,. ]+)\s+(\w+)|(?:private|protected)\s+final\s+([\w<>?,. ]+)\s+(\w+)\s*;')
SQL_WORD = re.compile(r'(?i)\b(SELECT|INSERT\s+INTO|UPDATE|DELETE\s+FROM|MERGE\s+INTO|CREATE\s+TABLE|ALTER\s+TABLE)\b')

def _line(text, offset):
    return text.count("\n", 0, offset) + 1

def analyze_java_repository(root: Path) -> dict:
    out = {"classes": [], "methods": [], "call_references": [], "injections": [],
           "spring_endpoints": [], "kafka_listeners": [], "kafka_producers": [],
           "sql_statements": [], "avro_contracts": [], "configuration_keys": [],
           "limitations": [
             "Parser Java heurístico: no sustituye al compilador ni resuelve sobrecargas, genéricos o dispatch dinámico.",
             "Las llamadas se detectan por nombre y pueden incluir falsos positivos; las dependencias externas no se expanden.",
             "Los topics y contratos pueden estar definidos en configuración o librerías externas no incluidas."
           ]}
    files = 0
    for p in root.rglob("*"):
        if p.is_symlink() or not p.is_file() or any(x in SKIP for x in p.relative_to(root).parts):
            continue
        rel = p.relative_to(root).as_posix()
        try:
            if p.stat().st_size > 1_000_000: continue
            source = p.read_text(encoding="utf-8", errors="replace")
        except OSError: continue
        files += 1
        if p.suffix.lower() == ".java":
            for m in CLASS.finditer(source):
                out["classes"].append({"name":m.group(2),"kind":m.group(1),"file":rel,"line":_line(source,m.start())})
            class_positions = [(m.start(), m.group(2)) for m in CLASS.finditer(source)]
            for m in METHOD.finditer(source):
                name, args = m.group(1), m.group(2)
                enclosing_class = next((class_name for offset, class_name in reversed(class_positions) if offset < m.start()), None)
                start, depth, i, quote = m.end(), 1, m.end(), None
                while i < len(source) and depth:
                    ch = source[i]
                    if quote:
                        if ch == quote and (i == 0 or source[i-1] != "\\"): quote = None
                    elif ch in "\"'": quote = ch
                    elif ch == "{": depth += 1
                    elif ch == "}": depth -= 1
                    i += 1
                body = source[start:i-1] if depth == 0 else source[start:min(len(source),start+6000)]
                line = _line(source,m.start())
                calls = sorted(set(re.findall(r'\b([A-Za-z_$][\w$]*)\s*\(',body)))
                calls = [c for c in calls if c not in {name,"if","for","while","switch","catch","return","new","synchronized"}]
                branches = [{"kind":x.group(1),"line":_line(source,start+x.start())} for x in re.finditer(r'\b(if|else\s+if|switch|case|throw|try|catch)\b',body)]
                effects = sorted(set(x.group(1).lower().replace(" ","_") for x in re.finditer(r'\b(insert\s+into|update|delete\s+from|save|saveAll|deleteById|publish|send|produce|write|commit)\b',body,re.I)))
                out["methods"].append({"name":name,"class_name":enclosing_class,"parameters":args.strip(),"file":rel,"line":line,"end_line":_line(source,i),"calls":calls[:100],"branches_and_errors":branches[:100],"possible_effects":effects,"confidence":"inferred"})
                for callee in calls: out["call_references"].append({"caller":name,"callee":callee,"file":rel,"line":line,"confidence":"inferred"})
            for m in ANNOTATIONS.finditer(source):
                ann,args=m.group(1),m.group(2) or ""
                item={"annotation":ann,"arguments":args.strip()[:500],"file":rel,"line":_line(source,m.start())}
                (out["spring_endpoints"] if ann.endswith("Mapping") else out["kafka_listeners"] if ann=="KafkaListener" else []).append(item) if ann.endswith("Mapping") or ann=="KafkaListener" else None
            for m in INJECT.finditer(source):
                out["injections"].append({"type":(m.group(2) or m.group(4) or "").strip(),"field":m.group(3) or m.group(5),"file":rel,"line":_line(source,m.start())})
            for m in re.finditer(r'(?i)(?:KafkaTemplate|StreamBridge|ProducerRecord)[^;\n]{0,300}',source):
                out["kafka_producers"].append({"expression":m.group(0).strip()[:300],"file":rel,"line":_line(source,m.start())})
        if p.suffix.lower() in {".sql",".java",".xml",".yaml",".yml",".properties",".avsc",".avdl",".proto"}:
            for m in SQL_WORD.finditer(source):
                stmt=source[m.start():min(len(source),m.start()+700)].split(";")[0]
                out["sql_statements"].append({"operation":m.group(1).upper(),"file":rel,"line":_line(source,m.start()),"excerpt":stmt[:700]})
            for m in re.finditer(r'(?i)(?:topic|topics|dataTopic|outcomingTopic)\s*[=:]\s*["\']([^"\']+)["\']',source):
                out["configuration_keys"].append({"kind":"topic_candidate","value":m.group(1),"file":rel,"line":_line(source,m.start())})
            if p.suffix.lower() in {".avsc",".avdl",".proto"}:
                for m in re.finditer(r'\b(?:record|message|enum|protocol)\s+([A-Za-z_]\w*)',source):
                    out["avro_contracts"].append({"name":m.group(1),"file":rel,"line":_line(source,m.start()),"format":p.suffix.lower()})
    for key in ("classes","methods","call_references","injections","spring_endpoints","kafka_listeners","kafka_producers","sql_statements","avro_contracts","configuration_keys"):
        out[key]=out[key][:10000]
    out["summary"]={"files_scanned":files,**{k:len(out[k]) for k in ("classes","methods","call_references","spring_endpoints","kafka_listeners","kafka_producers","sql_statements","avro_contracts")}}
    return out
