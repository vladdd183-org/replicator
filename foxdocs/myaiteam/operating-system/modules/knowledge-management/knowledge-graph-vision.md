# Видение: от документов к графу знаний

**Модуль:** `knowledge-management`  
**Дата:** 2026-02-09  
**Статус:** 📋 Vision (не для реализации сейчас)  
**DRI:** Архитектор

---

## Цель документа

Долгосрочный roadmap эволюции системы знаний FatData — от файлов в Git до AI-powered графа знаний. Документ **не является планом реализации**. Это ориентир, опирающийся на исследования команды в `myaiteam/`.

---

## 1. Текущее состояние

| Аспект | Сейчас | Проблема |
|--------|--------|----------|
| Хранение | Markdown в Git (Gitea) | Нет единого поиска по всем репозиториям |
| Поиск | Ручной: `Ctrl+F`, grep | Новичок не знает, где искать |
| Связи | Ссылки между документами (вручную) | Ломаются, неявные связи не видны |
| Знания в головах | Участники помнят, но не записывают | Уход человека = потеря знаний |

Это нормально для 14 part-time участников. При росте — не выдержит.

---

## 2. Эволюция системы знаний

**Phase 1 — Files + Handbook-First (сейчас)**  
Markdown в Git. Handbook-First культура. Docs-as-Code.  
*Критерий перехода:* 80% процессных вопросов решаются ссылкой на документ.

**Phase 2 — Search + AI-assisted (6–12 месяцев)**  
Полнотекстовый поиск (MeiliSearch), AI-суммаризация, транскрипция встреч (Whisper).  
*Критерий перехода:* Поиск покрывает все репозитории. AI-summary для каждой встречи.

**Phase 3 — Knowledge Graph + Semantic Search (12–24 месяца)**  
Граф знаний (SurrealDB), семантический поиск, GraphRAG для сложных вопросов.  
*Критерий перехода:* Граф покрывает >90% документов. Качество ответов выше ручного поиска.

**Phase 4 — Decentralized + Self-Evolving (24+ месяцев)**  
IPFS + Ceramic (децентрализация), AI-агенты поддерживают граф, Shadow Mode.

---

## 3. Целевая архитектура (из исследований)

```
┌─────────────────────────────────────────────┐
│  Application: Поиск, Q&A, Shadow Mode       │
├─────────────────────────────────────────────┤
│  AI: GraphRAG, Embeddings, COMPASS + MAKER  │
├─────────────────────────────────────────────┤
│  Graph: SurrealDB (graph + vector + FTS)    │
├─────────────────────────────────────────────┤
│  Storage: IPFS + IPLD, Ceramic + ComposeDB  │
├─────────────────────────────────────────────┤
│  Sources: Git repos, Chat, Recordings       │
└─────────────────────────────────────────────┘
```

**SurrealDB** — графы + векторный поиск + документы в одной БД. Self-hosted, бесплатный. Анализ: [Graph-Vector-Hybrid-Solutions.md](../../../Graph-Vector-Hybrid-Solutions.md).

**IPFS + Ceramic** — content-addressed storage, мутабельные потоки. Детали: [Decentralized-Knowledge-Stack-Guide.md](../../../Decentralized-Knowledge-Stack-Guide.md).

---

## 4. Что это даёт

| Возможность | Phase | Эффект |
|-------------|-------|--------|
| Полнотекстовый поиск | 2 | Ответ за секунды вместо минут |
| AI-summary встреч | 2 | Экономия ~30 мин/встречу |
| Семантический поиск | 3 | «Как решали X?» — даже если слово X не в тексте |
| Автообнаружение связей | 3 | Проект A решает ту же задачу, что проект B |
| Self-updating docs | 4 | AI предлагает обновить handbook при расхождении с практикой |
| Онбординг за часы | 3–4 | Новичок спрашивает — AI находит ответ в графе |

---

## 5. Связь с исследованиями

| Документ | Релевантность |
|----------|---------------|
| [Ultimate-Knowledge-Graph-Architecture-Guide.md](../../../Ultimate-Knowledge-Graph-Architecture-Guide.md) | Phase 3 — архитектура графа, GraphRAG, онтологии |
| [Decentralized-Knowledge-Stack-Guide.md](../../../Decentralized-Knowledge-Stack-Guide.md) | Phase 4 — IPFS + Ceramic + UCAN |
| [AI-Native-Organization-Masterguide.md](../../../AI-Native-Organization-Masterguide.md) | Phase 4 — COMPASS + MAKER, self-evolution |
| [Graph-Vector-Hybrid-Solutions.md](../../../Graph-Vector-Hybrid-Solutions.md) | Phase 3 — SurrealDB vs Neo4j vs GraphRAG |
| [Decentralized-Graph-Architecture.md](../../../Decentralized-Graph-Architecture.md) | Phase 3–4 — интеграция стека |

---

## 6. Следующий конкретный шаг

Когда модуль `knowledge-management` переходит в Active:

1. Поднять **MeiliSearch** (Docker, self-hosted, бесплатный)
2. Настроить индексацию markdown из Gitea-репозиториев
3. Дать команде доступ (веб-интерфейс или Telegram-бот)
4. Собрать фидбек за 1 месяц → решить, двигаться ли к Phase 3

---

## История изменений

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| — | 2026-02-09 | Команда FatData | Первая версия. Vision на основе исследований myaiteam/ |
