# Reasoning — Linha de raciocínio (da exploração ao resultado central)

> **Arco.** Exploramos inicialmente os dois datasets do desafio (GitSkills e SpecMine) e escopamos o estudo em **SpecMine** — a pergunta de rastreabilidade (spec→código, tarefas marcadas como concluídas mas sem código no commit) era a mais nova e apoiada pelo dado; o GitSkills ficou fora do escopo. Migramos do sample para o dataset completo e vimos que 10,3% das tasks concluídas têm código ausente no commit-âncora. Classificando essas referências, mostramos que 91% são arquivos reais (não ruído de path), que 84% são genuinamente ausentes (54% nunca escritos + 30% escritos-e-removidos), que a composição inverte com a maturidade, e que repositórios com requisitos de acessibilidade têm sistematicamente mais "nunca implementado".

---

## M0 — Sample stats (SpecMine)

1. **Pergunta:** como é o dado do SpecMine (sample)?
2. **Dado de origem:** SpecMine sample (v1.1): `spec_content_features.n_lines`, `spec_files.spec_role`.
3. **Código/critério:** `m0_sample_stats.py` — média/mediana/skew + Shapiro-Wilk (subsample de 5.000); % de specs com `spec_role='archived'`.
4. **Resultado:** `n_lines` média 90,8, mediana 56, skew 9,1, Shapiro p≈0; 51,5% das specs são `archived`.
5. **Decisão + alternativas:** usar **testes não-paramétricos** porque o dado é fortemente assimétrico e não-normal — rejeitei assumir normalidade.
6. **Significado:** o dado é *heavy-tailed*; dá o contexto e justifica as escolhas estatísticas de toda a análise.
7. **Ligação:** mostrou que precisávamos escolher **uma** pergunta específica — e ver se o sample era representativo (M1).

---

## M1 — Sample vs Full: o sample é representativo?

1. **Pergunta:** o sample difere muito do dataset completo?
2. **Dado:** SpecMine sample (v1.1) vs full (v1.0): `spec_files`, `openspec_code_refs`, `spec_links`, `pull_requests`.
3. **Código/critério:** `m1_sample_full.py` — contagem de linhas por tabela.
4. **Resultado:** sample 28.583 specs = 6,1% dos 470.795; refs 7,0%; a camada PR é 5.335 (89% dos 5.992).
5. **Decisão + alternativas:** migrar para o **full** — o sample é uma fatia star-curated pequena demais para o censo.
6. **Significado:** o fenômeno precisa ser medido no full, não no sample.
7. **Ligação:** levou à migração do sample para o **dataset completo** (M3).

---

## M2 — O pivô de pesquisa

1. **Pergunta:** qual é a pergunta real que o dado sustenta?
2. **Dado de origem:** (não é dado — é decisão) leitura do call do desafio + os dois preprints.
3. **Código/critério:** —.
4. **Resultado:** a **rastreabilidade (Q2)** vira o núcleo; a **acessibilidade (Q1)** vira secundária; a **revisão de PRs (Q3)** é rebaixada a ameaça; **confiança** vira motivação, nunca conclusão causal.
5. **Decisão + alternativas:** Q2 como central porque o SpecMine foi *desenhado* para isso (`openspec_code_refs` já traz `task_done` + `exists_at_anchor`); Q3 descartada porque todos os PRs do dataset têm `is_merged=1` (os rejeitados/fechados, onde a desconfiança apareceria, estão invisíveis).
6. **Significado:** esta decisão molda todos os passos seguintes.
7. **Ligação:** definiu a pergunta central (Q2), medida no full (M3).

## M3 — Censo full: o fenômeno existe em escala

1. **Pergunta:** quantos são "done but missing"?
2. **Dado:** `openspec_code_refs` com filtro `task_done=1 AND anchor_sha IS NOT NULL AND exists_at_anchor=0`.
3. **Código:** SQL via DuckDB (`SELECT ... GROUP BY`); gráfico `chart_census.png`.
4. **Resultado:** **34.227** referências = **10,3%** das 332.168 concluídas com âncora resolvida.
5. **Decisão:** denominador = refs concluídas **com** `anchor_sha`; os `NULL` (âncora ausente) são reportados à parte.
6. **Significado:** o "concluída sem código" não é marginal — é um fenômeno de escala populacional.
7. **Ligação:** antes de classificar, precisávamos entender a coluna `exists_at_anchor` (M4).

---

## M4 — Descoberta: `exists_at_anchor` não é binário

1. **Pergunta:** a coluna é realmente 0/1?
2. **Dado:** `openspec_code_refs`, coluna `exists_at_anchor`.
3. **Código:** SQL `GROUP BY exists_at_anchor`.
4. **Resultado:** `0` (51.979), `1` (361.083), `2` (130, em 5 repos), `NULL` (22.209) — e **`NULL` ⟺ `anchor_sha=NULL`** (correlação perfeita).
5. **Decisão:** documentar como **contribuição de qualidade de dados**; tratar `NULL` separadamente (não somar).
6. **Significado:** a coluna é sub-documentada no `DATA_DICTIONARY`; sem essa descoberta, qualquer headline estaria errado.
7. **Ligação:** permitiu medir o 10,3% com segurança e partir para a taxonomia.

---

## M5 — Taxonomia: arquivo real ou ruído de path?

1. **Pergunta:** dos 34.227, quantos são arquivo de verdade e quantos são ruído?
2. **Dado:** `openspec_code_refs`, filtro do M3, coluna `code_path`.
3. **Código:** `taxonomy.py` → `classify_path()` pela *forma* do path: `relative_ext` (diretório + extensão), `bare_ext` (só nome + extensão), `non_file` (glob / absoluto / sem extensão); gráfico `chart_taxonomy.png`.
4. **Resultado:** `relative_ext` 17.799 · `bare_ext` 13.326 · `non_file` 3.102 → **91% arquivo real, 9% ruído**.
5. **Decisão:** por que **3 níveis**, não 2? Porque `bare_ext` é ambíguo (não diz *onde* o arquivo deveria estar), diferente de `relative_ext` (lookup direto). Guardrail: **nunca somar** `non_file` com o "missing real".
6. **Significado:** o "done but missing" **não é** path malformado — é arquivo que deveria existir e não existe.
7. **Ligação:** os 17.799 `relative_ext` viram a população da Fase 3.

---

## M6 — Acessibilidade: o que as specs pedem?

1. **Pergunta:** quais preocupações de acessibilidade aparecem, e em que proporção são verificáveis?
2. **Dado:** `specs.jsonl` (470.795 specs, texto bruto) + `spec_content_features` (contexto).
3. **Código:** `extract_accessibility.py` — streaming + vocabulário (`WCAG`, `Section 508`, `ADA`, `a11y`, `screen reader`, `alt text`, `ARIA`, `keyboard`, `contrast ratio`, etc.) + regra de **verificável por linha**; gráfico `chart_accessibility.png`.
4. **Resultado:** **97.883** linhas de requisito em 10.717 repos; **27,1% verificáveis**; openspec 37,0% vs docs_embedded 8,9%.
5. **Decisão:** "verificável" é **por linha** (`shall`/`must` ou limiar mensurável), não por spec; `ADA` case-sensitive (evitar a linguagem Ada e o token Cardano); `caption`/`transcript` removidos (falsos-positivos).
6. **Significado:** ferramentas formais (openspec, speckit) produzem requisitos de acessibilidade **muito mais verificáveis**.
7. **Ligação:** alimenta a ponte acessibilidade × implementação (M8).

---

## M7 — Calibração: quanto é normalização de path?

1. **Pergunta:** quanto do "missing" poderia ser só caminho escrito diferente?
2. **Dado:** `openspec_code_refs` com `exists_at_anchor=1` e `resolved_path` preenchido.
3. **Código:** comparação `resolved_path != code_path`.
4. **Resultado:** `relative_ext` resolve em path diferente em **15,2%**; `bare_ext` em 94,8% (mas isso é **tautológico** — nome solto sempre ganha diretório ao resolver).
5. **Decisão:** usar **15,2%** como sinal de renomeação/normalização; **não** citar o 94,8% (seria um erro de interpretação).
6. **Significado:** motiva a camada de renames/temporal da Fase 3.
7. **Ligação:** define o que a Fase 3 precisa recuperar.

## M8 — Fase 3 + Ponte: quantos são de fato "never"?

1. **Pergunta:** dos "done but missing", quantos são *nunca implementados* (vs. renomeados ou implementados depois)?
2. **Dado:** `taxonomy_e0.csv` (17.799 `relative_ext`) + `spec_files` (estrelas/linguagem) + `git clone` dos repos.
3. **Código:** `phase3.py` — `classify_ref()` com 5 buckets, `ALL_BRANCHES=True`, `git log --diff-filter=A` / `--follow`; gráfico `phase3_by_bucket.png` + `chart_bridge.png`.
4. **Resultado:** **never 54,5%** (mediana por repo 66,7%) · deleted_before_anchor 29,5% · created_later 9,2% · renamed 4,1% · other 2,7% · alternative_path 0%. **Inversão por maturidade** (0–9: deleted 46% > never 41%; 10+: never ~57–59%). **Ponte:** never a11y 60,4% vs sem-a11y 41,5%, persistindo em todos os buckets.
5. **Decisão:** amostragem **por repo** (não por ref) **determinística** (`SEED=42` + largest-remainder → mesmo frame = mesmos 152 repos, o sorteio não varia entre execuções); `ALL_BRANCHES=True` (conservador); `git clone` em vez de API (único passo não-determinístico — git é mutável); 5 buckets; reportar **refs e repos** (aninhamento).
6. **Significado:** **84% são genuinamente ausentes** no âncora; em repos sérios é não-implementação, em repos 0-star é churn; acessibilidade é "aspiracional" (escrita mas não shippa).
7. **Ligação:** é o resultado central do paper.

---

## Glossário

| Termo | Definição exata |
|---|---|
| `done but missing` | ref com `task_done=1`, `anchor_sha` não-nulo e `exists_at_anchor=0` |
| `exists_at_anchor` | 0 (ausente), 1 (presente), 2 (ambíguo), NULL (âncora ausente ⟺ `anchor_sha` NULL) |
| `anchor_sha` | commit contra o qual o tree foi resolvido |
| `code_path` | caminho de código citado pela task no `tasks.md` |
| `relative_ext` | caminho relativo com diretório e extensão (`src/foo.ts`) |
| `bare_ext` | só nome + extensão (`foo.ts`), sem diretório |
| `non_file` | glob / absoluto / sem extensão |
| `verifiable` | linha com `shall`/`must` **ou** limiar mensurável (razão, AA/AAA, comparador, número+unidade) |
| `never` | arquivo nunca commitado em nenhuma branch (`ALL_BRANCHES=True`) |
| `deleted_before_anchor` | arquivo escrito e removido antes do âncora |
| `created_later` | arquivo commitado depois do âncora |
| `renamed` | arquivo existe sob outro nome (via `--follow`) |
| `alternative_path` | mesmo basename em outro caminho (0 casos) |
| `other` | âncora ausente no clone (force-push) ou ambíguo (adicionado antes do âncora sem deleção/renomeação detectada) |

## Log de decisões

| Decisão | Alternativa rejeitada | Motivo |
|---|---|---|
| Q2 como núcleo | Q1 ou Q3 como núcleo | SpecMine desenhado para isso |
| Confiança = motivação | confiança = conclusão causal | dado não suporta causalidade |
| Drop Q3 | manter Q3 | `is_merged=1` (viés de sobrevivência) |
| Full SpecMine, não GitSkills | baixar ambos | GitSkills fora do caminho crítico |
| Taxonomia em 3 níveis | 2 níveis | `bare_ext` é ambíguo |
| `ALL_BRANCHES=True` | restrito à default | "never" mais conservador/defensável |
| Amostrar por repo | amostrar por ref | custo é por repo; aninhamento |
| Amostra determinística (`SEED=42`) | amostra aleatória | sorteio reprodutível; só o clone é não-determinístico |
| `git clone` local | GitHub API | sem rate limit; `--follow` p/ rename |
| Verificável por linha | por spec | granularidade correta |
| `%cI` (commit date) | `%aI` (author date) | commits rebasados/squashados |
| Reportar refs **e** repos | só refs | aninhamento distorce proporção |


