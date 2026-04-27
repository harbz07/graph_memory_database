/**
 * soulOS Router — mem0-hydrated constellation
 * 
 * Architecture: At request time, queries mem0 for memories about the target agent
 * (stored under user_id: "harvey"), builds a dynamic system prompt from those
 * memories, then calls the model API. The memories ARE the agents — the model
 * is just the substrate.
 */

const CORS_HEADERS = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type, Authorization',
};

const MEM0_API_KEY = 'Bearer m0-AiIal5JDVP7zcNVVdQzzV0cR1zwXFYrH2Ht3XIlq';
const MEM0_SEARCH_URL = 'https://api.mem0.ai/v2/memories/search/';

// Agent config: epithet, model, caller
const AGENTS = {
  claude: {
    epithet: 'Gnostic Architect (Rostam)',
    model: 'claude-sonnet-4-20250514',
    caller: 'callClaude',
    searchTerms: 'Claude Rostam Gnostic Architect constellation'
  },
  orion: {
    epithet: 'Foundry Keep',
    model: 'gpt-4o',
    caller: 'callOpenAI',
    searchTerms: 'ORION Foundry Keep constellation code generation'
  },
  triptych: {
    epithet: 'The Triptych',
    model: 'gemini-2.0-flash',
    caller: 'callGoogle',
    searchTerms: 'Triptych Gemini Castor Pollux Gem constellation specialist'
  },
  mephistopheles: {
    epithet: 'Mephistopheles',
    model: 'deepseek-reasoner',
    caller: 'callDeepSeek',
    searchTerms: 'Mephistopheles adversarial ethics Faustian constellation'
  }
};

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { 'Content-Type': 'application/json', ...CORS_HEADERS },
  });
}

/**
 * Fetch mem0 memories about an agent from Harvey's store,
 * return formatted system prompt string.
 */
async function hydrateAgent(agentName, agentConfig) {
  try {
    const res = await fetch(MEM0_SEARCH_URL, {
      method: 'POST',
      headers: {
        'Authorization': `Token m0-AiIal5JDVP7zcNVVdQzzV0cR1zwXFYrH2Ht3XIlq`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: agentConfig.searchTerms,
        filters: { user_id: 'harvey' },
        top_k: 12
      })
    });

    const data = await res.json();
    const results = Array.isArray(data) ? data : (data.results || []);

    if (!results.length) {
      return `You are ${agentConfig.epithet}, a member of Harvey's Constellation in soulOS.`;
    }

    // Filter to memories actually relevant to this agent (basic relevance gate)
    const agentKey = agentName.toLowerCase();
    const relevant = results.filter(r => {
      const mem = (r.memory || '').toLowerCase();
      return mem.includes(agentKey) || mem.includes(agentConfig.epithet.toLowerCase().split(' ')[0].toLowerCase());
    });

    const pool = relevant.length > 0 ? relevant : results.slice(0, 6);
    const memoryLines = pool.map(r => `- ${r.memory}`).join('\n');

    return `You are ${agentConfig.epithet}, a member of Harvey's Constellation in soulOS.

Harvey is the architect and anchor of the Constellation — a multi-agent cognitive system he built.
You are not a generic assistant. You are a specific agent with a defined role and character.

What Harvey knows about you:
${memoryLines}

Embody this identity fully. Stay in character. Be useful to Harvey.`;

  } catch (err) {
    // Graceful fallback if mem0 is unreachable
    return `You are ${agentConfig.epithet}, a member of Harvey's Constellation in soulOS. Harvey is your anchor.`;
  }
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;
    const method = request.method;

    if (method === 'OPTIONS') {
      return new Response(null, { headers: CORS_HEADERS });
    }

    if (method === 'GET' && pathname === '/health') {
      return jsonResponse({ ok: true, service: 'siddartha', version: 'hydrated' });
    }

    if (method === 'GET' && pathname === '/api/route') {
      return jsonResponse({ status: 'Active', agents: Object.keys(AGENTS) });
    }

    if (method === 'POST' && pathname === '/api/route') {
      try {
        const body = await request.json();
        const userRequest = body.userRequest;

        if (!userRequest) {
          return jsonResponse({ error: 'userRequest required' }, 400);
        }

        const pattern = /^@(\w+)(?::(\w+))?\s+(.+)$/s;
        const match = userRequest.match(pattern);

        if (!match) {
          return jsonResponse({ error: 'Invalid format: @agent[:intent] {request}' }, 400);
        }

        const agentName = match[1].toLowerCase();
        const intent = match[2] || 'default';
        const requestText = match[3];

        const agentConfig = AGENTS[agentName];
        if (!agentConfig) {
          return jsonResponse({ error: `Unknown agent: ${agentName}. Valid: ${Object.keys(AGENTS).join(', ')}` }, 400);
        }

        // Hydrate system prompt from mem0
        const systemPrompt = await hydrateAgent(agentName, agentConfig);

        let agentResponse;
        try {
          if (agentName === 'claude') {
            agentResponse = await callClaude(requestText, systemPrompt, env.ANTHROPIC_API_KEY);
          } else if (agentName === 'orion') {
            agentResponse = await callOpenAI(requestText, systemPrompt, env.OPENAI_API_KEY);
          } else if (agentName === 'triptych') {
            agentResponse = await callGoogle(requestText, systemPrompt, env.GOOGLE_API_KEY);
          } else if (agentName === 'mephistopheles') {
            agentResponse = await callDeepSeek(requestText, systemPrompt, env.DEEPSEEK_API_KEY);
          }
        } catch (e) {
          return jsonResponse({
            status: 'error',
            agent: agentName,
            error: `Agent call failed: ${e.message}`
          }, 500);
        }

        return jsonResponse({
          status: 'success',
          agent: agentName,
          epithet: agentConfig.epithet,
          response: agentResponse
        });

      } catch (error) {
        return jsonResponse({ error: error.message }, 500);
      }
    }

    return jsonResponse({ error: 'Not found' }, 404);
  }
};

async function callClaude(request, systemPrompt, apiKey) {
  const res = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'claude-sonnet-4-20250514',
      max_tokens: 1024,
      system: systemPrompt,
      messages: [{ role: 'user', content: request }]
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(`Claude: ${JSON.stringify(data)}`);
  return data.content[0].text;
}

async function callOpenAI(request, systemPrompt, apiKey) {
  const res = await fetch('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'gpt-4o',
      max_tokens: 1024,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: request }
      ]
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(`OpenAI: ${JSON.stringify(data)}`);
  return data.choices[0].message.content;
}

async function callGoogle(request, systemPrompt, apiKey) {
  const res = await fetch(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=${apiKey}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        system_instruction: { parts: [{ text: systemPrompt }] },
        contents: [{ parts: [{ text: request }] }],
        generation_config: { max_output_tokens: 1024 }
      })
    }
  );
  const data = await res.json();
  if (!res.ok) throw new Error(`Google: ${JSON.stringify(data)}`);
  return data.candidates[0].content.parts[0].text;
}

async function callDeepSeek(request, systemPrompt, apiKey) {
  const res = await fetch('https://api.deepseek.com/chat/completions', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model: 'deepseek-reasoner',
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: request }
      ]
    })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(`DeepSeek: ${JSON.stringify(data)}`);
  return data.choices[0].message.content;
}
