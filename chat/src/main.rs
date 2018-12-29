#![feature(trait_alias)]

mod actors;
mod api;
mod registry;
mod util;

use actix_web::{http, server, App};

use crate::actors::Connection;

fn main() {
    util::init_log();
    // XXX http auth!
    server::new(|| App::new().route("/", http::Method::GET, Connection::handle))
        .bind("0.0.0.0:7777")
        .unwrap()
        .run();
}
