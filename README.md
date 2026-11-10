# mule-copilot-starter

Набор инструкций, агентов и скиллов для **GitHub Copilot** (VS Code agent mode и Copilot CLI) под Mule 4 воркспейсы. Переписан с нуля по мотивам Claude-харнесса Ceer: тот же пайплайн (анализ → реализация → независимое ревью), но без привязки к конкретному воркспейсу, без дублей и с упором на экономию токенов.

Главная фича — **`/mule-init`**: агент измеряет стиль кода, который команда писала руками (до появления агентов), и генерирует из него `house-style-*.instructions.md`. После этого всё, что пишет агент, должно выглядеть как код команды: отступы, раскладка атрибутов, имена flow и `doc:name`, шапки DWL, ключи конфигов, имена тестов, язык текстов и стиль коммитов.

---

## Что внутри

```
template/
├── AGENTS.md                          # ядро: приоритеты, режим ответа, токен-бюджет, hard rules (~1.4K токенов)
└── .github/
    ├── copilot-instructions.md        # контракт для /init (блок mule-starter), остальное — на /init
    ├── instructions/                  # path-scoped дефолты (грузятся только для подходящих файлов)
    │   ├── mule-flows.instructions.md      **/src/main/mule/**/*.xml
    │   ├── dataweave.instructions.md       **/*.dwl
    │   ├── munit.instructions.md           **/src/test/**
    │   ├── mule-config.instructions.md     yaml/properties/pom.xml
    │   └── terraform.instructions.md       *.tf / *.tfvars
    │   (+ house-style-*.instructions.md — генерирует /mule-init)
    ├── agents/                        # mule-conductor, mule-analyzer, mule-implementer, mule-bugfixer, mule-reviewer, mule-architect
    ├── prompts/                       # /mule-init, /mule-go, /mule-review (VS Code)
    ├── skills/                        # 21 skill, грузятся по требованию (в контексте всегда только описания, ~1.3K токенов)
    │   ├── caveman/                   # краткий режим ответов (по умолчанию ВКЛ)
    │   ├── mule-init/                 # калибровка стиля + scripts/profile_workspace.py
    │   ├── mule-ruleset/  mule-error-strategy/  mule-reuse/  mule-dataweave/  mule-munit/
    │   ├── mule-oas-contract/  mule-config-matrix/  mule-quality-gate/  verify-before-done/
    │   ├── systematic-debugging/  integration-architecture/  premortem/  git-task-branch/
    │   ├── mule-security-scan/  mule-dwl-mutation/  mule-new-project/  mule-live-test/
    │   └── anypoint-platform/  terraform-gate/
    └── mule-starter/                  # состояние: profile.md, rulesets/, memory/lessons.md, log.md, installed-at
install.sh
```

---

## Требования

- **VS Code** с GitHub Copilot (Chat в режиме *Agent*). Agent Skills и custom agents есть в актуальных версиях (1.108+). Если в `/`-меню нет скиллов, проверь, что включена настройка `chat.useAgentSkills`.
- и/или **Copilot CLI** (`copilot`). Он читает те же `AGENTS.md`, `.github/instructions`, `.github/agents`, `.github/skills`.
- `python3` и `git` (для `install.sh`, сканеров и `/mule-init`).
- Для Mule-пайплайна: `mvn`, JDK для Mule, `xmllint`. Опционально: `semgrep`, `tflint`, `trivy`, `checkov`, `anypoint-cli-v4`, `jq`.

---

## Установка

### Вариант 1. В воркспейс (рекомендуется)

```bash
cd ~/mule-copilot-starter
./install.sh ~/Ceer --dry-run   # посмотреть, что будет сделано
./install.sh ~/Ceer
```

Что делает скрипт:
- копирует `.github/agents`, `.github/skills`, `.github/prompts` и шипованные `.github/instructions/*.instructions.md`;
- в `AGENTS.md` и `.github/copilot-instructions.md` вставляет блок `<!-- mule-starter:begin … end -->`. Существующий текст этих файлов сохраняется под блоком;
- создаёт `.github/mule-starter/` (`log.md`, `memory/lessons.md`, `installed-at` с сегодняшней датой).

Повторный запуск безопасен. Starter-файлы обновятся. Сгенерированные файлы не перезаписываются никогда: `house-style-*`, `profile.md`, rulesets, lessons, log.

### Вариант 2. Персонально, для всех воркспейсов (Copilot CLI + VS Code)

```bash
./install.sh --personal          # skills → ~/.copilot/skills, agents → ~/.copilot/agents
```

Per-workspace части (`AGENTS.md`, instructions, результат `/mule-init`) всё равно ставятся через вариант 1. Если скилл с тем же именем есть и в проекте, побеждает проектный.

### Вариант 3. Вручную

Скопируй содержимое `template/` в корень воркспейса (тот, что открываешь в VS Code). Если `AGENTS.md` / `.github/copilot-instructions.md` уже есть, вставь блок `mule-starter` из шаблона в начало.

### Удаление

```bash
./install.sh ~/Ceer --uninstall  # удаляет starter-файлы и блоки; house-style-* и .github/mule-starter/ оставляет
```

---

## Первый запуск: `/mule-init`

1. Открой воркспейс в VS Code → Chat → режим **Agent**.
2. Набери **`/mule-init`**. Встроенный `/init` тоже сработает: блок `mule-starter` в `copilot-instructions.md` / `AGENTS.md` велит ему сначала прогнать скилл `mule-init`. Но `/mule-init` работает гарантированно.
3. Агент запустит `profile_workspace.py` (только чтение, ~5 с на 87 проектах) и получит метрики стиля.
4. **Вопрос про дату отсечки.** Скрипт ищет следы прежних агентов (`.claude/`, `CLAUDE.md`, `.cursor/` …). Если они старше даты установки, агент спросит, с какой даты не учиться. Для Ceer он предложит `2026-04-24` — первое появление `.claude`. С этой отсечкой из обучения исключаются ~1700 файлов, которые уже трогал агент. Стиль учится только по коду, написанному руками.
5. Агент прочитает 2–3 эталонных файла на категорию и запишет:

| Файл | Что внутри |
|---|---|
| `.github/instructions/house-style.instructions.md` | язык текстов, политика комментариев, стиль коммитов и веток (с реальными примерами) |
| `house-style-mule-xml.instructions.md` | отступы, атрибут-на-строку, `/>`, имена flow и `doc:name` (с примерами), логгер-паттерн |
| `house-style-dataweave.instructions.md` | шапка, `output` + точное написание опций, отступы, имена файлов и переменных |
| `house-style-config.instructions.md` | вложенные/точечные ключи, регистр, кавычки, env-имена, плейсхолдер секретов |
| `house-style-munit.instructions.md` | имена сьютов и тестов, моки, точка входа, фикстуры |
| `house-style-docs.instructions.md` | язык, заголовки, структура README |
| `.github/mule-starter/profile.md` | факты: слои, reference-проекты, parent POM, команды build/test, env-имена, control plane |

**Как решается, что станет правилом.** Доля доминирующего варианта ≥ 80 % даёт MUST. От 60 до 80 % — PREFER (внутри существующего файла побеждает файл). Меньше 60 % — правила нет, агент зеркалит редактируемый файл. Пример с Ceer: отступы в DWL делятся на 2 пробела / табы / 4 пробела как 38/30/13 %, поэтому правила нет и агент копирует соседний файл. А у XML доля «один атрибут на строку» 92 %, это MUST. Каждое правило помечено доказательством `[0.92 · 213 files]`.

**Правки команды.** Пиши их в секцию `## Overrides` любого `house-style-*` файла: при повторном `/mule-init` она сохраняется дословно. Перезапускай `/mule-init` после крупных изменений кодовой базы.

> `.github` и `.github/mule-starter/` стоит закоммитить, чтобы стиль и rulesets были общими для команды. Корень `~/Ceer` не git-репозиторий: можно положить стартер в отдельный репо, а для команды использовать `--personal`.

---

## Ежедневная работа

| Что нужно | VS Code | Copilot CLI |
|---|---|---|
| Задача / баг / PDF / скриншот | `/mule-go <текст или путь>` или выбрать агента **mule-conductor** | `/agent mule-conductor`, затем задача |
| Независимое ревью текущих изменений | `/mule-review` или агент **mule-reviewer** | `/agent mule-reviewer` |
| Архитектура новой интеграции | агент **mule-architect** | `/agent mule-architect` |
| Конкретный скилл | `/mule-munit`, `/mule-dataweave`, … | `/mule-munit …` или «use the mule-munit skill» |
| Переобучить стиль | `/mule-init` | `/mule-init` |

**Lanes у conductor.** Механическая правка (≤ 4 файлов, без новой логики) идёт по fast lane: conductor правит сам в своём контексте, затем одно независимое ревью. Всё остальное идёт по full lane: analyzer (если ruleset не покрывает задачу) → implementer/bugfixer → reviewer, self-heal до 3 итераций. Отдельная стадия edge-case-tester из Ceer влита в implementer (Test Necessity Gate), reviewer проверяет ledger. Это минус один субагент на прогон.

### Caveman

Включён по умолчанию (`full`) для ответов в чате. Не трогает код, комментарии, коммиты, PR, доки, rulesets: они пишутся полным текстом в house style.

- `/caveman lite` / `full` / `ultra` — уровень
- `normal mode` или `stop caveman` — выключить
- Для предупреждений о безопасности, необратимых действиях и инструкций, которые ты выполняешь руками, агент сам переходит на нормальный текст.

---

## Где экономятся токены

- **Ядро.** Всегда в контексте ~1.4K токенов (`AGENTS.md`) плюс описания скиллов ~1.3K. Для сравнения: `CLAUDE.md` Ceer — 28 KB, ~7K токенов на каждый запрос.
- **Progressive disclosure.** Тела скиллов, references и path-scoped instructions грузятся только когда нужны.
- **Сканеры вместо чтения.** `profile_workspace.py`, `reuse_scan.py`, `check_config_matrix.py`, `scan_dwl_usage.py`, `check_oas_contract.py` выдают компактные факты вместо чтения десятков файлов.
- **Бюджеты состояния.** Ruleset ≤ 15 KB (в Ceer доходили до 200 KB), lessons ≤ 8 KB, `log.md` читается только через `grep`.
- **Без дублей.** Каждое правило живёт в одном месте; агенты передают пути, а не пересказ правил.
- **Caveman.** Короткие ответы и ultra-формат в handoff между агентами.
- **Fast lane и слитая стадия edge-case.** Меньше субагентов на прогон.

---

## Воркспейс, где уже настроен Claude Code (как Ceer)

Copilot читает не только `.github/`, но и **`.claude/skills/`** и **`CLAUDE.md`**. В Ceer это даст дубли (19 старых скиллов) и +28 KB контекста на каждый запрос.

1. В настройках **воркспейса** (`.vscode/settings.json` или секция `settings` в `Ceer.code-workspace`) выключи CLAUDE.md:
   ```json
   "chat.useClaudeMdFile": false
   ```
2. Выполни **Chat: Open Customizations** и посмотри, какие скиллы загружены. Если там есть скиллы из `.claude/skills`, отключи эту локацию в `chat.agentSkillsLocations` (формат зависит от версии VS Code, смотри подсказку в Settings). Можно и временно переименовать папку, если Claude Code в этом воркспейсе больше не нужен. При совпадении имён побеждает `.github/skills`.
3. Copilot CLI тоже читает `CLAUDE.md` из корня. Если запускаешь `copilot` в `~/Ceer`, учитывай это или запускай из подпапки проекта.
4. В `Ceer.code-workspace` стоит `"**/.github": true` в `files.exclude`. На Copilot это не влияет, просто скрывает файлы в Explorer. Убери строку, если хочешь видеть сгенерированные инструкции.
5. Знания из `.claude/memory` (решения с датами, проверенные gotchas, команды сборки) `/mule-init` переносит сам, сжато, в `profile.md` и `memory/lessons.md`.

---

## Что изменилось относительно Ceer-харнесса

| Ceer (Claude Code) | Здесь (Copilot) |
|---|---|
| `CLAUDE.md` 28 KB + `memory.md` + 9 topic-файлов, правила повторены 4–5 раз | `AGENTS.md` 5.6 KB + path-scoped instructions; каждое правило в одном месте |
| Захардкожены пути, groupId, JDK, env-имена Ceer | Всё воркспейс-специфичное генерирует `/mule-init` в `profile.md` / `house-style-*` |
| 10 агентов | 6 агентов. mule-tester, api-project-creator, anypoint-*, terraform-engineer стали скиллами; edge-case-tester влит в implementer |
| `run_state.py`, Python-хуки (`pre-bash-safety`, сенсоры) | Правила только в инструкциях. Жёсткое enforcement (запрет `git push` и т. п.) при необходимости настраивай через terminal auto-approve/deny в VS Code или Copilot hooks |
| Стиль описан вручную | Стиль измеряется по коду, написанному руками до агентов, правила с доказательствами |
| Rulesets до 200 KB, лог 380 KB | Бюджеты 15 KB / ротация лога |
| `concise mode` хуком | Скилл `caveman` (lite/full/ultra), по умолчанию ВКЛ |

---

## Troubleshooting

- **Скиллы не видны в `/`.** Обнови VS Code и проверь `chat.useAgentSkills`. Выполни *Chat: Open Customizations*. В CLI: `/skills list`, `/skills reload`.
- **Агентов нет в списке.** Файлы должны лежать в `.github/agents/*.agent.md` в корне открытой папки воркспейса. Для multi-root `.code-workspace` — в первой папке.
- **`/init` переписал copilot-instructions.md без блока.** Запусти `./install.sh <ws>` ещё раз (вернёт блок) или `/mule-init`.
- **Агент пишет «не в стиле».** Проверь `house-style-*` (правило могло попасть в NO RULE). Добавь своё в `## Overrides` или перезапусти `/mule-init` с другой датой отсечки.
- **Сканер стиля вручную.** `python3 .github/skills/mule-init/scripts/profile_workspace.py . --before 2026-04-24 --out /tmp/facts.json`
