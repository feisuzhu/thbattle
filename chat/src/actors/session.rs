use actix::{Actor, Addr, AsyncContext, Context, Handler, Recipient};
use log::{debug, info};

use super::connection::Close;
use super::room::{Join, Leave, Room};
use crate::api::{Event, Message, Request, User};
use crate::registry::{ROOMS, SESSIONS};

#[derive(Debug)]
pub struct Session {
    conn: Recipient<Event>,
    me: Option<User>,
    joined_rooms: Vec<(String, Addr<Room>)>,
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
        self.conn.do_send(Event::Message(msg)).unwrap();
    }
}

impl Handler<Close> for Session {
    type Result = ();

    fn handle(&mut self, _msg: Close, _ctx: &mut Self::Context) {
        let u = self.me.as_ref().unwrap().clone();
        self.joined_rooms
            .drain(..)
            .map(|(_, addr)| {
                addr.do_send(Leave(u.clone()));
            })
            .count();
    }
}

impl Session {
    pub fn new(conn: Recipient<Event>) -> Self {
        Session {
            conn,
            me: None,
            joined_rooms: vec![],
        }
    }

    fn dispatch(&mut self, req: Request, ctx: &mut <Self as Actor>::Context) {
        match req {
            Request::Login { token: t } => {
                if self.me.is_none() {
                    self.handle_login(t, ctx)
                }
            }
            req => {
                if self.me.is_none() {
                    self.conn.do_send(Event::LoginRequired).unwrap();
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
        if let Some(s) = SESSIONS.query(&msg.entity) {
            msg.sender = self.me.clone();
            debug!(
                "Session {:?} requested to send {:?}, forwarding to corresponding SESSION",
                self.me, msg,
            );
            s.do_send(msg);
            return;
        }
        if let Some(r) = ROOMS.query(&msg.entity) {
            msg.sender = self.me.clone();
            debug!(
                "Session {:?} requested to send {:?}, forwarding to corresponding ROOM",
                self.me, msg,
            );
            r.do_send(msg);
            return;
        }
        debug!("Undelivered message: {:?}", msg);
        self.conn.do_send(Event::Undelivered(msg)).unwrap();
    }

    fn handle_login(&mut self, token: String, ctx: &mut <Self as Actor>::Context) {
        // TODO: impl properly
        let id = format!("User:{}", token);

        SESSIONS.register(id.clone(), &ctx.address());
        self.me = Some(User { id, name: token });
        self.conn.do_send(Event::Success).unwrap();

        debug!("Logged in as {:?}", self.me);
    }

    fn handle_join(&mut self, room_id: String, _ctx: &mut <Self as Actor>::Context) {
        debug!("Requested to join {:?}", room_id);
        if self.joined_rooms.iter().any(|(id, _)| *id == room_id) {
            return;
        }

        let room = ROOMS.get(&room_id);
        room.do_send(Join(self.me.as_ref().unwrap().clone()));
        self.joined_rooms.push((room_id.clone(), room));
        self.conn.do_send(Event::Success).unwrap();
    }

    fn handle_leave(&mut self, room_id: String, _ctx: &mut <Self as Actor>::Context) {
        debug!("Requested to leave {:?}", room_id);

        if let Some((i, (_, addr))) = self
            .joined_rooms
            .iter()
            .enumerate()
            .find(|(_, (id, _))| **id == room_id)
        {
            addr.do_send(Leave(self.me.as_ref().unwrap().clone()));
            self.joined_rooms.remove(i);
            self.conn.do_send(Event::Success).unwrap();
        }
    }
}
