use std::fmt::Debug;
use std::ops::{Deref, DerefMut};

use super::base::ZeroSized;
use super::game::{Game, Result};
use super::object::GameObject;

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ActionPhase {
    /// Ready to fire.
    Ready,
    /// Cancelled before execution (by event handlers during `action_before`).
    Cancelled,
    /// Failed pre-validation (`is_valid()` returned false, or shootdown).
    Invalid,
    /// Executed and completed. `succeeded` records the outcome of `apply()`.
    Succeeded,
    Failed,
}

// Alias
pub type ActionObject = GameObject;

///|
type ActionEffectInner = stack_dst::Value<dyn Action, stack_dst::buffers::Ptr1>;

/// Component, should be zero sized struct implements Action trait
#[derive(Copy, Clone)]
pub struct ActionEffect(ZeroSized<dyn Action>);

impl Deref for ActionEffect {
    type Target = dyn Action;

    fn deref(&self) -> &Self::Target {
        &*self.0
    }
}

impl DerefMut for ActionEffect {
    fn deref_mut(&mut self) -> &mut Self::Target {
        &mut *self.0
    }
}

impl ActionEffect {
    fn new<T: Action + Debug + Copy + 'static>(val: T) -> Self {
        Self(ZeroSized::new(val))
    }
}

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
    /// entities. So this is an necessary condition. Actions survived ActionShootdown are considere
    /// truly ready to fire.
    fn is_valid(&self, g: &mut Game, act: &ActionObject) -> Result<bool>;
}
