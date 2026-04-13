# 🌐 Децентрализованные технологии

> **Связанные документы:**
> - [Architecture: Decentralized Stack](../architecture/decentralized-stack.md)
> - [Architecture: Privacy & Access](../architecture/privacy-access.md)
> - [Reference: Glossary](../reference/glossary.md)

---

## 1. Зачем децентрализация?

### 1.1 Проблемы централизации

| Проблема | Описание |
|----------|----------|
| **Single point of failure** | Сервер упал — всё недоступно |
| **Vendor lock-in** | Зависимость от провайдера |
| **Censorship** | Данные могут быть удалены |
| **Privacy** | Провайдер видит все данные |
| **Ownership** | Вы не владеете своими данными |

### 1.2 Преимущества децентрализации

| Преимущество | Описание |
|--------------|----------|
| **Resilience** | Нет единой точки отказа |
| **Sovereignty** | Полный контроль над данными |
| **Privacy** | Шифрование end-to-end |
| **Interoperability** | Открытые протоколы |
| **Verifiability** | Криптографические доказательства |

---

## 2. Content Addressing (IPFS)

### 2.1 Концепция

**Location-based** (традиционный):
```
https://server.com/path/to/file.txt
         ↑
    Где находится
```

**Content-addressed** (IPFS):
```
ipfs://QmXyz123...
           ↑
    Что это (хэш содержимого)
```

### 2.2 Ключевые свойства

| Свойство | Описание |
|----------|----------|
| **Immutability** | Изменение контента = новый CID |
| **Deduplication** | Одинаковый контент хранится один раз |
| **Verification** | CID = proof что контент не изменён |
| **Distribution** | Файлы реплицируются по сети |

### 2.3 Компоненты экосистемы IPFS

```
┌─────────────────────────────────────────────────────────────────┐
│  IPFS      │ Content-addressed storage (blobs)                  │
├────────────┼────────────────────────────────────────────────────┤
│  IPLD      │ Linked data model (ссылки по CID)                  │
├────────────┼────────────────────────────────────────────────────┤
│  IPNS      │ Mutable pointers (стабильные ссылки)               │
├────────────┼────────────────────────────────────────────────────┤
│  libp2p    │ P2P networking (обнаружение, транспорт)            │
├────────────┼────────────────────────────────────────────────────┤
│  PubSub    │ Real-time messaging (уведомления)                  │
└────────────┴────────────────────────────────────────────────────┘
```

---

## 3. Decentralized Identity (DIDs)

### 3.1 Что такое DID

**DID (Decentralized Identifier)** — идентификатор, не зависящий от центрального реестра.

```
did:method:specific-identifier

Примеры:
did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK
did:web:example.com
did:ethr:0x1234...
```

### 3.2 Преимущества

| Преимущество | Описание |
|--------------|----------|
| **Self-sovereign** | Пользователь контролирует свой ID |
| **No registry** | Не нужен центральный реестр |
| **Cryptographic** | Владение доказывается подписью |
| **Portable** | Работает везде |

### 3.3 DID Document

```json
{
  "@context": "https://www.w3.org/ns/did/v1",
  "id": "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
  "verificationMethod": [{
    "id": "#key-1",
    "type": "Ed25519VerificationKey2020",
    "publicKeyMultibase": "z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
  }],
  "authentication": ["#key-1"],
  "capabilityDelegation": ["#key-1"]
}
```

---

## 4. Capability-Based Authorization (UCAN)

### 4.1 Концепция

**RBAC (традиционный)**:
```
Пользователь → Роль → Права
     ↓
Сервер проверяет роль
```

**UCAN (capability-based)**:
```
Capability (токен) содержит:
├── Кто выдал (issuer)
├── Кому (audience)
├── Что можно делать (capabilities)
├── Когда истекает (expiration)
└── Доказательство (proof chain)

Верификация без сервера!
```

### 4.2 Атенуация

Права **только уменьшаются** при делегации:

```
Alice (owner):      space: "alice/*", can: "*"
         │
         │ delegate (attenuate)
         ▼
Company:            space: "alice/work/*", can: "read"
         │
         │ delegate (further attenuate)
         ▼
AI Agent:           space: "alice/work/project-x/*", can: "read"
                    + constraints: { "content-type": "public" }
```

---

## 5. Decentralized Encryption (Lit Protocol)

### 5.1 Проблема

IPFS публичен — любой кто знает CID может скачать файл.

### 5.2 Решение: Encrypt-then-Store

```
1. Шифруем локально (AES-256)
2. Ключ разбиваем между нодами Lit (threshold)
3. Сохраняем ciphertext в IPFS
4. Определяем Access Control Conditions

Результат:
├── В IPFS: зашифрованный blob (бесполезен без ключа)
├── В Lit: части ключа + условия доступа
└── Расшифровка: докажи право → получи ключ → расшифруй
```

### 5.3 Access Control Conditions

```javascript
// Владеет NFT
{ contractAddress: '0x...', method: 'balanceOf', 
  returnValueTest: { comparator: '>', value: '0' } }

// В списке адресов
{ returnValueTest: { key: ':userAddress', comparator: 'contains', 
  value: ['0xAlice...', '0xBob...'] } }

// Временный доступ
{ returnValueTest: { key: 'timestamp', comparator: '<', 
  value: '1735689600' } }

// Комбинации
[ condition1, { operator: 'and' }, condition2 ]
```

---

## 6. Structured Decentralized Data (Ceramic)

### 6.1 Зачем Ceramic

IPFS хранит raw bytes. Нам нужно:
- Схемы данных
- Мутабельность (обновления)
- GraphQL queries
- История изменений

### 6.2 Архитектура

```
ComposeDB (GraphQL queries)
         │
    Streams (append-only event logs)
         │
     Events (подписанные DID)
         │
  IPFS (storage) + Blockchain (anchoring)
```

### 6.3 Streams

**Stream = append-only log of events**

Каждый event подписан DID автора. Current state = результат применения всех events.

---

## 7. Real-Time P2P (OrbitDB)

### 7.1 Когда нужен OrbitDB

Ceramic использует blockchain anchoring → задержки (минуты).
Для real-time collaboration нужны **CRDTs**.

### 7.2 Merkle-CRDTs

```
Peer A: op1 ──► op2 ──► op3
                  ╲
                   ╲ merge (instant!)
                    ╲
Peer B: op1 ──► op4 ──► merged state
```

Операции коммутативны → автоматическое разрешение конфликтов.

---

## 8. Сравнение: Centralized vs Decentralized

| Аспект | Centralized | Decentralized |
|--------|-------------|---------------|
| **Storage** | S3, PostgreSQL | IPFS, Ceramic |
| **Identity** | Username/password | DID, Keys |
| **Auth** | OAuth, JWT | UCAN |
| **Encryption** | Server-side | Lit Protocol (client-side) |
| **Real-time** | WebSocket server | PubSub, OrbitDB |

---

## 9. Когда использовать децентрализацию

### 9.1 Хорошие кейсы

| Сценарий | Почему децентрализация |
|----------|----------------------|
| **Multi-org collaboration** | Никто не контролирует данные |
| **Sensitive data** | Полный контроль над приватностью |
| **Censorship resistance** | Данные не удалят |
| **Verifiability needed** | Криптографические доказательства |
| **Long-term storage** | Не зависим от провайдера |

### 9.2 Плохие кейсы

| Сценарий | Почему централизация лучше |
|----------|---------------------------|
| **Simple prototype** | Overkill, сложнее настроить |
| **Real-time gaming** | Задержки неприемлемы |
| **Strict compliance** | Может не соответствовать требованиям |
| **Low-tech users** | UX сложнее |

---

## 10. Практические рекомендации

### 10.1 Минимальный стек

```
IPFS + IPNS + локальный кэш
```

### 10.2 Командный стек

```
IPFS + Ceramic + Lit Protocol + UCAN + PubSub
```

### 10.3 Гибридный подход

Начните с централизованного MVP, добавляйте децентрализацию по мере роста:

1. **Phase 1**: PostgreSQL + S3
2. **Phase 2**: + IPFS для файлов
3. **Phase 3**: + Ceramic для metadata
4. **Phase 4**: + Lit для encryption
5. **Phase 5**: Full decentralization

---

*Источники: Decentralized-Knowledge-Stack-Guide.md, Decentralized-Graph-Architecture.md*
