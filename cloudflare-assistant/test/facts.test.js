import test from 'node:test';
import assert from 'node:assert/strict';
import { runTool } from '../src/facts.js';
import { handleAsk } from '../src/worker.js';

test('aggregation uses ratio of sums across months', () => {
  const july = runTool('analyze_jobs', { group_by: 'crew', start_month: '2026-07', end_month: '2026-08' });
  const full = runTool('analyze_jobs', { group_by: 'crew', start_month: '2026-06', end_month: '2026-08' });
  assert.equal(july.rows.length, 5);
  assert.equal(full.rows.length, 5);
  assert.ok(full.rows.every(x => x.jobs > 0 && x.gross_margin_pct <= 100));
  const row = full.rows[0];
  assert.equal(row.gross_margin_pct, Math.round(10000 * row.gross_profit / row.revenue) / 100);
});

test('rejects out of range months and unsupported groupings', () => {
  assert.ok(runTool('analyze_jobs', { group_by: 'crew', start_month: '2026-09', end_month: '2026-10' }).error);
  assert.ok(runTool('analyze_jobs', { group_by: 'crew;DROP', start_month: '2026-07', end_month: '2026-08' }).error);
});

test('public endpoint rejects unknown origin before calling upstream', async () => {
  const response = await handleAsk(new Request('https://example.com/api/ask', {
    method: 'POST', headers: { origin: 'https://evil.example', 'content-type': 'application/json' },
    body: JSON.stringify({ question: 'Show margins' }),
  }), {});
  assert.equal(response.status, 403);
});

test('model function request receives data before final answer', async () => {
  const originalFetch = globalThis.fetch;
  let calls = 0;
  globalThis.fetch = async (_, options) => {
    calls++;
    const body = JSON.parse(options.body);
    if (calls === 1) return Response.json({ output: [{
      type: 'function_call', name: 'analyze_jobs', call_id: 'call_demo',
      arguments: JSON.stringify({ group_by: 'crew', start_month: '2026-07', end_month: '2026-08' }),
    }] });
    const toolResult = body.input.at(-1);
    assert.equal(toolResult.type, 'function_call_output');
    assert.equal(toolResult.call_id, 'call_demo');
    assert.equal(JSON.parse(toolResult.output).rows.length, 5);
    return Response.json({ output: [{ type: 'message', content: [
      { type: 'output_text', text: 'Here is the July crew breakdown.' },
    ] }] });
  };
  try {
    const env = {
      OPENAI_API_KEY: 'test-only',
      SITE_RATE: { limit: async () => ({ success: true }) },
      USER_RATE: { limit: async () => ({ success: true }) },
    };
    const response = await handleAsk(new Request('https://example.com/api/ask', {
      method: 'POST', headers: { origin: 'https://landscapingdemo.hicksanalytics.com',
        'content-type': 'application/json', 'cf-connecting-ip': '203.0.113.1' },
      body: JSON.stringify({ question: 'How did crews perform in July?' }),
    }), env);
    assert.equal(response.status, 200);
    const data = await response.json();
    assert.equal(data.answer, 'Here is the July crew breakdown.');
    assert.equal(data.trace[0].result.rows.length, 5);
    assert.equal(calls, 2);
  } finally {
    globalThis.fetch = originalFetch;
  }
});
