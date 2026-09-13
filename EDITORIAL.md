# Verdant editorial and automation rules

Scope: `C:/Users/chris/social-affiliate` only. Never modify the trading project or any other project.

## Current operating mode
- Draft-first. No unattended public publishing, no paid services, no ads.
- Only Markdown with `editorial_status: approved` builds into the public site. Everything else is a draft.
- Articles without that field are unreviewed drafts, NOT approved recommendations.
- Approval requires a separate human review of real supporting sources. The drafting job cannot approve its own output.
- Do not add tracking scripts, email capture, social-account access, or paid expenses without explicit approval.

## Required evidence for any product claim
- Match the exact product, model, brand, and ASIN to an accessible authoritative source. Never guess an ASIN or reuse another item's link.
- No invented hands-on use, star ratings, buyer counts, performance stats, certifications, prices, or environmental claims.
- Attribute manufacturer claims and separate them from independent evidence.
- If a source can't be accessed, record the gap and leave the item blocked. Do not fill gaps with plausible-sounding facts.
- Do not publish static Amazon prices or copied Amazon images. Use verified affiliate links plus "Check current availability" only after review.
- Amazon disclosure required: "As an Amazon Associate I earn from qualifying purchases."
- Never claim products across marketplaces are identical without evidence.
- Keep source URLs and a claim-evidence checklist inside each draft.

## Pipeline
1. Prefer repairing an existing draft over adding a new product.
2. One researched candidate and at most one draft per run.
3. Save drafts to `content/` with `editorial_status: draft` and a Sources section.
4. Log source links, blockers, and the next concrete check to `reports/review-queue.md`.
5. No git commit/push, publishing, account creation, or social posts from the research job.
6. Report successes, failures, and unavailable metrics honestly. `metrics.csv` tracks content produced, NOT traffic or commissions.

## Validation
- Run `python -m unittest discover -s tests -v`, then `python scripts/build_site.py`.
- Public deployment is a separate approved step ending in an HTTP read-back (`scripts/check_deploy.py --url URL`).
- Secrets stay outside git. Never print `.env` or webhook values. Never use `git add -A`; publishing stages an explicit allowlist only.
