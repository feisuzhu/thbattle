use actix::{Actor, Context};

// use crate::api::{Event, Message, Request};
use aya::util::WeakRegistry;

mod common;

struct A;

impl Actor for A {
    type Context = Context<Self>;
}

#[test]
fn test_weak_registry() {
    common::init_log();

    let sys = actix::System::new("test");
    let r: WeakRegistry<A> = WeakRegistry::new();
    let a1 = A.start();
    let a2 = A.start();
    let a3 = A.start();
    r.register("a1".to_owned(), &a1);
    r.register("a2".to_owned(), &a2);
    r.register("a3".to_owned(), &a3);

    assert!(r.query(&"a1".to_owned()).unwrap() == a1);
    assert!(r.query(&"a2".to_owned()).unwrap() == a2);
    assert!(r.query(&"a3".to_owned()).unwrap() == a3);

    drop(a1);

    common::run_later(())
        .with(move |()| {
            assert!(r.query(&"a1".to_owned()).is_none());
            assert!(r.query(&"a3".to_owned()).unwrap() == a3);
            actix::System::current().stop();
        })
        .fire();

    sys.run();
}
