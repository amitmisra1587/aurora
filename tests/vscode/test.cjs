// Run inside an isolated VS Code Extension Development Host, not plain Node.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { execFileSync } = require('node:child_process');
const vscode = require('vscode');

const report = { vscode: vscode.version, checks: [] };
function record(name, details) {
  report.checks.push({ name, details });
  console.log(`[aurora-vscode] ${name}: ${JSON.stringify(details)}`);
  if (process.env.AURORA_VSCODE_TEST_REPORT) {
    fs.writeFileSync(process.env.AURORA_VSCODE_TEST_REPORT, JSON.stringify(report, null, 2));
  }
}
async function until(fn, description, timeout = 30000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    const value = await fn();
    if (value) return value;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw new Error(`Timed out: ${description}`);
}
async function call(name, input = {}, logResult = true) {
  const tool = await until(() => vscode.lm.tools.find(t => t.name.endsWith(name)), name, 240000);
  const result = await vscode.lm.invokeTool(tool.name, { input });
  const text = result.content.map(part => part.value ?? part.text ?? '').join('\n');
  const parsed = JSON.parse(text);
  if (logResult) record(name, { tool: tool.name, result: parsed });
  return parsed;
}

exports.run = async function () {
  try {
    const workspace = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
    assert(workspace, 'Open the isolated Aurora checkout as the workspace');
    record('workspace', workspace);

    const cancellation = new vscode.CancellationTokenSource();
    const skill = await until(async () => (await vscode.chat.getSkills(cancellation.token))
      .find(s => s.name === 'msresearch-aurora-air-pollution'), 'canonical skill discovery');
    assert(skill.description);
    const resolvedSkill = fs.realpathSync(skill.uri.fsPath);
    assert.equal(resolvedSkill, path.join(workspace, '.agents/skills/msresearch-aurora-air-pollution/SKILL.md'));
    record('skill_discovery', { name: skill.name, uri: skill.uri.toString(), resolvedSkill });

    const definitions = await until(() => {
      const entries = vscode.lm.mcpServerDefinitions.filter(d => d.label === 'aurora_air_pollution');
      return entries.length ? entries : undefined;
    }, 'workspace MCP discovery');
    assert.equal(definitions.length, 1);
    record('mcp_discovery', definitions.map(d => ({ label: d.label, command: d.command, args: d.args })));

    // Trust only the reviewed test workspace's server in this disposable profile.
    await vscode.commands.executeCommand('workbench.mcp.startServer', '*', {
      autoTrustChanges: true, errorOnUserInteraction: true, waitForLiveTools: true,
    });
    let lastState;
    const setup = await until(async () => {
      const status = await call('setup_status', {}, false);
      if (status.state !== lastState) {
        record('setup_status', status);
        lastState = status.state;
      }
      assert.notEqual(status.state, 'failed', JSON.stringify(status));
      return status.state === 'ready' ? status : undefined;
    }, 'minimal setup', 240000);
    assert(setup.config.startsWith(process.env.HOME));
    const environment = await call('inspect_environment');
    assert.equal(environment.fork_import_verified, true);
    assert.equal(environment.dependencies.torch, null);
    assert.equal(environment.dependencies.numpy, null);
    assert.deepEqual((await call('list_runs')).jobs, []);
    await call('inspect_assets');
    assert.equal((await call('knowledge_validate')).ok, true);
    const tools = vscode.lm.tools.filter(t => t.name.includes('aurora')).map(t => t.name);
    assert.equal(tools.length, 26);
    record('tools', tools);

    const claude = vscode.extensions.getExtension('anthropic.claude-code');
    assert(claude, 'Install the Claude Code extension in the isolated test profile');
    if (claude) {
      await claude.activate();
      assert(claude.isActive);
      await until(async () => (await vscode.commands.getCommands(true))
        .includes('claude-vscode.editor.open'), 'Claude editor command registration');
      const binary = path.join(claude.extensionPath, 'resources/native-binary/claude');
      const inventory = execFileSync(binary, ['plugin', 'details', 'aurora-air-pollution@aurora'], {
        encoding: 'utf8', timeout: 30000,
      });
      assert.match(inventory, /Skills \(5\)/);
      assert.match(inventory, /MCP servers \(1\)/);
      record('claude_extension', { version: claude.packageJSON.version, active: claude.isActive, inventory });
    }
    report.passed = true;
    record('passed', true);
  } catch (error) {
    report.passed = false;
    record('failed', { message: error.message, stack: error.stack });
    throw error;
  }
};
