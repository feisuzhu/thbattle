pub mod connection;
pub mod room;
pub mod session;

pub use self::connection::Connection;
pub use self::room::Room;
pub use self::session::Session;

/*
 * Connection 负责 websocket 连接
 * Session 负责一个用户的登录和状态维护，以及接受消息
 * Room 负责管理房间的相关状态和消息转发
 */
