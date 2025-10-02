# Kolb's Cycle MCP Server

A Model Context Protocol (MCP) server implementing Dr. Justin Sung's Modified Kolb's Cycle methodology for systematic self-improvement through daily pattern tracking and experimentation.

## Overview

This MCP server enables Claude Desktop to:
- Store and track behavioral patterns with evolving confidence scores
- Manage 7-day experiments with daily observations
- Detect cross-domain pattern connections
- Recommend data-driven experiments
- Calculate compound gains (1% daily improvement methodology)

## Architecture

### Database Schema (PostgreSQL)
- **behavioral_patterns** - Discovered patterns with confidence evolution
- **experiments** - 7-day experiments with daily observations
- **pattern_experiments** - Many-to-many relationships
- **insights** - Breakthrough connections and learnings
- **active_experiments** - Currently running experiments
- **experiment_recommendations** - Recommendation history

### MCP Tools (12 total)

**Pattern Management (4)**
- `store_pattern` - Create new pattern with 0.3 initial confidence
- `get_patterns_by_domain` - Retrieve filtered patterns
- `update_pattern_confidence` - Evolve confidence with evidence
- `find_related_patterns` - Cross-domain detection

**Experiment Management (4)**
- `create_experiment` - Schedule experiment for tomorrow
- `get_active_experiments` - List running experiments
- `record_daily_observation` - Add daily data point
- `recommend_experiments` - Generate 3 personalized suggestions

**Analytics (4)**
- `create_insight` - Capture breakthrough connections
- `calculate_compound_gains` - Show 1% daily improvement trajectory
- `get_session_summary` - Daily activity recap
- Additional analytics tools

### MCP Resources (2)
- `pattern://{pattern_id}` - Full pattern details
- `experiment://{experiment_id}` - Full experiment details

## Installation

### Prerequisites
- macOS (tested on Sequoia)
- Homebrew
- Python 3.11+
- PostgreSQL 15+
- Claude Desktop

### Setup Steps

1. **Database Setup**
   ```bash
   # PostgreSQL should already be installed and running
   # Database 'knowledge_mcp' should already exist

   # Verify
   psql knowledge_mcp -c "SELECT COUNT(*) FROM behavioral_patterns;"
   ```

2. **Python Environment** (already configured)
   ```bash
   cd "/Users/ruben/Documents/GitHub/Kolb's MCP"

   # Virtual environment already created at .venv
   # Dependencies already installed
   ```

3. **Environment Variables** (already configured)
   ```bash
   # .env file already created with:
   # DATABASE_URL=postgresql://ruben@localhost:5432/knowledge_mcp
   # LOG_LEVEL=INFO
   ```

4. **Claude Desktop Integration** (already configured)
   Configuration added to `~/Library/Application Support/Claude/claude_desktop_config.json`

## Usage

### Starting the Server

The server auto-starts when Claude Desktop launches. To manually test:

```bash
cd "/Users/ruben/Documents/GitHub/Kolb's MCP"
.venv/bin/python src/kolb_mcp/server.py
```

### Daily Workflow

1. **Start Session** - Claude calls `get_active_experiments()` to show what's being tracked
2. **Experience Reflection** - Guide through 7 reflection questions
3. **Pattern Identification** - Claude calls `store_pattern()` or `update_pattern_confidence()`
4. **Cross-Domain Analysis** - Claude calls `find_related_patterns()`
5. **Experiment Design** - Claude calls `recommend_experiments()` and `create_experiment()`
6. **Session Summary** - Claude calls `get_session_summary()` for recap

### Example: Storing a Pattern

```python
# Claude calls this via MCP
store_pattern({
  "description": "Procrastinate on tasks requiring >2 hours of uninterrupted focus",
  "pattern_type": "behavioral",
  "domains": ["work"],
  "triggers": ["complex tasks", "uncertainty", "fatigue"],
  "frequency": "daily",
  "confidence": 0.3
})
# Returns: {"success": True, "pattern_id": "pat_2025_10_02_abc123", ...}
```

### Example: Creating an Experiment

```python
# Claude calls this via MCP
create_experiment({
  "domain": "work",
  "hypothesis": "Working in 90-minute focused blocks will increase deep work completion by 30%",
  "intervention": "Set timer for 90 min, disable all notifications, close email/slack",
  "primary_metrics": ["deep work hours completed", "task completion rate"],
  "guardrail_metrics": ["stress level", "energy at end of day"],
  "duration_days": 7,
  "target_pattern_id": "pat_2025_10_02_abc123"
})
# Returns: {"success": True, "experiment_id": "exp_2025_10_02_wor", ...}
```

## Monitoring

### Logs
Server logs are written to `/tmp/kolb_mcp.log`:

```bash
tail -f /tmp/kolb_mcp.log
```

### Database Health
Check database size and table counts:

```bash
psql knowledge_mcp -c "\dt+"
psql knowledge_mcp -c "SELECT COUNT(*) FROM behavioral_patterns;"
psql knowledge_mcp -c "SELECT COUNT(*) FROM experiments;"
```

### MCP Inspector Testing
Test tools manually:

```bash
npx @modelcontextprotocol/inspector .venv/bin/python src/kolb_mcp/server.py
```

Opens web interface at `http://localhost:5173` for interactive testing.

## Troubleshooting

### Server Won't Start
1. Check PostgreSQL is running: `brew services list | grep postgresql`
2. Verify DATABASE_URL in .env matches your PostgreSQL setup
3. Check logs: `tail -f /tmp/kolb_mcp.log`

### Tools Not Appearing in Claude Desktop
1. Restart Claude Desktop completely
2. Check config: `cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | grep kolb`
3. Verify Python path: `.venv/bin/python --version`

### Database Connection Errors
```bash
# Restart PostgreSQL
brew services restart postgresql@15

# Test connection
psql knowledge_mcp -c "SELECT version();"
```

## Performance

### Targets
- Tool response time: <500ms (p95)
- Complex analysis: <1s (p99)
- Database query time: <100ms (p95)
- Daily session duration: 15-20 minutes

### Optimization
- Connection pool: 2-10 connections
- GIN indexes on JSONB fields
- B-tree indexes on frequently queried columns
- Query timeout: 5 seconds (fail fast)

## Development

### Project Structure
```
/Users/ruben/Documents/GitHub/Kolb's MCP/
├── database/
│   └── schema.sql              # PostgreSQL schema
├── src/kolb_mcp/
│   ├── server.py               # Main MCP server (12 tools)
│   ├── database/
│   │   ├── pool.py             # Connection pool manager
│   │   └── queries.py          # SQL query constants
│   ├── models/
│   │   ├── pattern.py          # Pydantic models
│   │   ├── experiment.py
│   │   └── insight.py
│   ├── tools/                  # (Future: separate tool modules)
│   └── utils/
├── tests/                      # (Future: test suite)
├── .env                        # Environment variables
├── .env.example                # Template
└── pyproject.toml              # Dependencies
```

### Adding New Tools

1. Add function with `@mcp.tool()` decorator to `server.py`
2. Use Pydantic models for parameters
3. Check database availability with `_check_db_available()`
4. Return structured dict with `success` field
5. Add comprehensive error handling

### Database Migrations

Future schema changes should use Alembic:

```bash
# Initialize (when needed)
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add journaling support"

# Apply migration
alembic upgrade head
```

## Roadmap

### Phase 1: Core (Complete ✓)
- [x] Pattern storage and retrieval
- [x] Experiment tracking
- [x] Cross-domain analysis
- [x] Compound gains calculation

### Phase 2: Testing (Next)
- [ ] MCP Inspector validation
- [ ] Manual testing in Claude Desktop
- [ ] Enhanced Claude Project prompt

### Phase 3: Enhancement (Future)
- [ ] Journaling integration
- [ ] Advanced analytics (ML-based pattern prediction)
- [ ] Notion/Calendar sync
- [ ] Multi-user support

## Support

### Logs Location
- Server logs: `/tmp/kolb_mcp.log`
- Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`

### Database Backup
```bash
# Backup database
pg_dump knowledge_mcp > backup_$(date +%Y%m%d).sql

# Restore database
psql knowledge_mcp < backup_YYYYMMDD.sql
```

## License

Private project for personal use.

## Credits

- **Methodology**: Dr. Justin Sung's Modified Kolb's Cycle
- **Protocol**: Model Context Protocol (MCP) by Anthropic
- **Framework**: FastMCP by @jlowin
