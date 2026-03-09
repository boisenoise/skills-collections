# Readiness Scoring Reference

<!-- SCOPE: GO/NO-GO conditions and coverage thresholds ONLY. For scoring formula, Anti-Hallucination, and AC Matrix format, see SKILL.md. -->

For Readiness Score formula, Anti-Hallucination Verification, and Task-AC Coverage Matrix format, see [SKILL.md §Final Assessment Model](../SKILL.md#final-assessment-model).

---

## GO/NO-GO Verdict

| Verdict | Meaning | Conditions |
|---------|---------|------------|
| **GO** | Story ready for execution | Penalty Points = 0, Readiness Score >= 5, Anti-Hallucination VERIFIED |
| **NO-GO** | Story requires fixes | Any of: Penalty Points >0, Score <5, FLAGGED claims |

---

## Coverage Thresholds

| Coverage | Status | Gate Impact |
|----------|--------|-------------|
| 100% | Full coverage | No penalty |
| 80-99% | Partial | -3 penalty points |
| <80% | Insufficient | -5 penalty points, NO-GO |

---

**Version:** 2.0.0
**Last Updated:** 2026-02-07
