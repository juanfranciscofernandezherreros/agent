# Start autonomous MiniAgent development with Claude Code

## 1. Clone or update
```bash
git clone https://github.com/juanfranciscofernandezherreros/agent.git
cd agent
```
If already cloned:
```bash
cd agent
git pull
git status
git branch
```
Confirm you are on the intended branch (normally `main`) and preserve any local changes.

## 2. Start Claude Code
From the repository root:
```bash
claude
```

## 3. Initial instruction
Paste this prompt into Claude Code:

> Continúa con el desarrollo de MiniAgent siguiendo estrictamente las instrucciones de CLAUDE.md y la documentación del proyecto.
>
> Trabaja en modo autónomo sobre el backlog completo.
>
> - Lee las instrucciones, el SDD, los planes de implementación de las tareas y el plan de ejecución.
> - Comienza por la primera tarea elegible según las prioridades y dependencias.
> - Implementa, ejecuta pruebas, revisa los cambios y actualiza la documentación y el tracker.
> - Cumple la estrategia de eficiencia de tokens, evitando exploraciones y lecturas redundantes.
> - No te detengas para pedirme aprobación en decisiones técnicas rutinarias.
> - Continúa automáticamente con la siguiente tarea elegible después de cada checkpoint.
> - No marques tareas como completadas sin validación real.
> - No ejecutes código de los repositorios que MiniAgent analice ni modifiques esos repositorios.
> - Mantén los cambios pequeños, seguros y revisables.
> - Si una tarea está bloqueada, documenta el motivo y continúa con tareas independientes.
>
> Empieza ahora. No te limites a elaborar un plan: ejecuta el trabajo.

## 4. Work loop expected
Claude should repeatedly:
1. Select the highest-priority eligible backlog task with dependencies satisfied.
2. Read that task's plan and mapped SDD requirements; inspect only relevant code and tests.
3. Implement a small cohesive change.
4. Run focused tests, expand validation as needed, review the diff and safety.
5. Update task status/checkpoint with real evidence.
6. Continue immediately to the next eligible task without waiting for routine approval.

## 5. Resume after a session ends
Open Claude Code again from the repository root:
```bash
claude
```
Then send:
> Continúa autónomamente con la siguiente tarea elegible del backlog. Revisa el checkpoint para no repetir trabajo y sigue hasta el siguiente límite real de sesión.

Claude should use the execution tracker to resume and avoid redoing completed work.

## Important
Do not ask Claude to implement the entire backlog in one giant patch. It should work task-by-task with tests and checkpoints. Checkpoints are progress summaries, not approval gates. Human input is needed only for genuine blockers, permissions/credentials, irreversible actions, or material scope decisions.
