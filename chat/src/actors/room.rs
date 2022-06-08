use std::num::NonZeroU32;

#[allow(unused)]
use log::{debug, info};

use actix::prelude::*;

use crate::api::Message;
use crate::registry::{ROOMS, SESSIONS};

#[derive(Debug)]
pub struct Room {
    id: String,
    users: Vec<NonZeroU32>,
}

#[derive(Debug, Message)]
#[rtype(result = "()")]
pub struct Join(pub NonZeroU32);

#[derive(Debug, Message)]
#[rtype(result = "()")]
pub struct Leave(pub NonZeroU32);

impl Room {
    pub fn spawn(key: impl Into<String>) -> Addr<Self> {
        Self {
            id: key.into(),
            users: vec![],
        }
        .start()
    }
}

impl Actor for Room {
    type Context = Context<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        ROOMS.insert(self.id.clone(), ctx.address());
        debug!("Room {} started and registered", self.id);
    }
}

impl Handler<Join> for Room {
    type Result = ();
    fn handle(&mut self, msg: Join, _ctx: &mut Self::Context) {
        debug!("Room {} handled {} join", self.id, msg.0);
        self.users.push(msg.0);
    }
}

impl Handler<Leave> for Room {
    type Result = ();
    fn handle(&mut self, msg: Leave, ctx: &mut Self::Context) {
        debug!("Room {} handled {} leave", self.id, msg.0);
        if let Some(p) = self.users.iter().position(|u| *u == msg.0) {
            self.users.remove(p);
        }
        if self.users.len() == 0 {
            ROOMS.remove(&self.id);
            ctx.stop();
        }
    }
}

impl Handler<Message> for Room {
    type Result = ();
    fn handle(&mut self, msg: Message, _ctx: &mut Self::Context) {
        debug!(
            "Room {} received msg {:?}, forwarding to members",
            self.id, msg
        );
        let (good, bad): (Vec<_>, _) = self
            .users
            .iter()
            .enumerate()
            .map(|(i, u)| (i, SESSIONS.get(&u)))
            .partition(|(_, a)| a.is_some());

        good.into_iter()
            .fold((), |_, (_, a)| a.unwrap().do_send(msg.clone()));

        bad.into_iter().rfold((), |_, (i, _)| {
            self.users.remove(i);
        });
    }
}
