use std::any::Any;
use std::collections::{HashMap, HashSet};
use std::fmt;

use crate::action::Action;
use crate::game::Game;
use crate::result::Result;

/// An event handler that reacts to game events.
///
/// Handlers are topologically sorted by `execute_before` / `execute_after`
/// constraints and dispatched in that order. During dispatch, each handler
/// can modify the action (cancel it, mark done, etc.) or trigger side
/// effects through the game reference — including recursive `process_action`.
#[derive(Debug, Copy)]
pub struct EventHandler {
    execute_before: &'static [&'static str],
    execute_after: &'static [&'static str],
    dispatch: &'static str,
    handle: fn(&mut Game, evt_type: GameEvent) -> Result<()>,
}
