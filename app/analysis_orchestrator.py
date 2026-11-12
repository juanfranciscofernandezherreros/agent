from pathlib import Path
import html, json, re, uuid
from .config import WORKSPACES_DIR
from .engines import clone_repository, analyze_repository
from .deep_analysis import analyze_repository_deep
from .functional_analysis import analyze_functional_behavior
from .java_analysis import analyze_java_repository
from .report_details import java_catalog, write_individual_reports
from .rich_report import build_integral_html
from .quality_analysis import analyze_quality

def slug(s):
    return re.sub(r"[^a-zA-Z0-9_-]+","-",s).strip("-_")[:60] or "service"

def correlate(repositories):
    topics, contracts = {}, {}
    producer_evidence = []
    for repo in repositories:
        ja = repo.get("java_analysis", {})
        service = repo.get("name", "unknown")

        for item in ja.get("configuration_keys", []):
            topic = item.get("value")
            if topic:
                topics.setdefault(topic, []).append({
                    "repository": service, "role": "configuration",
                    "file": item.get("file"), "line": item.get("line"),
                    "evidence": item.get("value"), "kind": item.get("kind")
                })

        for item in ja.get("kafka_listeners", []):
            args = item.get("arguments", "")
            literals = re.findall(r'["\']([^"\']+)["\']', args)
            for topic in literals:
                topics.setdefault(topic, []).append({
                    "repository": service, "role": "consumer_candidate",
                    "file": item.get("file"), "line": item.get("line"),
                    "evidence": args
                })

        for item in ja.get("kafka_producers", []):
            expression = item.get("expression", "")
            producer_evidence.append({
                "repository": service, "file": item.get("file"),
                "line": item.get("line"), "expression": expression
            })
            literals = re.findall(r'["\']([^"\']+)["\']', expression)
            for topic in literals:
                if topic and len(topic) < 250:
                    topics.setdefault(topic, []).append({
                        "repository": service, "role": "producer_candidate",
                        "file": item.get("file"), "line": item.get("line"),
                        "evidence": expression
                    })

        for item in ja.get("avro_contracts", []):
            contract = item.get("name")
            if contract:
                contracts.setdefault(contract, []).append({
                    "repository": service, "file": item.get("file"),
                    "line": item.get("line"), "format": item.get("format")
                })

    topic_candidates = []
    for topic, evidence in sorted(topics.items()):
        unique = {}
        for item in evidence:
            key = (item.get("repository"), item.get("role"), item.get("file"), item.get("line"))
            unique[key] = item
        evidence = list(unique.values())
        services = sorted({item["repository"] for item in evidence})
        roles = sorted({item.get("role", "unknown") for item in evidence})
        topic_candidates.append({
            "topic": topic, "evidence": evidence, "repositories": services,
            "roles_detected": roles,
            "cross_service_candidate": len(services) > 1,
            "producer_and_consumer_candidates": "producer_candidate" in roles and "consumer_candidate" in roles
        })

    shared_contracts = []
    for contract, evidence in sorted(contracts.items()):
        services = sorted({item["repository"] for item in evidence})
        shared_contracts.append({
            "contract": contract, "evidence": evidence, "repositories": services,
            "cross_service_candidate": len(services) > 1
        })

    return {
        "topic_candidates": topic_candidates,
        "shared_contract_candidates": shared_contracts,
        "producer_candidates": producer_evidence,
        "limitations": [
            "La correlación de topics combina valores literales de configuración, anotaciones de consumidores y expresiones de productores; las expresiones dinámicas pueden no resolverse.",
            "Una coincidencia de topic y la presencia de productor/consumidor candidatos no demuestra que estén conectados en el despliegue ni que compartan el mismo tipo de payload.",
            "Los topics definidos mediante placeholders, perfiles externos, constantes indirectas o configuración remota pueden no detectarse.",
            "Los contratos se agrupan por nombre; no se comparan namespaces, campos, tipos, defaults, nullability ni reglas de compatibilidad.",
            "No se deducen garantías de entrega, orden, atomicidad, idempotencia ni semántica de negocio solo por compartir un topic."
        ]
    }

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
          "- Puntuación estática: "+str(r.get("quality_analysis",{}).get("score","N/D"))+"/100 ("+str(r.get("quality_analysis",{}).get("rating","sin datos"))+")",
          "- Candidatos de bug: "+str(r.get("quality_analysis",{}).get("summary",{}).get("bug_candidates",0)),
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

def run_group_analysis(group_id,name,repositories,clone_token=None,clone_host=None):
    folder=WORKSPACES_DIR/group_id; folder.mkdir(parents=True,exist_ok=True)
    results,failures=[],[]
    for item in repositories:
        try:
            member_id=str(uuid.uuid4()); source=clone_repository(member_id,item["git_url"],auth_token=clone_token,auth_host=clone_host)
            inv=analyze_repository(source); deep=analyze_repository_deep(source,inv)
            functional=analyze_functional_behavior(source); java=analyze_java_repository(source)
            quality=analyze_quality(source,deep,functional,java)
            dest=folder/"repositories"/slug(item["name"]); dest.mkdir(parents=True,exist_ok=True)
            member={"project_name":item["name"],"inventory":inv,"deep_analysis":deep,
              "functional_analysis":functional,"java_analysis":java,"quality_analysis":quality,
              "completion_status":"STATIC_ANALYSIS_COMPLETED","runtime_validation":"NOT_PERFORMED"}
            (dest/"analysis.json").write_text(json.dumps(member,indent=2,ensure_ascii=False),encoding="utf-8")
            write_individual_reports(dest,item["name"],inv,deep,functional,java,member)
            results.append({"name":item["name"],"inventory":inv,"deep_analysis":deep,
              "functional_analysis":functional,"java_analysis":java,"quality_analysis":quality,"artifact_dir":str(dest.relative_to(folder))})
        except Exception as exc: failures.append({"repository":item["name"],"error":str(exc)})
    if not results: raise RuntimeError("No se pudo analizar ningún repositorio: "+json.dumps(failures,ensure_ascii=False))
    result={"analysis_version":"5.0","group_name":name,"repositories":results,
      "integration_analysis":correlate(results),"failures":failures,
      "completion_status":"STATIC_ANALYSIS_COMPLETED" if not failures else "PARTIAL_ANALYSIS_COMPLETED",
      "runtime_validation":"NOT_PERFORMED"}
    (folder/"analysis.json").write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding="utf-8")
    (folder/"analysis.md").write_text(markdown(name,result) + "\n" + java_catalog(result),encoding="utf-8")
    (folder/"analysis.html").write_text(build_integral_html(name,result),encoding="utf-8")
    return result
