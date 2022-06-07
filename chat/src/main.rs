mod actors;
mod api;
mod registry;
mod util;

use actix_web::{http, web, App, HttpServer};
use argparse::{ArgumentParser, Store};

use crate::actors::Connection;

pub struct AyaState {
    pub backend: String,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    util::init_log();

    let mut state = AyaState {
        backend: "http://localhost:8000/graphql-msgpack".to_string(),
    };

    {
        let mut parser = ArgumentParser::new();
        parser
            .refer(&mut state.backend)
            .add_option(&["--backend"], Store, "");
        parser.parse_args_or_exit();
    }

    HttpServer::new(|| App::new().route("/", web::get().to(Connection::handle)))
        .bind("0.0.0.0:7777")?
        .run()
        .await
}
