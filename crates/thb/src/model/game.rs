use std::cell::Ref;

use log::debug;

use super::action::{ActionEffect, ActionObject, ActionPhase};
use super::object::{GameObject, Handle, ObjectArena};

#[derive(Debug, thiserror::Error)]
pub enum AlternativePath {
    // ----- Game Flow -----
    #[error("The game ended in a defined manner, there should be winners")]
    GameEnded { winners: Vec<Handle> },

    #[error("Players are gone, so we abort the game.")]
    Halt,

    #[error("Unwind resolution stack to {unwind_to:?}")]
    InterruptActionFlow { unwind_to: Handle },

    // ----- Action Flow -----
    #[error("Action was shotdown in the ActionShootdown event")]
    ActionWasShotdown,

    #[error("Action cancelled in ActionBefore event, stop resolving")]
    ActionCancelled,
    /*
    #[error(transparent)]
    Error(#[from] anyhow::Error),
    */
}

pub type Result<T> = std::result::Result<T, AlternativePath>;

///|
pub struct GameVariant {
    pub name: &'static str,
    pub seats: u8,
    pub npcs: (),
    pub params: (),
    pub bootstrap: fn() -> ActionObject,
}

/// Core game state and action processing engine.
///
/// Owns the event dispatcher and provides the action lifecycle loop.
/// Game-mode-specific state (cards, characters, board) lives in separate
/// types owned by the game mode, not here. This struct is the *engine*.
pub struct Game {
    pub variant: &'static GameVariant,

    // Sequence for synchronization
    pub sequence: u64,

    // All GameObject lies here, they don't destruct.
    pub arena: ObjectArena,

    // Actions currently resolving
    pub action_stack: Vec<Handle>,

    // Actions and EventHandlers currently resolving
    pub hybrid_stack: Vec<Handle>,
}

pub enum GameEvent {
    /// Action passed its own is_valid test, seeking for wider scope validation.
    /// Action object not push onto action_stack
    ActionShootdown(Handle),

    /// Action has passed validation and ready to fire. `EventHandler`s
    /// during this phase may cancel it, replace it (uncommon), or trigger
    /// sub-`Action`s before it proceeds.
    ///
    /// If cancelled, execution halts immediately — subsequent `EventHandler`s are skipped
    /// and neither `ActionApply` nor `ActionAfter` will fire. `ActionDone`,
    /// however, is always emitted regardless of outcome.
    ///
    /// During this event the Action sits on top of `action_stack`.
    ActionBefore,

    /// Last notification before the action executes, after surviving
    /// `ActionBefore` hooks. Cancelling or replacing is no longer allowed, but
    /// sub-actions may still be fired.
    ///
    /// During this event the action sits on top of `action_stack`.
    ActionApply,

    /// The action's `apply()` has completed. Again, only sub-actions may be
    /// fired — no cancellation or replacement.
    ///
    /// During this event the action sits on top of `action_stack`.
    ActionAfter,

    /// Emitted unconditionally at the end of action resolution. Ideal for
    /// cleanup work. By this point the action has been popped from
    /// `action_stack`.
    ActionDone(Handle),
}

impl Game {
    pub fn new(variant: &'static GameVariant) -> Self {
        Self {
            variant: variant,
            sequence: 0,
            arena: ObjectArena::new(),
            action_stack: vec![],
            hybrid_stack: vec![],
        }
    }

    pub fn next_seq(&mut self) -> u64 {
        self.sequence += 1;
        self.sequence
    }

    /*
    def process_action(self, action: A) -> bool:
        // if self.ended:
        //     return False

        if not action.can_fire():
            log.debug('action invalid %s' % action.__class__.__name__)
            return False

        try:
            action.succeeded = False
        except AttributeError:
            pass

        action = self.emit_event('action_before', action)
        if action.done:
            log.debug('action already done %s' % action.__class__.__name__)
            rst = action.succeeded
        elif action.cancelled:
            log.debug('action cancelled, not firing: %s' % action.__class__.__name__)
            rst = False
        elif not action.can_fire():
            log.debug('action invalid, not firing: %s' % action.__class__.__name__)
            action.invalid = True
            rst = False
        else:
            log.debug('applying action %s' % action.__class__.__name__)
            action = self.emit_event('action_apply', action)
            assert not action.cancelled
            try:
                self.action_stack.append(action)
                self.hybrid_stack.append(action)
                hybrid = self.hybrid_stack  # noqa, when crashes pytest will show hybrid stack here by inspecting local variables
                rst = action.apply_action()
            except InterruptActionFlow as e:
                if e.unwind_to is action:
                    rst = False
                else:
                    raise
            finally:
                _a = self.action_stack.pop()
                _b = self.hybrid_stack.pop()
                assert _a is _b is action

                # If exception occurs here,
                # the action should be abandoned,
                # code below makes no sense,
                # so it's ok to ignore them.

            assert rst in (True, False), 'Action.apply_action must return boolean!'
            try:
                action.succeeded = rst
            except AttributeError:
                pass

            action = self.emit_event('action_after', action)

            rst = action.succeeded
            action.done = True

        self.emit_event('action_done', action)

        return rst
    */

    /// Process a game action through the full lifecycle.
    ///
    /// ```text
    /// validate → action_before → action_apply → apply() → action_after → action_done
    /// ```
    ///
    /// Event handlers may cancel the action during `action_before`.
    /// [`Interrupt::ActionFlowBreak`] targeting this action is caught locally;
    /// all other interrupts propagate up.
    pub fn process_action(&mut self, mut action: GameObject) -> Result<bool> {
        use ActionPhase::*;
        use AlternativePath::*;
        use GameEvent::*;

        let g = self;

        let effect: ActionEffect = *action.need();
        let phase: ActionPhase = *action.need();

        match phase {
            Succeeded | Failed => {
                panic!("action already done");
            }
            Cancelled => {
                debug!("{} was cancelled, not executing", effect.name());
                return Ok(false);
            }
            Invalid => {
                debug!("{} was invalid, not executing", effect.name());
                return Ok(false);
            }
            _ => (),
        }

        let aid = g.arena.add(action);

        // Pre-validation.
        if !g.can_fire(aid)? {
            let [act] = g.arena.reference([aid]);
            *act.need::<ActionPhase>() = Invalid;
            debug!("...");
            return Ok(false);
        }

        g.action_stack.push(aid);
        g.hybrid_stack.push(aid);
        let mut g = {
            let la = g.action_stack.len();
            let lh = g.hybrid_stack.len();
            scopeguard::guard(g, move |g| {
                assert!(g.action_stack.len() == la, "Unbalanced action_stack!");
                assert!(g.hybrid_stack.len() == lh, "Unbalanced hybrid_stack!");
                assert!(
                    g.action_stack[g.action_stack.len() - 1] == aid,
                    "Tampered action_stack!"
                );
                assert!(
                    g.hybrid_stack[g.hybrid_stack.len() - 1] == aid,
                    "Tampered hybrid_stack!"
                );
                g.action_stack.pop();
                g.hybrid_stack.pop();
            })
        };

        // --- ActionBefore: handlers may cancel or resolve early ---
        match g.emit_event(ActionBefore) {
            Ok(()) => {}
            Err(ActionCancelled) => {
                debug!("...");
                let [act] = g.arena.reference([aid]);
                *act.need::<ActionPhase>() = Cancelled;
            }
            Err(v) => return Err(v),
        }

        {
            let [act] = g.arena.reference([aid]);
            let phase: ActionPhase = *act.need();
            match phase {
                rst @ (Succeeded | Failed) => {
                    debug!("...");
                    return Ok(rst == Succeeded);
                }
                Cancelled => {
                    debug!("...");
                    return Ok(false);
                }
                _ => {}
            }
        }

        // Re-validate after handler modifications.
        if !g.can_fire(aid)? {
            let [act] = g.arena.reference([aid]);
            *act.need::<ActionPhase>() = Invalid;
            debug!("...");
            return Ok(false);
        }

        // --- action_apply + execute ---
        match g.emit_event(ActionApply) {
            Ok(v) => {
                act.need::<i32>();
            }
            _ => {}
        }
        Ok(true)
    }

    pub fn can_fire(&mut self, aid: Handle) -> Result<bool> {
        use AlternativePath::ActionWasShotdown;
        use GameEvent::ActionShootdown;

        let [act] = self.arena.reference([aid]);
        let effect = act.need::<ActionEffect>();
        if !(effect.is_valid(self, act)?) {
            debug!("action failed is_valid check: {}", effect.name());
            return Ok(false);
        }
        match self.emit_event(ActionShootdown(aid)) {
            Ok(_) => Ok(true),
            Err(ActionWasShotdown) => {
                debug!("action was shotdown: {}", effect.name());
                Ok(false)
            }
            Err(v) => Err(v),
        }
    }

    /// Dispatch an event to observer → ad-hoc handlers → regular handlers.
    ///
    /// For action events (`action_*`), dispatch stops early if cancelled.
    #[must_use]
    pub fn emit_event(&mut self, ev: GameEvent) -> Result<()> {
        /*
        let is_action_event = evt_type.starts_with("action_");

        // Observer gets first crack (swap pattern, same as handlers).
        if let Some(mut observer) = self.ev_observer.take() {
            let result = observer.handle(evt_type, action, self);
            self.ev_observer = Some(observer);
            result?;
        }

        // Ad-hoc handlers (highest priority, LIFO insertion order).
        let adhoc_indices = self.dispatcher.relevant_adhoc_indices(evt_type);
        for idx in adhoc_indices {
            if is_action_event && action.meta().status.is_cancelled() {
                return Ok(());
            }
            self.dispatch_adhoc_handler(idx, evt_type, action)?;
        }

        // Regular handlers (topologically sorted).
        let handler_indices = self.dispatcher.relevant_handler_indices(evt_type);
        for idx in handler_indices {
            if is_action_event && action.meta().status.is_cancelled() {
                return Ok(());
            }
            self.dispatch_handler(idx, evt_type, action)?;
        }

        Ok(())
        */
        Ok(())
    }

    /*

    /// Dispatch to a regular handler via the swap pattern.
    ///
    /// The handler is [`Option::take`]n out of the dispatcher, called with
    /// `&mut self`, then restored. This lets the handler call back into
    /// `game.process_action()` (re-entrant dispatch) without borrow conflicts.
    /// A `None` slot means the handler is already executing — skip it.
    fn dispatch_handler(
        &mut self,
        idx: usize,
        evt_type: &str,
        action: &mut dyn Action,
    ) -> GameResult<()> {
        let mut handler = match self.dispatcher.handlers[idx].take() {
            Some(h) => h,
            None => return Ok(()), // handler is mid-execution (re-entrant skip)
        };

        let handler_name = handler.name().to_string();

        let result = handler.handle(evt_type, action, self);

        self.dispatcher.handlers[idx] = Some(handler);

        result
    }

    /// Same swap pattern for ad-hoc handlers.
    fn dispatch_adhoc_handler(
        &mut self,
        idx: usize,
        evt_type: &str,
        action: &mut dyn Action,
    ) -> GameResult<()> {
        let mut handler = match self.dispatcher.adhoc[idx].take() {
            Some(h) => h,
            None => return Ok(()),
        };

        let handler_name = handler.name().to_string();

        let result = handler.handle(evt_type, action, self);

        self.dispatcher.adhoc[idx] = Some(handler);

        result
    }
    */
}
