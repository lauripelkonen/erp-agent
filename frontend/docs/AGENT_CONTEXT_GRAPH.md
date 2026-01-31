# Agent Context Graph (ACG)

## A System for Developing AI Agent "Taste" Through Accumulated Decision Patterns

**Version:** 0.1.0
**Status:** Draft
**Author:** Lauri Pelkonen + Claude
**Date:** 2026-01-23

---

## 1. Overview

### 1.1 The Problem

AI agents lack persistent memory across sessions. Each conversation starts fresh, losing accumulated knowledge about:
- How decisions were made previously
- What approaches worked or failed
- Organizational preferences and patterns
- Domain-specific "taste" developed over time

This forces humans to re-explain context repeatedly and prevents AI from developing situated judgment.

### 1.2 The Solution

The Agent Context Graph (ACG) is a hierarchical decision memory system that:
- Captures decision chains (what was read → what was decided → what was written)
- Organizes patterns into queryable trees (design, strategy, technical, etc.)
- Enables semantic retrieval of relevant precedents during agent execution
- Incorporates feedback loops to learn from outcomes
- Distills accumulated patterns into principles over time

### 1.3 Core Insight

Human "taste" is pattern recognition from accumulated experience + feedback. ACG replicates this for AI agents by:
1. Logging decisions with full reasoning context
2. Organizing patterns hierarchically for efficient retrieval
3. Weighting patterns by outcome feedback
4. Compressing frequent patterns into principles

---

## 2. Architecture

### 2.1 System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENT RUNTIME                             │
│                                                                  │
│   ┌─────────┐    ┌──────────────┐    ┌─────────────────────┐   │
│   │  Task   │───▶│   Retriever  │───▶│  Context Injection  │   │
│   │  Input  │    │              │    │                     │   │
│   └─────────┘    └──────────────┘    └─────────────────────┘   │
│                         │                       │               │
│                         ▼                       ▼               │
│                  ┌─────────────┐         ┌───────────┐         │
│                  │   Context   │         │   Agent   │         │
│                  │    Graph    │◀────────│ Execution │         │
│                  │     (DB)    │  log    │           │         │
│                  └─────────────┘         └───────────┘         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

```
1. TASK RECEIVED
       │
       ▼
2. EMBED TASK ──────────────────┐
       │                        │
       ▼                        ▼
3. RETRIEVE PRINCIPLES    SEMANTIC SEARCH
   (always loaded)        (top-k patterns)
       │                        │
       └────────┬───────────────┘
                │
                ▼
4. INJECT PRECEDENT CONTEXT INTO PROMPT
                │
                ▼
5. AGENT EXECUTES (READ → DECIDE → WRITE)
                │
                ▼
6. LOG DECISION TO CONTEXT GRAPH
                │
                ▼
7. [ASYNC] COLLECT OUTCOME FEEDBACK
                │
                ▼
8. [PERIODIC] DISTILL PATTERNS INTO PRINCIPLES
```

---

## 3. Data Schema

### 3.1 Hierarchical Tree Structure

The context graph is organized as a tree of domains, each containing sub-domains and decision patterns:

```
context_graph/
├── design/
│   ├── visual/
│   │   ├── color/
│   │   ├── typography/
│   │   ├── layout/
│   │   └── animation/
│   ├── ux/
│   │   ├── navigation/
│   │   ├── forms/
│   │   └── feedback/
│   └── brand/
│       ├── tone/
│       └── identity/
├── technical/
│   ├── architecture/
│   ├── patterns/
│   ├── performance/
│   └── security/
├── strategy/
│   ├── product/
│   ├── market/
│   ├── pricing/
│   └── positioning/
├── content/
│   ├── copywriting/
│   ├── seo/
│   └── documentation/
└── process/
    ├── workflow/
    ├── communication/
    └── decision-making/
```

### 3.2 Core Data Types

#### 3.2.1 Decision Pattern

```typescript
interface DecisionPattern {
  // Identity
  id: string;                      // UUID
  created_at: string;              // ISO timestamp
  updated_at: string;              // ISO timestamp

  // Location in tree
  domain: string;                  // e.g., "design"
  subdomain: string;               // e.g., "visual/animation"
  tags: string[];                  // e.g., ["svg", "landing-page", "B2B"]

  // Context capture
  task_description: string;        // What was the agent asked to do
  inputs_read: InputRecord[];      // Files/resources read before decision
  decision_made: string;           // What was decided
  outputs_written: OutputRecord[]; // Files/resources written
  reasoning: string;               // Why this decision was made
  alternatives_considered: string[]; // Other options that were rejected

  // Retrieval
  context_embedding: number[];     // Vector embedding for semantic search
  summary: string;                 // One-line summary for prompt injection

  // Feedback
  outcome_score: number | null;    // 1-10, null if not yet rated
  outcome_notes: string | null;    // Qualitative feedback
  feedback_date: string | null;    // When feedback was provided

  // Metadata
  agent_model: string;             // e.g., "claude-opus-4-5-20251101"
  session_id: string;              // Links related decisions
  human_validated: boolean;        // Was this reviewed by human
}

interface InputRecord {
  type: "file" | "url" | "database" | "api";
  path: string;
  summary: string;                 // What was relevant from this input
}

interface OutputRecord {
  type: "file" | "edit" | "create";
  path: string;
  summary: string;                 // What was written/changed
}
```

#### 3.2.2 Principle

Principles are distilled from multiple decision patterns:

```typescript
interface Principle {
  id: string;
  domain: string;
  subdomain: string;

  // Content
  statement: string;               // e.g., "Use monochrome #2600FF for all UI elements"
  rationale: string;               // Why this principle exists
  examples: string[];              // Brief examples of application
  exceptions: string[];            // When this principle doesn't apply

  // Provenance
  derived_from: string[];          // IDs of patterns this was distilled from
  pattern_count: number;           // How many patterns support this
  confidence: number;              // 0-1, based on consistency and outcomes

  // Priority
  weight: number;                  // Higher = more important, used in conflicts

  // Lifecycle
  created_at: string;
  last_validated: string;
  status: "active" | "deprecated" | "experimental";
}
```

#### 3.2.3 Domain Node

```typescript
interface DomainNode {
  id: string;
  path: string;                    // e.g., "design/visual/animation"
  name: string;                    // e.g., "animation"
  description: string;

  // Hierarchy
  parent_id: string | null;
  children_ids: string[];

  // Aggregates
  pattern_count: number;
  principle_count: number;
  avg_outcome_score: number | null;

  // Retrieval hints
  keywords: string[];              // Help with routing queries
  typical_tasks: string[];         // Example tasks in this domain
}
```

### 3.3 JSON File Structure

For a file-based implementation:

```
acg/
├── config.json                    # Global settings
├── principles/
│   ├── design.json
│   ├── technical.json
│   ├── strategy.json
│   └── ...
├── patterns/
│   ├── design/
│   │   ├── visual/
│   │   │   ├── animation/
│   │   │   │   ├── index.json     # Domain metadata + pattern list
│   │   │   │   ├── p_abc123.json  # Individual pattern
│   │   │   │   └── p_def456.json
│   │   │   └── color/
│   │   │       └── ...
│   │   └── ...
│   └── ...
├── embeddings/
│   └── patterns.index             # Vector index for semantic search
└── feedback/
    └── pending.json               # Patterns awaiting outcome feedback
```

---

## 4. Retrieval System

### 4.1 Retrieval Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  LEVEL 1: PRINCIPLES                                        │
│  ─────────────────────                                      │
│  • Always loaded into system prompt                         │
│  • ~20-50 items max                                         │
│  • Highest confidence, most validated                       │
│  • Example: "We use #2600FF as primary brand color"         │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 2: DOMAIN PATTERNS                                   │
│  ────────────────────────                                   │
│  • Retrieved based on task domain classification            │
│  • 5-15 items per relevant domain                           │
│  • Filtered by subdomain tags                               │
│  • Example: Animation patterns when task involves SVG       │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 3: SEMANTIC MATCHES                                  │
│  ─────────────────────────                                  │
│  • Retrieved via embedding similarity                       │
│  • Top-k most similar to current task                       │
│  • Weighted by outcome scores                               │
│  • Example: "Last time we built a B2B hero section..."      │
├─────────────────────────────────────────────────────────────┤
│  LEVEL 4: EXPLICIT QUERIES                                  │
│  ─────────────────────────                                  │
│  • Agent explicitly searches for precedents                 │
│  • Used when agent is uncertain                             │
│  • Natural language queries against graph                   │
│  • Example: Agent asks "How did we handle animation timing?"│
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Retrieval Algorithm

```typescript
interface RetrievalConfig {
  max_principles: number;           // Default: 30
  max_domain_patterns: number;      // Default: 10
  max_semantic_matches: number;     // Default: 5
  min_similarity_threshold: number; // Default: 0.7
  outcome_weight: number;           // Default: 0.3 (how much outcome affects ranking)
  recency_weight: number;           // Default: 0.1 (slight preference for recent)
}

async function retrieveContext(
  task: string,
  config: RetrievalConfig
): Promise<RetrievalResult> {

  // 1. Always load active principles
  const principles = await db.principles.find({
    status: "active",
    limit: config.max_principles,
    orderBy: { weight: "desc" }
  });

  // 2. Classify task domain
  const taskDomains = await classifyTaskDomains(task);
  // Returns e.g., ["design/visual/animation", "technical/patterns"]

  // 3. Retrieve domain-specific patterns
  const domainPatterns = await Promise.all(
    taskDomains.map(domain =>
      db.patterns.find({
        subdomain: { startsWith: domain },
        limit: config.max_domain_patterns,
        orderBy: { outcome_score: "desc", created_at: "desc" }
      })
    )
  );

  // 4. Semantic search across all patterns
  const taskEmbedding = await embed(task);
  const semanticMatches = await db.patterns.semanticSearch({
    embedding: taskEmbedding,
    limit: config.max_semantic_matches,
    minSimilarity: config.min_similarity_threshold,
    scoreFunction: (pattern, similarity) => {
      const outcomeBoost = (pattern.outcome_score || 5) / 10 * config.outcome_weight;
      const recencyBoost = recencyScore(pattern.created_at) * config.recency_weight;
      return similarity + outcomeBoost + recencyBoost;
    }
  });

  // 5. Deduplicate and rank
  const allPatterns = deduplicateById([
    ...domainPatterns.flat(),
    ...semanticMatches
  ]);

  return {
    principles,
    patterns: allPatterns,
    domains: taskDomains
  };
}
```

### 4.3 Context Injection Format

```typescript
function formatContextInjection(retrieval: RetrievalResult): string {
  return `
## Established Principles

${retrieval.principles.map(p => `- **${p.statement}**
  ${p.rationale}`).join('\n\n')}

## Relevant Past Decisions

${retrieval.patterns.map(p => `### ${p.summary}
- **Context:** ${p.task_description}
- **Decision:** ${p.decision_made}
- **Reasoning:** ${p.reasoning}
${p.outcome_score ? `- **Outcome:** ${p.outcome_score}/10 - ${p.outcome_notes}` : ''}`).join('\n\n')}

## Active Domains
This task appears related to: ${retrieval.domains.join(', ')}
`;
}
```

---

## 5. Agent Loop Integration

### 5.1 Enhanced Agent Loop

```typescript
class ACGAgent {
  private db: ContextGraphDB;
  private session_id: string;
  private readLog: InputRecord[] = [];

  async execute(task: string): Promise<ExecutionResult> {
    this.session_id = generateSessionId();
    this.readLog = [];

    // 1. Retrieve relevant context
    const context = await retrieveContext(task);
    const contextPrompt = formatContextInjection(context);

    // 2. Execute with context
    const result = await this.runAgent(task, contextPrompt);

    // 3. Log decision
    await this.logDecision(task, result, context.domains);

    return result;
  }

  // Wrapper for READ operations
  async read(path: string): Promise<string> {
    const content = await readFile(path);
    const summary = await summarizeContent(content, path);

    this.readLog.push({
      type: "file",
      path,
      summary
    });

    return content;
  }

  // Wrapper for WRITE operations
  async write(path: string, content: string, reasoning: string): Promise<void> {
    await writeFile(path, content);

    // This triggers decision logging
    await this.logDecision(
      `Write to ${path}`,
      {
        outputs: [{ type: "create", path, summary: reasoning }],
        reasoning
      }
    );
  }

  private async logDecision(
    task: string,
    result: ExecutionResult,
    domains: string[]
  ): Promise<void> {
    const pattern: DecisionPattern = {
      id: generateId(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),

      domain: domains[0]?.split('/')[0] || 'uncategorized',
      subdomain: domains[0] || 'uncategorized',
      tags: await extractTags(task, result),

      task_description: task,
      inputs_read: this.readLog,
      decision_made: result.summary,
      outputs_written: result.outputs,
      reasoning: result.reasoning,
      alternatives_considered: result.alternatives || [],

      context_embedding: await embed(task + ' ' + result.reasoning),
      summary: await generateOneliner(task, result),

      outcome_score: null,
      outcome_notes: null,
      feedback_date: null,

      agent_model: "claude-opus-4-5-20251101",
      session_id: this.session_id,
      human_validated: false
    };

    await this.db.patterns.insert(pattern);
    await this.db.feedback.addPending(pattern.id);
  }

  // Explicit precedent search (agent can call this)
  async searchPrecedents(query: string): Promise<DecisionPattern[]> {
    const embedding = await embed(query);
    return this.db.patterns.semanticSearch({
      embedding,
      limit: 10,
      minSimilarity: 0.6
    });
  }
}
```

### 5.2 Tool Definitions for Agent

```typescript
const acgTools = [
  {
    name: "search_precedents",
    description: "Search for relevant past decisions and patterns. Use when uncertain about how to approach something or want to maintain consistency with previous work.",
    parameters: {
      query: {
        type: "string",
        description: "Natural language description of what you're looking for"
      },
      domain: {
        type: "string",
        description: "Optional: limit search to specific domain (e.g., 'design/visual')",
        optional: true
      }
    }
  },
  {
    name: "get_principles",
    description: "Get established principles for a specific domain",
    parameters: {
      domain: {
        type: "string",
        description: "Domain path (e.g., 'design/visual/color')"
      }
    }
  },
  {
    name: "flag_decision",
    description: "Flag a decision as important or uncertain for human review",
    parameters: {
      decision_summary: {
        type: "string"
      },
      flag_reason: {
        type: "string",
        enum: ["high_impact", "uncertain", "contradicts_precedent", "new_domain"]
      }
    }
  }
];
```

---

## 6. Feedback System

### 6.1 Feedback Collection

Patterns are only valuable if we know which ones led to good outcomes.

```typescript
interface FeedbackRequest {
  pattern_id: string;
  task_summary: string;
  decision_summary: string;
  created_at: string;
}

// Feedback can be collected via:

// 1. Explicit rating
async function rateDecision(
  pattern_id: string,
  score: number,        // 1-10
  notes: string
): Promise<void> {
  await db.patterns.update(pattern_id, {
    outcome_score: score,
    outcome_notes: notes,
    feedback_date: new Date().toISOString()
  });
}

// 2. Implicit signals
async function recordImplicitFeedback(pattern_id: string, signal: ImplicitSignal) {
  // Signals:
  // - User accepted output without changes → positive
  // - User requested revisions → slightly negative
  // - User rejected/rewrote entirely → negative
  // - Pattern was referenced by future decisions → positive
}

// 3. Downstream metrics
async function linkMetrics(pattern_id: string, metrics: MetricLink) {
  // Link to measurable outcomes:
  // - Conversion rate change after landing page update
  // - Error rate after code pattern adoption
  // - Time saved on similar tasks
}
```

### 6.2 Feedback UI (CLI Example)

```
$ acg feedback pending

Pending feedback for 3 decisions:

[1] 2026-01-22 - design/visual/animation
    Task: Create SVG animation for Purchase Order page
    Decision: Used monochrome #2600FF, process-visualization style

    Rate (1-10): 8
    Notes: Client approved, matched brand well

[2] 2026-01-21 - technical/architecture
    Task: Structure landing page components
    Decision: Separate algorithmic art into dedicated component folder

    Rate (1-10): 9
    Notes: Made components highly reusable

[3] ...
```

---

## 7. Principle Distillation

### 7.1 Automatic Distillation

When enough patterns accumulate in a domain, distill them into principles:

```typescript
async function distillPrinciples(domain: string): Promise<Principle[]> {
  // 1. Get all patterns in domain with good outcomes
  const patterns = await db.patterns.find({
    subdomain: { startsWith: domain },
    outcome_score: { gte: 7 },
    limit: 100
  });

  if (patterns.length < 10) {
    return []; // Not enough data to distill
  }

  // 2. Cluster similar patterns
  const clusters = await clusterByEmbedding(patterns, {
    min_cluster_size: 3,
    similarity_threshold: 0.8
  });

  // 3. For each cluster, extract principle
  const principles: Principle[] = [];

  for (const cluster of clusters) {
    const principle = await llm.generate({
      prompt: `
        Analyze these ${cluster.length} successful decisions and extract
        a single, actionable principle that captures their common pattern.

        Decisions:
        ${cluster.map(p => `- ${p.summary}: ${p.reasoning}`).join('\n')}

        Output format:
        - Statement: [One clear, imperative sentence]
        - Rationale: [Why this principle works]
        - Exceptions: [When this might not apply]
      `
    });

    principles.push({
      id: generateId(),
      domain: domain.split('/')[0],
      subdomain: domain,
      statement: principle.statement,
      rationale: principle.rationale,
      examples: cluster.slice(0, 3).map(p => p.summary),
      exceptions: principle.exceptions,
      derived_from: cluster.map(p => p.id),
      pattern_count: cluster.length,
      confidence: avgOutcomeScore(cluster) / 10,
      weight: cluster.length * avgOutcomeScore(cluster),
      created_at: new Date().toISOString(),
      last_validated: new Date().toISOString(),
      status: "experimental"
    });
  }

  return principles;
}
```

### 7.2 Principle Lifecycle

```
experimental ──[validation]──▶ active ──[contradiction]──▶ deprecated
     │                           │                              │
     │                           │                              │
     └────[insufficient data]────┴──────[manual override]───────┘
```

- **Experimental**: Newly distilled, needs validation
- **Active**: Validated by human or consistent positive outcomes
- **Deprecated**: Contradicted by newer patterns or manually retired

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Define JSON schema files
- [ ] Implement basic CRUD for patterns
- [ ] Create logging wrapper for agent READ/WRITE operations
- [ ] Build CLI for viewing and rating patterns

### Phase 2: Retrieval (Week 3-4)
- [ ] Integrate embedding model (e.g., OpenAI ada-002 or local)
- [ ] Implement vector index for semantic search
- [ ] Build retrieval function with domain classification
- [ ] Create context injection formatting

### Phase 3: Agent Integration (Week 5-6)
- [ ] Wrap existing agent with ACG hooks
- [ ] Add explicit search tools for agent
- [ ] Implement session tracking
- [ ] Test end-to-end loop

### Phase 4: Feedback & Learning (Week 7-8)
- [ ] Build feedback collection UI
- [ ] Implement implicit signal tracking
- [ ] Create principle distillation pipeline
- [ ] Add principle management UI

### Phase 5: Optimization (Ongoing)
- [ ] Tune retrieval parameters
- [ ] Optimize embedding storage/search
- [ ] Build analytics dashboard
- [ ] Implement pattern decay/archival

---

## 9. Example: Full Cycle

### 9.1 Task Execution

```
INPUT: "Create an animated SVG for the pricing page hero section"

RETRIEVAL:
  Principles loaded: 12
  - "Use monochrome #2600FF for all brand visuals"
  - "B2B landing pages prioritize clarity over decoration"
  - ...

  Domain patterns (design/visual/animation): 8
  - "POGenerationEngine: AI processing visualization worked well for PO page"
  - "SmartReorderTrigger: Chart-based animation for data concepts"
  - ...

  Semantic matches: 3
  - "Hero SVG for wholesale page: network/flow visualization"
  - ...

EXECUTION:
  Agent reads: pricing page structure, brand guidelines, existing SVG components
  Agent decides: Create PricingTierFlow.tsx with animated tier comparison
  Agent writes: new component file

LOGGING:
  Pattern saved:
  - domain: design/visual/animation
  - task: Create animated SVG for pricing page hero
  - decision: Tier comparison visualization with flowing connections
  - reasoning: Pricing is about comparing options, flow shows progression
  - inputs: [pricing page, brand docs, 3 existing SVGs]
  - outputs: [PricingTierFlow.tsx]

FEEDBACK (later):
  Score: 8/10
  Notes: "Clean, on-brand, client approved without changes"
```

### 9.2 Principle Emergence

After 15 similar SVG decisions:

```
DISTILLED PRINCIPLE:
  Statement: "Use process-flow visualizations for B2B concept pages"
  Rationale: "B2B buyers need to understand how things work, not just
              what they look like. Flow/process diagrams consistently
              outperform decorative illustrations."
  Derived from: 15 patterns (avg outcome: 8.2/10)
  Status: experimental → active (after human validation)
```

---

## 10. Open Questions

1. **Embedding model choice**: Local vs API? Cost vs quality tradeoff.

2. **Conflict resolution**: When principles contradict, how to decide? Weight-based? Recency? Human-in-loop?

3. **Cross-project transfer**: Can patterns from Project A help Project B? Domain vs project-specific knowledge.

4. **Privacy/security**: Decision logs may contain sensitive info. Access control needed.


5. **Scaling**: At what point does file-based JSON need to become a proper database?

6. **Multi-agent**: How do patterns transfer between different AI models or agent configurations?

7. **Scope boundary**: Is the graph strictly project-local or shared across projects? Define isolation and permissions.

8. **Logging policy**: Which decisions get logged (all vs high-impact)? How to prevent low-value noise?

9. **Feedback sparsity**: What happens when outcomes are delayed or missing? Fallback weighting and decay strategy.

10. **Evaluation loop**: How do we measure "better taste"? Define metrics (acceptance rate, revision rate, time saved).

---

## Appendix A: JSON Schema Files

### A.1 config.json

```json
{
  "version": "0.1.0",
  "retrieval": {
    "max_principles": 30,
    "max_domain_patterns": 10,
    "max_semantic_matches": 5,
    "min_similarity_threshold": 0.7,
    "outcome_weight": 0.3,
    "recency_weight": 0.1
  },
  "distillation": {
    "min_patterns_for_principle": 10,
    "min_outcome_score": 7,
    "cluster_similarity_threshold": 0.8
  },
  "embedding": {
    "model": "text-embedding-3-small",
    "dimensions": 1536
  },
  "domains": [
    "design",
    "technical",
    "strategy",
    "content",
    "process"
  ]
}
```

### A.2 Pattern Example

```json
{
  "id": "pat_abc123",
  "created_at": "2026-01-22T14:30:00Z",
  "updated_at": "2026-01-22T14:30:00Z",
  "domain": "design",
  "subdomain": "design/visual/animation",
  "tags": ["svg", "landing-page", "B2B", "hero-section"],
  "task_description": "Create animated SVG for Purchase Order Automation page hero",
  "inputs_read": [
    {
      "type": "file",
      "path": "/src/pages/PurchaseOrderAutomation.tsx",
      "summary": "Landing page structure, needs hero visual"
    },
    {
      "type": "file",
      "path": "/src/components/AlgorithmicArt/POGenerationEngine.tsx",
      "summary": "Reference for animation style"
    }
  ],
  "decision_made": "Created POGenerationEngine with AI processor visualization showing inputs flowing to generated PO document",
  "outputs_written": [
    {
      "type": "create",
      "path": "/src/components/AlgorithmicArt/POGenerationEngine.tsx",
      "summary": "SVG component with animated data flow visualization"
    }
  ],
  "reasoning": "PO automation is about AI processing multiple inputs (inventory, sales, suppliers) to generate output. Visualized as flow diagram to show the 'engine' concept. Used brand color #2600FF, monochrome style consistent with other components.",
  "alternatives_considered": [
    "Abstract geometric pattern - rejected as too decorative for B2B",
    "Screenshot of actual PO - rejected as not visually interesting"
  ],
  "summary": "AI engine visualization for PO automation hero",
  "outcome_score": 8,
  "outcome_notes": "Client approved, animation timing felt right, consistent with brand",
  "feedback_date": "2026-01-23T10:00:00Z",
  "agent_model": "claude-opus-4-5-20251101",
  "session_id": "sess_xyz789",
  "human_validated": true
}
```

---

## Appendix B: CLI Commands

```bash
# Initialize new context graph
acg init

# View patterns
acg patterns list [--domain <domain>] [--limit <n>]
acg patterns show <pattern_id>
acg patterns search "<query>"

# Manage principles
acg principles list [--domain <domain>]
acg principles add --domain <domain> --statement "<statement>"
acg principles validate <principle_id>
acg principles deprecate <principle_id>

# Feedback
acg feedback pending
acg feedback rate <pattern_id> --score <1-10> --notes "<notes>"

# Distillation
acg distill <domain> [--dry-run]

# Analytics
acg stats [--domain <domain>]
acg report --from <date> --to <date>

# Export/Import
acg export --format json > backup.json
acg import < backup.json
```

---

*This document is a living specification. Update as implementation progresses.*
