#![feature(bind_by_move_pattern_guards)]

use log::debug;
use std::sync::{Arc, Mutex};

use actix::{Actor, Context, Handler};

use aya::actors::Session;
use aya::api::{Event, Message, Request, User};

mod common;

type Sink = Arc<Mutex<Vec<Event>>>;

struct EventSink {
    sink: Sink,
}

impl Actor for EventSink {
    type Context = Context<Self>;
}

impl Handler<Event> for EventSink {
    type Result = ();
    fn handle(&mut self, ev: Event, _ctx: &mut Self::Context) {
        self.sink.lock().unwrap().push(ev);
        debug!("EventSink received something, put it in sink");
    }
}

impl EventSink {
    fn new(sink: Sink) -> EventSink {
        EventSink { sink }
    }
}

#[test]
fn test_pm() {
    common::init_log();

    actix::System::run(|| {
        let sink: Sink = Arc::new(Mutex::new(vec![]));

        let s1 = Session::new(EventSink::new(sink.clone()).start().recipient()).start();
        let s2 = Session::new(EventSink::new(sink.clone()).start().recipient()).start();

        s1.do_send(Request::Login {
            token: "test_pm:s1".to_owned(),
        });
        s2.do_send(Request::Login {
            token: "test_pm:s2".to_owned(),
        });

        common::run_later((sink, s1, s2))
            .with(|(s, _, _)| {
                assert_eq!(
                    vec![Event::Success, Event::Success],
                    s.lock().unwrap().drain(..).collect::<Vec<_>>(),
                );
            })
            .with(|(_, s1, _)| {
                s1.do_send(Request::Message(Message {
                    entity: "User:test_pm:s2".to_owned(),
                    channel: "test_pm".to_owned(),
                    text: "text".to_owned(),
                    sender: None,
                }))
            })
            .with(|(sink, _, _)| {
                let mut s = sink.lock().unwrap();

                assert_eq!(s.len(), 1);
                let ev = s.pop().unwrap();
                match ev {
                    Event::Message(m) => {
                        let tp = (&m.entity[..], &m.channel[..], &m.text[..]);
                        assert_eq!(tp, ("User:test_pm:s2", "test_pm", "text"));
                        match m.sender {
                            Some(User { id, .. }) if &id[..] == "User:test_pm:s1" => (),
                            _ => panic!("Unexpected user id!"),
                        }
                    }
                    a => panic!("Not a message: {:?}!", a),
                }
            })
            .with(|_| actix::System::current().stop())
            .fire();
    });
}

#[test]
fn test_room() {
    common::init_log();

    actix::System::run(|| {
        let sink1: Sink = Arc::new(Mutex::new(vec![]));
        let sink2: Sink = Arc::new(Mutex::new(vec![]));

        let s1 = Session::new(EventSink::new(sink1.clone()).start().recipient()).start();
        let s2 = Session::new(EventSink::new(sink2.clone()).start().recipient()).start();

        s1.do_send(Request::Login {
            token: "test_room:s1".to_owned(),
        });
        s2.do_send(Request::Login {
            token: "test_room:s2".to_owned(),
        });

        s1.do_send(Request::Join {
            room: "test_room:foo".to_owned(),
        });
        s2.do_send(Request::Join {
            room: "test_room:foo".to_owned(),
        });

        common::run_later((sink1, sink2, s1, s2))
            .with(|(n1, n2, _, _)| {
                assert_eq!(
                    vec![Event::Success, Event::Success],
                    n1.lock().unwrap().drain(..).collect::<Vec<_>>(),
                );
                assert_eq!(
                    vec![Event::Success, Event::Success],
                    n2.lock().unwrap().drain(..).collect::<Vec<_>>(),
                );
            })
            .with(|(_, _, s1, s2)| {
                s1.do_send(Request::Message(Message {
                    entity: "test_room:foo".to_owned(),
                    channel: "test_room".to_owned(),
                    text: "text".to_owned(),
                    sender: None,
                }));
                s2.do_send(Request::Message(Message {
                    entity: "test_room:foo".to_owned(),
                    channel: "test_room".to_owned(),
                    text: "text".to_owned(),
                    sender: None,
                }));
            })
            .with(|(n1, n2, _, _)| {
                let squash = |s: &mut Sink| -> Vec<_> {
                    s.lock()
                        .unwrap()
                        .drain(..)
                        .map(|ev| match ev {
                            Event::Message(m) => m,
                            _ => panic!("Something is not a Event::Message"),
                        })
                        .map(|m| match m.sender {
                            Some(User { id, .. }) => vec![m.entity, m.channel, m.text, id],
                            _ => panic!("Can't match m.sender!"),
                        })
                        .collect()
                };

                let v1 = squash(n1);
                assert_eq!(v1.len(), 2);
                assert_eq!(
                    v1[0],
                    vec!["test_room:foo", "test_room", "text", "User:test_room:s1"]
                        .into_iter()
                        .map(|v| v.to_owned())
                        .collect::<Vec<_>>()
                );
                assert_eq!(
                    v1[1],
                    vec!["test_room:foo", "test_room", "text", "User:test_room:s2"]
                        .into_iter()
                        .map(|v| v.to_owned())
                        .collect::<Vec<_>>()
                );

                let v2 = squash(n2);
                assert_eq!(v2.len(), 2);
                assert_eq!(
                    v2[0],
                    vec!["test_room:foo", "test_room", "text", "User:test_room:s1"]
                        .into_iter()
                        .map(|v| v.to_owned())
                        .collect::<Vec<_>>()
                );
                assert_eq!(
                    v2[1],
                    vec!["test_room:foo", "test_room", "text", "User:test_room:s2"]
                        .into_iter()
                        .map(|v| v.to_owned())
                        .collect::<Vec<_>>()
                );
            })
            .with(|_| actix::System::current().stop())
            .fire();
    });
}