pub struct ReadMessage(pub i32);
impl From<ReadMessage> for String {
    fn from(v: ReadMessage) -> String {
        format!("AT+CMGR={}", v.0)
    }
}

pub struct TakeMessage(pub i32);
impl From<TakeMessage> for String {
    fn from(v: TakeMessage) -> String {
        format!("AT+CMGRD={}", v.0)
    }
}

pub struct DeleteMessage(pub i32);
impl From<DeleteMessage> for String {
    fn from(v: DeleteMessage) -> String {
        format!("AT+CMGD={}", v.0)
    }
}

/* not working
pub enum BatchDeleteMessage {
    Read = 1,
    ReadAndSent = 2,
    ReadAndUnsent = 3,
    All = 4,
}
impl From<BatchDeleteMessage> for String {
    fn from(v: BatchDeleteMessage) -> String {
        format!("AT+CMGD=1,{}", v as i32)
    }
}

*/

pub enum SelectMessageFormat {
    PDU = 0,
    Text = 1,
}

impl From<SelectMessageFormat> for String {
    fn from(v: SelectMessageFormat) -> String {
        format!("AT+CMGF={}", v as i32)
    }
}

pub enum CNMIMode {
    Buffered = 0,
    DirectOrDiscard = 1,
    DirectOrBuffered = 2,
}

pub enum CNMIMessageType {
    NoIndication = 0,
    SendIndicator = 1,
    SendContent = 2,
    SendContentOnlyIfSmsDeliver = 3,
}

pub struct SetNewMessageIndication(pub CNMIMode, pub CNMIMessageType);

impl From<SetNewMessageIndication> for String {
    fn from(v: SetNewMessageIndication) -> String {
        format!("AT+CNMI={},{}", v.0 as i32, v.1 as i32)
    }
}

// AT+CMGS Send message
