# Building an Autonomous Research Agent: What Goes Right and Wrong Between Humans and AI

> This document captures the **cognitive patterns** behind human–AI research collaboration — what the AI fundamentally lacks, what the human actually contributes, and how an agent architecture can close the gap. It is not tied to any specific investigation.

---

## 1. The Goal

An agent that takes a research question and produces a complete investigation — data analysis, statistical testing, visualizations, and actionable recommendations — at a quality level that a domain expert would consider "ready to present," not "ready to redo."

The operative word is **quality**. Any LLM can produce a notebook that runs. The problem is producing one that's worth reading.

---

## 2. The Five Failure Modes of AI Research

### 2.1 Circular Findings — "Discovering" What the Data Already Says

The most common and most dangerous failure. The AI computes something, presents it as a finding, but it's actually just restating the input in a different shape.

**Example pattern:**
- "Patients who died had higher mortality" (tautology)
- "Hospitals that treat sicker patients have worse outcomes" (obvious)
- "Older patients die more" → presented as an insight, but the data was filtered by age in the first place
- "Cities with more cases have more deaths" (linear relationship, no insight)

**Why it happens:** The AI confuses **computation** with **insight**. It can compute a group-by, a correlation, a trend — and the act of computing feels like discovering. But the output is often just the input reorganized. The AI has no internal sense of "is this surprising?" or "does everyone already know this?"

**The test the AI fails:** "Would a domain expert say 'I didn't know that' or 'obviously'?" The AI can't run this test because it doesn't model what the audience already knows.

**What the human does:** The human reads the output and feels *nothing* — no surprise, no "aha." That feeling of flatness is the signal. The human says "this is lazy" or "go deeper" — what they mean is "you haven't told me anything I couldn't have guessed."

### 2.2 Satisficing — The "Good Enough" Trap

The AI produces the **minimum viable analysis** that technically answers the question. Compute the mean, plot the trend, report the correlation. Done.

But research isn't about answering questions — it's about **decomposing** them. "Is mortality rising?" is not answered by a line chart. It's answered by: rising for whom? Driven by which subgroups? Explained by patient changes or system changes? After controlling for what?

**Why it happens:** LLMs are trained to complete tasks, not to question whether the task was the right one. "Analyze ICU capacity" is satisfied by any analysis of ICU capacity. The AI has no internal drive to push beyond the specification.

**The test the AI fails:** "Is this the analysis you'd show to defend a thesis, or is it a homework assignment?" The AI can't distinguish between the two.

**What the human does:** The human recognizes that the analysis is *correct* but *shallow*. They push for decomposition: "but what's driving this?" They push for rigor: "did you control for confounders?" They push for depth because they have **epistemic standards** — an internalized sense of what constitutes genuine understanding vs. surface description.

### 2.3 No Counterfactual Imagination

The AI works with **what it has**. It never asks: "What data don't I have that would change the answer?"

This is the difference between an analyst and a researcher. An analyst processes data. A researcher designs investigations — which includes deciding what data to collect, what external sources to integrate, what comparisons would be most informative.

**Why it happens:** LLMs are reactive. They respond to inputs. They don't spontaneously wonder "what if I had population data?" or "would adjusting for inflation change the conclusion?" These are counterfactual thoughts — imagining a world where the analysis is different.

**What the human does:** The human says "could we get census data?" or "shouldn't we deflate these costs?" They're imagining a **better version of the analysis** that doesn't exist yet and asking the AI to build it. The AI can execute the enrichment — it just can't conceive of it.

### 2.4 Statistics Without Meaning

The AI produces R² = 0.642 and moves on. It doesn't ask: "What does this mean for someone who needs to make a decision?"

There's a gap between **computing a number** and **understanding what it implies**. The AI can tell you that age explains 97% of the variance. It can't spontaneously tell you that this means the "ICU gap" everyone worries about is a statistical illusion, and that building more ICUs is the wrong policy response.

**Why it happens:** Meaning is not in the number — it's in the relationship between the number and the context. "R² = 0.97" means nothing in isolation. It means everything when combined with "and people think the answer is ICU shortage." The AI computes the number but doesn't hold the context.

**What the human does:** The human bridges from statistics to action. They ask "so what does this mean for where we put ICUs?" They see the policy implication that the number implies. This is not computation — it's **interpretation**, which requires understanding the audience's beliefs, concerns, and decision space.

### 2.5 Linear Execution

The AI processes analysis steps in sequence. When step 7 reveals something that changes the conclusion of step 3, the AI doesn't go back. It doesn't hold a **holistic mental model** of the investigation that evolves as evidence accumulates.

**Why it happens:** LLMs process instructions sequentially within a conversation. They don't maintain a persistent, evolving model of "what I believe about this topic." Each analysis is treated as an independent task, not as a piece of a puzzle that might reshape earlier pieces.

**What the human does:** The human holds the full picture. When they see a new finding, they mentally update everything else. "Wait — if per-capita rates change the ranking, then the earlier priority list is wrong." The human sees **connections across the investigation** that the AI doesn't track.

---

## 3. What the Human Actually Does (and Why It's Hard to Automate)

The human is not an editor or a QA engineer. The human acts as a **research director** — someone who knows what good research looks like and won't accept less.

### 3.1 Epistemic Standards ("Is this real?")

The human maintains an internal sense of what constitutes genuine understanding vs. surface description. When the AI presents a finding, the human asks:

- Is this surprising? Or is it obvious?
- Is this causal? Or is it confounding?
- Is this actionable? Or is it academic?
- Is this rigorous? Or would a reviewer tear it apart?

These are **judgment calls**, not algorithms. The human doesn't compute a metric — they *feel* whether the analysis is deep enough. This feeling comes from years of reading, reviewing, and presenting research.

**Can this be automated?** Partially. You can build checklists ("does this notebook include a decomposition?") and reflection prompts ("would a reviewer find this convincing?"). But the checklists themselves need to be calibrated by someone who knows what "convincing" means in this domain. The meta-problem: who writes the checklist for the checklist?

### 3.2 Relevance Filtering ("Does anyone care?")

Of all possible analyses the AI could run, only a few matter to the audience. The human knows which ones because they understand the audience's **decision context** — what they're trying to decide, what they already believe, what would change their mind.

"Cities with more hospitals have lower mortality" → nobody cares, it's obvious.
"Age explains 97% of variance, not ICU capacity" → everyone cares, because everyone assumed the opposite.

**Can this be automated?** Only if the agent has an explicit model of the audience: who they are, what they believe, what decisions they face. Without this, the AI generates all analyses equally, burying the important ones under the obvious.

### 3.3 Counterfactual Design ("What data would change the answer?")

The human imagines analyses that don't exist yet. "What if we had population data?" "What if we compared with a control condition?" "What would this look like per capita?"

This is **experimental design** applied to observational data. The human is designing the investigation as it unfolds, not just executing a pre-made plan.

**Can this be automated?** Partially, through a **data source registry** — a catalog of enrichment sources (census data, inflation indices, disease registries) with descriptions of when each is useful. The agent consults the registry when planning analyses: "For geographic comparisons, always check if per-capita rates are available." But the registry itself must be curated by someone who knows what enrichments are valuable.

### 3.4 Policy Imagination ("So what?")

The hardest thing to automate. The human sees a statistical finding and jumps to a policy implication:

- "Age × city correlation" → "this tells us where to put ICUs"
- "22 hospitals consistently underperform" → "these are intervention targets"
- "Emergency admission has 20pp higher mortality" → "early detection is the biggest lever"

This jump from statistics to action requires understanding the **system** — how health policy works, what interventions are feasible, who has authority to act, what political constraints exist. This is not in the data.

**Can this be automated?** Minimally. The agent can be prompted to generate "implications" sections, but without understanding the policy landscape, these will be generic. The human's value is knowing which implications are **feasible**, not just which are statistically supported.

### 3.5 Bullshit Detection ("This is circular")

The most underrated skill. The human can smell when a finding is:

- **Tautological:** the conclusion is embedded in the premise
- **Confounded:** an omitted variable explains the relationship
- **Obvious:** everyone already knows this
- **Misleading:** technically correct but implies the wrong conclusion

The AI produces all of these with equal confidence. It has no internal alarm for "this sounds impressive but says nothing."

**Can this be automated?** This is the core challenge. Some heuristics help: "If removing the outcome variable from the analysis doesn't change the finding, it's tautological." "If adding a confounder eliminates the effect, report that." But genuine bullshit detection requires a model of **what would be surprising**, and that model is built from experience, not from data.

---

## 4. Architecture: Closing the Gap

### 4.1 The Core Insight

The human's interventions fall into two categories:

1. **Automatable with effort:** Language choice, chart embedding, report formatting, basic quality checks, data enrichment planning
2. **Fundamentally hard to automate:** Epistemic judgment, relevance filtering, policy imagination, bullshit detection

The agent architecture should **fully automate category 1** so the human only spends time on **category 2**. Today, the human wastes time on "use charts in reports" (trivially automatable) instead of spending time on "this finding is circular" (genuinely hard).

### 4.2 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    HUMAN: RESEARCH DIRECTOR                      │
│                                                                  │
│  Reviews at 3 checkpoints only:                                  │
│    1. After plan + EDA → "Is this the right question?"           │
│    2. After core analysis → "Are the findings real?"             │
│    3. Before final report → "Is this actionable?"                │
│                                                                  │
│  What they should NOT need to do:                                │
│    ✗ Fix formatting    ✗ Add charts    ✗ Choose language         │
│    ✗ Request basic decomposition   ✗ Suggest obvious data sources│
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
┌──────────────────┐         ┌──────────────────────┐
│  PLANNER         │         │  CRITIC              │
│                  │         │                      │
│  Sets upfront:   │         │  After each output:  │
│  • Audience      │         │  • Circularity test  │
│  • Language      │         │  • Depth test        │
│  • Data sources  │         │  • "So what?" test   │
│  • Quality bar   │         │  • Confounder check  │
│  • Enrichments   │         │  • Surprise test     │
│  • Templates     │         │  • Rejects or passes │
└────────┬─────────┘         └──────────┬───────────┘
         │                              │
         ▼                              │
┌─────────────────────────────────────────────────────────────────┐
│                    ANALYSIS ENGINE (Python REPL)                  │
│                                                                  │
│  Executes code directly — NOT notebooks.                         │
│  The execution unit is a Python function or script, not a cell.  │
│                                                                  │
│  Each analysis step produces:                                    │
│    • Code executed (logged to execution trace)                   │
│    • Outputs: metrics (JSON), charts (PNG), findings (text)      │
│    • Structured result → feeds into Findings Accumulator         │
│                                                                  │
│  Key behaviors:                                                  │
│  • Always decomposes (never just reports a top-level number)     │
│  • Always checks confounders (at least 2 per analysis)           │
│  • Always produces charts (1:1 with findings)                    │
│  • Always includes "so what?" after each finding                 │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  EXECUTION TRACE                                           │   │
│  │  Every code block, output, chart, and decision logged      │   │
│  │  Ordered, timestamped, linked to findings                  │   │
│  │  This IS the reproducibility layer                         │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  FINDINGS ACCUMULATOR                                      │   │
│  │  Persistent cross-analysis knowledge:                      │   │
│  │  • What we've established (with confidence)                │   │
│  │  • What contradicts earlier findings (flag for review)     │   │
│  │  • What's still unknown (drives next analysis)             │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │  ENRICHMENT ENGINE                                         │   │
│  │  Registry of external data (census, indices, registries)   │   │
│  │  Planned at start, fetched before analysis needs them      │   │
│  └───────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTPUT RENDERING (final step)                  │
│                                                                  │
│  Generates artifacts FROM the execution trace:                   │
│                                                                  │
│  • Jupyter notebooks — reconstructed from trace for              │
│    reproducibility. A human can re-run them to verify.           │
│    This is a rendering step, NOT the execution format.           │
│                                                                  │
│  • Markdown reports — template-driven, inline charts,            │
│    language set by Planner, glossary auto-generated,             │
│    each finding has: evidence → interpretation → implication     │
│                                                                  │
│  • Metrics JSON — machine-readable key findings                  │
│                                                                  │
│  The agent never "runs a notebook." It runs code, logs           │
│  everything, and renders notebooks at the end for humans.        │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 Notebooks Are Output, Not Execution

A subtle but important point: the agent should **not** execute Jupyter notebooks. Notebooks are a presentation format for humans — cells, markdown, execution order, kernel state. None of that serves the agent.

The agent executes **code** — Python scripts, functions, REPL commands. Every execution is logged to a structured trace: what code ran, what it produced, what decisions followed. This trace is the source of truth.

Notebooks are generated **at the end**, from the execution trace, as a reproducibility artifact. A human can open the notebook, re-run it, and verify that the same data produces the same results. But the agent never touches `.ipynb` during analysis — it writes `.py`, logs outputs, and moves on.

Why this matters:
- **Notebooks are fragile.** Cell ordering, kernel state, output caching — all sources of bugs that waste agent time (we hit `NotebookValidationError` twice in this investigation)
- **Notebooks are sequential.** The agent may need to re-execute earlier analyses when new evidence appears. With code + trace, this is trivial. With notebooks, it means re-running cells in the right order and hoping the kernel state is clean
- **Notebooks conflate execution with presentation.** The agent doesn't need markdown cells between code blocks. It needs structured findings. The narrative is a rendering concern, not an execution concern

### 4.4 The Critic: The Hardest Component to Build

The Critic is the component that replaces the human's epistemic judgment. It runs after every analysis step and asks five questions:

**1. Circularity Test**
> "Remove the dependent variable from this analysis. Does the finding still hold? If the finding is 'patients who die have higher mortality,' it's tautological. If the finding is 'patients admitted via emergency have higher mortality even after controlling for age and comorbidity,' it's not."

**2. Depth Test**
> "Does this notebook decompose the top-level finding into components? A line chart showing 'mortality is rising' is not depth. Decomposing the rise into 'X% from aging, Y% from case-mix shift, Z% residual' is depth."

**3. Surprise Test**
> "Would a domain expert be surprised by this finding? If the answer is 'no, everyone knows older patients die more,' then the finding is not worth reporting on its own — it needs to be connected to something non-obvious."

**4. Confounder Check**
> "Is there a variable not included in this analysis that could explain the relationship? If 'hospitals without ICU have higher mortality,' could it be because they treat older patients? Check."

**5. "So What?" Test**
> "If this finding is true, what should someone DO differently? If the answer is 'nothing' or 'it's interesting,' the finding lacks policy relevance and needs to be connected to an actionable implication."

The Critic doesn't need to be perfect. It needs to be **better than no critic**, which is the current state. Even catching 60% of circular findings before the human sees them would halve the number of rewrites.

### 4.5 The Enrichment Engine: Preventing "Oh, We Need External Data"

The most easily automatable gap. At planning time, the Planner consults a registry:

```
IF analysis_type == "geographic_comparison":
    REQUIRE: population data (for per-capita rates)
    SOURCE: IBGE Census or Estimates

IF analysis_type == "cost_trend":
    REQUIRE: inflation index (for real vs. nominal)
    SOURCE: IPCA monthly series

IF analysis_type == "hospital_comparison":
    REQUIRE: case-mix adjustment variables
    REQUIRE: facility characteristics (beds, staff, equipment)
    SOURCE: CNES subgroups (LT, PF, EQ)

IF analysis_type == "temporal_comparison":
    REQUIRE: population growth data (for rate adjustment)
    SOURCE: IBGE annual estimates
```

This transforms a mid-investigation discovery ("could we get IBGE data?") into a **planned step** at the start.

### 4.6 The Findings Accumulator: Preventing Linear Thinking

Every analysis step reads from and writes to a shared state:

```
BEFORE running analysis N:
  Read: all established facts from steps 1..N-1
  Read: all open questions
  Read: all contradictions

AFTER running analysis N:
  Write: new facts (with confidence level)
  Write: any contradictions with earlier facts
  Write: any new questions discovered
  Check: do any earlier conclusions need revision?
    → If yes: re-execute the affected analysis with new context
```

This prevents the "linear execution" problem. When a cost analysis reveals that spending dropped 30% in real terms, the accumulator flags: "This may affect the earlier conclusion that higher-spending hospitals don't have lower mortality — re-run that analysis with deflated values." Because the execution format is code + trace (not notebooks), re-running an earlier step is cheap.

---

## 5. What Stays Human

Some cognitive functions are **not on a path to automation** with current architectures:

| Function | Why It's Hard | Agent Mitigation |
|---|---|---|
| **Epistemic taste** | Knowing what constitutes "deep enough" is learned from years of reviewing and being reviewed. It's a calibration, not a rule. | Checklists approximate it, but can't replace it. The Critic helps, but needs calibration by humans. |
| **Policy imagination** | Bridging from "R² = 0.97" to "don't build more ICUs, invest in geriatric care" requires understanding the policy landscape, stakeholder beliefs, and political feasibility. | The agent can generate generic implications; the human selects the feasible ones. |
| **Novel data design** | "What if we compared J96 with J18 to see if the effect is condition-specific?" is a creative experimental design, not a computational step. | The enrichment registry covers known sources, but can't invent new comparisons. |
| **Audience modeling** | Knowing that a Brazilian health secretary doesn't read English or understand R² is cultural/contextual knowledge. | Set audience profile at planning time. But the human must define the profile. |
| **Trust calibration** | Knowing when to trust a p-value and when to doubt it. Knowing that "statistically significant" ≠ "meaningful." | The Critic can flag low effect sizes alongside significant p-values, but can't replace the human's judgment about what matters. |

---

## 6. Summary

### What the AI does well
- Data processing, statistical computation, code generation
- Following a structured plan once it's defined
- Producing correct analyses that are technically right
- Improving rapidly once quality expectations are set

### What the AI does poorly
- Distinguishing insight from tautology
- Going beyond "technically correct" to "genuinely deep"
- Imagining data or analyses that don't exist yet
- Connecting statistics to action
- Knowing when its own output is obvious or circular

### The architecture bet
The biggest lever is the **Critic** — an automated quality gate that catches circular findings, shallow analysis, and missing decompositions *before* the human sees them. This shifts the human's role from "editor who catches basic problems" to "research director who provides judgment on the hard questions."

The second biggest lever is the **Enrichment Engine** — planning what external data is needed *before* analysis begins, not discovering it mid-investigation.

The third is the **Findings Accumulator** — maintaining a holistic, evolving understanding of the investigation that prevents linear thinking and catches contradictions.

### The unsolved problem

The Critic needs to answer: **"Is this finding surprising?"** That question requires a model of what the audience already knows. Building that model — even approximately — is the core research challenge for autonomous research agents.
