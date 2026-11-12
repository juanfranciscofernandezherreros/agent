import httpx

def canonical(value):
    if isinstance(value, dict):
        return {k: canonical(v) for k,v in sorted(value.items())}
    if isinstance(value, list):
        return [canonical(v) for v in value]
    return value

async def compare_services(original_url, reconstructed_url, cases, timeout):
    results = []
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        for i, case in enumerate(cases, 1):
            method = str(case.get("method","GET")).upper()
            path = str(case.get("path","/"))
            if not path.startswith("/"): path = "/" + path
            kwargs = {"headers":case.get("headers",{}), "params":case.get("params")}
            if "json" in case: kwargs["json"] = case["json"]
            try:
                a = await client.request(method, original_url.rstrip("/") + path, **kwargs)
                b = await client.request(method, reconstructed_url.rstrip("/") + path, **kwargs)
                try: abody = a.json()
                except Exception: abody = a.text
                try: bbody = b.json()
                except Exception: bbody = b.text
                same_status, same_body = a.status_code == b.status_code, canonical(abody) == canonical(bbody)
                ok = same_status and same_body
                results.append({"case":i,"method":method,"path":path,"status":"PASS" if ok else "FAIL",
                    "original_status":a.status_code,"reconstructed_status":b.status_code,
                    "body_equal":same_body,"original_body":abody,"reconstructed_body":bbody})
            except Exception as exc:
                results.append({"case":i,"method":method,"path":path,"status":"BLOCKED","error":str(exc)})
    passed = sum(x["status"]=="PASS" for x in results)
    failed = sum(x["status"]=="FAIL" for x in results)
    blocked = sum(x["status"]=="BLOCKED" for x in results)
    return {"summary":{"total":len(results),"passed":passed,"failed":failed,"blocked":blocked},
      "dimension_status":"VERIFIED" if failed==0 and blocked==0 else "PARTIALLY_VERIFIED",
      "important_limit":"Solo evalúa estos casos HTTP; no prueba equivalencia universal, DB, eventos, integraciones ni rendimiento.",
      "results":results}
