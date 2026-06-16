use std::any::type_name;
use std::fmt::Debug;

use crate::utils::embedded::Embedded;
use crate::utils::traitcast::{Castable, CastableInfra};
use nonmax::NonMaxU32;

#[derive(Debug, Copy, Clone, Default, Castable)]
#[casts_to()]
struct EmptyComponentSlot;

const COMPONENTS: usize = 6;

pub struct GameObject {
    components: [Embedded<dyn Castable, 16>; COMPONENTS],
}

macro_rules! find_slot {
    ($components:expr, $T:ty) => {
        $components
            .iter()
            .position(|v| CastableInfra::<$T>::is(&**v))
            .unwrap_or_else(|| panic!("need: {} not present", type_name::<$T>()))
    };
}

impl GameObject {
    pub fn new() -> GameObject {
        GameObject {
            components: std::array::from_fn(|_| Embedded::new(EmptyComponentSlot)),
        }
    }

    pub fn component<T: 'static>(&mut self) -> Option<&mut T> {
        for v in self.components.iter_mut() {
            if let Some(cv) = v.downcast_mut() {
                return Some(cv);
            }
        }
        None
    }

    pub fn need<T: 'static>(&mut self) -> &mut T {
        let a = find_slot!(self.components, T);
        let [s1] = self
            .components
            .get_disjoint_mut([a])
            .expect("need: indices disjoint by construction");
        s1.downcast_mut().unwrap()
    }

    pub fn need2<T1: 'static, T2: 'static>(&mut self) -> (&mut T1, &mut T2) {
        let a = find_slot!(self.components, T1);
        let b = find_slot!(self.components, T2);
        let [s1, s2] = self
            .components
            .get_disjoint_mut([a, b])
            .expect("need2: indices disjoint by construction");
        (s1.downcast_mut().unwrap(), s2.downcast_mut().unwrap())
    }

    pub fn need3<T1: 'static, T2: 'static, T3: 'static>(&mut self) -> (&mut T1, &mut T2, &mut T3) {
        let a = find_slot!(self.components, T1);
        let b = find_slot!(self.components, T2);
        let c = find_slot!(self.components, T3);
        let [s1, s2, s3] = self
            .components
            .get_disjoint_mut([a, b, c])
            .expect("need3: indices disjoint by construction");
        (
            s1.downcast_mut().unwrap(),
            s2.downcast_mut().unwrap(),
            s3.downcast_mut().unwrap(),
        )
    }

    pub fn add<T: Castable + Copy + Debug + 'static>(&mut self, component: T) -> &mut T {
        for v in self.components.iter_mut() {
            if CastableInfra::<EmptyComponentSlot>::is(&**v) {
                *v = Embedded::new(component);
                return v.downcast_mut().unwrap();
            }
        }
        panic!("Too many components");
    }

    pub fn ensure<T: Castable + Copy + Debug + Default + 'static>(&mut self) -> &mut T {
        // The borrow checker can't see that component()'s borrow ends
        // before add() in the `None` branch, since the returned reference
        // could alias with `self` through the `return v` path. A raw pointer
        // sidesteps this limitation while preserving soundness.
        let ptr: *mut Self = self;
        // SAFETY: `ptr` is derived from a valid `&mut self` and is never
        // aliased. In the Some branch we return the reference from
        // component() which is valid for the lifetime of self. In the None
        // branch we call add() on the same valid pointer, obtaining a new
        // mutable reference. At no point do both references coexist.
        unsafe {
            if let Some(v) = (*ptr).component() {
                return v;
            }
            (*ptr).add(Default::default())
        }
    }
}

///|
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct Handle(NonMaxU32);
pub struct ObjectArena(Vec<GameObject>);

impl ObjectArena {
    pub fn new() -> ObjectArena {
        ObjectArena(vec![])
    }

    pub fn add(&mut self, obj: GameObject) -> Handle {
        self.0.push(obj);
        Handle(NonMaxU32::new((self.0.len() - 1).try_into().unwrap()).unwrap())
    }

    pub fn reference<const N: usize>(&mut self, handles: [Handle; N]) -> [&mut GameObject; N] {
        self.0
            .get_disjoint_mut(handles.map(|v| v.0.get() as usize))
            .unwrap()
    }
}

pub use thb_macros::with;

#[cfg(test)]
mod with_tests {
    use super::*;
    use thb_macros::with;

    struct Host {
        arena: ObjectArena,
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq, Castable)]
    #[casts_to()]
    struct CompA(u32);

    #[derive(Debug, Clone, Copy, PartialEq, Eq, Castable)]
    #[casts_to()]
    struct CompB(i64);

    #[derive(Debug, Clone, Copy, PartialEq, Eq, Castable)]
    #[casts_to()]
    struct CompC(u8);

    fn make_host() -> (Host, Handle, Handle, Handle, Handle) {
        let mut arena = ObjectArena::new();
        let mut o1 = GameObject::new();
        o1.add(CompA(1));
        let h1 = arena.add(o1);

        let mut o2 = GameObject::new();
        o2.add(CompB(-2));
        let h2 = arena.add(o2);

        let mut o3 = GameObject::new();
        o3.add(CompA(30));
        o3.add(CompB(31));
        o3.add(CompC(32));
        let h3 = arena.add(o3);

        let mut o4 = GameObject::new();
        o4.add(CompB(40));
        let h4 = arena.add(o4);

        (Host { arena }, h1, h2, h3, h4)
    }

    #[test]
    fn plain_name_binds_gameobject() {
        let (mut g, h1, _h2, _h3, _h4) = make_host();
        let act = h1;
        with!(g, |act| {
            assert_eq!(*act.need::<CompA>(), CompA(1));
            *act.need::<CompA>() = CompA(11);
        });
        let [obj] = g.arena.reference([h1]);
        assert_eq!(*obj.need::<CompA>(), CompA(11));
    }

    #[test]
    fn at_handle_binds_gameobject() {
        let (mut g, h1, _h2, _h3, _h4) = make_host();
        let action2 = h1;
        with!(g, |act: @action2| {
            *act.need::<CompA>() = CompA(42);
        });
        let [obj] = g.arena.reference([h1]);
        assert_eq!(*obj.need::<CompA>(), CompA(42));
    }

    #[test]
    fn typed_same_name_handle() {
        let (mut g, h1, _h2, _h3, _h4) = make_host();
        let c1 = h1;
        with!(g, |c1: CompA| {
            assert_eq!(*c1, CompA(1));
            *c1 = CompA(7);
        });
        let [obj] = g.arena.reference([h1]);
        assert_eq!(*obj.need::<CompA>(), CompA(7));
    }

    #[test]
    fn typed_at_handle() {
        let (mut g, _h1, h2, _h3, _h4) = make_host();
        let act3 = h2;
        with!(g, |c2: CompB@act3| {
            assert_eq!(*c2, CompB(-2));
            *c2 = CompB(99);
        });
        let [obj] = g.arena.reference([h2]);
        assert_eq!(*obj.need::<CompB>(), CompB(99));
    }

    #[test]
    fn doc_example_full_signature() {
        let (mut g, h1, h2, h3, h4) = make_host();
        let act = h1;
        let action2 = h2;
        let c1 = h3;
        let act3 = h4;

        with!(g, |act, act2: @action2, c1: CompA, c2: CompB@act3| {
            assert_eq!(*act.need::<CompA>(), CompA(1));
            assert_eq!(*act2.need::<CompB>(), CompB(-2));
            assert_eq!(*c1, CompA(30));
            assert_eq!(*c2, CompB(40));
        });
    }

    #[test]
    fn two_components_same_handle_uses_need2() {
        let (mut g, _h1, _h2, h3, _h4) = make_host();
        let target = h3;
        with!(g, |a: CompA@target, b: CompB@target| {
            assert_eq!(*a, CompA(30));
            assert_eq!(*b, CompB(31));
            *a = CompA(300);
            *b = CompB(310);
        });
        let [obj] = g.arena.reference([h3]);
        assert_eq!(*obj.need::<CompA>(), CompA(300));
        assert_eq!(*obj.need::<CompB>(), CompB(310));
    }

    #[test]
    fn three_components_same_handle_uses_need3() {
        let (mut g, _h1, _h2, h3, _h4) = make_host();
        let target = h3;
        with!(g, |a: CompA@target, b: CompB@target, c: CompC@target| {
            assert_eq!(*a, CompA(30));
            assert_eq!(*b, CompB(31));
            assert_eq!(*c, CompC(32));
            *c = CompC(99);
        });
        let [obj] = g.arena.reference([h3]);
        assert_eq!(*obj.need::<CompC>(), CompC(99));
    }

    #[test]
    #[should_panic]
    fn duplicate_handles_panic() {
        let (mut g, h1, _h2, _h3, _h4) = make_host();
        let a = h1;
        let b = h1;
        with!(g, |x: @a, y: @b| {
            let _ = (x, y);
        });
    }

    #[test]
    fn deref_single_binding_copies_component() {
        let (mut g, h1, _h2, _h3, _h4) = make_host();
        let copied: CompA = with!(g, |c: *CompA@h1| {
            c
        });
        assert_eq!(copied, CompA(1));
    }

    #[test]
    fn deref_in_group_mixes_with_ref() {
        let (mut g, _h1, _h2, h3, _h4) = make_host();
        with!(g, |a: *CompA@h3, b: CompB@h3| {
            assert_eq!(a, CompA(30));
            assert_eq!(b, &mut CompB(31));
            b.0 = 99;
        });
        with!(g, |b: CompB@h3| {
            assert_eq!(b.0, 99);
        });
    }
}
