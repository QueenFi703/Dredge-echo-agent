/**
 * JavaScript bridge adapter for Aster.
 *
 * Maps .co action declarations to JavaScript functions and provides a
 * lightweight runtime that can execute cycles in a Node.js or browser context.
 *
 * Usage
 * -----
 *   const { CoRuntime } = require('./js_adapter');
 *
 *   const runtime = new CoRuntime();
 *
 *   runtime.bindAction('learn', (source, target) => {
 *     console.log(`Learning from ${source} into ${target}`);
 *   });
 *
 *   runtime.runCycle('training', ['learn', 'evaluate']);
 */

'use strict';

/**
 * Lightweight runtime for executing .co programs in JavaScript.
 */
class CoRuntime {
  constructor() {
    /** @type {Map<string, Function>} */
    this._actions = new Map();
    /** @type {string[]} */
    this._log = [];
  }

  /**
   * Register a JavaScript function as the implementation of a named action.
   *
   * @param {string} actionName  - The action name as declared in the .co program.
   * @param {Function} handler   - A function accepting (source, target).
   */
  bindAction(actionName, handler) {
    if (typeof handler !== 'function') {
      throw new TypeError(`Handler for action "${actionName}" must be a function`);
    }
    this._actions.set(actionName, handler);
  }

  /**
   * Execute a named cycle by invoking each step in order.
   *
   * @param {string}   cycleName  - Human-readable name for logging.
   * @param {string[]} steps      - Ordered list of action names to execute.
   * @param {Object}   [context]  - Optional shared context object passed to each action.
   */
  runCycle(cycleName, steps, context = {}) {
    this._log.push(`[cycle:${cycleName}] begin`);

    for (const step of steps) {
      const handler = this._actions.get(step);
      if (!handler) {
        const msg = `[cycle:${cycleName}] WARNING: action "${step}" not registered`;
        this._log.push(msg);
        console.warn(msg);
        continue;
      }
      this._log.push(`[cycle:${cycleName}] execute ${step}`);
      handler(context.source, context.target);
    }

    this._log.push(`[cycle:${cycleName}] end`);
  }

  /**
   * Return the execution log as an array of strings.
   *
   * @returns {string[]}
   */
  getLog() {
    return [...this._log];
  }

  /**
   * Clear the execution log.
   */
  clearLog() {
    this._log = [];
  }
}

/**
 * Translate a .co action declaration into a JavaScript function signature string.
 *
 * @param {string} actionName
 * @param {string} source
 * @param {string} target
 * @returns {string}
 */
function actionToJS(actionName, source, target) {
  return [
    `function ${actionName}(${source}, ${target}) {`,
    `  // Action: ${source} -> ${target}`,
    `  return ${target};`,
    '}',
  ].join('\n');
}

// CommonJS export (works in Node.js; tree-shakeable bundlers handle ESM)
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { CoRuntime, actionToJS };
}
