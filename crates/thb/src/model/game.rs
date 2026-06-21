use std::rc::Rc;

use log::debug;

use super::action::{ActionEffect, ActionObject, ActionPhase};
use super::event::EventDispatcher;
use super::object::{with, GameObject, Handle, ObjectArena};

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

    // In-game players, identified by their index.
    pub players: Vec<Handle>,

    // Actions currently resolving
    pub action_stack: Vec<Handle>,

    // Actions and EventHandlers currently resolving
    pub hybrid_stack: Vec<Handle>,

    // GameEvents are dispatched by dispatcher
    pub dispatcher: Rc<EventDispatcher>,
}

#[derive(Copy, Clone, strum::EnumDiscriminants)]
#[strum_discriminants(
    name(GameEventKind),
    derive(
        Hash,
        PartialOrd,
        Ord,
        strum::FromRepr,
        strum::EnumIter,
        strum::EnumCount
    ),
    repr(u8)
)]
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
            players: vec![],
            action_stack: vec![],
            hybrid_stack: vec![],
            dispatcher: Rc::new(EventDispatcher::build(&[])),
        }
    }

    pub fn next_seq(&mut self) -> u64 {
        self.sequence += 1;
        self.sequence
    }

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

        let effect: ActionEffect = *action.need();
        let phase: ActionPhase = *action.need();

        match phase {
            Done(_) => {
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

        let act = self.arena.add(action);

        // Pre-validation.
        if !self.can_fire(act)? {
            with!(self, |phase: ActionPhase@act| {
                *phase = Invalid;
            });
            debug!("...");
            return Ok(false);
        }

        self.action_stack.push(act);
        self.hybrid_stack.push(act);
        let balancer = {
            let la = self.action_stack.len();
            let lh = self.hybrid_stack.len();
            let g: *mut Game = self;
            scopeguard::guard((), move |()| {
                // SAFETY: We are not capturing &mut Game into anything, so it must be valid at the
                // point of return
                let g = unsafe { &mut *g };
                assert!(g.action_stack.len() == la, "Unbalanced action_stack!");
                assert!(g.hybrid_stack.len() == lh, "Unbalanced hybrid_stack!");
                g.action_stack.pop();
                g.hybrid_stack.pop();
            })
        };

        // --- ActionBefore: handlers may cancel or resolve early ---
        match self.emit_event(ActionBefore) {
            Ok(()) => {}
            Err(ActionCancelled) => {
                debug!("...");
                with!(self, |phase: ActionPhase@act| {
                    *phase = Cancelled;
                });
            }
            Err(v) => return Err(v),
        }

        // act might be replaced
        let act = *self.action_stack.last().unwrap();
        let phase = with!(self, |phase: *ActionPhase@act| { phase });

        match phase {
            Done(rst) => {
                debug!("...");
                return Ok(rst);
            }
            Cancelled => {
                debug!("...");
                return Ok(false);
            }
            _ => {}
        }

        // Re-validate after handler modifications.
        if !self.can_fire(act)? {
            with!(self, |phase: ActionPhase@act| {
                *phase = Invalid;
            });
            debug!("...");
            return Ok(false);
        }

        // --- action_apply + execute ---
        self.emit_event(ActionApply)?;
        let phase = with!(self, |phase: *ActionPhase@act| { phase });
        assert!(phase != Cancelled);
        let rst = effect.apply(self);
        drop(balancer);
        let rst = match rst {
            Ok(v) => v,
            Err(InterruptActionFlow { unwind_to }) => {
                if unwind_to != act {
                    return Err(InterruptActionFlow { unwind_to });
                } else {
                    false
                }
            }
            Err(v) => return Err(v),
        };
        with!(self, |phase: ActionPhase@act| {
            *phase = Done(rst);
        });

        // --- action_done ---
        self.emit_event(ActionDone(act))?;

        Ok(rst)
    }

    #[must_use]
    pub fn can_fire(&mut self, aid: Handle) -> Result<bool> {
        use AlternativePath::ActionWasShotdown;
        use GameEvent::ActionShootdown;

        let [act] = self.arena.reference([aid]);
        let effect = *act.need::<ActionEffect>();
        if !(effect.is_valid(self, aid)?) {
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

    #[must_use]
    pub fn emit_event(&mut self, ev: GameEvent) -> Result<()> {
        // TODO: adhoc handlers
        self.dispatcher.clone().dispatch(self, ev)
    }
}
