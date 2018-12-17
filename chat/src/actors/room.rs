#[allow(unused)]
use log::{debug, info};

use actix::{Actor, Addr, AsyncContext, Context, Handler};
use actix_derive::Message;

use crate::api::{Message, User};
use crate::registry::{ROOMS, SESSIONS};
use crate::util::WeakRegistryDefault;

#[derive(Debug)]
pub struct Room {
    id: String,
    users: Vec<User>,
}

#[derive(Debug, Message)]
pub struct Join(pub User);

#[derive(Debug, Message)]
pub struct Leave(pub User);

impl Actor for Room {
    type Context = Context<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        ROOMS.register(self.id.clone(), &ctx.address());
        debug!("Room {} started and registered", self.id);
    }
}

impl WeakRegistryDefault<Self> for Room {
    fn new(key: &String) -> Addr<Self> {
        Self {
            id: key.clone(),
            users: vec![],
        }
        .start()
    }
}

impl Handler<Join> for Room {
    type Result = ();
    fn handle(&mut self, msg: Join, _ctx: &mut Self::Context) {
        debug!("Room {} handled {} join", self.id, msg.0.id);
        self.users.push(msg.0);
    }
}

impl Handler<Leave> for Room {
    type Result = ();
    fn handle(&mut self, msg: Leave, _ctx: &mut Self::Context) {
        debug!("Room {} handled {} leave", self.id, msg.0.id);
        if let Some(p) = self.users.iter().position(|u| u.id == msg.0.id) {
            self.users.remove(p);
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
            .map(|(i, u)| (i, SESSIONS.query(&u.id)))
            .partition(|(_, a)| a.is_some());

        // XXX: sooo many copies!
        good.into_iter()
            .map(|(_i, a)| a.unwrap().do_send(msg.clone()))
            .count();

        bad.into_iter()
            .rev()
            .map(|(i, _)| {
                self.users.remove(i);
            })
            .count();
    }
}
