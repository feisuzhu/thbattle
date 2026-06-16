use std::any::TypeId;
use std::collections::{HashMap, HashSet};
use std::rc::Rc;

use strum::EnumCount;

use crate::utils::embedded::ZeroSized;
use super::game::Result;
use super::game::{Game, GameEvent, GameEventKind};

#[derive(Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Debug)]
pub struct ShortId(u64);

#[inline]
pub const fn short_id(tid: TypeId) -> ShortId {
    let (a, b): (u64, u64) = unsafe { std::mem::transmute(tid) };
    ShortId(a ^ b)
}

/// An event handler that reacts to game events.
///
/// Handlers are topologically sorted by `execute_before` / `execute_after`
/// constraints and dispatched in that order. During dispatch, each handler
/// can modify the action (cancel it, mark done, etc.) or trigger side
/// effects through the game reference — including recursive `process_action`.
///
/// EventHandlers themselves should be zero sized, they must store their data
/// on other components. Each handler's identity in the topo-sort graph is
/// its [`name`](EventHandler::name).
pub trait EventHandler
where
    Self: 'static,
{
    /// Name, for debugging and logging
    fn name(&self) -> &'static str {
        std::any::type_name::<Self>()
    }

    /// Used for sorting
    fn id(&self) -> ShortId {
        short_id(std::any::TypeId::of::<Self>())
    }

    /// This EventHandler should run before said EventHandlers
    fn execute_before(&self) -> &'static [ShortId] {
        &[]
    }

    /// This EventHandler should run after said EventHandlers
    fn execute_after(&self) -> &'static [ShortId] {
        &[]
    }

    /// The events this EventHandler will process. Perf optimization to not iterate every
    /// EventHandler for events. You will not receive the event if the kind is not specified here.
    fn interested(&self) -> &'static [GameEventKind] {
        &[]
    }

    /// Actual logic of the EventHandler. Assuming top of action_stack is what's interested.
    fn handle(&self, g: &mut Game, ev: GameEvent) -> Result<()>;
}

pub struct EventDispatcher {
    handlers: [Box<[ZeroSized<dyn EventHandler>]>; GameEventKind::COUNT],
}

impl EventDispatcher {
    /// Topo-sort handlers by `execute_before` / `execute_after`, then bucket
    /// them by `interested()` into per-`GameEventKind` slices preserving
    /// topo order. Direct port of `EventHandler.make_list` plus
    /// `_get_relevant_eh` cache in Python `src/game/base.py`. Panics on
    /// circular dependencies.
    pub fn build(handlers: &[ZeroSized<dyn EventHandler>]) -> Self {
        // Initial stable sort by `ShortId` to give the Kahn-style topo sort
        // a deterministic tie-breaker. `ShortId` order has no human meaning
        // and may shift across rustc/codegen versions, but it is stable
        // within a single build — which is all the algorithm requires.
        let mut nodes: Vec<ZeroSized<dyn EventHandler>> = handlers.to_vec();
        nodes.sort_by_key(|h| h.id());

        let n = nodes.len();
        let self_id: Vec<ShortId> = nodes.iter().map(|h| h.id()).collect();
        let idx_of: HashMap<ShortId, usize> = self_id
            .iter()
            .copied()
            .enumerate()
            .map(|(i, t)| (t, i))
            .collect();
        assert_eq!(
            idx_of.len(),
            n,
            "Duplicate EventHandler ShortId in dispatcher: {:?}",
            nodes.iter().map(|h| h.name()).collect::<Vec<_>>()
        );
        let allids: HashSet<ShortId> = self_id.iter().copied().collect();

        let filter_in_scope = |slice: &[ShortId]| -> HashSet<ShortId> {
            slice
                .iter()
                .copied()
                .filter(|t| allids.contains(t))
                .collect()
        };

        let before: Vec<HashSet<ShortId>> = nodes
            .iter()
            .map(|h| filter_in_scope(h.execute_before()))
            .collect();
        let mut after: Vec<HashSet<ShortId>> = nodes
            .iter()
            .map(|h| filter_in_scope(h.execute_after()))
            .collect();

        for i in 0..n {
            let me = self_id[i];
            for b in &before[i] {
                after[idx_of[b]].insert(me);
            }
        }

        let mut toposorted: Vec<ZeroSized<dyn EventHandler>> = Vec::with_capacity(n);
        let mut remaining: Vec<usize> = (0..n).collect();

        while !remaining.is_empty() {
            let (commit, deferred): (Vec<usize>, Vec<usize>) = remaining
                .iter()
                .copied()
                .partition(|&i| after[i].is_empty());

            if commit.is_empty() {
                let names: Vec<&'static str> = remaining.iter().map(|&i| nodes[i].name()).collect();
                panic!("Circular EventHandler dependency among: {names:?}");
            }

            for &i in &commit {
                let me = self_id[i];
                for b in &before[i] {
                    after[idx_of[b]].remove(&me);
                }
            }

            toposorted.extend(commit.iter().map(|&i| nodes[i]));
            remaining = deferred;
        }

        let mut buckets: [Vec<ZeroSized<dyn EventHandler>>; GameEventKind::COUNT] =
            std::array::from_fn(|_| Vec::new());
        for h in &toposorted {
            for &kind in h.interested() {
                buckets[kind as usize].push(*h);
            }
        }

        Self {
            handlers: buckets.map(Vec::into_boxed_slice),
        }
    }

    pub fn dispatch(self: Rc<Self>, g: &mut Game, ev: GameEvent) -> Result<()> {
        let kind = GameEventKind::from(&ev);
        for h in self.handlers[kind as usize].iter().copied() {
            h.handle(g, ev)?;
        }
        Ok(())
    }
}
