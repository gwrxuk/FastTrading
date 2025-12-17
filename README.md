# FastTrading

A production-grade cryptocurrency trading platform demonstrating expertise in:

- **Rust Development** - High-performance matching engine with sub-millisecond latency
- **Financial Infrastructure** - Real-time order matching, data integrity, and low-latency operations
- **AI-Powered Analytics** - Anomaly detection, risk scoring, price predictions, and portfolio analysis
- **Data Pipeline Engineering** - Kafka-based event streaming with Redis caching
- **System Integration** - CEX/DEX adapters for Binance, Uniswap, and more
- **Cloud-Native Deployment** - Kubernetes manifests and Terraform IaC for AWS
- **DevOps & Observability** - CI/CD pipelines with Prometheus, Grafana, and Jaeger
- **Database Optimization** - TimescaleDB for time-series data with continuous aggregates
- **Web3/Crypto Integration** - Wallet connection, signature verification, and blockchain interaction
- **Security & Compliance** - Encrypted secrets, rate limiting, and audit logging

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local development)
- Python 3.11+ (for local development)

### Launch with Docker

```bash
# Clone and start all services
cd FastTrading
docker-compose up -d

# Full stack with Rust services, Kafka, and observability
docker-compose -f docker-compose.full.yml up -d

# View logs
docker-compose logs -f

# Access the platform
# Frontend:         http://localhost:3000
# API Docs:         http://localhost:8000/docs
# Matching Engine:  http://localhost:8080
# Prometheus:       http://localhost:9091
# Grafana:          http://localhost:3001
# Jaeger:           http://localhost:16686
```

### Development Mode

```bash
# Start with hot-reloading
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Deploy to Kubernetes

```bash
# Apply Kubernetes manifests
kubectl apply -k k8s/overlays/production

# Or use Terraform for full AWS infrastructure
cd terraform
terraform init
terraform plan -var-file=environments/production.tfvars
terraform apply -var-file=environments/production.tfvars
```

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        NGINX / AWS ALB (Production)                       │
│                      Rate Limiting / SSL / Load Balancing                 │
└──────────────────────────────────────────────────────────────────────────┘
                                      │
         ┌────────────────────────────┼────────────────────────────┐
         ▼                            ▼                            ▼
┌─────────────────┐         ┌─────────────────┐          ┌─────────────────┐
│  NextJS Frontend│         │   FastAPI API   │          │    WebSocket    │
│  React + Wagmi  │         │   REST + Auth   │          │   Real-time     │
│  RainbowKit     │         │   Python 3.11   │          │   Price Feeds   │
└─────────────────┘         └─────────────────┘          └─────────────────┘
                                      │
                   ┌──────────────────┼──────────────────┐
                   ▼                  ▼                  ▼
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │ Rust Matching   │ │ Data Pipeline   │ │ Exchange Gateway│
         │ Engine (Axum)   │ │ (Rust + Kafka)  │ │ CEX/DEX Adapters│
         │ Sub-ms Latency  │ │ Event Streaming │ │ Binance/Uniswap │
         └─────────────────┘ └─────────────────┘ └─────────────────┘
                   │                  │                  │
    ┌──────────────┴──────────────────┴──────────────────┴──────────────┐
    │                         Message Bus                                │
    │                     Apache Kafka (MSK)                            │
    └───────────────────────────────────────────────────────────────────┘
                   │                  │                  │
         ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
         │  TimescaleDB    │ │     Redis       │ │   Prometheus    │
         │  PostgreSQL     │ │  Cache/PubSub   │ │   Grafana       │
         │  Time-Series    │ │  Session Store  │ │   Jaeger        │
         └─────────────────┘ └─────────────────┘ └─────────────────┘
```

## 💡 Key Features

### Financial Infrastructure

- **High-Performance Order Matching Engine**
  - Price-time priority matching algorithm
  - Support for Market, Limit, Stop-Limit orders
  - Sub-millisecond order processing

- **Real-time Market Data**
  - WebSocket price streaming
  - Order book depth updates
  - Trade execution notifications

- **Data Integrity**
  - PostgreSQL with optimized indexes
  - Transaction-safe order execution
  - Immutable trade audit logs

### AI-Powered Analytics

- **Anomaly Detection**
  - Volume spike identification
  - Large trade (whale) detection
  - Rapid trading pattern analysis
  - Wash trading detection
  - Market manipulation indicators

- **Risk Management**
  - Dynamic user risk scoring
  - Portfolio concentration analysis
  - Volatility exposure metrics
  - Real-time risk recommendations

- **Price Predictions**
  - Technical analysis-based forecasting
  - Moving average signals (SMA/EMA)
  - RSI and momentum indicators
  - Confidence-scored predictions

- **Portfolio Analytics**
  - Comprehensive position tracking
  - P&L analysis with metrics
  - Win rate & Sharpe ratio calculation
  - AI-generated insights and recommendations

- **Market Sentiment**
  - Buy/sell pressure analysis
  - Volume trend detection
  - Real-time sentiment scoring

### Web3 Integration

- **Multi-Wallet Support**
  - MetaMask, WalletConnect, Rainbow
  - Coinbase Wallet, and more via RainbowKit

- **Secure Wallet Binding**
  - EIP-191 signature verification
  - Nonce-based replay protection
  - Message expiration for security

- **Transaction Management**
  - Gas estimation
  - Deposit/Withdrawal tracking
  - Confirmation monitoring

### Technical Excellence

- **Async-First Architecture**
  - FastAPI with async/await
  - AsyncPG for non-blocking database
  - aioredis for async caching

- **Optimized API Performance**
  - ORJSON for fast serialization
  - GZip compression
  - Connection pooling

- **Modern Frontend**
  - NextJS 14 with App Router
  - React Query for data fetching
  - Tailwind CSS for styling
  - Lightweight Charts for trading view
  - AI Analytics Dashboard with real-time insights
  - Interactive risk visualization and sentiment gauges

## 📁 Project Structure

```
FastTrading/
├── rust-services/                    # High-performance Rust microservices
│   ├── matching-engine/              # Order matching engine
│   │   ├── src/
│   │   │   ├── orderbook.rs          # Lock-free order book
│   │   │   ├── engine.rs             # Matching logic
│   │   │   └── api.rs                # HTTP API
│   │   └── Dockerfile
│   ├── data-pipeline/                # Real-time data aggregation
│   │   ├── src/
│   │   │   ├── aggregator.rs         # OHLCV candle aggregation
│   │   │   └── consumer.rs           # Kafka consumer
│   │   └── Dockerfile
│   ├── exchange-gateway/             # CEX/DEX integrations
│   │   └── src/adapters/
│   │       ├── binance.rs            # Binance adapter
│   │       └── uniswap.rs            # Uniswap V3 adapter
│   └── common/                       # Shared types and utilities
│
├── backend/                          # Python FastAPI services
│   ├── app/
│   │   ├── api/                      # REST endpoints
│   │   │   └── endpoints/
│   │   │       └── analytics.py      # AI analytics endpoints
│   │   ├── models/                   # SQLAlchemy models
│   │   ├── schemas/
│   │   │   └── analytics.py          # AI analytics schemas
│   │   ├── services/
│   │   │   └── ai_analytics.py       # AI analytics service
│   │   └── websocket/                # Real-time handlers
│   ├── migrations/                   # Database migrations
│   ├── tests/                        # Test suite
│   └── Dockerfile
│
├── frontend/                         # NextJS React frontend
│   ├── src/
│   │   ├── app/                      # App router pages
│   │   ├── components/
│   │   │   ├── analytics/            # AI analytics components
│   │   │   │   ├── AIAnalyticsDashboard.tsx
│   │   │   │   ├── RiskScoreCard.tsx
│   │   │   │   ├── AnomalyAlerts.tsx
│   │   │   │   ├── PricePredictions.tsx
│   │   │   │   ├── PortfolioInsights.tsx
│   │   │   │   └── MarketSentiment.tsx
│   │   │   └── trading/              # Trading components
│   │   ├── hooks/
│   │   │   └── useAnalytics.ts       # Analytics React hooks
│   │   └── lib/                      # API & WebSocket clients
│   └── Dockerfile
│
├── k8s/                              # Kubernetes manifests
│   ├── base/                         # Base configurations
│   ├── services/                     # Service deployments
│   └── monitoring/                   # Prometheus, Grafana
│
├── terraform/                        # Infrastructure as Code
│   ├── main.tf                       # AWS resources
│   ├── variables.tf                  # Input variables
│   └── environments/                 # Environment configs
│
├── .github/workflows/                # CI/CD pipelines
│   ├── ci.yaml                       # Build & test
│   └── cd.yaml                       # Deploy to K8s
│
├── monitoring/                       # Observability configs
│   └── prometheus.yml
│
├── docker-compose.yml                # Basic stack
├── docker-compose.full.yml           # Full stack with Kafka
└── README.md
```

## 🔌 API Endpoints

### Authentication
```
POST /api/v1/auth/register  - Create account
POST /api/v1/auth/login     - Get JWT token
GET  /api/v1/auth/me        - Get user profile
POST /api/v1/auth/bind-wallet - Bind Ethereum wallet
```

### Trading
```
POST   /api/v1/orders       - Place order
GET    /api/v1/orders       - List orders
GET    /api/v1/orders/{id}  - Get order
DELETE /api/v1/orders/{id}  - Cancel order
GET    /api/v1/orders/book/{symbol} - Order book
```

### Market Data
```
GET /api/v1/market/price/{symbol}    - Current price
GET /api/v1/market/prices            - All prices
GET /api/v1/market/ticker/{symbol}   - 24hr stats
GET /api/v1/market/candles/{symbol}  - OHLCV data
```

### Wallet
```
POST /api/v1/wallets/sign-message  - Get sign message
POST /api/v1/wallets/bind          - Bind wallet
GET  /api/v1/wallets/balances      - Get balances
POST /api/v1/wallets/withdraw      - Create withdrawal
```

### AI Analytics
```
GET /api/v1/analytics/anomalies           - Detect trading anomalies
GET /api/v1/analytics/risk/user           - Get user risk score
GET /api/v1/analytics/predictions/{symbol} - AI price predictions
GET /api/v1/analytics/portfolio           - Portfolio analysis with insights
GET /api/v1/analytics/sentiment/{symbol}  - Market sentiment analysis
GET /api/v1/analytics/summary             - Dashboard summary
GET /api/v1/analytics/insights            - AI recommendations
GET /api/v1/analytics/metrics             - Trading performance metrics
```

## 🌐 WebSocket Channels

```javascript
// Connect
const ws = new WebSocket('ws://localhost:8000/ws?token=JWT_TOKEN');

// Subscribe to price updates
ws.send(JSON.stringify({ action: 'subscribe', channel: 'prices:ETH-USDT' }));

// Subscribe to trades
ws.send(JSON.stringify({ action: 'subscribe', channel: 'trades:ETH-USDT' }));

// Subscribe to your orders (requires auth)
ws.send(JSON.stringify({ action: 'subscribe', channel: 'orders' }));

// Subscribe to AI analytics (requires auth)
ws.send(JSON.stringify({ action: 'subscribe', channel: 'analytics:anomaly' }));
ws.send(JSON.stringify({ action: 'subscribe', channel: 'analytics:risk' }));

// Subscribe to market predictions & sentiment
ws.send(JSON.stringify({ action: 'subscribe', channel: 'analytics:predictions' }));
ws.send(JSON.stringify({ action: 'subscribe', channel: 'analytics:sentiment' }));
```

## 🔐 Security Features

- JWT authentication with configurable expiration
- BCrypt password hashing
- Rate limiting (100 req/min general, 10 order/sec trading)
- EIP-191 signature verification for wallet binding
- CORS protection
- SQL injection prevention via parameterized queries
- XSS protection headers
- AI-powered anomaly detection for suspicious trading patterns
- Wash trading and market manipulation detection
- Real-time risk monitoring and alerts

## 🛠️ Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection | `postgresql+asyncpg://...` |
| `REDIS_URL` | Redis connection | `redis://redis:6379/0` |
| `SECRET_KEY` | JWT signing key | (required) |
| `ETH_NODE_URL` | Ethereum RPC endpoint | Infura |
| `WALLETCONNECT_PROJECT_ID` | WalletConnect project | (optional) |

## 📊 Performance Optimizations

### Rust Matching Engine
- Lock-free order book with atomic operations
- Price-time priority with heap-based queues
- Sub-millisecond order matching latency
- Zero-copy message passing

### Backend (Python)
- Connection pooling (20 connections)
- Async database operations with asyncpg
- Redis caching for hot data
- ORJSON for fast serialization

### AI Analytics
- Real-time anomaly detection with statistical analysis
- Dynamic risk scoring with weighted factors
- Technical indicator calculations (RSI, SMA, momentum)
- Portfolio analysis with Sharpe ratio and drawdown metrics
- Market sentiment analysis from order flow

### Database (TimescaleDB)
- Hypertables for time-series data
- Continuous aggregates for OHLCV candles
- Automatic data compression (7+ days)
- Retention policies (365 days for trades)

### Frontend
- React Query with smart caching
- Debounced WebSocket updates
- Virtualized lists for large datasets
- Code splitting and lazy loading

### Infrastructure
- Kubernetes HPA for auto-scaling
- Pod anti-affinity for HA
- CPU-optimized nodes for trading workloads
- Multi-AZ deployment

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest -v

# Frontend tests  
cd frontend
npm run test
```

## 📦 Deployment

### Production with Docker

```bash
# Build and deploy
docker-compose --profile production up -d

# With SSL (configure nginx/ssl/)
docker-compose --profile production up -d nginx
```

### Kubernetes

Kubernetes manifests available in `k8s/` directory (coming soon).

## 📄 License

MIT License - see LICENSE file for details.

---

Built with ❤️ for the crypto trading community

