# 📊 SaaS Analytics PoC — Evaluación Técnica: Ingeniero de Innovación

> **Prueba Técnica | Analítica de Datos**  
> Modalidad: Remota Individual | Stack: Python + Power BI | Duración: ~90 min

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Arquitectura del Proyecto](#arquitectura-del-proyecto)
3. [Instalación y Ejecución](#instalación-y-ejecución)
4. [Modelo de Datos](#modelo-de-datos)
5. [KPIs Definidos y Justificación](#kpis-definidos-y-justificación)
6. [Insights Principales](#insights-principales)
7. [Diseño del Dashboard Power BI](#diseño-del-dashboard-power-bi)
8. [Recomendaciones de Negocio](#recomendaciones-de-negocio)

---

## Resumen Ejecutivo

Este repositorio contiene una **Prueba de Concepto (PoC) analítica completa** para un cliente SaaS que desea mejorar su toma de decisiones sobre producto y usuarios.

El análisis cubre **18 meses de datos simulados** (~2,500 usuarios, ~212,000 eventos, ~10,000 transacciones) y responde tres preguntas clave:

| Pregunta | Respuesta Encontrada |
|---|---|
| ¿Qué métricas importan? | MRR, Tasa de Activación, Error Rate por Plan, Feature Adoption |
| ¿Qué problemas existen? | Alta fricción en plan Free (18% error rate), baja conversión Free→Paid (7.5%), caída de retención mes 12 |
| ¿Dónde enfocar esfuerzos? | Activación de usuarios Free, reducción de errores, monetización de power users |

---

## Arquitectura del Proyecto

```
saas_analytics/
│
├── data/
│   ├── raw/                    # Datasets originales generados
│   │   ├── users.csv
│   │   ├── events.csv
│   │   └── transactions.csv
│   └── processed/              # Datasets limpios para BI
│       ├── users_enriched.csv
│       ├── events_enriched.csv
│       ├── transactions_enriched.csv
│       ├── feature_adoption.csv
│       ├── monthly_revenue.csv
│       ├── geo_summary.csv
│       ├── plan_summary.csv
│       └── kpi_summary.json
│
├── src/
│   ├── generate_data.py        # Generación de datasets realistas
│   └── eda_and_kpis.py         # EDA completo + cómputo de KPIs
│
├── dashboard/
│   └── saas_analytics.pbix     # Dashboard Power BI (ver instrucciones)
│
├── docs/
│   └── insights_report.md      # Reporte narrativo de hallazgos
│
└── README.md                   # Este archivo
```

---

## Instalación y Ejecución

### Requisitos
```
Python >= 3.9
pandas >= 2.0
numpy >= 1.24
faker >= 20.0
```

### Paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/saas-analytics-poc.git
cd saas-analytics-poc

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate   # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Generar datasets
python src/generate_data.py

# 5. Ejecutar EDA y KPIs
python src/eda_and_kpis.py

# 6. Abrir dashboard (requiere Power BI Desktop)
# Archivo: dashboard/saas_analytics.pbix
# Fuente: data/processed/ (ruta relativa)
```

---

## Modelo de Datos

### Diagrama Relacional

```
users (user_id PK)
  ├── events (user_id FK) ──── N eventos por usuario
  └── transactions (user_id FK) ──── N transacciones por usuario
```

### Descripción de Campos

**users.csv**
| Campo | Tipo | Descripción | Notas |
|---|---|---|---|
| user_id | string | PK único | Formato: U00001 |
| signup_date | date | Fecha de registro | Rango: jul 2023 – dic 2024 |
| country | string | País del usuario | 8 países LATAM + España + USA |
| plan | string | Tipo de plan | Free / Basic / Pro |
| is_active | bool | Usuario activo | Proxy de engagement |

**events.csv**
| Campo | Tipo | Descripción | Notas |
|---|---|---|---|
| event_id | string | PK único | Formato: E0000001 |
| user_id | string | FK a users | |
| event_type | string | Tipo de evento | login / feature_use / error / upgrade |
| event_date | date | Fecha del evento | |
| feature_name | string | Funcionalidad usada | Null si no aplica |

**transactions.csv**
| Campo | Tipo | Descripción | Notas |
|---|---|---|---|
| transaction_id | string | PK único | Formato: T0000001 |
| user_id | string | FK a users | |
| amount | float | Monto en USD | 0 si status=failed |
| transaction_date | date | Fecha de cobro | Mensual recurrente |
| status | string | Estado | completed / failed |

### Supuestos del Modelo

> ⚠️ **Supuesto 1**: `is_active` en users.csv es un flag estático (no calculado en tiempo real). En producción, debería ser dinámico (ej: activo = logueó en los últimos 30 días).

> ⚠️ **Supuesto 2**: Los precios son fijos (Basic: $29/mes, Pro: $89/mes). No se modelan upgrades mid-cycle ni proration.

> ⚠️ **Supuesto 3**: No hay tabla de `sessions` explícita; se infieren sesiones a partir de eventos `login`.

---

## KPIs Definidos y Justificación

Se definieron **10 KPIs agrupados en 4 dimensiones**:

### Dimensión 1: Salud del Negocio (Revenue)

| KPI | Valor | Justificación |
|---|---|---|
| MRR (Avg 3 meses) | $35,167 | Métrica base de cualquier SaaS. Predice flujo de caja y growth. |
| Revenue Total (18m) | $481,036 | Valida la simulación; permite calcular ARPU. |
| Transaction Success Rate | 95.83% | Tasa de fallo de cobro impacta directamente el MRR real. |

### Dimensión 2: Adquisición y Retención de Usuarios

| KPI | Valor | Justificación |
|---|---|---|
| Tasa de Activación | 63.6% | Mide qué fracción de la base registrada genera valor. |
| Retención M12 | 51.5% | Benchmark SaaS saludable: >40% a 12 meses. |
| Upgrade CVR (Free→Paid) | 7.47% | Palanca de crecimiento más rentable en freemium. |

### Dimensión 3: Producto y Engagement

| KPI | Valor | Justificación |
|---|---|---|
| Feature Adoption Rate | Variable por feature | Identifica qué features generan valor real. |
| Error Rate Global | 9.43% | Proxy de fricción/bugs; afecta retención. |
| Error Rate en Free | 18.1% | Señal crítica: el plan de captación tiene el peor UX. |

### Dimensión 4: Segmentación

| KPI | Valor | Justificación |
|---|---|---|
| Power Users (top 10%) | 71% son Pro | Identifica el perfil ideal para upsell y advocacy. |

---

## Insights Principales

### 🔴 INSIGHT 1 — Alta Fricción en el Plan Free (Crítico)

- El plan Free tiene una **tasa de error del 18.1%**, casi el doble que Basic (10%) y cuatro veces más que Pro (5.1%).
- Esto significa que el primer contacto del usuario con el producto es el más propenso a errores.
- **Impacto**: Reduce conversión Free→Paid porque el usuario abandona antes de experimentar el valor.
- **Acción**: Auditar las features disponibles en Free para detectar errores de integración o de onboarding. Priorizar una mejora de la experiencia en las primeras 48 horas.

### 🔴 INSIGHT 2 — Caída de Retención a los 12 Meses (Crítico)

- La retención cae a **51.5% en el mes 12**, lo que indica un evento de "fatiga" o pérdida de valor percibido a largo plazo.
- No hay suficientes features avanzadas o casos de uso para mantener el engagement pasado el año.
- **Acción**: Diseñar un programa de "re-engagement" en el mes 10-11 (new features, webinars, cases de uso avanzados).

### 🟡 INSIGHT 3 — API Integration está Sub-utilizada (Oportunidad)

- `api_integration`, `scheduled_reports` y `team_collaboration` tienen **adoption rate < 24%** a pesar de ser features exclusivas de Pro.
- Los Pro users que SÍ las usan generan más sesiones (power users).
- **Acción**: Programa de enablement/onboarding específico para estas features en las primeras 2 semanas del plan Pro. Potencial de aumentar retención Pro significativamente.

### 🟡 INSIGHT 4 — Chile y LATAM son el Core, pero USA tiene Mayor Activación (Oportunidad)

- Chile representa el 29% de la base de usuarios.
- USA, con solo 68 usuarios, tiene **72% de tasa de activación** (vs 62-67% del resto).
- **Acción**: Investigar qué diferencia al segmento USA (perfil, uso de features, soporte). Si el patrón escala, puede ser un mercado prioritario de expansión.

### 🟢 INSIGHT 5 — MRR en Crecimiento Sostenido (Positivo)

- El MRR creció de ~$33K a ~$52K entre julio 2024 y noviembre 2024 (+58%).
- El crecimiento es orgánico y constante, sin picos artificiales.
- **Acción**: Mantener el momentum. Modelar el punto de inflexión donde se justifica inversión en Sales.

---

## Diseño del Dashboard Power BI

### Página 1 — Executive Overview

**Objetivo**: Vista C-Level. Una pantalla, máxima claridad.

Componentes:
- **4 KPI Cards** (grande, top): MRR, Usuarios Activos, Transaction Success Rate, Error Rate
- **Line Chart**: Evolución MRR mensual (18 meses)
- **Donut Chart**: Distribución por plan (Free/Basic/Pro)
- **Slicer**: Período de tiempo (mes/trimestre)

### Página 2 — User Analysis

**Objetivo**: Segmentación de usuarios para marketing y producto.

Componentes:
- **Map Visual**: Usuarios por país (bubble size = usuarios, color = tasa de activación)
- **Stacked Bar**: Usuarios por plan + estado (activo/inactivo) por país
- **Matrix**: Plan × País con métricas cruzadas
- **Slicer**: Plan, País, Estado

### Página 3 — Product & Feature Adoption

**Objetivo**: Visibilidad de qué funcionalidades generan valor.

Componentes:
- **Horizontal Bar**: Feature adoption rate (ordenado por uso)
- **Clustered Bar**: Errores por plan (comparativa directa)
- **Line**: Sesiones promedio por mes (trend de engagement)
- **Scatter**: Usuarios por sesiones vs plan (identificar power users)

### Página 4 — Revenue Deep Dive

**Objetivo**: Análisis financiero para el CFO o equipo de growth.

Componentes:
- **Waterfall Chart**: Composición del MRR (por plan)
- **Line**: Comparativa MRR Real vs MRR Teórico (detectar churn implícito)
- **Bar**: Transacciones fallidas por mes
- **KPI**: ARPU por plan

### Medidas DAX Clave (Power BI)

```dax
-- MRR Real
MRR_Real = 
CALCULATE(
    SUM(transactions_enriched[amount]),
    transactions_enriched[status] = "completed",
    DATESMTD(transactions_enriched[transaction_date])
)

-- Tasa de Activación
Activation_Rate = 
DIVIDE(
    COUNTROWS(FILTER(users_enriched, users_enriched[is_active] = TRUE())),
    COUNTROWS(users_enriched)
)

-- Error Rate por Plan
Error_Rate = 
DIVIDE(
    CALCULATE(COUNTROWS(events_enriched), events_enriched[event_type] = "error"),
    CALCULATE(COUNTROWS(events_enriched), events_enriched[event_type] = "login")
)

-- ARPU
ARPU = DIVIDE([MRR_Real], [Active_Paying_Users])
```

---

## Recomendaciones de Negocio

### Prioridad Alta

1. **Fix el onboarding del plan Free** — Reducir el error rate de 18% a <10% puede aumentar la conversión Free→Paid en ~2-3 pp. Impacto estimado: +$5K MRR en 6 meses.

2. **Programa de re-engagement en mes 10** — Enviar comunicaciones proactivas, ofrecer features nuevas o descuentos de upgrade antes de que el usuario llegue al año. Objetivo: mejorar retención M12 de 51% a 65%.

### Prioridad Media

3. **Enablement de features Pro sub-utilizadas** — `api_integration` y `team_collaboration` tienen solo 24% de adopción entre usuarios Pro. Un onboarding guiado en semana 1-2 puede aumentar el stickiness y reducir churn Pro.

4. **Investigar segmento USA** — 72% de activación sugiere un perfil de usuario distinto. Análisis cualitativo + expansión experimental.

### Prioridad Baja

5. **Reducir transacciones fallidas** — 4.2% de fallos de pago. Implementar retry automático y notificaciones puede recuperar ~$18K/año.

---