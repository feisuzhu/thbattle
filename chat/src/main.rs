mod actors;
mod api;
mod registry;
mod util;

use actix_web::{web, App, HttpServer};
use argparse::{ArgumentParser, Store};

use crate::actors::Connection;

// #[derive(Clone)]
// pub struct AyaState {
//     pub backend: String,
// }

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    util::init_log();

    let mut backend = "http://localhost:8000/graphql-msgpack".to_string();
    let mut bind = "0.0.0.0:7777".to_string();

    {
        let mut parser = ArgumentParser::new();
        parser
            .refer(&mut backend)
            .add_option(&["--backend"], Store, "");
        parser.refer(&mut bind).add_option(&["--bind"], Store, "");
        parser.parse_args_or_exit();
    }

    HttpServer::new(move || App::new().route("/", web::get().to(Connection::handle)))
        .bind(&bind)?
        .run()
        .await
}
