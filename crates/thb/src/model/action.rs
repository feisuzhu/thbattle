use std::fmt::Debug;

use super::game::{Game, Result};
use super::object::{GameObject, Handle};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ActionPhase {
    /// Ready to fire.
    Ready,
    /// Cancelled before execution (by event handlers during `action_before`).
    Cancelled,
    /// Failed pre-validation (`is_valid()` returned false, or being shotdown).
    Invalid,
    /// Executed and completed. The boolean value indicates if the Action successfully 'applied',
    /// or, finished its designed purpose (happy path)
    Done(bool),
}

// Alias
pub type ActionObject = GameObject;

pub trait Action {
    /// For debugging and logging
    fn name(&self) -> &'static str {
        std::any::type_name::<Self>()
    }

    /// Execute this action's game logic. Return `true` if it succeeded.
    /// Assumes the action on top of action stack is the action to be resolved.
    ///
    /// May call `g.process_action()` to trigger sub-actions (recursive).
    fn apply(&self, g: &mut Game) -> Result<bool>;

    /// Pre-check: is this action valid and ready to fire?
    /// Only considers the Action's own requirements; does not consider interactions with other
    /// entities. So this is an necessary condition. Actions survived ActionShootdown are
    /// considered truly ready to fire.
    fn is_valid(&self, g: &mut Game, act: Handle) -> Result<bool>;
}
