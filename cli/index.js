#!/usr/bin/env node

/**
 * MAPrompt Cards CLI — Install prompt cards from the command line.
 *
 * Usage:
 *   npx map-cards install <card-name>
 *   npx map-cards list
 *   npx map-cards search <query>
 *   npx map-cards info <card-name>
 */

const https = require('https');
const http = require('http');

const API_BASE = process.env.MAP_API_URL || 'http://localhost:8000/api';

function request(url) {
    return new Promise((resolve, reject) => {
        const mod = url.startsWith('https') ? https : http;
        mod.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode >= 400) {
                    reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                } else {
                    resolve(JSON.parse(data));
                }
            });
        }).on('error', reject);
    });
}

function postRequest(url, body) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(url);
        const mod = parsed.protocol === 'https:' ? https : http;
        const options = {
            hostname: parsed.hostname,
            port: parsed.port,
            path: parsed.pathname,
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
        };
        const req = mod.request(options, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => {
                if (res.statusCode >= 400) {
                    reject(new Error(`HTTP ${res.statusCode}: ${data}`));
                } else {
                    resolve(JSON.parse(data));
                }
            });
        });
        req.on('error', reject);
        req.write(JSON.stringify(body));
        req.end();
    });
}

async function install(name) {
    try {
        const data = await postRequest(`${API_BASE}/cards/${name}/download`, {});
        console.log(`\n  MAP Card: ${data.title}`);
        console.log(`  ${'='.repeat(40)}`);
        console.log(`\n${data.prompt}`);
        console.log(`\n  Installs: ${data.download_count}`);
        if (data.variables && data.variables.length > 0) {
            console.log(`\n  Variables:`);
            for (const v of data.variables) {
                console.log(`    - ${v.name}: ${v.description} (default: ${v.default || 'none'})`);
            }
        }
        console.log('');
    } catch (err) {
        console.error(`Error: Card '${name}' not found or server unreachable.`);
        console.error(`  Make sure the MAPrompt Cards server is running at ${API_BASE}`);
        process.exit(1);
    }
}

async function list() {
    try {
        const data = await request(`${API_BASE}/cards?limit=100`);
        console.log(`\n  MAPrompt Cards (${data.count} available)\n`);
        for (const card of data.cards) {
            const stars = card.avg_rating ? ` ★${card.avg_rating}` : '';
            console.log(`  ${card.name.padEnd(35)} ${card.category.padEnd(15)} ${card.download_count} installs${stars}`);
        }
        console.log(`\n  Install: npx map-cards install <name>\n`);
    } catch (err) {
        console.error('Error: Could not connect to MAPrompt Cards server.');
        process.exit(1);
    }
}

async function search(query) {
    try {
        const data = await request(`${API_BASE}/cards?q=${encodeURIComponent(query)}`);
        console.log(`\n  Search results for "${query}" (${data.count} found)\n`);
        for (const card of data.cards) {
            console.log(`  ${card.name.padEnd(35)} ${card.description.slice(0, 60)}...`);
        }
        console.log('');
    } catch (err) {
        console.error('Error: Could not connect to MAPrompt Cards server.');
        process.exit(1);
    }
}

async function info(name) {
    try {
        const card = await request(`${API_BASE}/cards/${name}`);
        console.log(`\n  ${card.title}`);
        console.log(`  ${'='.repeat(40)}`);
        console.log(`  Author:    ${card.author}`);
        console.log(`  Category:  ${card.category}`);
        console.log(`  Version:   ${card.version}`);
        console.log(`  Platforms: ${(card.platforms || []).join(', ')}`);
        console.log(`  Tags:      ${(card.tags || []).join(', ')}`);
        console.log(`  Installs:  ${card.download_count}`);
        console.log(`  Rating:    ${card.avg_rating || 0} (${card.rating_count} ratings)`);
        console.log(`\n  ${card.description}\n`);
    } catch (err) {
        console.error(`Error: Card '${name}' not found.`);
        process.exit(1);
    }
}

// Parse CLI args
const [,, command, ...args] = process.argv;

switch (command) {
    case 'install':
    case 'i':
        if (!args[0]) { console.error('Usage: map-cards install <name>'); process.exit(1); }
        install(args[0]);
        break;
    case 'list':
    case 'ls':
        list();
        break;
    case 'search':
    case 's':
        if (!args[0]) { console.error('Usage: map-cards search <query>'); process.exit(1); }
        search(args.join(' '));
        break;
    case 'info':
        if (!args[0]) { console.error('Usage: map-cards info <name>'); process.exit(1); }
        info(args[0]);
        break;
    default:
        console.log(`
  MAPrompt Cards CLI v0.1.0

  Usage:
    map-cards install <name>   Install a prompt card (prints to stdout)
    map-cards list             List all available cards
    map-cards search <query>   Search for cards
    map-cards info <name>      Show card details

  Environment:
    MAP_API_URL    API base URL (default: http://localhost:8000/api)
        `);
}
