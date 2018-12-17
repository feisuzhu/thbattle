use std::time::Instant;

use actix::{Actor, ActorContext, Addr, AsyncContext, Handler, StreamHandler};
use actix_derive::Message;
use actix_web::ws;
use actix_web::{Error, HttpRequest, HttpResponse};
use serde_json as json;

use super::session::Session;
use crate::api::{Event, Request};

/*
const HEARTBEAT_DURATION: Duration = Duration::from_secs(10);
const TIMEOUT_DURATION: Duration = Duration::from_secs(30);
// */

#[derive(Debug)]
pub struct Connection {
    hb: Instant,
    session: Option<Addr<Session>>,
}

#[derive(Debug, Message)]
pub struct Close;

impl Actor for Connection {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        self.session = Some(Session::new(ctx.address().recipient()).start())
    }

    fn stopped(&mut self, _ctx: &mut Self::Context) {
        self.session.as_ref().unwrap().do_send(Close);
        self.session = None
    }
}

// TODO keepalive logics

impl StreamHandler<ws::Message, ws::ProtocolError> for Connection {
    fn handle(&mut self, msg: ws::Message, ctx: &mut Self::Context) {
        self.hb = Instant::now();
        match msg {
            ws::Message::Text(s) => match json::from_str::<Request>(&s) {
                Ok(r) => {
                    self.session.as_ref().unwrap().do_send(r);
                }
                Err(e) => {
                    ctx.text(json::to_string(&Event::Error(e.to_string())).unwrap());
                }
            },
            ws::Message::Ping(s) => {
                ctx.pong(&s);
            }
            ws::Message::Pong(_) => {}
            ws::Message::Close(_) => {
                // TODO
                ctx.stop();
            }
            ws::Message::Binary(_) => {} // TODO: support msgpack
        }
    }
}

impl Handler<Event> for Connection {
    type Result = ();
    fn handle(&mut self, msg: Event, ctx: &mut Self::Context) {
        ctx.text(json::to_string(&msg).unwrap())
    }
}

impl Connection {
    pub fn new() -> Self {
        Connection {
            hb: Instant::now(),
            session: None,
        }
    }

    pub fn handle(r: HttpRequest) -> Result<HttpResponse, Error> {
        ws::start(&r, Connection::new())
    }
}
