# Professional-Grade BTC Options Agent Roadmap

This document describes the major upgrades implemented to showcase the
project as a production-ready BTC options trading agent.

## Highlights

- **Institutional Data Pipeline** – A Deribit-focused client with retry
  logic, disk caching, and historical backfill utilities lives in
  `bot/data`. The `MarketDataPipeline` exposes clean helper methods for
  fetching option instruments, order books, and trades for downstream
  analytics.
- **Composable Agent Infrastructure** – The `bot/infrastructure`
  scheduler introduces typed async channels that prevent cross-talk
  between components and make it trivial to add health checks and
  metrics.
- **Research-Grade Analytics** – The enhanced smirk analytics module now
  supports higher-order IV moments, surface fitting, and regime detection
  to demonstrate quantitative depth.
- **Modular Strategy & Risk** – A new strategy engine accepts arbitrary
  feature providers and produces risk-aware signals. Risk tooling includes
  Kelly sizing, CVaR helpers, and markdown risk reports for daily ops.
- **Execution, Backtesting, and Observability** – Skeleton execution
  adapters, walk-forward backtesting helpers, and a lightweight metrics
  registry round out the production story.

## Next Steps

1. Wire the new modules into the existing `AgentManager` orchestration.
2. Replace mock data usage in pipelines/tests with the Deribit client via
   API credentials.
3. Add CI workflows to execute the new analytics and backtesting tests.
4. Extend the observability layer with an HTTP exporter (Prometheus or
   OpenTelemetry).

These foundations make it straightforward to keep iterating and to speak
about a cohesive architecture during interviews.
