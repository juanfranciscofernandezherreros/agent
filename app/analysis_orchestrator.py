from pathlib import Path
import html, json, re, uuid
from .config import WORKSPACES_DIR
from .engines import clone_repository, analyze_repository
from .deep_analysis import analyze_repository_deep
from .functional_analysis import analyze_functional_behavior
from .java_analysis import analyze_java_repository

def slug(s):
    return re.sub(r"[^a-zA-Z0-9_-]+","-",s).strip("-_")[:60] or "service"

def correlate(repositories):
    topics, contracts = {}, {}
    for repo in repositories:
        ja=repo["java_analysis"]
        for x in ja["configuration_keys"]:
            topics.setdefault(x["value"],[]).append({"repository":repo["name"],**x})
        for x in ja["avro_contracts"]:
            contracts.setdefault(x["name"],[]).append({"repository":repo["name"],**x})
        for x in ja["kafka_listeners"]:
            for topic in re.findall(r'["\']([^"\']+)["\']',x.get("arguments","")):
                topics.setdefault(topic,[]).append({"repository":repo["name"],"role":"listener",**x})
    return {
      "topic_candidates":[{"topic":k,"evidence":v,"repositories":sorted(set(x["repository"] for x in v)),
       "cross_service_candidate":len(set(x["repository"] for x in v))>1} for k,v in sorted(topics.items())],
      "shared_contract_candidates":[{"contract":k,"evidence":v,"repositories":sorted(set(x["repository"] for x in v)),
       "cross_service_candidate":len(set(x["repository"] for x in v))>1} for k,v in sorted(contracts.items())],
      "limitations":["Coincidir por nombre no demuestra conexión activa ni compatibilidad del payload.",
       "Topics definidos mediante configuración externa o constantes pueden no detectarse.",
       "No se deducen garantías de entrega, orden ni semántica solo por compartir un topic."]}

def markdown(name,a):
    out=["# Análisis integral: "+name,"","> Análisis estático. No se ejecutaron los repositorios ni sus dependencias.","",
      "## Resumen", "- Repositorios: "+str(len(a["repositories"])),
      "- Clases Java: "+str(sum(x["java_analysis"]["summary"]["classes"] for x in a["repositories"])),
      "- Métodos Java: "+str(sum(x["java_analysis"]["summary"]["methods"] for x in a["repositories"])),
      "- Referencias de llamadas: "+str(sum(x["java_analysis"]["summary"]["call_references"] for x in a["repositories"])),"",
      "## Análisis por microservicio"]
    for r in a["repositories"]:
        j=r["java_analysis"]["summary"]; f=r["functional_analysis"].get("summary",{})
        out += ["### "+r["name"],"- Commit: "+str(r["inventory"].get("commit_sha")),
          "- Lenguajes: "+json.dumps(r["inventory"].get("languages",{}),ensure_ascii=False),
          "- Clases/métodos Java: "+str(j["classes"])+"/"+str(j["methods"]),
          "- SQL/listeners Kafka: "+str(j["sql_statements"])+"/"+str(j["kafka_listeners"]),
          "- Operaciones/reglas inferidas: "+str(f.get("operations",0))+"/"+str(f.get("business_rules",0)),
          "- Evidencias individuales: "+r["artifact_dir"],""]
    out += ["## Correlación entre servicios","### Topics"]
    for x in a["integration_analysis"]["topic_candidates"]:
        out.append("- "+x["topic"]+" — "+", ".join(x["repositories"]))
    out += ["","### Contratos"]
    for x in a["integration_analysis"]["shared_contract_candidates"]:
        out.append("- "+x["contract"]+" — "+", ".join(x["repositories"]))
    out += ["","## Limitaciones","- El parser Java es heurístico; no resuelve tipos, overloads ni dispatch dinámico.",
      "- Los contratos compartidos son candidatos, no compatibilidad Avro verificada.",
      "- No se ejecutan tests, SQL, Maven/Gradle, brokers ni servicios.",
      "- La ausencia de detección no demuestra ausencia de funcionalidad."]
    if a["failures"]: out += ["","## Repositorios no analizados"]+["- "+x["repository"]+": "+x["error"] for x in a["failures"]]
    return "\n".join(out)+"\n"

def html_report(name,a):
    title=html.escape(name)
    data=json.dumps(a,ensure_ascii=False).replace("</","<\\/")
    cards="".join("<article><h3>"+html.escape(r["name"])+"</h3><p>Clases Java: "+str(r["java_analysis"]["summary"]["classes"])+" · Métodos: "+str(r["java_analysis"]["summary"]["methods"])+" · SQL: "+str(r["java_analysis"]["summary"]["sql_statements"])+"</p></article>" for r in a["repositories"])
    return """<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>"""+title+"""</title><style>body{font:15px/1.55 system-ui;margin:0;background:#f4f7fb;color:#172033}.hero{padding:36px 5%;background:linear-gradient(120deg,#10254c,#2457c5,#087e8b);color:white}main{max-width:1100px;margin:28px auto;padding:0 18px}article,section{background:white;border:1px solid #dce4ef;border-radius:12px;padding:16px;margin:12px 0}.metrics{display:flex;gap:12px;flex-wrap:wrap}.metric{font-size:1.7rem;color:#2457c5;font-weight:bold}input{padding:10px;width:80%;border:1px solid #ccd5e3;border-radius:8px}pre{white-space:pre-wrap}</style><header class="hero"><h1>"""+title+"""</h1><p>Deep Reverse Engineering & Analysis Orchestrator</p><p>Informe estático; las correlaciones son candidatos con evidencia.</p></header><main><section><h2>Flujo coordinado</h2><p>Repositorios Git → parsers por stack → análisis funcional → correlación de contratos → documentación técnica.</p></section><section><h2>Microservicios</h2>"""+cards+"""</section><section><h2>Topics y contratos compartidos</h2><input id="q" placeholder="Filtrar"><div id="results"></div></section><section><h2>Alcance</h2><p>No ejecuta código ni valida el comportamiento runtime. Las coincidencias de nombres no demuestran compatibilidad de mensajes.</p></section></main><script>const d="""+data+""";const rows=[...d.integration_analysis.topic_candidates.map(x=>({k:"topic",n:x.topic,r:x.repositories})),...d.integration_analysis.shared_contract_candidates.map(x=>({k:"contrato",n:x.contract,r:x.repositories}))];function draw(){let q=document.getElementById("q").value.toLowerCase();document.getElementById("results").innerHTML=rows.filter(x=>(x.n+x.r.join(" ")).toLowerCase().includes(q)).map(x=>"<p><b>"+x.k+": "+x.n+"</b> — "+x.r.join(", ")+"</p>").join("")||"<p>Sin resultados</p>"}document.getElementById("q").addEventListener("input",draw);draw()</script></html>"""

def run_group_analysis(group_id,name,repositories):
    folder=WORKSPACES_DIR/group_id; folder.mkdir(parents=True,exist_ok=True)
    results,failures=[],[]
    for item in repositories:
        try:
            member_id=str(uuid.uuid4()); source=clone_repository(member_id,item["git_url"])
            inv=analyze_repository(source); deep=analyze_repository_deep(source,inv)
            functional=analyze_functional_behavior(source); java=analyze_java_repository(source)
            dest=folder/"repositories"/slug(item["name"]); dest.mkdir(parents=True,exist_ok=True)
            member={"project_name":item["name"],"inventory":inv,"deep_analysis":deep,
              "functional_analysis":functional,"java_analysis":java,
              "completion_status":"STATIC_ANALYSIS_COMPLETED","runtime_validation":"NOT_PERFORMED"}
            (dest/"analysis.json").write_text(json.dumps(member,indent=2,ensure_ascii=False),encoding="utf-8")
            results.append({"name":item["name"],"inventory":inv,"deep_analysis":deep,
              "functional_analysis":functional,"java_analysis":java,"artifact_dir":str(dest.relative_to(folder))})
        except Exception as exc: failures.append({"repository":item["name"],"error":str(exc)})
    if not results: raise RuntimeError("No se pudo analizar ningún repositorio: "+json.dumps(failures,ensure_ascii=False))
    result={"analysis_version":"5.0","group_name":name,"repositories":results,
      "integration_analysis":correlate(results),"failures":failures,
      "completion_status":"STATIC_ANALYSIS_COMPLETED" if not failures else "PARTIAL_ANALYSIS_COMPLETED",
      "runtime_validation":"NOT_PERFORMED"}
    (folder/"analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    (folder/"analysis.md").write_text(markdown(name,result),encoding="utf-8")
    (folder/"analysis.html").write_text(html_report(name,result),encoding="utf-8")
    return result
