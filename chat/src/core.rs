use std::num::NonZeroU32;
use std::sync::Arc;

use actix::Addr;
use actix_web::{web, App, Error, HttpRequest, HttpResponse, HttpServer};
use actix_web_actors::ws;
use chashmap::CHashMap;

use crate::actors::{Connection, Room, Session};

#[derive(Debug, Default)]
pub struct ChatServerCore {
    pub backend: String,
    pub listen: String,
    pub sessions: CHashMap<NonZeroU32, Addr<Session>>,
    pub rooms: CHashMap<String, Addr<Room>>,
}

impl ChatServerCore {
    pub async fn serve(self: Arc<Self>) -> std::io::Result<()> {
        let me = self.clone();
        HttpServer::new(move || {
            App::new()
                .app_data(web::Data::new(me.clone()))
                .route("/", web::get().to(Self::handle))
        })
        .bind(&self.listen)?
        .run()
        .await
    }

    pub async fn handle(
        r: HttpRequest,
        s: web::Payload,
        me: web::Data<Arc<Self>>,
    ) -> Result<HttpResponse, Error> {
        ws::start(Connection::new((**me).clone()), &r, s)
    }
}
