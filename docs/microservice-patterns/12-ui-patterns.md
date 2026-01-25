# 12. UI Patterns

> **Паттерны для фронтенда микросервисов**

---

## Проблема UI в микросервисах

В микросервисах backend разбит на сервисы. А что с frontend?
- Один монолитный UI → bottleneck, сложно развивать
- UI нужны данные из разных сервисов
- Разные команды хотят независимость

UI Patterns решают: **как организовать фронтенд**.

---

## Паттерн 1: Client-side UI Composition

### 💡 Суть

**Браузер** собирает страницу из компонентов, которые загружаются от разных сервисов.

### 📝 Техническое объяснение

- Каждый микросервис предоставляет свой UI компонент (widget)
- Главное приложение (shell) загружает компоненты динамически
- Компоненты общаются через события или shared state

### 🏠 Аналогия: Конструктор LEGO

Страница — это **LEGO-набор**:
- Каждая команда делает свой блок (header, cart, recommendations)
- Браузер собирает блоки вместе
- Блоки можно заменять независимо

### ✅ Когда использовать

- SPA (Single Page Application)
- Разные команды владеют частями UI
- Нужна независимость деплоя frontend

### ❌ Когда НЕ использовать

- SEO критичен (SPA плохо индексируется)
- Медленные устройства (много JS)
- Простой UI

### 🔧 Пример (Module Federation / Webpack 5)

```javascript
// shell/webpack.config.js (главное приложение)
const ModuleFederationPlugin = require("webpack/lib/container/ModuleFederationPlugin");

module.exports = {
  plugins: [
    new ModuleFederationPlugin({
      name: "shell",
      remotes: {
        // Загружаем компоненты от других сервисов
        userProfile: "userProfile@http://user-service/remoteEntry.js",
        cart: "cart@http://cart-service/remoteEntry.js",
        recommendations: "recommendations@http://recommendations-service/remoteEntry.js",
      },
    }),
  ],
};


// shell/App.tsx
import React, { lazy, Suspense } from "react";

// Динамическая загрузка компонентов от других сервисов
const UserProfile = lazy(() => import("userProfile/Profile"));
const Cart = lazy(() => import("cart/MiniCart"));
const Recommendations = lazy(() => import("recommendations/ProductList"));

function App() {
  return (
    <div>
      <header>
        <Suspense fallback={<div>Loading profile...</div>}>
          <UserProfile userId={currentUser.id} />
        </Suspense>
        
        <Suspense fallback={<div>Loading cart...</div>}>
          <Cart />
        </Suspense>
      </header>
      
      <main>
        <Suspense fallback={<div>Loading recommendations...</div>}>
          <Recommendations category="electronics" />
        </Suspense>
      </main>
    </div>
  );
}
```

### Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   CLIENT-SIDE UI COMPOSITION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌────────────────────────────────────────────────────────────────────┐   │
│   │                         Browser                                     │   │
│   │                                                                     │   │
│   │  ┌──────────────────────────────────────────────────────────────┐  │   │
│   │  │                    Shell Application                          │  │   │
│   │  │                                                               │  │   │
│   │  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │  │   │
│   │  │  │  Header     │ │   Cart      │ │  User       │            │  │   │
│   │  │  │  Component  │ │  Component  │ │  Component  │            │  │   │
│   │  │  │  (shared)   │ │  (remote)   │ │  (remote)   │            │  │   │
│   │  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘            │  │   │
│   │  │         │               │               │                    │  │   │
│   │  └─────────┼───────────────┼───────────────┼────────────────────┘  │   │
│   │            │               │               │                        │   │
│   └────────────┼───────────────┼───────────────┼────────────────────────┘   │
│                │               │               │                            │
│      Load at   │               │               │                            │
│      runtime   ▼               ▼               ▼                            │
│                                                                             │
│   ┌────────────────┐  ┌────────────────┐  ┌────────────────┐               │
│   │  Cart Service  │  │  User Service  │  │  Reco Service  │               │
│   │                │  │                │  │                │               │
│   │  cart.js       │  │  user.js       │  │  reco.js       │               │
│   │  cart.css      │  │  user.css      │  │  reco.css      │               │
│   └────────────────┘  └────────────────┘  └────────────────┘               │
│                                                                             │
│   Каждый сервис деплоит свой UI компонент независимо                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 2: Server-side Page Fragment Composition

### 💡 Суть

**Сервер** собирает страницу из фрагментов от разных сервисов, отдаёт готовый HTML.

### 📝 Техническое объяснение

- Edge Server (Nginx/CDN) или BFF запрашивает фрагменты
- Каждый сервис возвращает HTML-фрагмент
- Сервер склеивает и отдаёт клиенту
- Технологии: ESI (Edge Side Includes), Tailor

### 🏠 Аналогия: Газета

Газета собирается **в типографии** (сервер):
- Редакция спорта даёт свои страницы
- Редакция новостей — свои
- Типография склеивает в одну газету
- Читателю приходит готовый продукт

### ✅ Когда использовать

- SEO важен (готовый HTML)
- Медленные клиенты
- Кэширование фрагментов
- Legacy интеграция

### ❌ Когда НЕ использовать

- SPA с богатой интерактивностью
- Все фрагменты от одной команды

### 🔧 Пример (Edge Side Includes)

```html
<!-- Главная страница с ESI-тегами -->
<html>
<head>
  <title>My Shop</title>
</head>
<body>
  <!-- Header от User Service -->
  <esi:include src="http://user-service/fragments/header" />
  
  <main>
    <!-- Контент страницы -->
    <h1>Welcome!</h1>
    
    <!-- Рекомендации от Reco Service -->
    <esi:include src="http://reco-service/fragments/homepage-recommendations" />
  </main>
  
  <!-- Footer от CMS -->
  <esi:include src="http://cms/fragments/footer" />
</body>
</html>

<!-- Результат: CDN запрашивает каждый фрагмент, кэширует, склеивает -->
```

### Архитектура

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                 SERVER-SIDE FRAGMENT COMPOSITION                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌──────────┐                                                              │
│   │  Client  │                                                              │
│   │ (Browser)│                                                              │
│   └────┬─────┘                                                              │
│        │                                                                    │
│        │  GET /homepage                                                     │
│        ▼                                                                    │
│   ┌──────────────────────────────────────────────────────────┐             │
│   │                  Edge Server / CDN                        │             │
│   │                                                           │             │
│   │   1. Получить шаблон страницы                            │             │
│   │   2. Найти <esi:include> теги                            │             │
│   │   3. Запросить фрагменты параллельно                     │             │
│   │   4. Заменить теги на HTML                               │             │
│   │   5. Отдать готовую страницу                             │             │
│   │                                                           │             │
│   └───────┬────────────────┬────────────────┬────────────────┘             │
│           │                │                │                               │
│           ▼                ▼                ▼                               │
│   ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                       │
│   │ User Service │ │ Reco Service │ │  CMS         │                       │
│   │              │ │              │ │              │                       │
│   │ /fragments/  │ │ /fragments/  │ │ /fragments/  │                       │
│   │ header       │ │ recos        │ │ footer       │                       │
│   │              │ │              │ │              │                       │
│   │ <nav>...</nav│ │ <div>...</div│ │ <footer>...  │                       │
│   └──────────────┘ └──────────────┘ └──────────────┘                       │
│                                                                             │
│   Преимущества:                                                             │
│   • SEO-friendly (готовый HTML)                                            │
│   • Кэширование фрагментов независимо                                      │
│   • Быстрая загрузка (no JS bundle)                                        │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Паттерн 3: Micro Frontends

### 💡 Суть

**Независимые frontend-приложения**, интегрированные в единый UI.

### 📝 Техническое объяснение

Micro Frontends = микросервисы для frontend:
- Каждая команда владеет своим приложением (не компонентом)
- Разные технологии (React, Vue, Angular)
- Независимые деплои
- Интеграция через shell или iframe

### 🏠 Аналогия: Торговый центр

Торговый центр (shell) содержит разные **магазины** (micro frontends):
- Магазин одежды (React, команда A)
- Продуктовый магазин (Vue, команда B)
- Кинотеатр (Angular, команда C)

Каждый магазин работает независимо, но под одной крышей.

### ✅ Когда использовать

- Большие команды (>5 frontend разработчиков)
- Разные домены (checkout, catalog, admin)
- Нужна независимость технологий
- Legacy + new интеграция

### ❌ Когда НЕ использовать

- Маленькая команда
- Единый стек технологий
- Сильная связанность между частями UI

### 🔧 Подходы интеграции

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   MICRO FRONTENDS INTEGRATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. BUILD-TIME INTEGRATION (npm packages)                                   │
│  ──────────────────────────────────────                                    │
│                                                                             │
│     npm install @team-a/catalog-component                                   │
│     npm install @team-b/checkout-component                                  │
│                                                                             │
│     → Все собирается в один бандл                                          │
│     → Зависимости версий                                                   │
│     → Нужен деплой shell при изменении компонента                          │
│                                                                             │
│  2. RUN-TIME INTEGRATION (Module Federation)                                │
│  ────────────────────────────────────────────                              │
│                                                                             │
│     const Catalog = lazy(() => import("catalog/ProductList"));              │
│                                                                             │
│     → Загрузка в рантайме                                                  │
│     → Независимые деплои                                                   │
│     → Сложнее debugging                                                    │
│                                                                             │
│  3. SERVER-SIDE INTEGRATION (ESI / SSI)                                     │
│  ───────────────────────────────────────                                   │
│                                                                             │
│     <esi:include src="/catalog/fragment" />                                │
│                                                                             │
│     → SEO-friendly                                                         │
│     → Простой HTML                                                         │
│     → Ограниченная интерактивность                                         │
│                                                                             │
│  4. IFRAME INTEGRATION                                                      │
│  ─────────────────────                                                     │
│                                                                             │
│     <iframe src="https://checkout.example.com" />                          │
│                                                                             │
│     → Полная изоляция                                                      │
│     → Разные домены                                                        │
│     → Плохой UX (nested scrolling)                                         │
│     → Сложная коммуникация                                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Пример архитектуры

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MICRO FRONTENDS                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                         ┌────────────────────────┐                          │
│                         │     Shell / Host       │                          │
│                         │                        │                          │
│                         │  • Routing             │                          │
│                         │  • Auth                │                          │
│                         │  • Shared UI           │                          │
│                         └───────────┬────────────┘                          │
│                                     │                                       │
│          ┌──────────────────────────┼──────────────────────────┐           │
│          │                          │                          │            │
│          ▼                          ▼                          ▼            │
│   ┌──────────────┐          ┌──────────────┐          ┌──────────────┐     │
│   │  Catalog MF  │          │ Checkout MF  │          │  Account MF  │     │
│   │              │          │              │          │              │     │
│   │  Team A      │          │  Team B      │          │  Team C      │     │
│   │  React       │          │  Vue         │          │  React       │     │
│   │              │          │              │          │              │     │
│   │  /products/* │          │  /checkout/* │          │  /account/*  │     │
│   └──────────────┘          └──────────────┘          └──────────────┘     │
│          │                          │                          │            │
│          ▼                          ▼                          ▼            │
│   ┌──────────────┐          ┌──────────────┐          ┌──────────────┐     │
│   │   Catalog    │          │  Checkout    │          │   User       │     │
│   │   Service    │          │   Service    │          │   Service    │     │
│   └──────────────┘          └──────────────┘          └──────────────┘     │
│                                                                             │
│   Каждый MF:                                                               │
│   • Своя команда                                                           │
│   • Свой репозиторий                                                       │
│   • Свой CI/CD                                                             │
│   • Свой бэкенд сервис                                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Сравнение паттернов

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      UI PATTERNS COMPARISON                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Паттерн         │ Сборка    │ Независи-│ SEO  │ Когда                     │
│                  │           │ мость    │      │                            │
│  ────────────────│───────────│──────────│──────│────────────────────────────│
│                  │           │          │      │                            │
│  Client-side     │ Browser   │ Высокая  │ Плохо│ SPA, интерактивность       │
│  Composition     │ (JS)      │          │      │                            │
│                  │           │          │      │                            │
│  Server-side     │ Server    │ Средняя  │ Хорошо│ SEO, быстрая загрузка     │
│  Fragments       │ (HTML)    │          │      │                            │
│                  │           │          │      │                            │
│  Micro Frontends │ Оба       │ Очень    │ Зави-│ Большие команды,          │
│                  │ варианта  │ высокая  │ сит  │ разные домены              │
│                  │           │          │      │                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Чеклист UI Patterns

```markdown
## UI Patterns Checklist

### Client-side Composition
- [ ] Module Federation настроен
- [ ] Shared dependencies (React, etc.)
- [ ] Error boundaries для remote components
- [ ] Loading states / fallbacks
- [ ] Styling isolation (CSS modules / Shadow DOM)

### Server-side Fragments
- [ ] ESI/SSI настроен на CDN/Edge
- [ ] Caching strategy для фрагментов
- [ ] Fallback при недоступности фрагмента
- [ ] Timeout настроен

### Micro Frontends
- [ ] Shell application
- [ ] Routing strategy (shell vs MF)
- [ ] Shared state management
- [ ] Design system / UI kit
- [ ] Cross-MF communication
- [ ] Independent deployments
```

---

## Заключение серии

Это была последняя заметка в серии паттернов микросервисной архитектуры.

### Ключевые выводы

1. **Начинайте с модульного монолита** — декомпозируйте когда готовы
2. **Паттерны решают конкретные проблемы** — не используйте все сразу
3. **Observability критична** — без логов, метрик и трейсов вы слепы
4. **Resilience by design** — ожидайте сбоев и готовьтесь к ним
5. **Тестируйте на правильном уровне** — пирамида тестирования

### Навигация по серии

| # | Заметка | Ключевые паттерны |
|---|---------|-------------------|
| 00 | [Overview](./00-overview.md) | Обзор и навигация |
| 01 | [Cross-cutting](./01-cross-cutting-concerns.md) | Externalized Config, Chassis |
| 02 | [Decomposition](./02-decomposition-patterns.md) | By Capability, Database per Service |
| 03 | [Data](./03-data-patterns.md) | CQRS, Event Sourcing, Outbox, Saga |
| 04 | [Communication](./04-communication-patterns.md) | Messaging, RPI, Events |
| 05 | [API](./05-api-patterns.md) | API Gateway, BFF, GraphQL |
| 06 | [Discovery](./06-discovery-patterns.md) | Client/Server-side, Registry |
| 07 | [Observability](./07-observability-patterns.md) | Tracing, Logging, Metrics, Health |
| 08 | [Resilience](./08-resilience-patterns.md) | Circuit Breaker, Retry, Bulkhead |
| 09 | [Security](./09-security-patterns.md) | JWT, mTLS, Secrets |
| 10 | [Deployment](./10-deployment-patterns.md) | Containers, Serverless, Mesh |
| 11 | [Testing](./11-testing-patterns.md) | Component, Contract, E2E |
| 12 | [UI](./12-ui-patterns.md) | Micro Frontends, Composition |

---

<div align="center">

[← Testing](./11-testing-patterns.md) | **UI Patterns** | [Обзор →](./00-overview.md)

---

**Hyper-Porto v4.3** | Microservice Patterns Series | 2026

</div>
