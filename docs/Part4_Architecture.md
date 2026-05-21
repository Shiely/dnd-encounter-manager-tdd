# D&D Encounter Manager

## Part 4: Architectural Description and Agent Handoff Guide

**Version:** 1.0 | **Date:** May 2026

**Architecture:** Hexagonal (Ports and Adapters)

**Stack:** Python 3.12 + PySide6 | TDD on macOS | GitHub Repository

**Author:** james | **Location:** West Slope, OR, United States

*Prepared Monday, 04 May 2026 — Implementation-Ready Handoff Package for AI Coding Agent*

---

## Table of Contents

1. Purpose and How to Use This Document
2. Architecture: Hexagonal (Ports and Adapters)
   - 2.1 Chosen Style and Rationale
   - 2.2 Layer Diagram
   - 2.3 Import Rules — Enforced by mypy and CI
3. macOS Development Environment Setup
4. Complete File and Folder Structure
5. Domain Layer
6. Ports Layer
7. Application Layer
8. Adapters Layer
9. Bootstrap and Dependency Injection
10. GitHub Actions CI Configuration
11. Test-Driven Development Build Sequence
12. Key Design Decisions and Rationale
13. Checklist for the Coding Agent

---

## 1. Purpose and How to Use This Document

This document is the complete architectural specification for the D&D Encounter Manager desktop application. It is written as a handoff package for an AI coding agent. Read the entire document before writing a single line of code. The companion documents — Part 1 (Requirements), Part 2 (Analysis Artifacts), and Part 3 (Behavioral Specification) — contain the full functional and behavioral context.

This document contains the architectural decisions, implementation contracts, TDD build sequence, and environment setup instructions.

> **KEY COMMITMENTS — UNCONDITIONAL. NEVER VIOLATE.**
>
> - **Dependency inversion rule:** Code dependencies always point inward. Domain never imports adapters. Ports never import adapters. Application never imports adapters.
> - **HP automation invariant:** No code path other than an explicit DM-initiated edit command may write `current_hp` on any `EncounterEntity`.
> - **Port fidelity:** Every outbound port interface must have at least one stub implementation in `tests/conftest.py` that satisfies mypy before any application code is written.
> - **TDD sequence:** Red-green-refactor on every unit. No implementation file is created before its test file.

---

## 2. Architecture: Hexagonal (Ports and Adapters)

### 2.1 Chosen Style and Rationale

Architecture: Hexagonal (Ports and Adapters), coined by Alistair Cockburn.

**Key References:**
- *Game Programming Patterns*, Robert Nystrom (2014)
- *Clean Architecture*, Robert C. Martin (2017)
- *Design Patterns*, Gamma et al. (1994)

**Rationale for Hexagonal:**
1. Explicit named ports make every extension point discoverable.
2. Adapters are independently implementable.
3. The domain core contains zero external imports.
4. Future web migration is an adapter swap.

### 2.2 Layer Diagram

(See original PDF for diagram)

### 2.3 Import Rules

| Module Zone     | Permitted Imports                  | Prohibited Imports                     |
|-----------------|------------------------------------|----------------------------------------|
| `domain/`       | Python stdlib only                 | ports, application, adapters, pydantic, PySide6, jsonschema |
| `ports/`        | domain, typing                     | application, adapters                  |
| `application/`  | domain, ports, stdlib              | adapters, PySide6, jsonschema, platformdirs |
| `adapters/`     | application, ports, domain, any external | Other adapters (directly)         |
| `bootstrap.py`  | Everything (intentional exception) | —                                      |

> **Required:** Every domain file must start with:
> `# DOMAIN LAYER: stdlib imports only. No external packages. No ports. No adapters.`

---

## 3. macOS Development Environment Setup

(Full setup instructions from PDF — uv, Python 3.12, GitHub CLI, etc.)

## 4. Complete File and Folder Structure

(See original PDF for detailed tree)

## 5–13. Domain, Ports, Application, Adapters, Bootstrap, CI, TDD Sequence, Decisions & Checklist

**Full detailed content available in the original PDF.**

> **Note:** This Markdown version is a summarized reference. For complete details (especially the full TDD sequence in Section 11 and the Checklist in Section 13), please refer to the original `DND_Encounter_Manager_Part4_Architecture.pdf` in Google Drive.

---

*Converted from PDF on 2026-05-20*