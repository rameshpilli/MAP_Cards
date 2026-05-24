#!/usr/bin/env node

/**
 * MAPrompt Cards CLI.
 *
 * Usage:
 *   npx map-cards install <card-name> [--target codex|claude|markdown|prompt] [--dir .]
 *   npx map-cards list
 *   npx map-cards search <query>
 *   npx map-cards info <card-name>
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const http = require('http');

const API_BASE = (process.env.MAP_API_URL || 'http://localhost:8000/api').replace(/\/$/, '');
const REGISTRY_URL = process.env.MAP_REGISTRY_URL ||
    'https://raw.githubusercontent.com/map-cards/map-cards/main/web/data/cards.json';
const TARGETS = new Set(['codex', 'claude', 'cloud', 'markdown', 'prompt', 'json', 'yaml']);

function normalizeTarget(target) {
    return target === 'cloud' ? 'claude' : target;
}

function request(url, options = {}) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(url);
        const mod = parsed.protocol === 'https:' ? https : http;
        const req = mod.request({
            hostname: parsed.hostname,
            port: parsed.port,
            path: `${parsed.pathname}${parsed.search}`,
            method: options.method || 'GET',
            headers: { 'Content-Type': 'application/json' },
            timeout: 8000,
        }, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode >= 400) {
                    reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                    return;
                }
                try {
                    resolve(JSON.parse(data));
                } catch (err) {
                    reject(err);
                }
            });
        });
        req.on('timeout', () => req.destroy(new Error('Request timed out')));
        req.on('error', reject);
        if (options.body) req.write(JSON.stringify(options.body));
        req.end();
    });
}

function slugPath(name) {
    return encodeURIComponent(name);
}

async function fetchRegistryCards() {
    return request(REGISTRY_URL);
}

async function fetchCard(name) {
    try {
        return await request(`${API_BASE}/cards/${slugPath(name)}`);
    } catch (_) {
        const cards = await fetchRegistryCards();
        const card = cards.find(item => item.name === name);
        if (!card) throw new Error(`Card '${name}' not found`);
        return card;
    }
}

async function fetchBootstrap(name, target) {
    try {
        const data = await request(`${API_BASE}/cards/${slugPath(name)}/download`, {
            method: 'POST',
            body: { target },
        });
        return data.bootstrap;
    } catch (_) {
        const card = await fetchCard(name);
        return buildBootstrap(card, target);
    }
}

function cardManifest(card) {
    return {
        name: card.name,
        title: card.title,
        description: card.description,
        author: card.author,
        author_url: card.author_url || '',
        category: card.category,
        tags: card.tags || [],
        platforms: card.platforms || [],
        version: card.version || '1.0.0',
        license: card.license || 'MIT',
        variables: card.variables || [],
        prompt: card.prompt,
    };
}

function variablesMarkdown(variables) {
    if (!variables || variables.length === 0) return 'No variables declared.';
    return variables.map(variable => {
        const defaultText = variable.default ? ` Default: \`${variable.default}\`.` : '';
        return `- \`${variable.name}\`: ${variable.description}${defaultText}`;
    }).join('\n');
}

function renderMarkdown(card, codex = false) {
    const heading = codex ? `# MAPrompt Card: ${card.title}` : `# ${card.title}`;
    const codexUsage = codex
        ? `\n## Codex Usage\nUse this card as task-specific operating guidance when the user asks for ${card.description.toLowerCase()}\n`
        : '';
    return `${heading}

Name: \`${card.name}\`
Version: \`${card.version || '1.0.0'}\`
Category: \`${card.category}\`
Platforms: ${(card.platforms || []).join(', ')}
License: ${card.license || 'MIT'}

## Description
${card.description}
${codexUsage}
## Variables
${variablesMarkdown(card.variables || [])}

## Prompt
${card.prompt.trim()}
`;
}

function renderYaml(card) {
    const manifest = cardManifest(card);
    const lines = [];
    for (const [key, value] of Object.entries(manifest)) {
        if (Array.isArray(value)) {
            if (value.length === 0) {
                lines.push(`${key}: []`);
            } else if (typeof value[0] === 'object') {
                lines.push(`${key}:`);
                value.forEach(item => {
                    lines.push('  - ' + Object.entries(item).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join('\n    '));
                });
            } else {
                lines.push(`${key}: [${value.map(item => JSON.stringify(item)).join(', ')}]`);
            }
        } else if (key === 'prompt') {
            lines.push('prompt: |');
            String(value).split('\n').forEach(line => lines.push(`  ${line}`));
        } else {
            lines.push(`${key}: ${JSON.stringify(value)}`);
        }
    }
    return `${lines.join('\n')}\n`;
}

function buildClaudeManifest(card) {
    return JSON.stringify({
        schema_version: 'map-cards.claude.v1',
        card: cardManifest(card),
        claude: {
            name: card.name,
            display_name: card.title,
            memory_file: 'CLAUDE.md',
            memory_entry: renderMarkdown(card, false),
            variables: card.variables || [],
        },
    }, null, 2);
}

function buildBootstrap(card, target) {
    if (!TARGETS.has(target)) throw new Error(`Unsupported target '${target}'`);
    const base = {
        name: card.name,
        title: card.title,
        target,
        content_type: 'text/plain',
        filename: `${card.name}.txt`,
        content: card.prompt,
        next_steps: ['Paste the prompt into your AI tool.'],
    };
    if (target === 'codex') {
        return {
            ...base,
            label: 'Bootstrap into Codex',
            content_type: 'text/markdown',
            filename: `${card.name}.codex.md`,
            content: renderMarkdown(card, true),
        };
    }
    if (target === 'claude') {
        return {
            ...base,
            label: 'Install into Claude',
            content_type: 'application/json',
            filename: `${card.name}.claude.json`,
            content: buildClaudeManifest(card),
        };
    }
    if (target === 'markdown') {
        return {
            ...base,
            label: 'Download Markdown',
            content_type: 'text/markdown',
            filename: `${card.name}.md`,
            content: renderMarkdown(card),
        };
    }
    if (target === 'json') {
        return {
            ...base,
            content_type: 'application/json',
            filename: `${card.name}.json`,
            content: JSON.stringify(cardManifest(card), null, 2),
        };
    }
    if (target === 'yaml') {
        return {
            ...base,
            content_type: 'application/yaml',
            filename: `${card.name}.yaml`,
            content: renderYaml(card),
        };
    }
    return base;
}

function parseOptions(args) {
    const options = { target: 'codex', dir: process.cwd(), output: '', print: false };
    const positional = [];
    for (let i = 0; i < args.length; i += 1) {
        const arg = args[i];
        if (arg === '--target' || arg === '-t') {
            options.target = normalizeTarget((args[++i] || '').toLowerCase());
        } else if (arg.startsWith('--target=')) {
            options.target = normalizeTarget(arg.split('=')[1].toLowerCase());
        } else if (arg === '--dir' || arg === '-d') {
            options.dir = path.resolve(args[++i] || '.');
        } else if (arg.startsWith('--dir=')) {
            options.dir = path.resolve(arg.split('=')[1]);
        } else if (arg === '--output' || arg === '-o') {
            options.output = path.resolve(args[++i] || '');
        } else if (arg.startsWith('--output=')) {
            options.output = path.resolve(arg.split('=')[1]);
        } else if (arg === '--print' || arg === '-p') {
            options.print = true;
        } else {
            positional.push(arg);
        }
    }
    if (!TARGETS.has(options.target)) {
        throw new Error(`Unsupported target '${options.target}'. Use: ${Array.from(TARGETS).join(', ')}`);
    }
    return { positional, options };
}

function ensureDir(dir) {
    fs.mkdirSync(dir, { recursive: true });
}

function writeFile(filePath, content) {
    ensureDir(path.dirname(filePath));
    fs.writeFileSync(filePath, content.endsWith('\n') ? content : `${content}\n`, 'utf8');
}

function updateAgentsFile(rootDir, card, relativeArtifactPath) {
    const agentsPath = path.join(rootDir, 'AGENTS.md');
    const start = '<!-- map-cards:start -->';
    const end = '<!-- map-cards:end -->';
    const existing = fs.existsSync(agentsPath) ? fs.readFileSync(agentsPath, 'utf8') : '';
    const lines = existing.includes(start)
        ? existing.slice(existing.indexOf(start), existing.indexOf(end)).split('\n')
        : [];
    const entry = `- [${card.title}](${relativeArtifactPath}): ${card.description}`;
    const entries = new Set(lines.filter(line => line.startsWith('- ')));
    entries.add(entry);
    const block = `${start}
## MAPrompt Cards
${Array.from(entries).sort().join('\n')}
${end}`;
    const next = existing.includes(start) && existing.includes(end)
        ? `${existing.slice(0, existing.indexOf(start)).trimEnd()}\n\n${block}\n\n${existing.slice(existing.indexOf(end) + end.length).trimStart()}`
        : `${existing.trimEnd()}${existing.trim() ? '\n\n' : ''}${block}\n`;
    fs.writeFileSync(agentsPath, next, 'utf8');
    return agentsPath;
}

function updateClaudeFile(rootDir, card, promptText) {
    const claudePath = path.join(rootDir, 'CLAUDE.md');
    const start = '<!-- map-cards:start -->';
    const end = '<!-- map-cards:end -->';
    const existing = fs.existsSync(claudePath) ? fs.readFileSync(claudePath, 'utf8') : '';
    const entry = `## ${card.title}

Use this prompt card when the task matches: ${card.description}

${promptText.trim()}`;
    const block = `${start}
# MAPrompt Cards

${entry}
${end}`;
    const next = existing.includes(start) && existing.includes(end)
        ? `${existing.slice(0, existing.indexOf(start)).trimEnd()}\n\n${block}\n\n${existing.slice(existing.indexOf(end) + end.length).trimStart()}`
        : `${existing.trimEnd()}${existing.trim() ? '\n\n' : ''}${block}\n`;
    fs.writeFileSync(claudePath, next, 'utf8');
    return claudePath;
}

async function install(name, options) {
    const bootstrap = await fetchBootstrap(name, options.target);
    const card = await fetchCard(name);

    if (options.print) {
        console.log(bootstrap.content);
        return;
    }

    let written = [];
    if (options.output) {
        writeFile(options.output, bootstrap.content);
        written.push(options.output);
    } else if (options.target === 'codex') {
        const artifactPath = path.join(options.dir, '.codex', 'map-cards', bootstrap.filename);
        writeFile(artifactPath, bootstrap.content);
        const agentsPath = updateAgentsFile(options.dir, card, path.relative(options.dir, artifactPath));
        written = [artifactPath, agentsPath];
    } else if (options.target === 'claude') {
        const manifestPath = path.join(options.dir, '.claude', 'map-cards', bootstrap.filename);
        writeFile(manifestPath, bootstrap.content);
        const claudePath = updateClaudeFile(options.dir, card, card.prompt);
        written = [manifestPath, claudePath];
    } else {
        const filePath = path.join(options.dir, bootstrap.filename);
        writeFile(filePath, bootstrap.content);
        written = [filePath];
    }

    console.log(`\nInstalled ${card.title}`);
    console.log(`Target: ${options.target}`);
    written.forEach(filePath => console.log(`- ${path.relative(process.cwd(), filePath)}`));
    if (options.target === 'codex') {
        console.log('\nCodex bootstrap is ready. Start Codex from this workspace so it can read AGENTS.md.');
    } else if (options.target === 'claude') {
        console.log('\nClaude bootstrap is ready. Start Claude Code from this workspace so it can read CLAUDE.md.');
    }
}

async function list() {
    const cards = await fetchRegistryCards();
    console.log(`\nMAPrompt Cards (${cards.length} available)\n`);
    for (const card of cards) {
        const installs = Number(card.download_count || 0);
        console.log(`${card.name.padEnd(35)} ${card.category.padEnd(15)} ${installs} installs`);
    }
    console.log('\nInstall: npx map-cards install <name> --target codex\n');
}

async function search(query) {
    const q = query.toLowerCase();
    const cards = await fetchRegistryCards();
    const results = cards.filter(card => {
        const text = [card.name, card.title, card.description, card.author, ...(card.tags || [])].join(' ').toLowerCase();
        return text.includes(q);
    });
    console.log(`\nSearch results for "${query}" (${results.length} found)\n`);
    results.forEach(card => console.log(`${card.name.padEnd(35)} ${card.description.slice(0, 72)}`));
    console.log('');
}

async function info(name) {
    const card = await fetchCard(name);
    console.log(`\n${card.title}`);
    console.log('='.repeat(40));
    console.log(`Name:      ${card.name}`);
    console.log(`Author:    ${card.author}`);
    console.log(`Category:  ${card.category}`);
    console.log(`Version:   ${card.version}`);
    console.log(`Platforms: ${(card.platforms || []).join(', ')}`);
    console.log(`Tags:      ${(card.tags || []).join(', ')}`);
    console.log(`\n${card.description}\n`);
}

function help() {
    console.log(`
MAPrompt Cards CLI v0.1.0

Usage:
  map-cards install <name> [--target codex|claude|markdown|prompt] [--dir .]
  map-cards list
  map-cards search <query>
  map-cards info <name>

Install targets:
  codex      Write .codex/map-cards/<card>.md and update AGENTS.md
  claude     Write .claude/map-cards/<card>.json and update CLAUDE.md
  markdown   Write a portable Markdown prompt card
  prompt     Write the raw prompt text

Environment:
  MAP_API_URL       API base URL for tracked installs
  MAP_REGISTRY_URL  Static cards.json registry fallback
`);
}

async function main() {
    const [,, command, ...args] = process.argv;
    try {
        if (command === 'install' || command === 'i') {
            const { positional, options } = parseOptions(args);
            if (!positional[0]) throw new Error('Usage: map-cards install <name>');
            await install(positional[0], options);
        } else if (command === 'list' || command === 'ls') {
            await list();
        } else if (command === 'search' || command === 's') {
            if (!args[0]) throw new Error('Usage: map-cards search <query>');
            await search(args.join(' '));
        } else if (command === 'info') {
            if (!args[0]) throw new Error('Usage: map-cards info <name>');
            await info(args[0]);
        } else {
            help();
        }
    } catch (err) {
        console.error(`Error: ${err.message}`);
        process.exit(1);
    }
}

main();
