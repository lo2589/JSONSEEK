// Cordis bundle entry for jsonseek-dsh.
//
// Registers one model-callable tool per jsonseek sub-command on the dsh
// `tools` service. Each tool forwards the call to the local `jsonseek` CLI
// binary so we don't fork any of jsonseek's parsing, IO, or patch logic — we
// just translate a JSON payload into argv tokens and return the CLI output.
//
// Contract notes (read before editing):
//   - dsh tools are registered through the `tools` service:
//     `ctx.tools.register(definition)` — NOT via `ctx.registry.plugin()`,
//     which mounts a Cordis plugin and does not expose a model tool.
//   - `output` is mandatory: `register()` throws
//     `tool "<name>" must declare output { schema, render, presentationMeta? }`
//     without it. `render` returns ContentBlock[] (`{ type: 'text', text }`).
//   - `parameters` is a plain JSON Schema object projected to the model.
//
// Usage context: installed in a DeepSeek Harness profile whose node_modules
// contains this package (npm install / pnpm add). The upstream `jsonseek`
// CLI binary must be on PATH (`pip install jsonseek`).

import { execFile } from "node:child_process";
import { promisify } from "node:util";

const exec = promisify(execFile);

// Map jsonseek sub-command names → positional argument order. The upstream
// CLI is an argparse with positional arguments declared first; we mirror
// that here so tool calls never reverse-argument a sub-command.
const POSITIONAL_ORDER = {
  shape: ["file"],
  fields: ["file", "keyword"],
  ls: ["file", "path"],
  get: ["file", "path"],
  query: ["file", "keyword"],
  add: ["file", "path", "value"],
  del: ["file", "path"],
  set: ["file", "path", "value"],
  append: ["file", "path", "value"],
  extract: ["pattern", "path"],
  extend: ["file", "path", "value"],
  concat: ["pattern"],
  cutline: ["file", "line"],
  replaceline: ["file", "line", "content"],
};

const TOOL_DESCRIPTIONS = {
  shape: "Show the structure/shape of a JSON or JSONL file. Use this first to understand an unknown JSON file before doing anything else.",
  fields: "List keys + types in a JSON/JSONL file.",
  ls: "List children at a JSON path.",
  get: "Fetch a single value at a JSON path.",
  query: "Search JSON/JSONL content for a keyword.",
  set: "Set a value at a JSON path.",
  add: "Add a key/value to a JSON object.",
  del: "Delete a JSON key or array element.",
  append: "Append to a JSON array or JSONL file.",
  extract: "Extract a path from many JSON files matched by glob.",
  extend: "Extend a JSON array with another JSON array.",
  concat: "Concatenate multiple JSON files into a single JSONL stream.",
  cutline: "Extract one specific line from a text file (or JSONL).",
  replaceline: "Replace one specific line in a text file (or JSONL).",
};

// Per-sub-command optional flags as a JSON Schema object. Positional keys are
// marked `required` where the CLI requires them; every other key becomes an
// optional `--flag` on the argv line. Keep in sync with src/jsonseek/cli.py.
const PARAMETER_SCHEMAS = {
  shape: {
    type: "object",
    properties: {
      file: { type: "string", description: "Path to JSON/JSONL file" },
      "max-depth": { type: "integer", description: "Maximum depth to traverse" },
      "array-mode": { type: "string", enum: ["sample", "full"] },
      "sample-size": { type: "integer", description: "Records to sample for JSONL" },
      output: { type: "string", enum: ["pretty", "json"] },
    },
    required: ["file"],
  },
  fields: {
    type: "object",
    properties: {
      file: { type: "string" },
      keyword: { type: "string", description: "Filter fields by keyword" },
      top: { type: "boolean", description: "Show only top-level fields" },
      output: { type: "string", enum: ["pretty", "json"] },
    },
    required: ["file"],
  },
  ls: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Path to list (default: root)" },
      output: { type: "string", enum: ["pretty", "json"] },
    },
    required: ["file"],
  },
  get: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Path to retrieve" },
      output: { type: "string", enum: ["pretty", "json"] },
    },
    required: ["file", "path"],
  },
  query: {
    type: "object",
    properties: {
      file: { type: "string" },
      keyword: { type: "string", description: "Search term" },
      context: { type: "integer", description: "Lines of context around target line" },
      "case-sensitive": { type: "boolean" },
      exact: { type: "boolean" },
      "match-mode": { type: "string", enum: ["key", "value", "both"] },
      "max-results": { type: "integer" },
      "record-id-field": { type: "string" },
      "preview-field": { type: "string" },
      output: { type: "string", enum: ["pretty", "json"] },
    },
    required: ["file", "keyword"],
  },
  add: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Path to add at" },
      value: { description: "Value to add (JSON-encoded for objects/arrays)" },
      "create-missing": { type: "boolean" },
      "from-file": { type: "string" },
      backup: { type: "boolean" },
      "dry-run": { type: "boolean" },
    },
    required: ["file", "path", "value"],
  },
  del: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Path to delete" },
      yes: { type: "boolean" },
      backup: { type: "boolean" },
      "dry-run": { type: "boolean" },
    },
    required: ["file", "path"],
  },
  set: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Path to set" },
      value: { description: "Value to set (JSON-encoded for objects/arrays)" },
      "create-missing": { type: "boolean" },
      "from-file": { type: "string" },
      backup: { type: "boolean" },
      "dry-run": { type: "boolean" },
    },
    required: ["file", "path", "value"],
  },
  append: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Array path to append to" },
      value: { description: "Value to append (JSON-encoded for objects/arrays)" },
      backup: { type: "boolean" },
      "dry-run": { type: "boolean" },
    },
    required: ["file", "path", "value"],
  },
  extract: {
    type: "object",
    properties: {
      pattern: { type: "string", description: "Glob matching JSON files" },
      path: { type: "string", description: "Path to extract" },
      output: { type: "string", enum: ["pretty", "json"] },
      "include-missing": { type: "boolean" },
    },
    required: ["pattern", "path"],
  },
  extend: {
    type: "object",
    properties: {
      file: { type: "string" },
      path: { type: "string", description: "Array path to extend" },
      value: { description: "JSON array string to merge in" },
      backup: { type: "boolean" },
      "dry-run": { type: "boolean" },
    },
    required: ["file", "path", "value"],
  },
  concat: {
    type: "object",
    properties: {
      pattern: { type: "string", description: "Glob matching JSON files" },
      "output-file": { type: "string", description: "Output JSONL path" },
      "no-sort": { type: "boolean" },
    },
    required: ["pattern"],
  },
  cutline: {
    type: "object",
    properties: {
      file: { type: "string" },
      line: { type: "integer", description: "1-based line number" },
      "save-temp": { type: "boolean" },
    },
    required: ["file", "line"],
  },
  replaceline: {
    type: "object",
    properties: {
      file: { type: "string" },
      line: { type: "integer", description: "1-based line number" },
      content: { type: "string", description: "Replacement line text" },
      "from-file": { type: "string" },
      backup: { type: "boolean" },
      "dry-run": { type: "boolean" },
    },
    required: ["file", "line"],
  },
};

function paramsToArgv(subcommand, params = {}) {
  const argv = [];
  const positionalKeys = POSITIONAL_ORDER[subcommand] ?? [];

  // 1. positionals first, in declared order
  for (const key of positionalKeys) {
    if (params[key] === undefined || params[key] === null) continue;
    argv.push(encodeScalar(params[key]));
  }

  // 2. then optional flags
  const positionalSet = new Set(positionalKeys);
  for (const [key, value] of Object.entries(params)) {
    if (positionalSet.has(key)) continue;
    if (value === null || value === false || value === undefined) continue;
    const flag = "--" + key.replace(/_/g, "-");
    if (value === true) {
      argv.push(flag);
    } else if (Array.isArray(value)) {
      for (const v of value) argv.push(flag, encodeScalar(v));
    } else {
      argv.push(flag, encodeScalar(value));
    }
  }
  return argv;
}

function encodeScalar(value) {
  if (typeof value === "string") return value;
  if (typeof value === "boolean") return value ? "true" : "false";
  return JSON.stringify(value);
}

async function runJsonseek(subcommand, params) {
  const argv = ["jsonseek", subcommand, ...paramsToArgv(subcommand, params)];
  try {
    const { stdout, stderr } = await exec(argv[0], argv.slice(1), {
      maxBuffer: 64 * 1024 * 1024,
    });
    return { stdout, stderr, returncode: 0 };
  } catch (err) {
    // execFile raises on non-zero exit; surface its captured output.
    return {
      stdout: err.stdout ?? "",
      stderr: err.stderr ?? String(err.message ?? err),
      returncode: err.code ?? 1,
    };
  }
}

// The canonical result of every tool: the CLI's captured output. This is the
// value `output.schema` validates and `render` projects to model text.
const RESULT_SCHEMA = {
  type: "object",
  properties: {
    stdout: { type: "string" },
    stderr: { type: "string" },
    returncode: { type: "integer" },
  },
  required: ["stdout", "stderr", "returncode"],
};

function renderCliResult(_args, value) {
  const text = [
    value.stdout || "",
    value.stderr ? (value.stdout ? "\n" : "") + value.stderr : "",
  ].join("").trimEnd();
  return [{ type: "text", text: text === "" ? "(no output)" : text }];
}

// Build one ToolDefinition per sub-command. Shape matches what the dsh
// `tools` service accepts: name/description/parameters JSON Schema,
// mandatory `output { schema, render }`, and `execute` returning a
// lossless-JSON value.
function buildToolDefinition(subcommand) {
  return {
    name: `jsonseek_${subcommand}`,
    description: TOOL_DESCRIPTIONS[subcommand],
    parameters: PARAMETER_SCHEMAS[subcommand] ?? { type: "object" },
    output: {
      schema: RESULT_SCHEMA,
      render: renderCliResult,
    },
    async execute(args) {
      const params = args && typeof args === "object" ? args : {};
      return runJsonseek(subcommand, params);
    },
  };
}

const toolDefinitions = Object.keys(POSITIONAL_ORDER).map(buildToolDefinition);

// Cordis plugin contract — loaded by `name: jsonseek-dsh` in
// cordis.patch.yml. We register every jsonseek_* tool on the host `tools`
// service. `inject` names the services this plugin needs before apply() runs.
export const inject = ["tools"];

export function apply(ctx) {
  for (const def of toolDefinitions) {
    ctx.tools.register(def);
  }
}

export const name = "jsonseek-dsh";
export { toolDefinitions };
