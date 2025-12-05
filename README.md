<div align="center">

# 🏥 Healthcare Chatbot

**An intelligent, evidence-based healthcare assistant powered by RAG, Graph Databases, and LLMs**

[![Version](https://img.shields.io/badge/version-1.0.0-4CAF50?style=for-the-badge&logo=github)](https://github.com)
[![License](https://img.shields.io/badge/license-MIT-4CAF50?style=for-the-badge&logo=open-source-initiative)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)

[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Neo4j](https://img.shields.io/badge/Neo4j-008CC1?style=for-the-badge&logo=neo4j&logoColor=white)](https://neo4j.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-FF6B6B?style=for-the-badge)](https://www.trychroma.com/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)

---

### 🚀 Quick Navigation

[📋 Features](#-features) • [🛠️ Tech Stack](#️-tech-stack) • [🏗️ Architecture](#️-architecture) • [🚀 Installation](#-installation) • [💻 Usage](#-usage) • [📚 API Docs](#-api-documentation)

---

</div>

## 📖 Overview

> **Healthcare Chatbot** is a production-ready, intelligent healthcare assistant that provides evidence-based medical information and guidance. Built with cutting-edge AI technologies, it combines **Retrieval Augmented Generation (RAG)**, **Graph Database Intelligence**, and **Large Language Models** to deliver accurate, contextual, and safe healthcare responses.

### ✨ Key Highlights

<table>
<tr>
<td width="50%">

#### 🧠 **Intelligent Knowledge Retrieval**
- Vector-based semantic search across **110+ medical documents**
- Real-time citation and source attribution
- Domain-specific knowledge organization

</td>
<td width="50%">

#### 🕸️ **Graph-Powered Reasoning**
- Neo4j-powered medical reasoning
- Real-time safety checks and contraindications
- Red flag detection for critical conditions

</td>
</tr>
<tr>
<td width="50%">

#### 🔒 **Enterprise-Grade Security**
- JWT authentication with HTTP-only cookies
- Role-based access control (RBAC)
- Comprehensive input validation

</td>
<td width="50%">

#### ⚡ **High Performance**
- Multi-level caching (Redis + Browser)
- Connection pooling and optimized queries
- Real-time response generation

</td>
</tr>
</table>

---

## ✨ Features

### 🎯 Core Capabilities

<details>
<summary><b>1. 🧠 Hybrid RAG (Retrieval Augmented Generation)</b> - Click to expand</summary>

#### What it does:
- **Vector-based semantic search** using ChromaDB
- **110+ curated medical documents** from WHO, NHS, ICMR
- **Automatic citation** and source attribution
- **Domain-specific** knowledge organization

#### Why it matters:
- ✅ Evidence-based responses from verified sources
- ✅ Fast semantic search (not just keyword matching)
- ✅ Handles complex medical queries intelligently
- ✅ Transparent source citations for every response

</details>

<details>
<summary><b>2. 🕸️ Graph Database Intelligence (Neo4j)</b> - Click to expand</summary>

#### What it does:
- **Structured medical knowledge** as nodes and relationships
- **Real-time safety checks** and contraindication detection
- **Red flag identification** for critical conditions
- **Healthcare provider discovery** by location and specialty

#### Why it matters:
- ✅ Instant safety validation for medications/actions
- ✅ Critical condition detection and alerts
- ✅ Provider recommendations based on needs
- ✅ Fallback system ensures reliability

</details>

<details>
<summary><b>3. 🌐 Multi-Language Support</b> - Click to expand</summary>

#### Supported Languages:
- 🇬🇧 English
- 🇮🇳 Hindi
- 🇮🇳 Tamil
- 🇮🇳 Telugu
- 🇮🇳 Kannada
- 🇮🇳 Malayalam

#### Features:
- ✅ Automatic language detection
- ✅ Language-specific response generation
- ✅ Seamless multilingual conversations

</details>

<details>
<summary><b>4. 🛡️ Intelligent Safety System</b> - Click to expand</summary>

#### Safety Features:
- **Real-time safety flag detection**
- **Medical disclaimer integration**
- **Emergency guidance** for critical symptoms
- **Pregnancy-specific alerts** and recommendations

#### Protection Layers:
- ✅ Input validation and sanitization
- ✅ Output safety checks
- ✅ Medical disclaimers on every response
- ✅ Emergency contact guidance

</details>

<details>
<summary><b>5. 💾 Persistent Chat History</b> - Click to expand</summary>

#### Features:
- **Full conversation tracking** with PostgreSQL
- **Session management** and context preservation
- **Searchable chat history** with semantic search
- **Message metadata** and citations storage

#### Benefits:
- ✅ Review past health conversations
- ✅ Clinical value for healthcare providers
- ✅ Analytics and trend analysis
- ✅ Compliance and audit trail

</details>

<details>
<summary><b>6. 🔐 Enterprise Authentication</b> - Click to expand</summary>

#### Security Features:
- **JWT-based authentication** with HTTP-only cookies
- **Role-based access control** (Admin, User)
- **Secure password hashing** with bcrypt
- **Refresh token mechanism** for session management

#### Security Layers:
- ✅ Token-based authentication
- ✅ Secure cookie storage
- ✅ Password encryption
- ✅ Session management

</details>

<details>
<summary><b>7. ⚡ High-Performance Caching</b> - Click to expand</summary>

#### Caching Strategy:
- **Redis caching** for frequently accessed data
- **Browser localStorage** for instant UI updates
- **Multi-level cache invalidation** strategy
- **Optimized database queries**

#### Performance Benefits:
- ✅ Reduced database load
- ✅ Faster response times
- ✅ Improved user experience
- ✅ Scalable architecture

</details>

<details>
<summary><b>8. 🎨 Modern User Interface</b> - Click to expand</summary>

#### UI Features:
- **Beautiful, responsive design** with Tailwind CSS
- **Real-time chat interface** with markdown support
- **Chat history sidebar** with search functionality
- **Session management** and deletion
- **Loading states** and error handling

#### Design Highlights:
- ✅ Dark theme with emerald accents
- ✅ Smooth animations and transitions
- ✅ Mobile-responsive design
- ✅ Accessible and user-friendly

</details>

<details>
<summary><b>9. 👤 Health Profile Management</b> - Click to expand</summary>

#### Profile Features:
- **User health profile storage**
- **Medical conditions tracking**
- **Personalized recommendations** based on profile

#### Personalization:
- ✅ Customized health advice
- ✅ Condition-specific guidance
- ✅ Profile-based safety checks

</details>

<details>
<summary><b>10. 👍 Message Feedback System</b> - Click to expand</summary>

#### Feedback Features:
- **Thumbs up/down feedback** on assistant responses
- **Persistent storage** with foreign key constraints
- **Feedback persistence** across page reloads
- **Cache invalidation** for data consistency

#### Benefits:
- ✅ User engagement and satisfaction tracking
- ✅ Quality improvement insights
- ✅ Response accuracy monitoring

</details>

<details>
<summary><b>11. 🎯 Intelligent IP-Based User Routing</b> - Click to expand</summary>

#### Routing Features:
- **Smart user routing** based on IP tracking and authentication status
- **Three-tier redirect logic** for new users, returning users, and authenticated users
- **Fast IP lookup** with Redis caching (~1-5ms response time)
- **Session expiration handling** with clear user messaging

#### Routing Logic:
- ✅ **New users** → Redirected to landing page
- ✅ **Returning users with expired sessions** → Redirected to auth with "session expired" message
- ✅ **Authenticated users** → Seamless access to main application

#### Performance:
- ✅ Redis-cached IP lookups for minimal latency
- ✅ Async database updates (non-blocking)
- ✅ Proxy/load balancer support (X-Forwarded-For headers)
- ✅ Analytics-ready IP tracking

</details>
- ✅ Quality improvement through feedback analytics
- ✅ Data integrity with proper database constraints
- ✅ Seamless user experience with persistent feedback

</details>

<details>
<summary><b>11. 🛡️ Enhanced Security</b> - Click to expand</summary>

#### Security Features:
- **Comprehensive SQL injection detection** (1900+ patterns)
- **1924 test cases** with 100% pass rate
- **Zero false positives** - legitimate queries never blocked
- **Zero false negatives** - all injection attempts detected

#### Protection:
- ✅ Advanced injection detection (time-based, boolean-based)
- ✅ Well-tested patterns for production security
- ✅ Comprehensive coverage of attack vectors
- ✅ Battle-tested for real-world security

</details>

<details>
<summary><b>12. 🚪 Improved Logout & Session Management</b> - Click to expand</summary>

#### Logout Features:
- **Backend logout endpoint** with proper token revocation
- **Comprehensive logging** for monitoring and debugging
- **Clean session termination** with cookie clearing
- **Error handling** with graceful fallback

#### Benefits:
- ✅ Proper token revocation on logout
- ✅ Backend logging for security monitoring
- ✅ Clean session cleanup
- ✅ Reliable logout even if backend call fails

</details>

---

## 🛠️ Tech Stack

### 🔧 Backend Technologies

<table>
<tr>
<th>Category</th>
<th>Technology</th>
<th>Version</th>
</tr>
<tr>
<td><strong>Framework</strong></td>
<td>FastAPI</td>
<td>0.110.0</td>
</tr>
<tr>
<td><strong>Language</strong></td>
<td>Python</td>
<td>3.11+</td>
</tr>
<tr>
<td><strong>Database</strong></td>
<td>PostgreSQL (NeonDB)</td>
<td>Latest</td>
</tr>
<tr>
<td><strong>Vector DB</strong></td>
<td>ChromaDB</td>
<td>0.5.3</td>
</tr>
<tr>
<td><strong>Graph DB</strong></td>
<td>Neo4j</td>
<td>5.28.0</td>
</tr>
<tr>
<td><strong>Cache</strong></td>
<td>Redis</td>
<td>5.0.1</td>
</tr>
<tr>
<td><strong>LLM</strong></td>
<td>OpenAI GPT-4 / GPT-3.5</td>
<td>Latest</td>
</tr>
<tr>
<td><strong>Authentication</strong></td>
<td>JWT (python-jose, PyJWT)</td>
<td>Latest</td>
</tr>
<tr>
<td><strong>Validation</strong></td>
<td>Pydantic</td>
<td>2.7.1</td>
</tr>
</table>

### 🎨 Frontend Technologies

<table>
<tr>
<th>Category</th>
<th>Technology</th>
<th>Version</th>
</tr>
<tr>
<td><strong>Framework</strong></td>
<td>Next.js</td>
<td>14.2.6 (App Router)</td>
</tr>
<tr>
<td><strong>Language</strong></td>
<td>TypeScript</td>
<td>5.4</td>
</tr>
<tr>
<td><strong>Styling</strong></td>
<td>Tailwind CSS</td>
<td>3.4</td>
</tr>
<tr>
<td><strong>Icons</strong></td>
<td>Lucide React</td>
<td>Latest</td>
</tr>
<tr>
<td><strong>Markdown</strong></td>
<td>React Markdown + KaTeX</td>
<td>Latest</td>
</tr>
<tr>
<td><strong>HTTP Client</strong></td>
<td>Axios</td>
<td>1.13.2</td>
</tr>
</table>

### 🚀 DevOps & Tools

- **Package Manager**: npm / pnpm
- **Environment**: python-dotenv
- **Testing**: pytest 8.3.3
- **Code Quality**: ESLint, TypeScript
- **Version Control**: Git

---

## 🏗️ Architecture

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         🖥️ CLIENT LAYER (Next.js)                           │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │   🏠 Landing  │  │   🔐 Auth   │  │   💬 Chat    │  │   🔍 Search │   │
│  │    Page      │  │    Page     │  │  Interface │  │    Modal     │   │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘   │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                    React Components & State Management                │   │
│  │  • ChatMessage • ProfileCard • TopicSuggestions • WelcomeScreen     │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────┬───────────────────────────────────────┘
                                        │
                                ┌───────▼────────┐
                                │   HTTP/REST    │
                                │   (Axios)      │
                                │   Port: 3000   │
                                └───────┬────────┘
                                        │
┌───────────────────────────────────────▼───────────────────────────────────┐
│                    ⚙️ API LAYER (FastAPI - Python)                          │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      Middleware & Security                            │  │
│  │  • CORS • Rate Limiting • JWT Auth • Input Validation                │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   🔐 Auth    │  │   💬 Chat    │  │   👨‍💼 Admin   │  │   📊 Health  │  │
│  │   Routes    │  │   Routes     │  │   Routes     │  │   Routes     │  │
│  │              │  │              │  │              │  │              │  │
│  │ • Register  │  │ • Send Msg   │  │ • List Users │  │ • Get Profile│  │
│  │ • Login     │  │ • Get History│  │ • Manage     │  │ • Update     │  │
│  │ • Logout    │  │ • Sessions   │  │              │  │              │  │
│  └──────────────┘  └──────┬───────┘  └──────────────┘  └──────────────┘  │
│                            │                                               │
│  ┌─────────────────────────▼───────────────────────────────────────────┐  │
│  │                    🧠 BUSINESS LOGIC LAYER                           │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │  🔍 RAG      │  │  🕸️ Graph    │  │  🤖 LLM       │              │  │
│  │  │  Service     │  │  Service     │  │  Service      │              │  │
│  │  │              │  │              │  │              │              │  │
│  │  │ • Vector     │  │ • Safety     │  │ • OpenAI     │              │  │
│  │  │   Search     │  │   Checks     │  │   API        │              │  │
│  │  │ • Citations  │  │ • Red Flags  │  │ • Response   │              │  │
│  │  │ • Context    │  │ • Providers  │  │   Generation │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  │                                                                       │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │  │
│  │  │  🛡️ Safety   │  │  🌐 Language │  │  ⚡ Cache    │              │  │
│  │  │  Service     │  │  Service     │  │  Service     │              │  │
│  │  │              │  │              │  │              │              │  │
│  │  │ • Validation │  │ • Detection  │  │ • Redis      │              │  │
│  │  │ • Flags      │  │ • Translation│  │ • Invalidation│            │  │
│  │  │ • Disclaimers│ │              │  │              │              │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │  │
│  └─────────────────────────────────────────────────────────────────────┘  │
└───────┬───────────────┬───────────────┬───────────────┬───────────────┬───┘
        │               │               │               │               │
┌───────▼──────┐  ┌─────▼──────┐  ┌─────▼──────┐  ┌────▼──────┐  ┌───▼──────┐
│  🐘 PostgreSQL │  │  🔍 ChromaDB  │  │  🕸️ Neo4j   │  │  ⚡ Redis   │  │  🤖 OpenAI│
│   (NeonDB)    │  │   (Vector)    │  │  (Graph)    │  │  (Cache)   │  │  (LLM)   │
│               │  │              │  │            │  │            │  │          │
│ • 👥 Users    │  │ • 📚 Medical │  │ • 🔴 Red   │  │ • 💾 Sessions│ │ • GPT-4  │
│ • 💬 Sessions │  │   Knowledge │  │   Flags    │  │ • 📝 Messages│ │ • GPT-3.5│
│ • 📝 Messages │  │ • 🔢 Embeddings│ │ • 🏥 Providers│ │ • 💬 Responses│ │ • Embeddings│
│ • 🔐 Tokens   │  │ • 📄 110+ Docs│ │ • ⚠️ Safety │  │ • ⚡ Fast     │  │          │
│ • 👤 Profiles │  │              │  │   Rules    │  │   Access    │  │          │
└───────────────┘  └──────────────┘  └─────────────┘  └────────────┘  └──────────┘
```

### 🔄 Request Flow Diagram

```
┌─────────────┐
│   👤 User    │
│   Query      │
└──────┬───────┘
       │
       ▼
┌─────────────────┐
│  🖥️ Frontend     │
│  • Validate     │
│  • Format       │
└──────┬──────────┘
       │ HTTP POST /chat
       ▼
┌─────────────────┐
│  🔐 Auth        │
│  • JWT Verify   │
│  • User Check   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  ⚙️ Processing  │
│  • Lang Detect  │
│  • Input Valid  │
└──────┬──────────┘
       │
       ├─────────────────┬─────────────────┐
       ▼                 ▼                 ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  🔍 RAG      │  │  🕸️ Graph    │  │  ⚡ Cache    │
│  Service     │  │  Service     │  │  Check      │
│              │  │              │  │              │
│  • Vector    │  │  • Safety   │  │  • Redis     │
│    Search    │  │    Checks   │  │  • Browser   │
│  • Context   │  │  • Red Flags│  │              │
└──────┬───────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  🤖 LLM Service  │
                │  • OpenAI API    │
                │  • Context Merge │
                │  • Generation    │
                └────────┬─────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  🛡️ Safety      │
                │  • Validation   │
                │  • Disclaimers  │
                │  • Citations    │
                └────────┬─────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  💾 Storage     │
                │  • PostgreSQL   │
                │  • Redis Cache │
                └────────┬─────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  📤 Response     │
                │  • JSON Format  │
                │  • Citations    │
                │  • Metadata    │
                └────────┬─────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  🖥️ Frontend     │
                │  • Render       │
                │  • Update UI    │
                └─────────────────┘
```

### 📊 Component Interaction Flow

**Step-by-Step Process:**

1. **👤 User Query** 
   - User types question in chat interface
   - Frontend validates and formats request

2. **🔐 Authentication** 
   - JWT token sent in Authorization header
   - Backend validates token and extracts user info
   - User permissions checked

3. **⚙️ Query Processing** 
   - Language detection (auto-detect or user-specified)
   - Input validation and sanitization
   - SQL injection and XSS prevention

4. **🔍 Knowledge Retrieval (Parallel)**
   - **RAG Path**: ChromaDB vector search → Retrieve relevant medical documents
   - **Graph Path**: Neo4j Cypher queries → Safety checks, red flags, contraindications
   - **Cache Check**: Redis lookup for recent similar queries

5. **🤖 LLM Generation** 
   - Context from RAG and Graph merged
   - OpenAI API called with prompt + context
   - Response generated with citations

6. **🛡️ Response Processing** 
   - Safety validation on generated response
   - Medical disclaimers added
   - Citations formatted and attached
   - Facts extracted and structured

7. **💾 Storage** 
   - Message saved to PostgreSQL (user message + assistant response)
   - Session updated/created
   - Response cached in Redis (5 min TTL)
   - Browser cache updated (localStorage)

8. **📤 Response Delivery** 
   - JSON response sent to frontend
   - Frontend renders markdown, citations, safety info
   - UI updated with new message
   - Chat history refreshed

### 🔗 External Services Integration

```
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  🤖 OpenAI    │  │  🐘 NeonDB   │  │  🕸️ Neo4j     │     │
│  │  (LLM API)    │  │  (PostgreSQL)│  │  (Graph DB)   │     │
│  │               │  │              │  │              │     │
│  │ • GPT-4       │  │ • Managed    │  │ • Cloud/     │     │
│  │ • GPT-3.5     │  │   Database   │  │   Self-hosted│     │
│  │ • Embeddings  │  │ • Auto-scaling│ │ • Cypher     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │  ⚡ Redis     │  │  🔍 ChromaDB  │                        │
│  │  (Cache)      │  │  (Vector DB)  │                        │
│  │               │  │              │                        │
│  │ • Upstash     │  │ • Local      │                        │
│  │ • Self-hosted │  │ • Persistent │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Installation

### 📋 Prerequisites

Before you begin, ensure you have the following installed:

- ✅ **Python** 3.11 or higher
- ✅ **Node.js** 18+ and npm/pnpm
- ✅ **PostgreSQL** database (NeonDB recommended)
- ✅ **Neo4j** database (optional, has fallback)
- ✅ **Redis** server (optional, for caching)
- ✅ **OpenAI** API key

### 📥 Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/healthcare-chatbot.git
cd healthcare-chatbot
```

### 🐍 Step 2: Backend Setup

```bash
# Navigate to API directory
cd api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

> 💡 **Tip**: Make sure your virtual environment is activated before installing dependencies.

### ⚛️ Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
# or
pnpm install
```

### ⚙️ Step 4: Environment Configuration

Create a `.env` file in the `api/` directory:

```env
# 🗄️ Database Configuration
DATABASE_URL=postgresql://user:password@host:port/database

# 🕸️ Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# ⚡ Redis Configuration
REDIS_URL=redis://localhost:6379
# or for Upstash
UPSTASH_REDIS_REST_URL=https://your-redis-url.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token

# 🤖 OpenAI Configuration
OPENAI_API_KEY=sk-your-openai-api-key

# 🔐 JWT Configuration
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# 🌐 Application Configuration
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:3000
```

> ⚠️ **Important**: Never commit your `.env` file to version control!

### 🗄️ Step 5: Database Setup

```bash
# Run database migrations to create all tables
cd api
python scripts/create_tables.py

# Or run individual migration for IP tracking (optional, included in create_tables.py)
python scripts/create_ip_addresses_table.py
cd api
python scripts/create_tables.py

# Create admin user (optional)
python scripts/create_admin_user.py
```

### 📚 Step 6: Build RAG Index

```bash
# Build ChromaDB index from medical documents
cd api
python rag/build_index.py
```

> ⏱️ **Note**: This process may take a few minutes depending on the number of documents.

---

## ⚙️ Configuration

### 🔧 Backend Configuration

The backend server runs on port `8000` by default. You can change this in `api/start_server.py` or by setting the `PORT` environment variable.

```bash
export PORT=8000  # Linux/macOS
set PORT=8000     # Windows
```

### 🎨 Frontend Configuration

The frontend runs on port `3000` by default. Update `frontend/utils/api.ts` if your backend is on a different port.

### 🕸️ Neo4j Fallback

If Neo4j is unavailable, the system automatically uses an in-memory fallback. This ensures the application continues to function even without the graph database.

> ✅ **Reliability**: The system gracefully handles Neo4j unavailability.

---

## 💻 Usage

### 🚀 Starting the Backend

```bash
cd api
python start_server.py
# or
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API Endpoints:**
- 🌐 API: `http://localhost:8000`
- 📚 Swagger UI: `http://localhost:8000/docs`
- 📖 ReDoc: `http://localhost:8000/redoc`

### 🎨 Starting the Frontend

```bash
cd frontend
npm run dev
# or
pnpm dev
```

**Frontend:**
- 🌐 Application: `http://localhost:3000`

### 📱 Using the Application

1. **🏠 Landing Page**: Visit `http://localhost:3000` - New users will see the landing page
2. **🔐 Authentication**: Click "Get Started" to register/login
   - **New users**: Redirected to landing page
   - **Returning users with expired sessions**: Redirected to auth with "session expired" message
   - **Authenticated users**: Direct access to chat interface
3. **💬 Chat Interface**: After authentication, you'll be redirected to the chat interface
4. **❓ Ask Questions**: Type your health-related questions in the chat
5. **📜 View History**: Access your chat history from the sidebar
6. **🔍 Search**: Use the search modal to find specific conversations

> 💡 **Note**: The application uses intelligent IP-based routing to provide appropriate experiences for new users, returning users, and authenticated users.

---

## 📚 API Documentation

### 🔐 Authentication Endpoints

#### 📝 Register User

```http
POST /auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "user"
}
```

#### 🔑 Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "user@example.com",
    "full_name": "John Doe"
  }
}
```

#### 👤 Get Current User

```http
GET /auth/me
Authorization: Bearer <token>
```

#### 🚪 Logout

```http
POST /auth/logout
Authorization: Bearer <token>
```

#### 🌐 Check IP Address

```http
GET /auth/check-ip
```

**Response:**
```json
{
  "is_known": true,
  "has_authenticated": true,
  "ip_address": "192.168.1.1",
  "visit_count": 5
}
```

**Purpose:**
- Fast IP lookup for routing decisions
- Tracks whether IP has been seen before
- Indicates if IP has ever authenticated
- Used for intelligent user routing

**Performance:**
- Redis cached (5-minute TTL for known IPs)
- Sub-5ms response time on cache hit
- Async database updates (non-blocking)

### 💬 Chat Endpoints

#### 📤 Send Message

```http
POST /chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What are the symptoms of flu?",
  "lang": "en",
  "profile": {},
  "session_id": "optional-session-id"
}
```

**Response:**
```json
{
  "answer": "Flu symptoms include...",
  "citations": [...],
  "safety": {...},
  "facts": [...],
  "metadata": {
    "session_id": "session-uuid"
  }
}
```

#### 📋 Get Customer Sessions

```http
GET /customer/{customer_id}/sessions?limit=100
Authorization: Bearer <token>
```

#### 💬 Get Session Messages

```http
GET /session/{session_id}/messages?limit=1000
Authorization: Bearer <token>
```

#### 🗑️ Delete Session

```http
DELETE /session/{session_id}
Authorization: Bearer <token>
```

### 👨‍💼 Admin Endpoints

#### 👥 List All Users

```http
GET /admin/users
Authorization: Bearer <admin-token>
```

> 📖 **Complete API Documentation**: Visit `http://localhost:8000/docs` when the server is running for interactive API documentation.

---

## 📁 Project Structure

```
healthcare-chatbot/
│
├── 📂 api/                          # Backend API
│   ├── 📂 auth/                     # Authentication module
│   │   ├── jwt.py                   # JWT token handling
│   │   ├── middleware.py            # Auth middleware
│   │   ├── routes.py                # Auth routes
│   │   └── validation.py            # Input validation
│   │
│   ├── 📂 database/                 # Database layer
│   │   ├── client.py                # Database client
│   │   ├── service.py               # Database service
│   │   └── models.py                # Database models
│   │
│   ├── 📂 graph/                    # Neo4j graph database
│   │   ├── client.py                # Neo4j client
│   │   ├── cypher.py                # Cypher queries
│   │   └── fallback.py              # Fallback system
│   │
│   ├── 📂 rag/                      # RAG system
│   │   ├── build_index.py           # Index builder
│   │   ├── retriever.py             # Vector retrieval
│   │   └── data/                    # Medical documents (110+ files)
│   │
│   ├── 📂 services/                 # Business logic
│   │   └── cache.py                 # Redis caching
│   │
│   ├── main.py                      # FastAPI application
│   ├── models.py                    # Pydantic models
│   ├── pipeline_functions.py        # Chat pipeline
│   └── requirements.txt             # Python dependencies
│
├── 📂 frontend/                     # Next.js frontend
│   ├── 📂 app/                      # Next.js App Router
│   │   ├── 📂 auth/                 # Authentication pages
│   │   ├── 📂 chat/                 # Chat interface
│   │   ├── page.tsx                 # Landing page
│   │   └── layout.tsx              # Root layout
│   │
│   ├── 📂 components/               # React components
│   │   ├── ChatMessage.tsx          # Message component
│   │   ├── ProfileCard.tsx          # User profile
│   │   └── ...
│   │
│   ├── 📂 utils/                    # Utilities
│   │   ├── api.ts                   # API client
│   │   └── auth.ts                  # Auth utilities
│   │
│   ├── package.json                 # Node dependencies
│   └── tailwind.config.js           # Tailwind config
│
├── 📄 FEATURES.md                   # Detailed features doc
├── 📄 LICENSE                       # License file
└── 📄 README.md                     # This file
```

---

## 🔒 Security Features

<div align="center">

| Feature | Status | Description |
|---------|--------|-------------|
| 🔐 JWT Authentication | ✅ | HTTP-only cookies, secure token storage |
| 🔑 Password Hashing | ✅ | bcrypt with salt rounds |
| 🛡️ SQL Injection Prevention | ✅ | 1900+ detection patterns, 1924 test cases, 100% pass rate |
| 🚫 XSS Protection | ✅ | Input sanitization, output encoding |
| ✅ Input Validation | ✅ | Pydantic models, custom validators |
| 👥 Role-Based Access | ✅ | Admin/User roles with permissions |
| ⏱️ Rate Limiting | ✅ | Request throttling per IP |
| 🌐 CORS Configuration | ✅ | Secure cross-origin requests |
| 🔒 Session Management | ✅ | Secure session handling, proper logout with token revocation |
| 👍 Message Feedback | ✅ | Thumbs up/down feedback with persistent storage |

</div>

---

## 🧪 Testing

### Backend Testing

```bash
# Run all tests
cd api
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html

# Run specific test file
pytest tests/test_error_handling.py
```

### Frontend Testing

```bash
# Run tests (if configured)
cd frontend
npm test

# Run with coverage
npm test -- --coverage
```

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 📝 Contribution Steps

1. **🍴 Fork** the repository
2. **🌿 Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **💾 Commit** your changes (`git commit -m 'Add some amazing feature'`)
4. **📤 Push** to the branch (`git push origin feature/amazing-feature`)
5. **🔀 Open** a Pull Request

### 📋 Development Guidelines

- ✅ Follow **PEP 8** for Python code
- ✅ Use **TypeScript** for frontend code
- ✅ Write **tests** for new features
- ✅ Update **documentation** as needed
- ✅ Follow the existing **code style**
- ✅ Add **comments** for complex logic

### 🐛 Reporting Issues

If you find a bug or have a suggestion, please open an issue with:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)

---

## 📝 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

We would like to thank:

- 🏥 **Medical Knowledge Sources**: WHO, NHS, ICMR
- 🤖 **OpenAI** for LLM capabilities
- 🔍 **ChromaDB** for vector database
- 🕸️ **Neo4j** for graph database
- ⚡ **FastAPI** and **Next.js** communities
- 👥 All contributors and users

---

## 📧 Contact & Support

<div align="center">

### 💬 Get Help

- 🐛 **Bug Reports**: [Open an Issue](https://github.com/yourusername/healthcare-chatbot/issues)
- 💡 **Feature Requests**: [Open an Issue](https://github.com/yourusername/healthcare-chatbot/issues)
- 📧 **Questions**: Open a discussion on GitHub

---

<div align="center">

### ⭐ Star this repo if you find it helpful!

**Made with ❤️ for better healthcare accessibility**

[⬆ Back to Top](#-healthcare-chatbot)

</div>

</div>
