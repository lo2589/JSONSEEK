// Cordis apply() for jsonseek-dsh bundle.
//
// Registers one model-callable tool per jsonseek sub-command. Each tool
// forwards the call to the local `jsonseek` CLI binary so we don't fork any
// of jsonseek's parsing, IO, or patch logic — we just translate a JSON
// payload into argv tokens and return stdout/stderr/returncode to the host
// Loader.
//
// Usage context: installed in a DeepSeek Harness profile whose node_modules
// contains this package (npm install / pnpm add). The peer Python package
// `jsonseek-dsh` is optional — only required if you want to load this
// bundle from Python (`jsonseek_dsh.plugin.apply`).

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

// Build a single ToolDefinition per sub-command. We use the raw shape dsh's
// tool registry accepts — `name`, `description`, `parameters` JSON Schema,
// and `execute`. dsh's `defineTool` helper is the higher-level form, but a
// plain object with the same keys works the same way on the registry side.
function buildToolDefinition(subcommand) {
  return {
    name: `jsonseek_${subcommand}`,
    description: TOOL_DESCRIPTIONS[subcommand],
    parameters: {
      type: "object",
      additionalProperties: true,
    },
    async execute(args) {
      const params = args && typeof args === "object" ? args : {};
      const result = await runJsonseek(subcommand, params);
      return {
        stdout: result.stdout,
        stderr: result.stderr,
        returncode: result.returncode,
      };
    },
  };
}

const toolDefinitions = Object.keys(POSITIONAL_ORDER).map(buildToolDefinition);

// Cordis plugin contract — registered by `name: jsonseek-dsh` in
// cordis.patch.yml. We mount every jsonseek_* tool on the host ctx.tools
// registry.
export function apply(ctx) {
  // Cordis exposes tool registration via `ctx.registry.plugin(...)`. Each
  // entry is a Service subclass or a plain object with an `apply` method.
  // Wrapping each tool definition this way keeps it consistent with how
  // other dsh bundles register tools.
  for (const def of toolDefinitions) {
    class JsonseekTool {
      constructor(c) {
        this.ctx = c;
        this.name = def.name;
        this.description = def.description;
        this.parameters = def.parameters;
      }
      async execute(args) {
        return def.execute(args, { ctx: this.ctx });
      }
    }
    ctx.registry.plugin(JsonseekTool);
  }
}

export const name = "jsonseek-dsh";
export { toolDefinitions };