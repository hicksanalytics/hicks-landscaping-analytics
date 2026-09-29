# Static Cloudflare demo assistant

This is the Cloudflare version of **Ask the Data** for
`landscapingdemo.hicksanalytics.com`. It has a small fictional aggregate data
snapshot (`facts.json`), a Worker that keeps the OpenAI key on the server, and
an embeddable chat widget. It does not change the current live site until
deployed and its script tag is added to the static page.

## Build and test

From the repository root, run `python cloudflare-assistant/build_facts.py`
after updating `outputs/job_profitability.csv` and
`outputs/estimate_performance.csv`. In `cloudflare-assistant`, run
`npm test` and `npm install` before deployment. The snapshot deliberately
excludes the incomplete September 2026 jobs and customer names.

## Publish when the site source and Cloudflare account are available

1. In `cloudflare-assistant`, configure a unique rate-limit namespace ID in
   `wrangler.jsonc` if the sample IDs overlap with any existing binding in the
   account. The Worker is configured for the
   `landscapingai.hicksanalytics.com` custom domain.
2. Set the Worker secret with `npx wrangler secret put OPENAI_API_KEY`.
   Set a budget/usage alert for the API project.
3. Run `npx wrangler deploy` from this directory. Verify the Worker serves
   `/widget.js` and accepts `/api/ask` from the demo page.
4. Add this tag before `</body>` in the **actual static demo HTML** and
   redeploy that page:

   ```html
   <script defer src="https://landscapingai.hicksanalytics.com/widget.js"></script>
   ```

The assistant is intentionally a separate Worker so the existing static demo
can keep its deployment and domain. The origin check allows only
`https://landscapingdemo.hicksanalytics.com`. This is not user authentication:
an anonymous public endpoint can still be called by scripted clients that
forge an Origin header. Cloudflare's per-visitor and site limits reduce casual
abuse but are approximate and location-specific. Monitor costs after launch.

The Python Streamlit implementation in the repository has the same business
concept and additional live DuckDB tool execution. The static deployment
uses approved aggregate data and anonymized low-margin samples for predictable
performance and bounded exposure.
