use std::num::NonZeroU32;

use actix::{Actor, Addr, AsyncContext, Context, Handler, Recipient};
use log::debug;

use super::connection::Close;
use super::room::{Join, Leave, Room};
use crate::api::{Event, Message, Request};
use crate::registry::{ROOMS, SESSIONS};

#[derive(Debug)]
pub struct Session {
    conn: Recipient<Event>,
    me: Option<NonZeroU32>,
    rooms: Vec<(String, Addr<Room>)>,
}

impl Actor for Session {
    type Context = Context<Self>;
}

/// I requested to do something
/// Sent from Connection
impl Handler<Request> for Session {
    type Result = ();

    fn handle(&mut self, req: Request, ctx: &mut Self::Context) {
        self.dispatch(req, ctx)
    }
}

/// I received a message
impl Handler<Message> for Session {
    type Result = ();

    fn handle(&mut self, msg: Message, _ctx: &mut Self::Context) {
        debug!(
            "Session {:?} received a message {:?}, forwarding to conn",
            self.me, msg
        );
        self.conn.do_send(Event::Message(msg));
    }
}

impl Handler<Close> for Session {
    type Result = ();

    fn handle(&mut self, _msg: Close, _ctx: &mut Self::Context) {
        if let Some(u) = self.me {
            self.rooms.drain(..).fold((), |_, (_, addr)| {
                addr.do_send(Leave(u));
            });
        }
    }
}

impl Session {
    pub fn new(conn: Recipient<Event>) -> Self {
        Session {
            conn,
            me: None,
            rooms: vec![],
        }
    }

    #[allow(dead_code)]
    pub fn new_logged_in(conn: Recipient<Event>, uid: u32) -> Self {
        // For tests
        Session {
            conn,
            me: NonZeroU32::new(uid),
            rooms: vec![],
        }
    }

    fn dispatch(&mut self, req: Request, ctx: &mut <Self as Actor>::Context) {
        match req {
            Request::Login { token: t } => self.handle_login(t, ctx),
            req => {
                if self.me.is_none() {
                    self.conn.do_send(Event::LoginRequired);
                    return;
                };
                match req {
                    Request::Message(m) => self.handle_message(m, ctx),
                    Request::Join { room } => self.handle_join(room, ctx),
                    Request::Leave { room } => self.handle_leave(room, ctx),
                    _ => unimplemented!(),
                }
            }
        }
    }

    fn handle_message(&self, mut msg: Message, _ctx: &mut <Self as Actor>::Context) {
        // if let Some(s) = SESSIONS.query(&msg.entity) {
        //     msg.sender = self.me.clone();
        //     debug!(
        //         "Session {:?} requested to send {:?}, forwarding to corresponding SESSION",
        //         self.me, msg,
        //     );
        //     s.do_send(msg);
        //     return;
        // }
        if let Some(r) = ROOMS.query(&msg.entity) {
            msg.sender = self.me;
            debug!(
                "Session {:?} requested to send {:?}, forwarding to corresponding ROOM",
                self.me, msg,
            );
            r.do_send(msg);
            return;
        }
        debug!("Undelivered message: {:?}", msg);
        self.conn.do_send(Event::Undelivered(msg));
    }

    fn handle_login(&mut self, token: String, ctx: &mut <Self as Actor>::Context) {
        // TODO: impl properly
        // let id = format!("User:{}", token);

        let uid = match self.me {
            Some(v) => v,
            None => {
                self.me = NonZeroU32::new(233);
                self.me.unwrap()
            }
        };

        SESSIONS.register(uid, &ctx.address());
        self.conn.do_send(Event::Success);
        debug!("Logged in as {:?}", self.me);
    }

    fn handle_join(&mut self, room_id: String, _ctx: &mut <Self as Actor>::Context) {
        debug!("Requested to join {:?}", room_id);
        if self.rooms.iter().any(|(id, _)| *id == room_id) {
            return;
        }

        let room = ROOMS.get(&room_id);
        room.do_send(Join(self.me.as_ref().unwrap().clone()));
        self.rooms.push((room_id.clone(), room));
        self.conn.do_send(Event::Success);
    }

    fn handle_leave(&mut self, room_id: String, _ctx: &mut <Self as Actor>::Context) {
        debug!("Requested to leave {:?}", room_id);

        if let Some((i, (_, addr))) = self
            .rooms
            .iter()
            .enumerate()
            .find(|(_, (id, _))| **id == room_id)
        {
            addr.do_send(Leave(self.me.as_ref().unwrap().clone()));
            self.rooms.remove(i);
            self.conn.do_send(Event::Success);
        }
    }
}
