### Project Initiation Report: Persona-Driven API Hackathon System

#### 1\. EXECUTIVE SUMMARY & STRATEGIC VISION

##### The Problem of "Flat" LLM Responses

Current Large Language Model (LLM) implementations and standard Retrieval-Augmented Generation (RAG) systems suffer from "flat" output—providing identical answers regardless of the user's professional context. In specialized fields, this leads to  **semantic drift**  and  **contextual loss** . For example, a request for information on a specific protein will yield the same generic summary for a Pathologist as it does for a Medicinal Chemist, despite their vastly different requirements for clinical literature versus chemical properties. Standard "passive wrappers" fail to respect the unique terminological and data-sourcing needs of the professional user.

##### The Value Proposition: Intelligent Orchestration

The proposed solution is a  **Generalized Persona-Driven System**  that moves beyond the "simple wrapper" model. This system acts as an intelligent orchestrator, intercepting queries and using a "binding contract" to dictate the entire processing pipeline. By leveraging persona metadata, the system performs specialized terminology extraction, routes queries to domain-specific endpoints, and applies role-appropriate synthesis templates. This architecture ensures that the AI's "vibe" and technical depth are dynamically reconfigured to match the user's expertise.

##### Hackathon Event Context

The development will take place under the following strategic parameters:| Category | Details || \------ | \------ || **Event** | Gladstone Institute Hackathon || **Timeline** | July 7–13, 2026 || **Participant Scale** | 500 participants || **Team Composition** | 2 members || **Resources** | $200 API workspace credits (Claude/Anthropic) |

#### 2\. SYSTEM ARCHITECTURE & COMPONENT BLUEPRINT

##### High-Level Architecture Overview

The system follows a "Dotted Line" architecture, distinguishing between the existing RAG layer (standard retrieval) and our  **Persona-Driven Orchestration Layer** . This added layer sits between the user and the LLM, injecting persona-specific logic into the request lifecycle. To maintain architectural independence and generalize the solution, we are explicitly bypassing Claude’s native "science" connectors in favor of direct, open-source API integrations.

##### Component Breakdown

* **Front-End UI Scaffolding:**  A "thin scaffold" custom-built for the demo. By utilizing a custom UI rather than the standard Claude interface, we demonstrate a standalone product capable of independent deployment.  
* **Backend API Orchestration:**  The central engine utilizing the Claude API for intelligent routing. It translates the user's role into a set of execution instructions.  
* **The Config Contract (YAML):**  The "Binding Contract" of the system. This schema-driven routing file defines:  
* **Terminology Mapping:**  Associations between professional roles and specific keywords (e.g., specific drug nomenclature for chemists).  
* **Target Domain Endpoints:**  Direct routing to authoritative repositories.  
* **Importance Weights:**  Numerical values that influence how the LLM prioritizes retrieved data points during the final synthesis.  
* **Data Connector Layer:**  A modular layer using  **dependency injection**  to interface with authoritative repositories:  **PubChem, ChEMBL, PubMed, and PDB** . This layer includes "mock fallbacks" to mitigate latency and ensure demo stability during high-traffic hackathon periods.

#### 3\. TECHNICAL WORKFLOWS

##### Persona Identification Workflow

The system employs a two-pronged approach to establish user context:

1. **Active Profile Capture:**  Extracting professional data (e.g., Job Title, Organization) from stored user metadata at the session level.  
2. **Dynamic Contextual Extraction:**  Using LLM analysis to identify the persona and intent directly from the query syntax if profile metadata is absent or ambiguous.

##### Query Processing & Schema-Driven Routing

The orchestrator processes every query through the following high-velocity pipeline:

1. **Step 1: Role Identification:**  Determination of one of the four core personas:  **Medicinal Chemist, Pathologist, Regulatory Specialist, or Clinical Trial Lead.**  
2. **Step 2: Endpoint Selection:**  The YAML contract routes the query to specific authoritative sources (e.g., a Medicinal Chemist hits ChEMBL/PubChem; a Pathologist hits PubMed).  
3. **Step 3: Terminology & Importance Filtering:**  The system applies "Importance Weights" to the retrieved data, ensuring the most relevant technical sections are prioritized for synthesis.  
4. **Step 4: Spec-Driven Synthesis:**  Application of persona-specific synthesis templates to produce a response that matches the user’s professional vocabulary and analytical depth.

#### 4\. HACKATHON DEVELOPMENT ROADMAP

##### Phase 1: Centralized API Workspace & Environment Setup (Day 1\)

Establish a centralized Anthropic API workspace to manage the  $200 credit allocation ($ 100k/20x token limit). This phase includes provisioning team access and setting up the development environment to facilitate collaborative API testing without utilizing restricted corporate accounts.

##### Phase 2: Core YAML Schema Definition (Day 2\)

Codify the "Binding Contract" for the four target personas. This involves mapping the specific data source preferences and terminology associations for the Medicinal Chemist, Pathologist, Regulatory Specialist, and Clinical Trial Lead.

##### Phase 3: Data Connector & Latency Mitigation (Day 3-4)

Develop modules for the four primary biomedical APIs. To ensure the system is "generalized," we will prioritize direct API calls over native Claude Science tools. Local/offline mock datasets will be generated for each connector to serve as fail-safes during the demo.

##### Phase 4: Integration & Spec-Driven Demo (Day 5-7)

Assemble the backend orchestration engine with the frontend scaffold. Conduct rapid testing to verify that identical queries yield distinct, persona-appropriate responses. Finalize the "Persona-Driven Spec" for presentation.

#### 5\. DESIGN NOTES & CONSTRAINTS

##### Cross-Domain Scalability via Dependency Injection

While the Gladstone context focuses on life sciences, the system architecture is designed for "hot-swapping" domains. By using dependency injection for the data connectors and swapping the YAML configuration, the system can be instantly repurposed for Law (targeting patent databases) or Business Analysis (targeting financial filings) without altering the core orchestration logic.

##### Standardization vs. Customization

The primary design constraint is the elimination of the "one-size-fits-all" response. The system is architected to ensure that a Pathologist and a Chemist never receive the same response. This is achieved by constraining the LLM's data fetch to the specific, hard-coded endpoints and terminology filters defined in the YAML contract, ensuring technical authority and professional precision in every output.  
