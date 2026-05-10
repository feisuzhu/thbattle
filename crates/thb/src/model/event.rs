use std::any::TypeId;
use std::rc::Rc;

use crate::model::base::ZeroSized;
use crate::model::object::Handle;

use super::game::Result;
use super::game::{Game, GameEvent};

/// An event handler that reacts to game events.
///
/// Handlers are topologically sorted by `execute_before` / `execute_after`
/// constraints and dispatched in that order. During dispatch, each handler
/// can modify the action (cancel it, mark done, etc.) or trigger side
/// effects through the game reference — including recursive `process_action`.
///
/// EventHandlers themselves should be zero sized, they must store their data
/// on other components.
pub trait EventHandler {
    /// Name, for debugging and logging
    fn name(&self) -> &'static str {
        std::any::type_name::<Self>()
    }

    /// This EventHandler should run before said EventHandlers
    fn execute_before(&self) -> &'static [TypeId] {
        &[]
    }

    /// This EventHandler should run after said EventHandlers
    fn execute_after(&self) -> &'static [TypeId] {
        &[]
    }

    /// This EventHandler should be placed in a sub EventDispatcher,
    /// sub EventDispatcher represents a single point of time in EventHandler
    /// resolve order, but will resolve EventHandler under the group in a
    /// specific order, usually depends on the situation of game.
    fn dispatcher(&self) -> TypeId {
        TypeId::of::<EventDispatcher>()
    }

    /// Given the context, should we execute the `handle` now?
    /// Only used in `EventArbiter`s dispatching process, usually involved a
    /// Player/Character 'cause seat location.
    ///
    /// Note this is not the semantic of original `interested = []` in Python code,
    /// which is just a perf optimization.
    #[allow(unused_variables)]
    fn interested(&self, ctx: Handle) -> bool {
        true
    }

    /// Actual logic of the EventHandler. Assuming top of action_stack is what's interested.
    fn handle(&self, g: &mut Game, ev: GameEvent, ctx: Option<Handle>) -> Result<()>;
}

pub trait EventArbiter {
    fn dispatch<'a>(
        &self,
        handlers: &'a [ZeroSized<dyn EventHandler>],
        g: &mut Game,
        ev: GameEvent,
    ) -> Result<()>;
}

pub struct EventDispatcher {
    groups: Box<
        [(
            ZeroSized<dyn EventArbiter>,
            Box<[ZeroSized<dyn EventHandler>]>,
        )],
    >,
}

impl EventDispatcher {
    fn build(handlers: &[ZeroSized<dyn EventHandler>]) -> Self {
        // TODO: topo sort here
    }

    fn dispatch(self: Rc<Self>, g: &mut Game, ev: GameEvent) -> Result<()> {
        for (arbiter, handlers) in self.groups.iter() {
            arbiter.dispatch(handlers, g, ev)?;
        }
        Ok(())
    }
}

struct LinearEventArbiter;
impl EventArbiter for LinearEventArbiter {
    fn dispatch<'a>(
        &self,
        handlers: &'a [ZeroSized<dyn EventHandler>],
        g: &mut Game,
        ev: GameEvent,
    ) -> Result<()> {
        for h in handlers.iter().copied() {
            h.handle(g, ev, None)?;
        }
        Ok(())
    }
}

struct CounterClockwiseEventArbiter;
impl EventArbiter for CounterClockwiseEventArbiter {
    fn dispatch<'a>(
        &self,
        handlers: &'a [ZeroSized<dyn EventHandler>],
        g: &mut Game,
        ev: GameEvent,
    ) -> Result<()> {
        todo!()
    }
}
