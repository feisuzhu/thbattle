pub struct HangUp;
impl From<HangUp> for String {
    fn from(_v: HangUp) -> String {
        "AT+CHUP".into()
    }
}
