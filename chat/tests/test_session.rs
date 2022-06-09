use log::debug;
use std::num::NonZeroU32;
use std::sync::{Arc, Mutex};
use std::time::Duration;

use actix::clock::sleep;
use actix::{Actor, Context, Handler};
// use actix_rt::test;

use aya::actors::Session;
use aya::api;
use aya::core::ChatServerCore;

mod common;

type Sink = Arc<Mutex<Vec<api::Event>>>;

struct EventSink {
    sink: Sink,
}

impl Actor for EventSink {
    type Context = Context<Self>;
}

impl Handler<api::Event> for EventSink {
    type Result = ();
    fn handle(&mut self, ev: api::Event, _ctx: &mut Self::Context) {
        self.sink.lock().unwrap().push(ev);
        debug!("EventSink received something, put it in sink");
    }
}

impl EventSink {
    fn new(sink: Sink) -> EventSink {
        EventSink { sink }
    }
}

// PM is disabled
#[allow(dead_code)]
// #[actix_rt::test]
async fn test_pm() {
    common::init_log();

    let sink: Sink = Arc::new(Mutex::new(vec![]));

    let core = Arc::new(ChatServerCore::default());

    let s1 = Session::new(
        core.clone(),
        EventSink::new(sink.clone()).start().recipient(),
    )
    .start();

    let s2 = Session::new(
        core.clone(),
        EventSink::new(sink.clone()).start().recipient(),
    )
    .start();

    s1.do_send(api::Request::Login(api::Login {
        token: "test_pm:s1".to_owned(),
    }));
    s2.do_send(api::Request::Login(api::Login {
        token: "test_pm:s2".to_owned(),
    }));

    sleep(Duration::from_millis(1)).await;

    assert_eq!(
        vec![api::Event::Success, api::Event::Success],
        sink.lock().unwrap().drain(..).collect::<Vec<_>>(),
    );

    s1.do_send(api::Request::Message(api::Message {
        entity: "User:test_pm:s2".to_owned(),
        channel: "test_pm".to_owned(),
        text: "text".to_owned().into_bytes(),
        sender: None,
    }));

    sleep(Duration::from_millis(1)).await;

    {
        let mut s = sink.lock().unwrap();

        assert_eq!(s.len(), 1);
        let ev = s.pop().unwrap();
        match ev {
            api::Event::Message(m) => {
                let tp = (&m.entity[..], &m.channel[..], &m.text[..]);
                assert_eq!(
                    tp,
                    (
                        "User:test_pm:s2",
                        "test_pm",
                        "text".to_owned().into_bytes().as_ref()
                    )
                );
                match m.sender {
                    Some(id) if id.get() == 10001 => (),
                    _ => panic!("Unexpected user id!"),
                }
            }
            a => panic!("Not a message: {:?}!", a),
        }
    }
}

#[actix_rt::test]
async fn test_room() {
    common::init_log();

    let sink1: Sink = Arc::new(Mutex::new(vec![]));
    let sink2: Sink = Arc::new(Mutex::new(vec![]));

    let core = Arc::new(ChatServerCore::default());

    let s1 = Session::new_logged_in(
        core.clone(),
        EventSink::new(sink1.clone()).start().recipient(),
        10001,
    )
    .start();
    let s2 = Session::new_logged_in(
        core.clone(),
        EventSink::new(sink2.clone()).start().recipient(),
        10002,
    )
    .start();

    s1.do_send(api::Request::Login(api::Login {
        token: "whatever".to_owned(),
    }));
    s2.do_send(api::Request::Login(api::Login {
        token: "whatever".to_owned(),
    }));

    s1.do_send(api::Request::Join(api::Join {
        room: "test_room:foo".to_owned(),
    }));
    s2.do_send(api::Request::Join(api::Join {
        room: "test_room:foo".to_owned(),
    }));

    sleep(Duration::from_millis(1)).await;

    assert_eq!(
        vec![api::Event::Success, api::Event::Success],
        sink1.lock().unwrap().drain(..).collect::<Vec<_>>(),
    );
    assert_eq!(
        vec![api::Event::Success, api::Event::Success],
        sink2.lock().unwrap().drain(..).collect::<Vec<_>>(),
    );

    s1.do_send(api::Request::Message(api::Message {
        entity: "test_room:foo".to_owned(),
        channel: "test_room".to_owned(),
        text: "text".to_owned().into_bytes(),
        sender: None,
    }));
    s2.do_send(api::Request::Message(api::Message {
        entity: "test_room:foo".to_owned(),
        channel: "test_room".to_owned(),
        text: "text".to_owned().into_bytes(),
        sender: None,
    }));

    sleep(Duration::from_millis(1)).await;

    let squash = |s: &Sink| -> Vec<_> {
        s.lock()
            .unwrap()
            .drain(..)
            .map(|ev| match ev {
                api::Event::Message(m) => m,
                _ => panic!("Something is not a Event::Message"),
            })
            .collect()
    };

    let v1 = squash(&sink1);

    assert_eq!(
        v1[0],
        api::Message {
            entity: "test_room:foo".to_owned(),
            channel: "test_room".to_owned(),
            text: "text".to_owned().into_bytes(),
            sender: NonZeroU32::new(10001),
        }
    );
    assert_eq!(
        v1[1],
        api::Message {
            entity: "test_room:foo".to_owned(),
            channel: "test_room".to_owned(),
            text: "text".to_owned().into_bytes(),
            sender: NonZeroU32::new(10002),
        }
    );
    assert_eq!(v1.len(), 2);

    let v2 = squash(&sink2);

    assert_eq!(v2.len(), 2);
    assert_eq!(
        v2[0],
        api::Message {
            entity: "test_room:foo".to_owned(),
            channel: "test_room".to_owned(),
            text: "text".to_owned().into_bytes(),
            sender: NonZeroU32::new(10001),
        }
    );
    assert_eq!(
        v2[1],
        api::Message {
            entity: "test_room:foo".to_owned(),
            channel: "test_room".to_owned(),
            text: "text".to_owned().into_bytes(),
            sender: NonZeroU32::new(10002),
        }
    );
}
