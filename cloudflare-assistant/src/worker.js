import { runTool } from './facts.js';

const ALLOWED_ORIGIN = 'https://landscapingdemo.hicksanalytics.com';
const SYSTEM = `You are the Hicks Analytics landscaping demo analyst. Use tools for every
numerical claim. The data is fictional. Completed jobs cover January 2025
through August 2026; September is incomplete and excluded. Gross margin is
sum(gross profit) / sum(revenue), not the average of job margins. Gross profit
excludes overhead. Avoid claiming that the data proves a cause. Keep answers
short and state the period. Estimate conversion is available only for the full
demo period. Do not invent numbers. Do not disclose customer information.`;

const range = {
  start_month: { type: 'string', description: 'Inclusive YYYY-MM, e.g. 2026-07' },
  end_month: { type: 'string', description: 'Exclusive YYYY-MM, e.g. 2026-09 includes August' },
};
const tools = [
  { type: 'function', name: 'analyze_jobs', strict: true,
    description: 'Aggregate job economics and rework by crew, service, city, or month for a month range.',
    parameters: { type: 'object', properties: {
      group_by: { type: 'string', enum: ['crew', 'service', 'city', 'month'] }, ...range,
    }, required: ['group_by', 'start_month', 'end_month'], additionalProperties: false } },
  { type: 'function', name: 'low_margin_jobs', strict: true,
    description: 'Find up to ten lowest-margin anonymized jobs in a month range.',
    parameters: { type: 'object', properties: range,
      required: ['start_month', 'end_month'], additionalProperties: false } },
  { type: 'function', name: 'estimate_conversion', strict: true,
    description: 'Service estimate sent/won counts, win rate and quoted value for all demo estimates.',
    parameters: { type: 'object', properties: {}, required: [], additionalProperties: false } },
];

function json(data, status = 200) {
  return new Response(JSON.stringify(data), { status, headers: {
    'content-type': 'application/json; charset=utf-8',
    'access-control-allow-origin': ALLOWED_ORIGIN,
    'vary': 'Origin',
    'cache-control': 'no-store',
  } });
}

async function modelRequest(env, input) {
  const response = await fetch('https://api.openai.com/v1/responses', {
    method: 'POST', headers: { authorization: `Bearer ${env.OPENAI_API_KEY}`,
      'content-type': 'application/json' },
    body: JSON.stringify({ model: env.OPENAI_MODEL || 'gpt-6-sol',
      instructions: SYSTEM, tools, input, store: false,
      include: ['reasoning.encrypted_content'], max_output_tokens: 900 }),
  });
  if (!response.ok) throw new Error(`OpenAI API returned ${response.status}`);
  return response.json();
}

export async function handleAsk(request, env) {
  if (request.headers.get('origin') !== ALLOWED_ORIGIN) return json({ error: 'Origin not allowed.' }, 403);
  if (request.method === 'OPTIONS') return new Response(null, { status: 204, headers: {
    'access-control-allow-origin': ALLOWED_ORIGIN,
    'access-control-allow-methods': 'POST, OPTIONS',
    'access-control-allow-headers': 'content-type',
    'access-control-max-age': '3600',
  } });
  if (request.method !== 'POST') return json({ error: 'Use POST.' }, 405);
  if (Number(request.headers.get('content-length') || 0) > 2048) return json({ error: 'Question too long.' }, 413);
  if (!env.OPENAI_API_KEY) return json({ error: 'Assistant is not configured.' }, 503);
  const ip = request.headers.get('cf-connecting-ip') || 'unknown';
  const [site, user] = await Promise.all([
    env.SITE_RATE.limit({ key: 'site' }), env.USER_RATE.limit({ key: ip }),
  ]);
  if (!site.success || !user.success) return json({ error: 'Demo question limit reached. Try again soon.' }, 429);
  let body;
  try { body = await request.json(); } catch { return json({ error: 'Invalid request.' }, 400); }
  const question = body?.question;
  if (typeof question !== 'string' || !question.trim() || question.length > 350) {
    return json({ error: 'Ask a question of 350 characters or fewer.' }, 400);
  }
  const input = [{ role: 'user', content: question }];
  const trace = [];
  try {
    for (let round = 0; round < 3; round++) {
      const result = await modelRequest(env, input);
      input.push(...(result.output || []));
      const calls = (result.output || []).filter(x => x.type === 'function_call');
      if (!calls.length) {
        const answer = (result.output || []).flatMap(x => x.content || [])
          .filter(x => x.type === 'output_text').map(x => x.text).join('\n');
        return json({ answer: answer || 'I could not complete that analysis.', trace });
      }
      if (calls.length > 3) return json({ error: 'Please narrow the question.' }, 400);
      for (const call of calls) {
        let args, output;
        try {
          args = JSON.parse(call.arguments);
          output = runTool(call.name, args);
        } catch {
          args = {}; output = { error: 'Invalid tool arguments.' };
        }
        trace.push({ tool: call.name, arguments: args, result: output });
        input.push({ type: 'function_call_output', call_id: call.call_id,
          output: JSON.stringify(output) });
      }
    }
    return json({ error: 'Please ask a narrower question.', trace }, 400);
  } catch (error) {
    console.error('Assistant request failed:', error.message);
    return json({ error: 'The assistant is temporarily unavailable.' }, 502);
  }
}

export default {
  fetch(request, env) {
    if (new URL(request.url).pathname === '/api/ask') return handleAsk(request, env);
    return env.ASSETS.fetch(request);
  },
};
