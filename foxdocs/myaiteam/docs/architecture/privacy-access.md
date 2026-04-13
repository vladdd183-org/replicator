# 🔐 Приватность и контроль доступа

> **Связанные документы:**
> - [Architecture Overview](overview.md)
> - [Decentralized Stack](decentralized-stack.md)
> - [Reference: Glossary](../reference/glossary.md)

---

## 1. Обзор

### 1.1 Проблема

**Децентрализация обычно означает публичность.** IPFS публичен — любой кто знает CID может скачать файл.

Нам нужна **приватность + контроль доступа** в децентрализованной сети.

### 1.2 Решение

```
┌─────────────────────────────────────────────────────────────────┐
│              ПРИВАТНЫЕ ДАННЫЕ (Зашифрованы)                     │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   IPFS       │  │   Ceramic    │  │  Lit Protocol│          │
│  │  (CID публичны│ │  (DID-based) │  │  (Access Ctrl)│         │
│  │   данные заш.)│  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                           │                                     │
│                    ┌──────▼──────┐                              │
│                    │  Контроль   │                              │
│                    │   доступа    │                              │
│                    │  (DID/VC)   │                              │
│                    └─────────────┘                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ Расшифровка только для
                            │ авторизованных пользователей
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│         ПУБЛИЧНЫЕ ДАННЫЕ (Незашифрованы)                        │
│  • Метаданные (CID, структура)                                  │
│  • Публичные теги                                               │
│  • Статистика (без контента)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Два уровня защиты

### 2.1 UCAN vs Lit Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│                    UCAN vs LIT PROTOCOL                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│               UCAN                         LIT PROTOCOL         │
│               ────                         ────────────         │
│                                                                 │
│  Отвечает на:  "Можно ли СДЕЛАТЬ?"        "Можно ли ПРОЧИТАТЬ?"│
│                                                                 │
│  Когда:        ДО операции                ПРИ доступе к данным │
│                                                                 │
│  Защищает:     Операции (CRUD)            Данные (content)     │
│                                                                 │
│  Пример:       "Агент может добавлять     "Только члены команды│
│                 документы в project"       могут расшифровать"  │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  ПОЧЕМУ ОБА НУЖНЫ:                                              │
│                                                                 │
│  Только UCAN:    Агент может записать, но файл не зашифрован → │
│                  любой кто узнает CID прочитает!                │
│                                                                 │
│  Только Lit:     Файл зашифрован, но любой может его удалить,  │
│                  перезаписать, спамить базу!                    │
│                                                                 │
│  UCAN + Lit:     Операции контролируются + данные защищены     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. UCAN (User Controlled Authorization Networks)

### 3.1 Что это

**Capability-based authorization** без центрального сервера.

### 3.2 Delegation Chain

```
┌─────────────────────────────────────────────────────────────────┐
│                 UCAN DELEGATION CHAIN                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ROOT CAPABILITY (Alice owns her space)                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  issuer: did:key:alice                                    │  │
│  │  audience: did:key:alice                                  │  │
│  │  capabilities: [{ space: "alice/*", can: "*" }]           │  │
│  │  expiration: 2030-01-01                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ delegate (attenuated)                │
│                          ▼                                      │
│  DELEGATED TO COMPANY                                           │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  issuer: did:key:alice                                    │  │
│  │  audience: did:web:acme.com                               │  │
│  │  capabilities: [{ space: "alice/work/*", can: "read" }]   │  │
│  │  expiration: 2025-12-31                                   │  │
│  │  proof: [root_ucan_cid]                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                      │
│                          │ delegate (further attenuated)        │
│                          ▼                                      │
│  DELEGATED TO AI AGENT                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  issuer: did:web:acme.com                                 │  │
│  │  audience: did:key:research-agent                         │  │
│  │  capabilities: [{                                         │  │
│  │    space: "alice/work/project-x/*",                       │  │
│  │    can: "read",                                           │  │
│  │    constraints: { "content-type": "public" }              │  │
│  │  }]                                                       │  │
│  │  expiration: 2025-06-01                                   │  │
│  │  proof: [company_ucan_cid]                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Ключевые свойства UCAN

| Свойство | Описание |
|----------|----------|
| **Атенуация** | Права только уменьшаются при делегации |
| **Offline** | Верификация без сервера |
| **Time-bounded** | Автоматическая экспирация |
| **Revocable** | Можно отозвать |
| **Auditable** | Полная цепочка доказательств |

---

## 4. Lit Protocol

### 4.1 Encrypt-then-Store

```
┌─────────────────────────────────────────────────────────────────┐
│                LIT PROTOCOL: ENCRYPT-THEN-STORE                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ЗАПИСЬ:                                                        │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │  Документ   │────▶│  Шифрование │────▶│    IPFS     │       │
│  │  (plaintext)│     │  (AES-256)  │     │ (ciphertext)│       │
│  └─────────────┘     └──────┬──────┘     └─────────────┘       │
│                             │                                   │
│                             │ Ключ шифрования                   │
│                             ▼                                   │
│                ┌─────────────────────────────────┐              │
│                │      LIT PROTOCOL NETWORK       │              │
│                │                                 │              │
│                │  Ключ разделён на части:        │              │
│                │  ┌─────┐ ┌─────┐ ┌─────┐       │              │
│                │  │Node1│ │Node2│ │Node3│ ...   │              │
│                │  │share│ │share│ │share│       │              │
│                │  └─────┘ └─────┘ └─────┘       │              │
│                │                                 │              │
│                │  + Access Control Conditions    │              │
│                │    (кто может расшифровать)     │              │
│                └─────────────────────────────────┘              │
│                                                                 │
│  В IPFS хранится: encrypted blob (бесполезен без ключа!)       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 Процесс расшифровки

```
1. Скачиваешь ciphertext из IPFS (публичный, но зашифрованный)

2. Идёшь к Lit Protocol с доказательством:
   "Я Alice, у меня есть право на этот документ"

3. Lit ноды НЕЗАВИСИМО проверяют Access Control Conditions:
   ┌─────────────────────────────────────────────────────────┐
   │  Условие: "Владеет NFT компании" или "В allowlist"      │
   │                                                         │
   │  Node 1: ✓ Проверил → даёт свою часть ключа             │
   │  Node 2: ✓ Проверил → даёт свою часть ключа             │
   │  Node 3: ✓ Проверил → даёт свою часть ключа             │
   └─────────────────────────────────────────────────────────┘

4. Собираешь threshold (например, 2 из 3) частей ключа

5. Расшифровываешь локально

✅ Без прохождения проверки Lit — файл бесполезен
```

### 4.3 Access Control Conditions

```javascript
// 1. Владеет NFT компании
{
  contractAddress: '0x...',
  standardContractType: 'ERC721',
  method: 'balanceOf',
  returnValueTest: { comparator: '>', value: '0' }
}

// 2. Адрес в allowlist
{
  conditionType: 'evmBasic',
  returnValueTest: {
    key: ':userAddress',
    comparator: 'contains',
    value: ['0xAlice...', '0xBob...', '0xAgent...']
  }
}

// 3. Минимум X токенов
{
  contractAddress: '0x...',
  standardContractType: 'ERC20',
  method: 'balanceOf',
  returnValueTest: { comparator: '>=', value: '100000000000000000000' }
}

// 4. Временный доступ (до определённой даты)
{
  conditionType: 'evmBasic',
  returnValueTest: {
    key: 'timestamp',
    comparator: '<',
    value: '1735689600'
  }
}

// 5. Комбинации
[
  { /* условие 1 */ },
  { operator: 'and' },
  { /* условие 2 */ },
  { operator: 'or' },
  { /* условие 3 */ }
]
```

---

## 5. Сравнение решений

| Решение | Шифрование | Контроль доступа | Децентрализация | Сложность |
|---------|-----------|------------------|-----------------|-----------|
| **OriginTrail DKG** | ✅ Встроено | ✅ Владелец узла | ✅ Полная | 🟢 Низкая |
| **Lit Protocol** | ✅ BLS | ✅ ACC (условия) | ✅ Полная | 🟡 Средняя |
| **Ceramic + JOSE** | ✅ JOSE | ✅ DID-based | ✅ Полная | 🟡 Средняя |
| **IPFS + AES** | ✅ AES-256 | ⚠️ Вручную | ✅ Полная | 🟢 Низкая |

---

## 6. OriginTrail DKG

### 6.1 Готовое решение

**OriginTrail DKG** — готовый Decentralized Knowledge Graph с встроенной приватностью.

**Преимущества:**
- ✅ Public + Private assertions встроены
- ✅ Python SDK (`dkg.py`)
- ✅ W3C стандарты (JSON-LD, SPARQL)
- ✅ NFT ownership для Knowledge Assets

### 6.2 Пример использования

```python
from dkg import DKG
from dkg.providers import BlockchainProvider, NodeHTTPProvider

# Инициализация
node_provider = NodeHTTPProvider("http://localhost:8900")
blockchain_provider = BlockchainProvider("http://localhost:8545", PRIVATE_KEY)
dkg = DKG(node_provider, blockchain_provider)

# Создание Knowledge Asset с приватными данными
public_assertion = {
    "@context": "https://schema.org",
    "@id": "https://my-idea/001",
    "@type": "Idea",
    "name": "AI-стартап идея",
    "tags": ["ai", "startup"],  # Публичные теги
}

private_assertion = {
    "@context": "https://schema.org",
    "@id": "https://my-idea/001",
    "detailedPlan": "Детальный план...",  # Приватные данные
    "vector": [0.1, 0.2, 0.3, 0.4]         # Приватный вектор
}

# Создаём (публичное + приватное)
result = dkg.asset.create(
    {
        "public": public_assertion,
        "private": private_assertion
    },
    epochs_number=2
)

ual = result["UAL"]

# Получение публичных данных (доступно всем)
public_data = dkg.asset.get(ual, content_visibility="public")

# Получение приватных данных (только владелец)
private_data = dkg.asset.get(ual, content_visibility="private")
```

---

## 7. Гибридный подход

### 7.1 Разделение по уровням доступа

```python
class HybridKnowledgeGraph:
    """Гибридный граф: приватные и публичные данные"""
    
    async def add_knowledge(self, content, vector, tags, access_level):
        if access_level == "private":
            # Шифруем через Lit Protocol
            return await self.private_graph.add_node(
                content=content,
                vector=vector,
                tags=tags,
                access_conditions={"method": "did", "params": [self.my_did]}
            )
        elif access_level == "team":
            # Шифруем для команды
            team_dids = await self._get_team_dids()
            return await self.private_graph.add_node(
                content=content,
                vector=vector,
                tags=tags,
                access_conditions={
                    "operator": "or",
                    "conditions": [
                        {"method": "did", "params": [did]} 
                        for did in team_dids
                    ]
                }
            )
        else:  # public
            # Без шифрования
            return await self.public_graph.add_node(
                content=content,
                vector=vector,
                tags=tags
            )
```

---

## 8. Ключевые принципы

1. **Шифрование на клиенте** — данные шифруются до отправки в IPFS
2. **CID публичны, данные приватны** — CID можно публиковать, но данные зашифрованы
3. **Децентрализованный контроль** — через DID/VC/Lit Protocol
4. **Гибкие условия** — доступ на основе DID, токенов, API, комбинаций
5. **Метаданные публичны** — теги и структура могут быть публичными для поиска

---

## 9. Рекомендации

### 9.1 Быстрый старт

| Сценарий | Рекомендация |
|----------|--------------|
| **MVP, простая приватность** | IPFS + AES вручную |
| **Готовое решение** | OriginTrail DKG |
| **Максимальная гибкость** | Lit Protocol + UCAN |
| **Enterprise** | Ceramic + Lit + UCAN |

### 9.2 Установка

```bash
# OriginTrail DKG
pip install dkg==8.0.0a3

# Lit Protocol
pip install lit-sdk

# IPFS + AES
pip install ipfshttpclient pycryptodome
```

---

## 10. Навигация

| Следующий документ | Тема |
|--------------------|------|
| → [human-ai-collab.md](human-ai-collab.md) | Human-AI взаимодействие |
| → [../reference/glossary.md](../reference/glossary.md) | Глоссарий терминов |

---

*Источники: Decentralized-Private-Access-Control.md, Decentralized-Knowledge-Stack-Guide.md*
