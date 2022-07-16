use std::num::NonZeroU32;
use std::sync::Arc;

use actix::ActorContext;
use actix::{Actor, Addr, AsyncContext, Context, Handler, Message, Recipient};
use anyhow::{anyhow, bail};
use log::debug;
use rmp_serde as rmps;
use serde_derive::Serialize;

use crate::actors::connection;
use crate::actors::room;
use crate::api;
use crate::core::ChatServerCore;

#[derive(Debug)]
pub struct Session {
    core: Arc<ChatServerCore>,
    conn: Recipient<api::Event>,
    me: Option<NonZeroU32>,
    rooms: Vec<(String, Addr<room::Room>)>,
}

impl Actor for Session {
    type Context = Context<Self>;

    fn stopped(&mut self, _ctx: &mut Self::Context) {
        if let Some(uid) = self.me {
            debug!("Session {} stopped, unregister", uid);
            self.core.sessions.remove(&uid);
        }
    }
}

macro_rules! login_required {
    ($self:ident) => {
        if $self.me.is_none() {
            $self.conn.do_send(api::Event::LoginRequired);
            return;
        };
    };
}

#[derive(Message)]
#[rtype(result = "()")]
struct Sending(api::Message);

/// I requested to do something
/// Sent from Connection
impl Handler<api::Request> for Session {
    type Result = ();

    fn handle(&mut self, req: api::Request, ctx: &mut Self::Context) {
        match req {
            api::Request::Login(v) => ctx.notify(v),
            api::Request::Join(v) => ctx.notify(v),
            api::Request::Leave(v) => ctx.notify(v),
            api::Request::Message(v) => ctx.notify(Sending(v)),
            api::Request::Kick(_v) => (),
        }
    }
}

impl Handler<connection::Close> for Session {
    type Result = ();

    fn handle(&mut self, _msg: connection::Close, ctx: &mut Self::Context) {
        ctx.stop();
        if let Some(u) = self.me {
            self.rooms.drain(..).fold((), |_, (_, addr)| {
                addr.do_send(room::Leave(u));
            });
        }
    }
}

impl Handler<api::Login> for Session {
    type Result = ();

    fn handle(&mut self, msg: api::Login, ctx: &mut Self::Context) {
        if let Some(uid) = self.me {
            self.core.sessions.insert(uid, ctx.address());
            self.conn.do_send(api::Event::Success);
            return;
        }

        match self.login(msg.token) {
            Ok(uid) => {
                self.me = Some(uid);
                self.conn.do_send(api::Event::Success);
                self.core.sessions.insert(uid, ctx.address());
                debug!("Logged in as {:?}", uid);
            }
            Err(e) => {
                debug!("Login failed: {:?}", e);
                self.conn.do_send(api::Event::Error(e.to_string()));
            }
        }
    }
}

impl Handler<api::Message> for Session {
    type Result = ();

    fn handle(&mut self, msg: api::Message, _ctx: &mut Self::Context) {
        debug!(
            "Session {:?} received a message {:?}, forwarding to conn",
            self.me, msg
        );
        self.conn.do_send(api::Event::Message(msg));
    }
}

impl Handler<Sending> for Session {
    type Result = ();

    fn handle(&mut self, sending: Sending, _ctx: &mut Self::Context) {
        login_required!(self);

        let mut msg = sending.0;

        // if let Some(s) = SESSIONS.query(&msg.entity) {
        //     msg.sender = self.me.clone();
        //     debug!(
        //         "Session {:?} requested to send {:?}, forwarding to corresponding SESSION",
        //         self.me, msg,
        //     );
        //     s.do_send(msg);
        //     return;
        // }
        if let Some(r) = self.core.rooms.get(&msg.entity) {
            msg.sender = self.me;
            debug!(
                "Session {:?} requested to send {:?}, forwarding to corresponding ROOM",
                self.me, msg,
            );
            r.do_send(msg);
            return;
        }
        debug!("Undelivered message: {:?}", msg);
        self.conn.do_send(api::Event::Undelivered(msg));
    }
}

impl Handler<api::Join> for Session {
    type Result = ();

    fn handle(&mut self, msg: api::Join, _ctx: &mut Self::Context) {
        login_required!(self);

        let room_id = msg.room;
        debug!("Requested to join {:?}", room_id);

        let room = match self.core.rooms.get(&room_id) {
            Some(r) => r,
            None => {
                self.core.rooms.insert(
                    room_id.clone(),
                    room::Room::spawn(self.core.clone(), &room_id),
                );
                self.core.rooms.get(&room_id).unwrap()
            }
        };
        room.do_send(room::Join(self.me.as_ref().unwrap().clone()));
        self.rooms.push((room_id.clone(), room.clone()));
        self.conn.do_send(api::Event::Success);
    }
}

impl Handler<api::Leave> for Session {
    type Result = ();

    fn handle(&mut self, msg: api::Leave, _ctx: &mut Self::Context) {
        login_required!(self);

        let room_id = msg.room;

        debug!("Requested to leave {:?}", room_id);

        if let Some((i, (_, addr))) = self
            .rooms
            .iter()
            .enumerate()
            .find(|(_, (id, _))| **id == room_id)
        {
            addr.do_send(room::Leave(self.me.as_ref().unwrap().clone()));
            self.rooms.remove(i);
            self.conn.do_send(api::Event::Success);
        }
    }
}

impl Session {
    pub fn new(core: Arc<ChatServerCore>, conn: Recipient<api::Event>) -> Self {
        Session {
            core,
            conn,
            me: None,
            rooms: vec![],
        }
    }

    #[allow(dead_code)]
    pub fn new_logged_in(core: Arc<ChatServerCore>, conn: Recipient<api::Event>, uid: u32) -> Self {
        // For tests
        Session {
            core,
            conn,
            me: NonZeroU32::new(uid),
            rooms: vec![],
        }
    }

    fn login(&self, token: String) -> anyhow::Result<NonZeroU32> {
        #[derive(Serialize)]
        struct LoginVariables {
            pub token: String,
        }

        let payload = rmps::to_vec_named(&api::GraphQLRequest {
            query: r#"
                    query Login($token: String!) {
                        login { token(token: $token) { player { id } } }
                    }
                "#
            .to_owned(),
            variables: LoginVariables { token },
            strip: "login.token.player.id".to_owned(),
        })?;

        let resp = match ureq::post(&self.core.backend)
            .set("Content-Type", "application/msgpack")
            .send_bytes(&payload)
        {
            Ok(r) => r,
            Err(ureq::Error::Status(_code, r)) => r,
            Err(e) => bail!(e),
        };

        let mut rst: api::GraphQLResponse<Option<NonZeroU32>> =
            rmps::from_read(resp.into_reader())?;

        if let Some(errors) = rst.errors.take() {
            if errors.len() > 0 {
                bail!("Backend GraphQL Error: {}", errors[0].message);
            }
        }

        let uid: Option<NonZeroU32> = rst.data;

        match uid {
            Some(uid) => Ok(uid),
            None => Err(anyhow!("Login failed")),
        }
    }
}
