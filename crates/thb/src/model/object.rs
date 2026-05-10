use std::any::Any;
use std::fmt::Debug;
use std::num::NonZeroU32;
use std::slice::GetDisjointMutError;

use stack_dst::array_buf;
use stack_dst::Value;

type ZeroSizedTrait<T> = Value<T, stack_dst::buffers::Ptr1>;

#[derive(Debug, Copy, Clone, Default)]
struct EmptyComponentSlot;

const COMPONENTS: usize = 6;

pub struct GameObject {
    components: [Value<dyn Any, array_buf![usize; U2]>; COMPONENTS],
}

impl GameObject {
    pub fn new() -> GameObject {
        GameObject {
            components: std::array::from_fn(|_| {
                Value::new_stable(EmptyComponentSlot {}, |v| v as _).unwrap()
            }),
        }
    }

    pub fn component<T: 'static>(&mut self) -> Option<&mut T> {
        for v in self.components.iter_mut() {
            if v.is::<EmptyComponentSlot>() {
                break;
            }
            if let Some(cv) = v.downcast_mut::<T>() {
                return Some(cv);
            }
        }
        None
    }

    pub fn component2<T1: 'static, T2: 'static>(
        &mut self,
    ) -> (Option<&mut T1>, Option<&mut T2>) {
        assert!(
            std::any::TypeId::of::<T1>() != std::any::TypeId::of::<T2>(),
            "component2 requires distinct types"
        );
        let mut i1: Option<usize> = None;
        let mut i2: Option<usize> = None;
        for (idx, v) in self.components.iter().enumerate() {
            if v.is::<EmptyComponentSlot>() { break; }
            if i1.is_none() && v.is::<T1>() { i1 = Some(idx); continue; }
            if i2.is_none() && v.is::<T2>() { i2 = Some(idx); continue; }
        }
        match (i1, i2) {
            (Some(a), Some(b)) => {
                let [s1, s2] = self.components.get_disjoint_mut([a, b])
                    .expect("component2: indices disjoint by construction");
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>())
            }
            (Some(a), None) => (self.components[a].downcast_mut::<T1>(), None),
            (None, Some(b)) => (None, self.components[b].downcast_mut::<T2>()),
            (None, None) => (None, None),
        }
    }

    pub fn component3<T1: 'static, T2: 'static, T3: 'static>(
        &mut self,
    ) -> (Option<&mut T1>, Option<&mut T2>, Option<&mut T3>) {
        let ids = [
            std::any::TypeId::of::<T1>(),
            std::any::TypeId::of::<T2>(),
            std::any::TypeId::of::<T3>(),
        ];
        for i in 0..ids.len() {
            for j in (i + 1)..ids.len() {
                assert!(ids[i] != ids[j], "component3 requires distinct component types");
            }
        }
        let mut i1: Option<usize> = None;
        let mut i2: Option<usize> = None;
        let mut i3: Option<usize> = None;
        for (idx, v) in self.components.iter().enumerate() {
            if v.is::<EmptyComponentSlot>() { break; }
            if i1.is_none() && v.is::<T1>() { i1 = Some(idx); continue; }
            if i2.is_none() && v.is::<T2>() { i2 = Some(idx); continue; }
            if i3.is_none() && v.is::<T3>() { i3 = Some(idx); continue; }
        }
        // Match on which positions were found; pick the smallest array
        // size that fits and call `get_disjoint_mut` accordingly. The
        // collected indices come from distinct type matches and the
        // single-pass scan, so they are guaranteed disjoint.
        let expect_msg = "component3: indices disjoint by construction";
        match (i1, i2, i3) {
            (Some(a), Some(b), Some(c)) => {
                let [s1, s2, s3] = self.components.get_disjoint_mut([a, b, c]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>(), s3.downcast_mut::<T3>())
            }
            (Some(a), Some(b), None) => {
                let [s1, s2] = self.components.get_disjoint_mut([a, b]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>(), None)
            }
            (Some(a), None, Some(c)) => {
                let [s1, s3] = self.components.get_disjoint_mut([a, c]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), None, s3.downcast_mut::<T3>())
            }
            (None, Some(b), Some(c)) => {
                let [s2, s3] = self.components.get_disjoint_mut([b, c]).expect(expect_msg);
                (None, s2.downcast_mut::<T2>(), s3.downcast_mut::<T3>())
            }
            (Some(a), None, None) => (self.components[a].downcast_mut::<T1>(), None, None),
            (None, Some(b), None) => (None, self.components[b].downcast_mut::<T2>(), None),
            (None, None, Some(c)) => (None, None, self.components[c].downcast_mut::<T3>()),
            (None, None, None) => (None, None, None),
        }
    }

    pub fn component4<T1: 'static, T2: 'static, T3: 'static, T4: 'static>(
        &mut self,
    ) -> (
        Option<&mut T1>,
        Option<&mut T2>,
        Option<&mut T3>,
        Option<&mut T4>,
    ) {
        let ids = [
            std::any::TypeId::of::<T1>(),
            std::any::TypeId::of::<T2>(),
            std::any::TypeId::of::<T3>(),
            std::any::TypeId::of::<T4>(),
        ];
        for i in 0..ids.len() {
            for j in (i + 1)..ids.len() {
                assert!(ids[i] != ids[j], "component4 requires distinct component types");
            }
        }
        let mut i1: Option<usize> = None;
        let mut i2: Option<usize> = None;
        let mut i3: Option<usize> = None;
        let mut i4: Option<usize> = None;
        for (idx, v) in self.components.iter().enumerate() {
            if v.is::<EmptyComponentSlot>() { break; }
            if i1.is_none() && v.is::<T1>() { i1 = Some(idx); continue; }
            if i2.is_none() && v.is::<T2>() { i2 = Some(idx); continue; }
            if i3.is_none() && v.is::<T3>() { i3 = Some(idx); continue; }
            if i4.is_none() && v.is::<T4>() { i4 = Some(idx); continue; }
        }
        let expect_msg = "component4: indices disjoint by construction";
        match (i1, i2, i3, i4) {
            (Some(a), Some(b), Some(c), Some(d)) => {
                let [s1, s2, s3, s4] = self.components.get_disjoint_mut([a, b, c, d]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>(), s3.downcast_mut::<T3>(), s4.downcast_mut::<T4>())
            }
            (Some(a), Some(b), Some(c), None) => {
                let [s1, s2, s3] = self.components.get_disjoint_mut([a, b, c]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>(), s3.downcast_mut::<T3>(), None)
            }
            (Some(a), Some(b), None, Some(d)) => {
                let [s1, s2, s4] = self.components.get_disjoint_mut([a, b, d]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>(), None, s4.downcast_mut::<T4>())
            }
            (Some(a), None, Some(c), Some(d)) => {
                let [s1, s3, s4] = self.components.get_disjoint_mut([a, c, d]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), None, s3.downcast_mut::<T3>(), s4.downcast_mut::<T4>())
            }
            (None, Some(b), Some(c), Some(d)) => {
                let [s2, s3, s4] = self.components.get_disjoint_mut([b, c, d]).expect(expect_msg);
                (None, s2.downcast_mut::<T2>(), s3.downcast_mut::<T3>(), s4.downcast_mut::<T4>())
            }
            (Some(a), Some(b), None, None) => {
                let [s1, s2] = self.components.get_disjoint_mut([a, b]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), s2.downcast_mut::<T2>(), None, None)
            }
            (Some(a), None, Some(c), None) => {
                let [s1, s3] = self.components.get_disjoint_mut([a, c]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), None, s3.downcast_mut::<T3>(), None)
            }
            (Some(a), None, None, Some(d)) => {
                let [s1, s4] = self.components.get_disjoint_mut([a, d]).expect(expect_msg);
                (s1.downcast_mut::<T1>(), None, None, s4.downcast_mut::<T4>())
            }
            (None, Some(b), Some(c), None) => {
                let [s2, s3] = self.components.get_disjoint_mut([b, c]).expect(expect_msg);
                (None, s2.downcast_mut::<T2>(), s3.downcast_mut::<T3>(), None)
            }
            (None, Some(b), None, Some(d)) => {
                let [s2, s4] = self.components.get_disjoint_mut([b, d]).expect(expect_msg);
                (None, s2.downcast_mut::<T2>(), None, s4.downcast_mut::<T4>())
            }
            (None, None, Some(c), Some(d)) => {
                let [s3, s4] = self.components.get_disjoint_mut([c, d]).expect(expect_msg);
                (None, None, s3.downcast_mut::<T3>(), s4.downcast_mut::<T4>())
            }
            (Some(a), None, None, None) => (self.components[a].downcast_mut::<T1>(), None, None, None),
            (None, Some(b), None, None) => (None, self.components[b].downcast_mut::<T2>(), None, None),
            (None, None, Some(c), None) => (None, None, self.components[c].downcast_mut::<T3>(), None),
            (None, None, None, Some(d)) => (None, None, None, self.components[d].downcast_mut::<T4>()),
            (None, None, None, None) => (None, None, None, None),
        }
    }

    pub fn add<T: Debug + 'static>(&mut self, component: T) -> &mut T {
        for v in self.components.iter_mut() {
            if v.is::<EmptyComponentSlot>() {
                *v = Value::new_stable(component, |v| v as _).expect("Component size too big");
                return v.downcast_mut().unwrap();
            }
        }
        panic!("Too many components");
    }

    pub fn ensure<T: Debug + Default + 'static>(&mut self) -> &mut T {
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

    pub fn need<T: 'static>(&mut self) -> &mut T {
        self.component().unwrap_or_else(|| {
            panic!(
                "Requested component {} does not exist",
                std::any::type_name::<T>()
            )
        })
    }
}

///|
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub struct Handle(NonZeroU32);
pub struct ObjectArena(Vec<GameObject>);

impl ObjectArena {
    pub fn new() -> ObjectArena {
        ObjectArena(vec![GameObject::new()])
    }

    pub fn add(&mut self, obj: GameObject) -> Handle {
        self.0.push(obj);
        Handle(NonZeroU32::new((self.0.len() - 1).try_into().unwrap()).unwrap())
    }

    pub fn reference<const N: usize>(&mut self, handles: [Handle; N]) -> [&mut GameObject; N] {
        self.0
            .get_disjoint_mut(handles.map(|v| v.0.get() as usize))
            .unwrap()
    }
}

/*
`action` as Handle
with!(g, |act, act2: @action2, c1: ActionPhase, c2: Option<ActionEffect>@act3| {
    act is now &mut GameObject, got by g.arena.reference([act])
    act2 is now &mut GameObject, got by g.arena.reference([action2])
    c1 is not &mut ActionPhase, got by {
        let [obj] = g.arena.reference([c1])
        let c1 = obj.component::<ActionPhase>().unwrap();
    }
    c2 is now Option<&mut ActionEffect>, got by {
        let [obj] = g.arena.reference([act3])
        let c2 = obj.component::<ActionPhase>();
    }

    here's user's code, enclosed in the macro's braces
})
*/

pub use thb_macros::with;

#[cfg(test)]
mod with_tests {
    use super::*;
    use thb_macros::with;

    struct Host {
        arena: ObjectArena,
    }

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    struct CompA(u32);

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
    struct CompB(i64);

    #[derive(Debug, Clone, Copy, PartialEq, Eq)]
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
    fn option_present() {
        let (mut g, h1, _h2, _h3, _h4) = make_host();
        let target = h1;
        with!(g, |maybe_a: Option<CompA>@target| {
            assert!(maybe_a.is_some());
            *maybe_a.unwrap() = CompA(123);
        });
        let [obj] = g.arena.reference([h1]);
        assert_eq!(*obj.need::<CompA>(), CompA(123));
    }

    #[test]
    fn option_absent() {
        let (mut g, _h1, h2, _h3, _h4) = make_host();
        let target = h2;
        with!(g, |maybe_a: Option<CompA>@target| {
            assert!(maybe_a.is_none());
        });
    }

    #[test]
    fn doc_example_full_signature() {
        let (mut g, h1, h2, h3, h4) = make_host();
        let act = h1;
        let action2 = h2;
        let c1 = h3;
        let act3 = h4;

        with!(g, |act, act2: @action2, c1: CompA, c2: Option<CompB>@act3| {
            assert_eq!(*act.need::<CompA>(), CompA(1));
            assert_eq!(*act2.need::<CompB>(), CompB(-2));
            assert_eq!(*c1, CompA(30));
            assert!(c2.is_some());
            assert_eq!(*c2.unwrap(), CompB(40));
        });
    }

    #[test]
    fn two_components_same_handle_uses_component2() {
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
    fn three_components_same_handle_uses_component3() {
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
    fn mixed_option_and_required_same_handle() {
        let (mut g, _h1, _h2, h3, _h4) = make_host();
        let target = h3;
        with!(g, |a: CompA@target, missing: Option<u128>@target, b: CompB@target| {
            assert_eq!(*a, CompA(30));
            assert!(missing.is_none());
            assert_eq!(*b, CompB(31));
        });
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
}
