'use strict';

const assert = require('node:assert/strict');
const http = require('node:http');
const { spawn } = require('node:child_process');
const net = require('node:net');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.once('error', reject);
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      server.close(error => error ? reject(error) : resolve(port));
    });
  });
}

async function waitForHealth(url, child) {
  const deadline = Date.now() + 10_000;
  let lastError;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`Workbench server exited early (${child.exitCode}).`);
    try {
      const response = await fetch(url, { signal: AbortSignal.timeout(1000) });
      if (response.ok) return response.json();
    } catch (error) { lastError = error; }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Workbench health endpoint did not start: ${lastError || 'timeout'}`);
}

async function verifyInvalidTimeoutFallback() {
  const port = await freePort();
  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT, env: { ...process.env, USG_PORT: String(port), USG_MODEL_TIMEOUT_MS: '999' },
    stdio: ['ignore', 'ignore', 'ignore']
  });
  try {
    const health = await waitForHealth(`http://127.0.0.1:${port}/api/health`, child);
    assert.equal(health.modelTimeoutMs, 180_000, 'an out-of-range timeout falls back to the documented default');
    console.log('PASS: an out-of-range timeout safely falls back to 180 seconds.');
  } finally {
    child.kill('SIGTERM');
    await new Promise(resolve => {
      if (child.exitCode !== null) return resolve();
      const timer = setTimeout(() => { child.kill('SIGKILL'); resolve(); }, 3000);
      child.once('exit', () => { clearTimeout(timer); resolve(); });
    });
  }
}

async function main() {
  const fakePort = await freePort();
  const appPort = await freePort();
  let slowRequests = 0;
  const fakeOllama = http.createServer((req, res) => {
    if (req.url === '/api/chat') {
      slowRequests += 1;
      // Deliberately exceed the Workbench's configured one-second test timeout.
      setTimeout(() => {
        if (!res.destroyed) {
          res.writeHead(200, { 'content-type': 'application/json' });
          res.end(JSON.stringify({ message: { content: JSON.stringify({ intent: 'ASSERTION', claims: [] }) } }));
        }
      }, 2200);
      return;
    }
    res.writeHead(200, { 'content-type': 'application/json' });
    res.end(JSON.stringify({ models: [] }));
  });
  await new Promise((resolve, reject) => fakeOllama.listen(fakePort, '127.0.0.1', error => error ? reject(error) : resolve()));

  const child = spawn(process.execPath, ['server.js'], {
    cwd: ROOT,
    env: { ...process.env, USG_PORT: String(appPort), USG_MODEL_TIMEOUT_MS: '1000' },
    stdio: ['ignore', 'pipe', 'pipe']
  });
  let logs = '';
  child.stdout.on('data', chunk => { logs += chunk.toString(); });
  child.stderr.on('data', chunk => { logs += chunk.toString(); });

  try {
    const base = `http://127.0.0.1:${appPort}`;
    const health = await waitForHealth(`${base}/api/health`, child);
    assert.equal(health.version, '0.5.4', 'health endpoint reports Workbench v0.5.4');
    assert.equal(health.modelTimeoutMs, 1000, 'health endpoint exposes the configured timeout');
    const home = await fetch(`${base}/`);
    assert.equal(home.status, 200, 'Workbench root page is served by the local HTTP server');

    const response = await fetch(`${base}/api/interpret`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({
        ollamaUrl: `http://127.0.0.1:${fakePort}`,
        model: 'timeout-test-model',
        text: 'The customer needs the tool.'
      }),
      signal: AbortSignal.timeout(5000)
    });
    const payload = await response.json();
    assert.equal(response.status, 502, 'timed-out model requests return HTTP 502');
    assert.match(payload.error, /within 1 seconds?\./, 'timeout error reports the effective configured timeout');
    assert.equal(payload.failureCategory,'timeout','timeout is exposed as a typed generation failure');
    assert.equal(payload.correctionAudit.status,'generation_request_failed','failed generation still produces a correction audit');
    assert.equal(payload.correctionAudit.generationArtifacts[0].diagnostic.category,'timeout');
    assert.equal(payload.correctionAudit.generationArtifacts[0].diagnostic.responseReceived,false);
    assert.equal(slowRequests, 1, 'the fake Ollama endpoint received the request');
    console.log('PASS: health endpoint exposes the Workbench version and model timeout.');
    console.log('PASS: root UI is served successfully by the Workbench server.');
    console.log('PASS: a slow Ollama response is aborted at the configured timeout and returns a clear error.');
  } finally {
    child.kill('SIGTERM');
    await new Promise(resolve => {
      if (child.exitCode !== null) return resolve();
      const timer = setTimeout(() => { child.kill('SIGKILL'); resolve(); }, 3000);
      child.once('exit', () => { clearTimeout(timer); resolve(); });
    });
    await new Promise(resolve => fakeOllama.close(() => resolve()));
    if (logs.includes('EADDRINUSE')) throw new Error(`Could not bind Workbench test server. ${logs}`);
  }
  await verifyInvalidTimeoutFallback();
}

main().catch(error => {
  console.error(error && error.stack ? error.stack : String(error));
  process.exitCode = 1;
});
