pub mod calling;
pub mod sms;

pub use self::calling::*;
pub use self::sms::*;

pub struct RawCommand(String);

impl From<RawCommand> for String {
    fn from(v: RawCommand) -> String {
        v.0
    }
}

pub struct GetSubscriberNumber;
impl From<GetSubscriberNumber> for String {
    fn from(_v: GetSubscriberNumber) -> String {
        "AT+CNUM".into()
    }
}
