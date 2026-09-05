// Rust bridge adapter for Aster
//
// This file provides trait definitions and generated stub implementations
// for .co action declarations targeting Rust.
//
// The Rust adapter is intentionally minimal: it defines a trait that real
// Rust implementations should satisfy so that .co programs can drive
// Rust code via the transpiler output.
//
// Usage
// -----
// 1. The transpiler generates a Rust source file containing function stubs.
// 2. This adapter module provides the `CoAction` trait that those stubs
//    implement.
// 3. Implement the trait methods with your real Rust logic.
//
// Example
// -------
// For the .co program:
//
//     entity dataset
//     entity model
//     action learn(dataset -> model)
//
// The transpiler produces:
//
//     fn learn(dataset: &dyn std::any::Any, model: &mut dyn std::any::Any) {
//         // Action: dataset -> model
//     }
//
// You fill in the body.

use std::any::Any;

/// Trait implemented by every generated action stub.
///
/// Each .co action maps to one method on a struct that implements this trait.
pub trait CoAction {
    /// Execute the action, consuming `source` and writing into `target`.
    fn execute(&self, source: &dyn Any, target: &mut dyn Any);

    /// Human-readable name of the action (matches the .co declaration).
    fn name(&self) -> &str;
}

/// Thin wrapper that holds a closure and satisfies `CoAction`.
pub struct ClosureAction {
    action_name: String,
    handler: Box<dyn Fn(&dyn Any, &mut dyn Any) + Send + Sync>,
}

impl ClosureAction {
    pub fn new<F>(name: &str, handler: F) -> Self
    where
        F: Fn(&dyn Any, &mut dyn Any) + Send + Sync + 'static,
    {
        ClosureAction {
            action_name: name.to_string(),
            handler: Box::new(handler),
        }
    }
}

impl CoAction for ClosureAction {
    fn execute(&self, source: &dyn Any, target: &mut dyn Any) {
        (self.handler)(source, target);
    }

    fn name(&self) -> &str {
        &self.action_name
    }
}

/// Registry that maps action names to their `CoAction` implementations.
pub struct ActionRegistry {
    actions: std::collections::HashMap<String, Box<dyn CoAction + Send + Sync>>,
}

impl ActionRegistry {
    pub fn new() -> Self {
        ActionRegistry {
            actions: std::collections::HashMap::new(),
        }
    }

    /// Register an action implementation.
    pub fn register(&mut self, action: impl CoAction + Send + Sync + 'static) {
        self.actions.insert(action.name().to_string(), Box::new(action));
    }

    /// Execute a named action.  Returns `false` if the action is not registered.
    pub fn execute(&self, name: &str, source: &dyn Any, target: &mut dyn Any) -> bool {
        if let Some(action) = self.actions.get(name) {
            action.execute(source, target);
            true
        } else {
            false
        }
    }
}

impl Default for ActionRegistry {
    fn default() -> Self {
        Self::new()
    }
}
