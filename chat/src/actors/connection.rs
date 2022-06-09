use std::sync::Arc;
use std::time::Instant;

use actix::prelude::*;
use actix_web_actors::ws;
use rmp_serde as rmps;
use serde_json as json;

use super::session::Session;
use crate::api::{Event, Request};
use crate::core::ChatServerCore;

/*
const HEARTBEAT_DURATION: Duration = Duration::from_secs(10);
const TIMEOUT_DURATION: Duration = Duration::from_secs(30);
// */

#[derive(Debug)]
pub struct Connection {
    core: Arc<ChatServerCore>,
    hb: Instant,
    binary: bool,
    session: Option<Addr<Session>>,
}

#[derive(Debug, Message)]
#[rtype(result = "()")]
pub struct Close;

impl Actor for Connection {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        self.session = Some(Session::new(self.core.clone(), ctx.address().recipient()).start())
    }

    fn stopped(&mut self, _ctx: &mut Self::Context) {
        self.session.as_ref().unwrap().do_send(Close);
        self.session = None
    }
}

// TODO keepalive logics

impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for Connection {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        self.hb = Instant::now();
        match msg {
            Ok(ws::Message::Text(s)) => match json::from_str::<Request>(&s) {
                Ok(r) => {
                    self.binary = false;
                    self.session.as_ref().unwrap().do_send(r);
                }
                Err(e) => {
                    ctx.text(json::to_string(&Event::Error(e.to_string())).unwrap());
                }
            },
            Ok(ws::Message::Binary(s)) => match rmps::from_slice::<Request>(s.as_ref()) {
                Ok(r) => {
                    self.binary = true;
                    self.session.as_ref().unwrap().do_send(r);
                }
                Err(e) => {
                    ctx.binary(rmps::to_vec_named(&Event::Error(e.to_string())).unwrap());
                }
            },
            Ok(ws::Message::Ping(s)) => {
                ctx.pong(&s);
            }
            Ok(ws::Message::Pong(_)) => {}
            Ok(ws::Message::Close(_)) => {
                // TODO
                ctx.stop();
            }
            _ => ctx.stop(),
        }
    }
}

impl Handler<Event> for Connection {
    type Result = ();
    fn handle(&mut self, msg: Event, ctx: &mut Self::Context) {
        match self.binary {
            true => ctx.binary(rmps::to_vec_named(&msg).unwrap()),
            false => ctx.text(json::to_string(&msg).unwrap()),
        }
    }
}

impl Connection {
    pub fn new(core: Arc<ChatServerCore>) -> Self {
        Connection {
            core: core,
            hb: Instant::now(),
            binary: true,
            session: None,
        }
    }
}
