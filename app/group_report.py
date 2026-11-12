"""Informe global en Markdown/HTML básico del conjunto analizado."""
import html, json, re

def slug(s):
    return re.sub(r"[^a-zA-Z0-9_-]+","-",s).strip("-_")[:60] or "service"

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
